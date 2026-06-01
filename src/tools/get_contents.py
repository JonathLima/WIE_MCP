from __future__ import annotations

import asyncio
import logging
from typing import Optional

from src.tools.fetch_page import _fetch_page_structured
from src.utils.highlights import extract_highlights
from src.utils.summarizer import extractive_summary

logger = logging.getLogger(__name__)


async def _fetch_single_url(
    url: str,
    highlight_query: Optional[str],
    highlight_sentences: int,
    enable_summary: bool,
    max_tokens: int,
) -> dict:
    response = await _fetch_page_structured(url, max_tokens=max_tokens)

    if response is None:
        return {
            "url": url,
            "status_code": 500,
            "title": "",
            "content": "",
            "highlights": [],
            "summary": None,
        }

    highlights: list[str] = []
    if highlight_query and response.content:
        highlights = extract_highlights(
            response.content, highlight_query, num_sentences=highlight_sentences
        )

    summary: str | None = None
    if enable_summary and response.content:
        summary = extractive_summary(response.content, num_sentences=3)

    return {
        "url": url,
        "status_code": response.status_code,
        "title": response.title,
        "content": response.content,
        "highlights": highlights,
        "summary": summary,
    }


async def get_contents(
    urls: list[str],
    highlight_query: Optional[str] = None,
    highlight_sentences: int = 3,
    enable_summary: bool = False,
    max_tokens: int = 8000,
) -> str:
    logger.info(f"get_contents: {len(urls)} URLs")

    semaphore = asyncio.Semaphore(3)

    async def bounded_fetch(url: str):
        async with semaphore:
            return await _fetch_single_url(
                url, highlight_query, highlight_sentences, enable_summary, max_tokens
            )

    results = await asyncio.gather(*[bounded_fetch(u) for u in urls])

    lines = [f"## 📄 Contents ({len(results)} pages)"]
    lines.append("")

    for i, item in enumerate(results, 1):
        lines.append(f"### {i}. {item['title'] or item['url']}")
        lines.append(f"**URL:** {item['url']}")
        lines.append(f"**Status:** {item['status_code']}")

        if item["highlights"]:
            lines.append("**Highlights:**")
            for h in item["highlights"]:
                lines.append(f"> {h}")

        if item["summary"]:
            lines.append(f"**Summary:** {item['summary']}")

        lines.append("")
        lines.append(f"**Content:**\n{item['content'][:2000]}")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)