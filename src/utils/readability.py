from __future__ import annotations

import logging
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

logger = logging.getLogger(__name__)

NEGATIVE_PATTERNS = re.compile(
    r"(nav|footer|header|sidebar|ad|comment|menu|share|social|cookie|popup|modal|"
    r"breadcrumb|pagination|related|recommended|trending|newsletter|subscription|"
    r"widget|banner|promo|overlay|dialog|toast|tooltip|cookie-consent|"
    r"skip-link|skip-navigation|screen-reader-text)",
    re.IGNORECASE,
)

POSITIVE_PATTERNS = re.compile(
    r"(article|main|content|post|entry|story|body|page|document|reading|"
    r"reader|prose|text|description|summary|detail|section-content|"
    r"article-body|story-body|entry-content|post-content|page-content)",
    re.IGNORECASE,
)

REMOVE_ALWAYS = frozenset(
    {
        "script",
        "style",
        "noscript",
        "iframe",
        "svg",
        "canvas",
        "object",
        "embed",
        "form",
        "button",
        "select",
        "input",
        "textarea",
        "nav",
        "header",
        "footer",
        "aside",
    }
)

CLEAN_KEEP = frozenset(
    {
        "p",
        "br",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "ul",
        "ol",
        "li",
        "dl",
        "dt",
        "dd",
        "table",
        "thead",
        "tbody",
        "tr",
        "th",
        "td",
        "a",
        "strong",
        "em",
        "b",
        "i",
        "u",
        "blockquote",
        "pre",
        "code",
        "figure",
        "figcaption",
        "img",
        "picture",
        "source",
        "div",
        "span",
        "section",
        "article",
        "main",
        "details",
        "summary",
    }
)

def _score_element(element: Tag) -> float:
    score = 0.0

    class_id = ""
    if isinstance(element, Tag):
        classes = element.get("class", [])
        if isinstance(classes, list):
            classes = " ".join(classes)
        
        class_id = f"{element.get('id', '')} {classes} {element.get('name', '')}"

    if NEGATIVE_PATTERNS.search(class_id):
        score -= 25.0

    if POSITIVE_PATTERNS.search(class_id):
        score += 25.0

    text = element.get_text(strip=True)
    text_len = len(text)
    tag_name = element.name if isinstance(element, Tag) else ""

    if text_len > 0:
        if tag_name == "p" and text_len > 50:
            score += 5.0

        link_text_len = 0
        if isinstance(element, Tag):
            for a in element.find_all("a", recursive=False):
                link_text_len += len(a.get_text(strip=True))

        if text_len > 0:
            link_ratio = link_text_len / text_len
            if link_ratio > 0.5:
                score -= 10.0  # High link density = likely nav or ad

    return score

def _find_content_root(soup: BeautifulSoup) -> Tag | None:
    for tag_name in ("main", "article"):
        for elem in soup.find_all(tag_name):
            score = _score_element(elem)
            if score >= 0:
                return elem

    best_div: tuple[float, Tag | None] = (0.0, None)
    for div in soup.find_all("div"):
        score = _score_element(div)
        if score > best_div[0]:
            best_div = (score, div)

    if best_div[1] is not None:
        return best_div[1]

    return soup.find("body")

def _clean_element(element: Tag, source_url: str | None = None) -> None:
    if not isinstance(element, Tag):
        return

    for comment in element.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    for child in list(element.children):
        if isinstance(child, Tag) and child.name in REMOVE_ALWAYS:
            child.decompose()
        elif isinstance(child, Tag):
            _clean_element(child, source_url)

    if source_url and element.name == "img":
        src = element.get("src", "")
        if src and not src.startswith(("http://", "https://", "data:")):
            parsed_source = urlparse(source_url)
            base = f"{parsed_source.scheme}://{parsed_source.netloc}"
            if src.startswith("/"):
                element["src"] = f"{base}{src}"
            else:
                element["src"] = f"{base}/{src}"

def _element_to_markdown(element: Tag | NavigableString, depth: int = 0) -> str:
    if isinstance(element, NavigableString):
        text = str(element).strip()
        return text if text else ""

    if not isinstance(element, Tag):
        return ""

    tag = element.name or ""

    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        level = int(tag[1])
        adjusted = min(level + depth, 4)
        text = element.get_text(strip=True)
        if text:
            return f"{'#' * adjusted} {text}\n"
        return ""

    if tag == "p":
        text = _inline_content(element)
        return f"{text}\n" if text else ""

    if tag == "br":
        return "\n"

    if tag in ("ul", "ol"):
        return _list_to_markdown(element, ordered=(tag == "ol"))

    if tag == "li":
        text = _inline_content(element)
        return f"- {text}\n" if text else ""

    if tag == "blockquote":
        text = element.get_text(strip=True)
        if text:
            lines = text.split("\n")
            quoted = "\n".join(f"> {line}" for line in lines)
            return f"{quoted}\n"
        return ""

    if tag == "pre":
        code_elem = element.find("code")
        code_text = (code_elem or element).get_text()
        if code_text.strip():
            return f"```\n{code_text.strip()}\n```\n"
        return ""

    if tag == "code":
        text = element.get_text()
        if "\n" not in text:
            return f"`{text}`"
        return f"```\n{text.strip()}\n```\n"

    if tag == "table":
        return _table_to_markdown(element)

    if tag == "img":
        alt = element.get("alt", "image")
        src = element.get("src", "")
        if src:
            return f"![{alt}]({src})\n"
        return ""

    if tag == "hr":
        return "\n---\n"

    parts: list[str] = []
    for child in element.children:
        result = _element_to_markdown(child, depth)
        if result:
            parts.append(result)

    if tag in ("div", "section", "article", "main", "body"):
        return "\n".join(parts) + "\n"

    return element.get_text(strip=True)

