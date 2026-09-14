from __future__ import annotations

from bs4 import BeautifulSoup

INTERACTIVE_TAGS = {"a", "button", "input", "select", "textarea"}
INTERACTIVE_ROLES = {"button", "link", "checkbox", "radio", "textbox", "menuitem", "tab"}


def parse_interactive_snapshot(html: str, title: str = "", url: str = "") -> str:
    soup = BeautifulSoup(html, "html.parser")
    lines: list[str] = []

    lines.append(f"# Page Snapshot: {title or 'Untitled Page'}")
    if url:
        lines.append(f"**URL:** {url}")
    lines.append("")
    lines.append("## Interactive Elements")

    count = 0
    for el in soup.find_all(True):
        tag_name = el.name.lower()
        role = el.get("role", "").lower()
        is_clickable = el.get("onclick") or el.get("cursor") == "pointer"

        if tag_name not in INTERACTIVE_TAGS and role not in INTERACTIVE_ROLES and not is_clickable:
            continue

        count += 1
        attrs = []
        if el.get("id"):
            attrs.append(f'id="{el["id"]}"')
        if el.get("name"):
            attrs.append(f'name="{el["name"]}"')
        if el.get("type"):
            attrs.append(f'type="{el["type"]}"')
        if el.get("class"):
            classes = " ".join(el["class"]) if isinstance(el["class"], list) else str(el["class"])
            attrs.append(f'class="{classes}"')
        if el.get("href"):
            attrs.append(f'href="{el["href"]}"')

        attr_str = " " + " ".join(attrs) if attrs else ""
        text = el.get_text(strip=True)
        if len(text) > 60:
            text = text[:57] + "..."

        if tag_name in ("input", "img"):
            label_val = el.get("placeholder", "") or el.get("aria-label", "") or el.get("value", "")
            label = f' Label: "{label_val}"' if label_val else ""
            lines.append(f"- [{count}] <{tag_name}{attr_str}>{label}")
        else:
            lines.append(f"- [{count}] <{tag_name}{attr_str}>{text}</{tag_name}>")

    if count == 0:
        lines.append("_No interactive elements found on page._")

    return "\n".join(lines)
