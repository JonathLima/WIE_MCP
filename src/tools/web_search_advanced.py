from __future__ import annotations

import logging
import asyncio
from typing import Optional

import httpx

from src.config import get_searxng_config, get_server_config
from src.constants import SEARCH_TYPE_CONFIG, CATEGORY_ENGINES
from src.models import SearchRequestAdvanced, SearchResultAdvanced
from src.searxng_client import fetch_search_results
from src.utils.formatting import format_tool_error
from src.utils.dedup import normalize_url, get_domain_tier
from src.utils.query_expander import QueryExpander
from src.utils.highlights import extract_highlights
from src.utils.summarizer import extractive_summary
from src.utils.truncation import cap_response

logger = logging.getLogger(__name__)

_expander = QueryExpander()


async def _execute_search(
    query: str,
    search_type: str,
    num_results: int,
    category: Optional[str],
    engines: Optional[list[str]],
    timeout: float,
    safesearch: int = 0,
) -> list[dict]:
    config = get_searxng_config()
    type_config = SEARCH_TYPE_CONFIG.get(search_type, SEARCH_TYPE_CONFIG["auto"])

    variations = _expander.expand(query, search_type)

    engine_str = ",".join(engines) if engines else ",".join(config.engine_list)

    base_params = {
        "q": query,
        "format": "json",
        "pageno": "1",
        "language": "en",
        "safesearch": str(safesearch),
        "engines": engine_str,
    }
    if category:
        base_params["categories"] = category

    semaphore = asyncio.Semaphore(3)

    async def fetch_variation(var_query: str, weight: float):
        async with semaphore:
            params = base_params.copy()
            params["q"] = var_query
            try:
                results = await fetch_search_results(params, timeout * type_config.timeout_multiplier)
                for r in results:
                    r["_query_weight"] = weight
                return results, None
            except Exception as e:
                logger.warning(f"Query variation failed: {var_query} — {e}")
                return [], e

    capped_variations = variations[:min(type_config.query_variations, 5)]
    tasks = [
        fetch_variation(v["query"], float(v["weight"]))
        for v in capped_variations
    ]

    variation_results = await asyncio.gather(*tasks)

    all_results: list[dict] = []
    errors: list[Exception] = []
    for vr, err in variation_results:
        if err:
            errors.append(err)
        else:
            all_results.extend(vr)

    if len(errors) == len(tasks) and errors:
        raise errors[-1]

    return all_results


def _apply_domain_filters(
    results: list[dict],
    include_domains: Optional[list[str]],
    exclude_domains: Optional[list[str]],
) -> list[dict]:
    filtered = []
    for r in results:
        url = r.get("url", "")
        hostname = ""
        try:
            from urllib.parse import urlparse
            hostname = urlparse(url).hostname or ""
        except Exception:
            pass

        if exclude_domains:
            skip = False
            for ex in exclude_domains:
                if ex in hostname:
                    skip = True
                    break
            if skip:
                continue

        if include_domains:
            matched = any(inc in hostname for inc in include_domains)
            if not matched:
                continue

        r["_domain"] = hostname
        filtered.append(r)

    return filtered


def _apply_date_filters(
    results: list[dict],
    start_date: Optional[str],
    end_date: Optional[str],
) -> list[dict]:
    from datetime import datetime
    if not start_date and not end_date:
        return results

    def parse_date(date_str: str):
        for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None

    start_dt = parse_date(start_date) if start_date else None
    end_dt = parse_date(end_date) if end_date else None

    filtered = []
    for r in results:
        pub = r.get("publishedDate") or r.get("pubdate") or r.get("date", "")
        if not pub:
            filtered.append(r)
            continue

        pub_dt = parse_date(pub)
        if pub_dt:
            if start_dt and pub_dt < start_dt:
                continue
            if end_dt and pub_dt > end_dt:
                continue
        filtered.append(r)

    return filtered


def _build_advanced_result(
    raw: dict,
    query: str,
    highlight_sentences: int,
    enable_summary: bool = False,
) -> SearchResultAdvanced:
    url = raw.get("url", "")
    snippet = raw.get("content", "")
    hostname = raw.get("_domain", "")

    tier = get_domain_tier(url)
    weight = raw.get("_query_weight", 1.0)
    base_score = weight * 50

    highlights = []
    if highlight_sentences > 0 and snippet:
        highlights = extract_highlights(snippet, query, num_sentences=highlight_sentences)

    summary = None
    if enable_summary and snippet:
        summary = extractive_summary(snippet, num_sentences=3)

    return SearchResultAdvanced(
        title=raw.get("title", ""),
        url=url,
        snippet=snippet,
        published_date=raw.get("publishedDate") or raw.get("pubdate"),
        author=raw.get("author"),
        domain=hostname,
        domain_tier=tier,
        score=min(base_score + (50 if tier == 1 else 25 if tier == 2 else 10), 100),
        highlights=highlights,
        summary=summary,
        word_count=len(snippet.split()) if snippet else 0,
    )


_TIER_EMOJI: dict[int, str] = {1: "🟢", 2: "🔵", 3: "🟡", 4: "⚪"}