def _inline_content(element: Tag) -> str:
    parts: list[str] = []
    for child in element.children:
        if isinstance(child, NavigableString):
            parts.append(str(child))
        elif isinstance(child, Tag):
            if child.name == "strong" or child.name == "b":
                text = child.get_text(strip=True)
                parts.append(f"**{text}**" if text else "")
            elif child.name == "em" or child.name == "i":
                text = child.get_text(strip=True)
                parts.append(f"*{text}*" if text else "")
            elif child.name == "code":
                text = child.get_text()
                parts.append(f"`{text}`" if "\n" not in text else "")
            elif child.name == "a":
                text = child.get_text(strip=True)
                href = child.get("href", "")
                if href and text:
                    parts.append(f"[{text}]({href})")
                elif text:
                    parts.append(text)
            elif child.name == "br":
                parts.append("\n")
            elif child.name == "img":
                alt = child.get("alt", "image")
                src = child.get("src", "")
                if src:
                    parts.append(f"![{alt}]({src})")
            else:
                inner = _inline_content(child)
                parts.append(inner)

    return "".join(parts).strip()

def _list_to_markdown(element: Tag, ordered: bool = False) -> str:
    lines: list[str] = []
    idx = 1
    for child in element.children:
        if isinstance(child, Tag) and child.name == "li":
            text = _inline_content(child)
            if text:
                if ordered:
                    lines.append(f"{idx}. {text}")
                else:
                    lines.append(f"- {text}")
                idx += 1

    return "\n".join(lines) + "\n" if lines else ""

def _table_to_markdown(element: Tag) -> str:
    rows_data: list[list[str]] = []
    has_header = False

    thead = element.find("thead")
    if thead:
        for tr in thead.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all(["th", "td"])]
            if cells:
                rows_data.append(cells)
                has_header = True

    tbody = element.find("tbody") or element
    for tr in tbody.find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
        if cells:
            rows_data.append(cells)

    if not rows_data:
        return ""

    if not has_header and rows_data:
        has_header = True

    lines: list[str] = []
    if has_header and rows_data:
        headers = rows_data[0]
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join("---" for _ in headers) + " |")
        for row in rows_data[1:]:
            padded = row + [""] * (len(headers) - len(row))
            lines.append("| " + " | ".join(padded[: len(headers)]) + " |")

    return "\n".join(lines) + "\n" if lines else ""

def extract_readability_content(
    html: str,
    source_url: str | None = None,
    max_length: int = 10000,
) -> dict[str, str | list | bool]:
    try:
        import trafilatura
        from trafilatura import extract_metadata as traf_extract_metadata

        # --- trafilatura primary extraction ---
        traf_content = trafilatura.extract(
            html,
            output_format="markdown",
            include_comments=False,
            favor_recall=True,
            url=source_url,
        )

        # Metadata (title, author, date)
        meta = traf_extract_metadata(html, default_url=source_url or "")
        traf_title: str = (meta.title or "") if meta else ""
        traf_author: str = (meta.author or "") if meta else ""
        traf_date: str = (meta.date or "") if meta else ""

        # Content-language: read from <html lang="..."> via BeautifulSoup
        traf_lang = ""
        try:
            soup_lang = BeautifulSoup(html, "html.parser")
            html_tag = soup_lang.find("html")
            if html_tag and isinstance(html_tag, Tag):
                lang_attr = html_tag.get("lang", "")
                if lang_attr:
                    traf_lang = str(lang_attr).split("-")[0].lower()
        except Exception:
            pass

    except ImportError:
        traf_content = None
        traf_title = ""
        traf_author = ""
        traf_date = ""
        traf_lang = ""

    # --- Soup fallback pipeline (also used for headings/description/tables) ---
    soup = BeautifulSoup(html, "html.parser")

    title = traf_title
    if not title:
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)

    description = ""
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc:
        description = meta_desc.get("content", "")

    headings: list[dict[str, str]] = []
    for tag_name in ("h1", "h2", "h3"):
        for h in soup.find_all(tag_name):
            text = h.get_text(strip=True)
            if text:
                headings.append({"level": tag_name, "text": text})

    if traf_content:
        content = traf_content
    else:
        # soup-based extraction fallback
        content_root = _find_content_root(soup)
        if content_root:
            _clean_element(content_root, source_url)
            content = _element_to_markdown(content_root)
        else:
            content = soup.get_text(separator="\n", strip=True)

    content = re.sub(r"\n{3,}", "\n\n", content)
    content = content.strip()

    was_truncated = False
    if len(content) > max_length:
        content = content[:max_length]
        last_break = content.rfind("\n\n")
        if last_break > max_length * 0.8:
            content = content[:last_break]
        content += "\n\n---\n*Content truncated to fit context window.*"
        was_truncated = True

    return {
        "title": title,
        "description": description,
        "content": content,
        "headings": headings,
        "was_truncated": was_truncated,
        "content_language": traf_lang,
        "author": traf_author,
        "published_date": traf_date,
    }
