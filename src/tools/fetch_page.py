from __future__ import annotations

import asyncio
import json
import logging
import random
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from src.config import get_fetch_config, FetchConfig
from src.errors import (
    MCPToolError,
    FetchBlockedError,
    FetchConnectionError,
    FetchHTTPError,
    FetchParseError,
    FetchTimeoutError,
    FetchURLError,
)
from src.models import (
    FetchRequest,
    FetchResponse,
    LinkSummary,
    StructuredData,
    TableData,
    ToolErrorResponse,
)
from src.utils.readability import extract_readability_content
from src.utils.truncation import smart_truncate
from src.utils.formatting import format_tool_error

logger = logging.getLogger(__name__)

try:
    from curl_cffi.requests import AsyncSession
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False
    logger.warning("curl_cffi not available, will use httpx fallback")

try:
    import nodriver as uc
    NODRIVER_AVAILABLE = True
except (ImportError, SyntaxError) as exc:
    NODRIVER_AVAILABLE = False
    logger.warning("nodriver not available, browser fallback disabled: %s", exc)

_BROWSER_SEMAPHORE: asyncio.Semaphore | None = None

def _get_browser_semaphore() -> asyncio.Semaphore:
    global _BROWSER_SEMAPHORE
    if _BROWSER_SEMAPHORE is None:
        config = get_fetch_config()
        _BROWSER_SEMAPHORE = asyncio.Semaphore(config.max_concurrent_browsers)
    return _BROWSER_SEMAPHORE

USER_AGENTS: list[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
]

CHROME_IMPERSONATIONS = ["chrome", "chrome110", "chrome120", "chrome136"]

_DISCARD_STATUS_CODES = frozenset({403, 429})

def _should_discard_status(sc: int) -> bool:
    """Return True if the status code should cause html_content to be discarded for fallback."""
    return sc in _DISCARD_STATUS_CODES or sc >= 500

def _extract_tables(soup: BeautifulSoup) -> list[TableData]:
    tables: list[TableData] = []

    for table in soup.find_all("table"):
        headers: list[str] = []
        rows: list[list[str]] = []

        thead = table.find("thead")
        if thead:
            for tr in thead.find_all("tr"):
                cells = [th.get_text(strip=True) for th in tr.find_all(["th", "td"])]
                if cells:
                    headers = cells
                    break

        tbody = table.find("tbody") or table
        all_rows = tbody.find_all("tr")

        if not headers and all_rows:
            first_row = all_rows[0]
            cells = [td.get_text(strip=True) for td in first_row.find_all(["th", "td"])]
            if cells:
                headers = cells
                all_rows = all_rows[1:]

        for tr in all_rows:
            cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if cells:
                rows.append(cells)

        if headers or rows:
            tables.append(TableData(headers=headers, rows=rows))

    return tables

def _extract_structured_data(soup: BeautifulSoup) -> list[StructuredData]:
    items: list[StructuredData] = []

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            raw = script.string or ""
            data = json.loads(raw)

            sd_type = ""
            if isinstance(data, dict):
                sd_type = data.get("@type", "")
            elif isinstance(data, list) and data:
                sd_type = data[0].get("@type", "") if isinstance(data[0], dict) else "list"

            items.append(StructuredData(type=sd_type, data=data))
        except (json.JSONDecodeError, TypeError, AttributeError) as exc:
            logger.debug("Failed to parse JSON-LD block: %s", exc)
            continue

    return items

def _extract_links_summary(soup: BeautifulSoup, source_url: str) -> LinkSummary:
    source_domain = urlparse(source_url).netloc.lower()
    internal = 0
    external = 0

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].strip()
        if not href or href.startswith("#") or href.startswith("javascript:"):
            continue

        if href.startswith("http"):
            link_domain = urlparse(href).netloc.lower()
            if link_domain == source_domain:
                internal += 1
            else:
                external += 1

    return LinkSummary(internal_count=internal, external_count=external)