def _format_advanced_response(
    query: str,
    results: list[SearchResultAdvanced],
    search_type: str,
    additional_queries: list[str],
) -> str:
    if not results:
        return f"## No Results Found\nNo results for: `{query}`"

    lines = [
        f"## Search Results — {len(results)} results  [{search_type.upper()}]",
        f"Query: `{query}`",
        "",
    ]

    for i, r in enumerate(results, 1):
        emoji = _TIER_EMOJI.get(r.domain_tier, "⚪")
        lines.append(f"### {i}. {r.title}")
        lines.append(f"URL: {r.url}")
        lines.append(f"Source: {emoji} {r.domain}  ·  Score: {r.score:.0f}/100")
        if r.snippet:
            lines.append(f"Snippet: {r.snippet[:300]}")
        if r.highlights:
            for h in r.highlights[:3]:
                lines.append(f"> {h}")
        if r.summary:
            lines.append(f"Summary: {r.summary}")
        if r.published_date:
            lines.append(f"Published: {r.published_date}")
        lines.append("")

    if additional_queries:
        lines.append(f"*Expanded queries: {', '.join(additional_queries)}*")

    return "\n".join(lines)


async def web_search_advanced(
    query: str,
    search_type: Optional[str] = None,
    num_results: int = 10,
    category: Optional[str] = None,
    include_domains: Optional[list[str]] = None,
    exclude_domains: Optional[list[str]] = None,
    start_published_date: Optional[str] = None,
    end_published_date: Optional[str] = None,
    start_crawl_date: Optional[str] = None,
    end_crawl_date: Optional[str] = None,
    include_text: Optional[list[str]] = None,
    exclude_text: Optional[list[str]] = None,
    user_location: Optional[dict] = None,
    safesearch: Optional[int] = None,
    enable_highlights: bool = True,
    highlight_sentences: int = 3,
    enable_summary: bool = False,
    additional_queries: bool = True,
) -> str:
    if search_type is None:
        search_type = get_server_config().default_search_type

    logger.info(f"web_search_advanced: query={query!r}, search_type={search_type}, num_results={num_results}")

    # Validate all parameters up front
    try:
        SearchRequestAdvanced(
            query=query,
            search_type=search_type,
            num_results=num_results,
            category=category,
            include_domains=include_domains,
            exclude_domains=exclude_domains,
            start_published_date=start_published_date,
            end_published_date=end_published_date,
            start_crawl_date=start_crawl_date,
            end_crawl_date=end_crawl_date,
            include_text=include_text,
            exclude_text=exclude_text,
            user_location=user_location,
            safesearch=safesearch,
            enable_highlights=enable_highlights,
            highlight_sentences=highlight_sentences,
            enable_summary=enable_summary,
            additional_queries=additional_queries,
        )
    except Exception as exc:
        return format_tool_error(
            error_code="SEARCH_VALIDATION_ERROR",
            message=f"Invalid search parameters: {exc}",
            retry_guidance=(
                "Ensure query is a non-empty string (max 500 chars), "
                "num_results is 1-100, search_type is one of "
                "auto/fast/instant/deep_lite/deep/deep_reasoning, "
                "and all optional fields use valid types."
            ),
        )


    type_config = SEARCH_TYPE_CONFIG.get(search_type, SEARCH_TYPE_CONFIG["auto"])
    category_engines = CATEGORY_ENGINES.get(category) if category else None

    config = get_searxng_config()
    effective_safesearch = safesearch if safesearch is not None else int(config.safesearch)

    try:
        raw_results = await _execute_search(
            query=query,
            search_type=search_type,
            num_results=num_results,
            category=category,
            engines=category_engines,
            timeout=config.timeout,
            safesearch=effective_safesearch,
        )
    except httpx.ConnectError:
        return "## Connection Error\nCannot connect to SearXNG. Verify Docker is running."
    except httpx.TimeoutException:
        return "## Timeout\nSearch timed out. Try a shorter query."
    except httpx.HTTPStatusError as e:
        return f"## HTTP Error {e.response.status_code}\nSearXNG returned an error. Try again."
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        return f"## Error\n{str(e)}"

    raw_results = _apply_domain_filters(raw_results, include_domains, exclude_domains)
    raw_results = _apply_date_filters(raw_results, start_published_date, end_published_date)

    seen: set[str] = set()
    deduplicated: list[dict] = []
    for r in raw_results:
        url = r.get("url", "")
        if not url:
            continue
        norm = normalize_url(url)
        if norm in seen:
            continue
        seen.add(norm)
        deduplicated.append(r)

    scored_results: list[SearchResultAdvanced] = []
    for raw in deduplicated[:num_results * 2]:
        sr = _build_advanced_result(
            raw, query,
            highlight_sentences=highlight_sentences if enable_highlights else 0,
            enable_summary=enable_summary and type_config.enable_summary,
        )
        scored_results.append(sr)

    scored_results.sort(key=lambda x: -x.score)

    variation_names = [v["query"] for v in _expander.expand(query, search_type)][:type_config.query_variations]
    additional_q: list[str] = [str(x) for x in variation_names[1:]] if len(variation_names) > 1 else []

    response_text = _format_advanced_response(
        query=query,
        results=scored_results[:num_results],
        search_type=search_type,
        additional_queries=additional_q,
    )

    return cap_response(response_text)
