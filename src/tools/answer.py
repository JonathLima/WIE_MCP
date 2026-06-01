from __future__ import annotations

import asyncio
import logging

from src.utils.summarizer import extractive_summary
from src.utils.highlights import extract_highlights

logger = logging.getLogger(__name__)

async def _fetch_and_extract(url: str, query: str, max_tokens: int) -> str:
    from src.tools.fetch_page import fetch_page
    try:
        content = await fetch_page(url, max_tokens=max_tokens)
        lines = [line for line in content.split("\n") if not line.startswith("#") and line.strip()]
        text = "\n".join(lines)
        highlights = extract_highlights(text, query, num_sentences=5)
        if highlights:
            return " ".join(highlights)
        return text[:1000]
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return ""

async def answer(query: str, urls: list[str]) -> str:
    logger.info(f"answer: query={query!r}, urls={urls}")

    if not urls:
        return "## ❌ No URLs provided\nProvide URLs to answer the question."

    semaphore = asyncio.Semaphore(3)

    async def bounded_fetch(url: str):
        async with semaphore:
            return await _fetch_and_extract(url, query, max_tokens=5000)

    results = await asyncio.gather(*[bounded_fetch(u) for u in urls])

    passages = [r for r in results if r]
    if not passages:
        return "## ❌ No content retrieved\nCould not fetch any of the provided URLs."

    combined = "\n\n".join(passages)
    answer_text = extractive_summary(combined, num_sentences=4)

    lines = [f'## Answer: "{query}"', ""]
    lines.append(answer_text)
    lines.append("")
    lines.append("---")
    lines.append(f"Sources ({len(urls)}):")
    for url in urls:
        lines.append(f"- {url}")

    return "\n".join(lines)