def _format_fetch_response(response: FetchResponse) -> str:
    lines: list[str] = []

    lines.append(f"# Page Content: {response.url}")
    lines.append("")

    if response.title:
        lines.append(f"**Title:** {response.title}")
    if response.description:
        lines.append(f"**Description:** {response.description}")
    lines.append("")

    if response.headings:
        lines.append("## Headings")
        for h in response.headings:
            level = h.get("level", "h").upper()
            text = h.get("text", "")
            if text:
                lines.append(f"- {level}: {text}")
        lines.append("")

    if response.structured_data:
        lines.append("## Structured Data (JSON-LD)")
        for sd in response.structured_data:
            if sd.type:
                lines.append(f"### Type: `{sd.type}`")
            lines.append("```json")
            lines.append(json.dumps(sd.data, indent=2, ensure_ascii=False))
            lines.append("```")
            lines.append("")

    if response.tables:
        for idx, table in enumerate(response.tables, start=1):
            lines.append(f"## Table {idx}")
            if table.headers:
                lines.append("| " + " | ".join(table.headers) + " |")
                lines.append("| " + " | ".join("---" for _ in table.headers) + " |")
            for row in table.rows:
                padded = row + [""] * max(0, (len(table.headers) - len(row)) if table.headers else 0)
                lines.append("| " + " | ".join(padded) + " |")
            lines.append("")

    if response.content:
        lines.append("## Content")
        lines.append(response.content)
        lines.append("")

    if response.links.internal_count > 0 or response.links.external_count > 0:
        lines.append("## Links Summary")
        lines.append(f"- Internal links: {response.links.internal_count}")
        lines.append(f"- External links: {response.links.external_count}")
        lines.append("")

    if response.was_truncated:
        lines.append("> ⚠️ Content was truncated to fit the context window.")
        lines.append("")

    return "\n".join(lines)



async def _fetch_with_curl_cffi(url: str, config: FetchConfig) -> tuple[str, int, str]:
    if not CURL_CFFI_AVAILABLE:
        raise ImportError("curl_cffi not available")

    async with AsyncSession(impersonate=random.choice(CHROME_IMPERSONATIONS)) as s:
        response = await s.get(
            url,
            timeout=config.timeout,
            follow_redirects=True,
        )
    
        return response.text, response.status_code, response.headers.get("content-type", "")

async def _fetch_with_nodriver(url: str, config: FetchConfig) -> tuple[str, int, str]:
    if not NODRIVER_AVAILABLE:
        raise ImportError("nodriver not available")

    semaphore = _get_browser_semaphore()
    
    async with semaphore:
        browser = None
        try:
            browser = await uc.start(headless=True)
            tab = await browser.get(url)
            
            await tab.wait_for("dom_content_loaded", timeout=config.timeout)
            
            html_content = await tab.get_content()
            
            try:
                status = await tab.evaluate("window.statusCode || 200")
                if not status or status == 0:
                    status = 200
            except Exception:
                status = 200
                
            return html_content, int(status), "text/html"
        finally:
            if browser:
                try:
                    await browser.stop()
                except Exception:
                    pass

