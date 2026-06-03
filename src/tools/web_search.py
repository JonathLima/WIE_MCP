from __future__ import annotations

import logging
from urllib.parse import urlparse

import httpx

from src.config import get_searxng_config
from src.models import SearchRequest, SearchResult, SearchResponse, ToolErrorResponse
from src.searxng_client import fetch_search_results
from src.utils.dedup import deduplicate_and_score
from src.utils.formatting import format_tool_error

logger = logging.getLogger(__name__)

try:
    from flashrank import Ranker, RerankRequest
    FLASHRANK_AVAILABLE = True
except ImportError:
    FLASHRANK_AVAILABLE = False
    logger.warning("flashrank not available, skipping AI reranking")

_ranker = None

def _get_ranker():
    global _ranker
    if _ranker is None and FLASHRANK_AVAILABLE:
        try:
            _ranker = Ranker()
            logger.info("FlashRank Ranker initialized")
        except Exception as exc:
            logger.warning("Failed to initialize FlashRank: %s", exc)
    return _ranker

def _rerank_with_flashrank(query: str, results: list[SearchResult]) -> list[SearchResult]:
    if not FLASHRANK_AVAILABLE or len(results) < 2:
        return results
    
    ranker = _get_ranker()
    if ranker is None:
        return results
    
    try:
        passages = [
            {
                "id": idx,
                "text": f"{r.title}. {r.snippet}" if r.snippet else r.title,
            }
            for idx, r in enumerate(results)
        ]
        
        rerank_request = RerankRequest(query=query, passages=passages)
        reranked = ranker.rerank(rerank_request)
        
        id_to_result = {r.id: r for r in results}
        reranked_results = [id_to_result[r["id"]] for r in reranked if r["id"] in id_to_result]
        
        logger.info("FlashRank reranked %d results", len(results))
        return reranked_results
        
    except Exception as exc:
        logger.warning("FlashRank reranking failed: %s", exc)
        return results

def _build_search_params(request: SearchRequest) -> dict[str, str]:
    config = get_searxng_config()

    params: dict[str, str] = {
        "q": request.query,
        "format": "json",
        "pageno": "1",
    }

    if request.categories:
        params["categories"] = request.categories
    else:
        params["categories"] = config.default_category

    if request.time_range:
        params["time_range"] = request.time_range

    params["language"] = "en"

    if request.safesearch is not None:
        params["safesearch"] = request.safesearch
    else:
        params["safesearch"] = config.safesearch

    params["engines"] = ",".join(config.engine_list)

    return params

_TIER_EMOJI: dict[int, str] = {1: "🟢", 2: "🔵", 3: "🟡", 4: "⚪"}

def _format_search_response(response: SearchResponse) -> str:
    if not response.results:
        return (
            "## No Results Found\n\n"
            f"No results for: `{response.query}`\n\n"
            "Suggestions: rephrase the query, broaden or narrow the terms, "
            "or try a different time range or category."
        )

    lines = [
        f"## Search Results — {len(response.results)} results",
        f"Query: `{response.query}`  |  Engines: {', '.join(response.engines_used)}",
        "",
    ]

    for idx, result in enumerate(response.results, start=1):
        emoji = _TIER_EMOJI.get(result.domain_tier, "⚪")
        hostname = urlparse(result.url_str).hostname or result.url_str
        lines.append(f"### {idx}. {result.title}")
        lines.append(f"URL: {result.url_str}")
        lines.append(f"Source: {emoji} {hostname}  ·  Score: {result.score:.0f}/100")
        if result.snippet:
            lines.append(f"Snippet: {result.snippet}")
        if result.published_date:
            lines.append(f"Published: {result.published_date}")
        lines.append("")

    return "\n".join(lines)


def _format_error(error: ToolErrorResponse) -> str:
    return format_tool_error(error.error_code, error.message, error.retry_guidance)


async def get_raw_searxng_results(
    query: str,
    time_range: str | None = None,
    categories: str | None = None,
    safesearch: str | None = None,
    limit: int = 10,
) -> list[dict]:
    try:
        request = SearchRequest(
            query=query,
            time_range=time_range,
            categories=categories,
            safesearch=safesearch,
            limit=limit,
        )
    except Exception:
        return []

    config = get_searxng_config()
    params = _build_search_params(request)
    try:
        raw_results = await fetch_search_results(params, timeout=config.timeout)
        return raw_results
    except Exception:
        return []

async def web_search(
    query: str,
    time_range: str | None = None,
    categories: str | None = None,
    safesearch: str | None = None,
    limit: int = 10,
) -> str:
    logger.info("web_search called: query=%r, time_range=%r, categories=%r, limit=%d",
                query, time_range, categories, limit)

    try:
        request = SearchRequest(
            query=query,
            time_range=time_range,
            categories=categories,
            safesearch=safesearch,
            limit=limit,
        )
    except Exception as exc:
        return format_tool_error(
            error_code="SEARCH_VALIDATION_ERROR",
            message=f"Invalid search parameters: {exc}",
            retry_guidance=(
                "Ensure query is a non-empty string (max 500 chars), "
                "limit is between 1-20, and time_range/categories/safesearch "
                "use valid values."
            ),
        )

    config = get_searxng_config()

    params = _build_search_params(request)

    try:
        raw_results = await fetch_search_results(params, timeout=config.timeout)
        engines_list = [e.strip() for e in params.get("engines", "").split(",") if e.strip()]
    except httpx.ConnectError:
        return (
            f"## Connection Error\n"
            f"Cannot reach SearXNG at `{config.host}`. Verify Docker is running."
        )
    except httpx.TimeoutException:
        return (
            f"## Timeout\n"
            f"SearXNG did not respond within {config.timeout}s. Try a shorter query."
        )
    except httpx.HTTPStatusError as exc:
        return f"## HTTP Error {exc.response.status_code}\nSearXNG returned an error. Try again."
    except Exception as exc:
        logger.error("web_search error: %s", exc, exc_info=True)
        return f"## Search Error\n{exc}"

    total_found = len(raw_results)

    results = deduplicate_and_score(raw_results, engines_list)

    if FLASHRANK_AVAILABLE and len(results) >= 2:
        results = _rerank_with_flashrank(query, results)

    results = results[: request.limit]

    if not results:
        logger.info("No results found for query: %r", query)
        response = SearchResponse(
            query=query,
            results=[],
            total_found=total_found,
            engines_used=engines_list,
            markdown="",
        )
        response.markdown = _format_search_response(response)
        return response.markdown

    response = SearchResponse(
        query=query,
        results=results,
        total_found=total_found,
        engines_used=engines_list,
        markdown="",
    )
    response.markdown = _format_search_response(response)

    logger.info(
        "web_search complete: query=%r, results=%d/%d",
        query,
        len(response.results),
        total_found,
    )

    return response.markdown
