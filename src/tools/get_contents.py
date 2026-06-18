from __future__ import annotations

import asyncio
import logging
from typing import Optional

from src.models import GetContentsRequest
from src.tools.fetch_page import _fetch_page_structured
from src.errors import MCPToolError, FetchBlockedError, FetchHTTPError
from src.utils.formatting import format_tool_error
from src.utils.highlights import extract_highlights
from src.utils.summarizer import extractive_summary
from src.utils.truncation import cap_response

logger = logging.getLogger(__name__)


async def _fetch_single_url(
    url: str,
    highlight_query: Optional[str],
    highlight_sentences: int,
    enable_summary: bool,
    max_tokens: int,
) -> dict:
    try:
        response = await _fetch_page_structured(url, max_tokens=max_tokens)
        
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
    except FetchBlockedError as exc:
        status_code = 429 if "429" in str(exc) else 403
        return {
            "url": url,
            "status_code": status_code,
            "title": "Blocked",
            "content": f"Error: {exc}",
            "highlights": [],
            "summary": None,
        }
    except FetchHTTPError as exc:
        return {
            "url": url,
            "status_code": exc.status_code,
            "title": f"HTTP Error {exc.status_code}",
            "content": f"Error: {exc}",
            "highlights": [],
            "summary": None,
        }
    except MCPToolError as exc:
        return {
            "url": url,
            "status_code": 500,
            "title": "Error",
            "content": f"Error: {exc}",
            "highlights": [],
            "summary": None,
        }
    except Exception as exc:
        logger.warning("_fetch_single_url failed for %s: %s", url, exc)
        return {
            "url": url,
            "status_code": 500,
            "title": "Error",
            "content": f"Unexpected error: {exc}",
            "highlights": [],
            "summary": None,
        }


async def get_contents(
    urls: list[str],
    highlight_query: Optional[str] = None,
    highlight_sentences: int = 3,
    enable_summary: bool = False,
    max_tokens: int = 8000,
) -> str:
    logger.info(f"get_contents: {len(urls)} URLs")

    # Validate parameters
    try:
        GetContentsRequest(
            urls=urls,
            highlight_query=highlight_query,
            highlight_sentences=highlight_sentences,
            enable_summary=enable_summary,
            max_tokens=max_tokens,
        )
    except Exception as exc:
        return format_tool_error(
            error_code="VALIDATION_ERROR",
            message=f"Invalid get_contents parameters: {exc}",
            retry_guidance=(
                "Ensure urls is a non-empty list with at most 20 URLs, "
                "highlight_sentences is 1-10, and max_tokens is 500-128000."
            ),
        )

    # Distribute token budget across URLs; cap at 10 URLs max
    effective_urls = urls[:10]
    per_url_budget = max(1000, max_tokens // len(effective_urls))
    per_url_content_chars = min(2000, per_url_budget * 4)  # ~4 chars/token

    semaphore = asyncio.Semaphore(3)

    async def bounded_fetch(url: str):
        async with semaphore:
            return await _fetch_single_url(
                url, highlight_query, highlight_sentences, enable_summary, per_url_budget
            )

    results = await asyncio.gather(*[bounded_fetch(u) for u in effective_urls])

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
        lines.append(f"**Content:**\n{item['content'][:per_url_content_chars]}")
        lines.append("")
        lines.append("---")
        lines.append("")

    return cap_response("\n".join(lines))