async def _fetch_with_httpx_fallback(url: str, config: FetchConfig) -> tuple[str, int, str]:
    ua = random.choice(USER_AGENTS)
    headers = {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    
    async with httpx.AsyncClient(timeout=config.timeout, follow_redirects=True) as client:
        response = await client.get(url, headers=headers)
        return response.text, response.status_code, response.headers.get("content-type", "")


async def _build_fetch_response(request: FetchRequest, config: FetchConfig) -> FetchResponse:
    """Core fetch logic. Returns a FetchResponse. Called by both fetch_page() and _fetch_page_structured()."""
    url_str = str(request.url)
    parsed = urlparse(url_str)

    if not parsed.scheme or not parsed.netloc:
        raise ValueError(
            f"Invalid URL '{url_str}'. Must include http:// or https:// and a valid domain."
        )

    token_budget = request.max_tokens if request.max_tokens else config.token_budget
    html_content = None
    status_code = 200
    content_type = "text/html"
    fetch_method = "unknown"

    if CURL_CFFI_AVAILABLE:
        try:
            logger.info("Attempting fetch with curl_cffi: %s", url_str)
            html_content, status_code, content_type = await _fetch_with_curl_cffi(url_str, config)
            fetch_method = "curl_cffi"
            if _should_discard_status(status_code):
                logger.warning("curl_cffi got status %d for %s, discarding", status_code, url_str)
                html_content = None
        except Exception as exc:
            logger.warning("curl_cffi failed for %s: %s", url_str, exc)
            html_content = None

    if html_content is None and NODRIVER_AVAILABLE:
        try:
            logger.info("Attempting fetch with nodriver: %s", url_str)
            html_content, status_code, content_type = await _fetch_with_nodriver(url_str, config)
            fetch_method = "nodriver"
            if _should_discard_status(status_code):
                logger.warning("nodriver got status %d for %s, discarding", status_code, url_str)
                html_content = None
        except Exception as exc:
            logger.warning("nodriver failed for %s: %s", url_str, exc)
            html_content = None

    if html_content is None:
        logger.info("Attempting fetch with httpx fallback: %s", url_str)
        try:
            html_content, status_code, content_type = await _fetch_with_httpx_fallback(url_str, config)
            fetch_method = "httpx"
        except Exception as exc:
            if isinstance(exc, httpx.TimeoutException):
                raise FetchTimeoutError(f"Timeout fetching {url_str}") from exc
            raise FetchConnectionError(f"Unable to connect to {url_str}") from exc

    logger.info("Fetch succeeded with %s: %s (status=%d)", fetch_method, url_str, status_code)

    # Check final status code after all fallback attempts
    if status_code in (403, 429):
        raise FetchBlockedError(f"Blocked by {url_str} (HTTP {status_code})")
    if status_code >= 400:
        raise FetchHTTPError(f"HTTP {status_code} from {url_str}", status_code=status_code)

    if "text/html" not in content_type and "application/xhtml" not in content_type:
        raw_text = html_content
        truncated_text, was_trunc = smart_truncate(raw_text, token_budget)
        lines = [
            f"# Content from: {url_str}",
            f"**Method:** {fetch_method}",
            f"**Content-Type:** {content_type}",
            f"**Status:** {status_code}",
            "",
            "```",
            truncated_text,
            "```",
        ]
        if was_trunc:
            lines.append("")
            lines.append("> ⚠️ Content was truncated to fit the context window.")
        return FetchResponse(
            url=url_str,
            status_code=status_code,
            content_type=content_type,
            title="",
            description="",
            headings=[],
            content=truncated_text,
            tables=[],
            structured_data=[],
            links=LinkSummary(),
            was_truncated=was_trunc,
            markdown="\n".join(lines),
        )

    try:
        soup = BeautifulSoup(html_content, "html.parser")
    except Exception as exc:
        logger.error("Failed to parse HTML from %s: %s", url_str, exc)
        raise FetchParseError(f"Failed to parse HTML from {url_str}") from exc

    readability_result = extract_readability_content(
        html_content,
        source_url=url_str,
        max_length=config.max_content_length,
    )

    tables = _extract_tables(soup)
    structured_data = _extract_structured_data(soup)
    links = _extract_links_summary(soup, url_str)

    content = readability_result["content"]
    truncated_content, was_truncated = smart_truncate(
        content,
        token_budget=token_budget,
    )

    fetch_response = FetchResponse(
        url=url_str,
        status_code=status_code,
        content_type=content_type,
        title=readability_result["title"],
        description=readability_result["description"],
        headings=readability_result["headings"],
        content=truncated_content,
        tables=tables,
        structured_data=structured_data,
        links=links,
        was_truncated=was_truncated or bool(readability_result["was_truncated"]),
        markdown="",
    )
    fetch_response.markdown = _format_fetch_response(fetch_response)
    fetch_response.markdown = f"> **Fetch method:** {fetch_method}\n\n" + fetch_response.markdown

    logger.info(
        "fetch_page complete: url=%r, method=%s, title=%r, content_len=%d, truncated=%s",
        url_str,
        fetch_method,
        fetch_response.title,
        len(fetch_response.content),
        fetch_response.was_truncated,
    )

    return fetch_response


async def fetch_page(url: str, max_tokens: int | None = None) -> str:
    logger.info("fetch_page called: url=%r, max_tokens=%r", url, max_tokens)
    config = get_fetch_config()
    token_budget = max_tokens or config.token_budget
    try:
        request = FetchRequest(url=url, max_tokens=token_budget)
    except Exception as exc:
        return f"## Invalid URL\n{exc}"
    try:
        response = await _build_fetch_response(request, config)
        return response.markdown
    except MCPToolError as exc:
        return format_tool_error(
            error_code=exc.error_code,
            message=str(exc),
            retry_guidance=exc.retry_guidance,
        )
    except Exception as exc:
        logger.error("fetch_page error for %s: %s", url, exc, exc_info=True)
        return f"## Fetch Error\n{exc}"


async def _fetch_page_structured(url: str, max_tokens: int | None = None) -> FetchResponse:
    """Internal-only. Returns FetchResponse directly. Used by get_contents to skip markdown parsing.
    Raises MCPToolError on failure.
    """
    config = get_fetch_config()
    token_budget = max_tokens or config.token_budget
    try:
        request = FetchRequest(url=url, max_tokens=token_budget)
    except Exception as exc:
        raise FetchURLError(f"Invalid URL '{url}': {exc}") from exc
    try:
        return await _build_fetch_response(request, config)
    except ValueError as exc:
        raise FetchURLError(str(exc)) from exc
