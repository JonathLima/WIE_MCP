from __future__ import annotations

import logging
import asyncio
from typing import Optional, cast

import httpx

from src.config import get_searxng_config, get_server_config
from src.constants import SEARCH_TYPE_CONFIG, CATEGORY_ENGINES
from src.models import SearchResultAdvanced
from src.utils.dedup import normalize_url, get_domain_tier
from src.utils.query_expander import QueryExpander
from src.utils.highlights import extract_highlights
from src.utils.summarizer import extractive_summary

logger = logging.getLogger(__name__)

_expander = QueryExpander()

async def _fetch_from_searxng(params: dict, timeout: float) -> list[dict]:
    config = get_searxng_config()
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(config.search_url, params=params)
        response.raise_for_status()
        data = response.json()
    return data.get("results", [])

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
                results = await _fetch_from_searxng(params, timeout * type_config.timeout_multiplier)
                for r in results:
                    r["_query_weight"] = weight
                return results, None
            except Exception as e:
                logger.warning(f"Query variation failed: {var_query} — {e}")
                return [], e

    tasks = [
        fetch_variation(v["query"], float(v["weight"]))
        for v in variations[:type_config.query_variations]
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
        publishedDate=raw.get("publishedDate") or raw.get("pubdate"),
        author=raw.get("author"),
        domain=hostname,
        domainTier=tier,
        score=min(base_score + (50 if tier == 1 else 25 if tier == 2 else 10), 100),
        highlights=highlights,
        summary=summary,
        wordCount=len(snippet.split()) if snippet else 0,
    )

def _format_advanced_response(
    query: str,
    results: list[SearchResultAdvanced],
    search_type: str,
    total_found: int,
    additional_queries: list[str],
) -> str:
    if not results:
        lines = ["## No Results Found", f"No results for: **{query}**"]
        return "\n".join(lines)

    type_label = f"{search_type.upper()} Search"
    lines = [f"## {type_label} ({len(results)} results)"]
    lines.append(f"**Query:** `{query}`")
    lines.append("")

    for i, r in enumerate(results, 1):
        tier_emoji = {1: "🟢", 2: "🔵", 3: "🟡", 4: "⚪"}.get(r.domainTier, "⚪")
        lines.append(f"### {i}. {r.title}")
        lines.append(f"**URL:** {r.url}")
        if r.snippet:
            lines.append(f"**Snippet:** {r.snippet[:200]}...")
        if r.highlights:
            lines.append("**Highlights:**")
            for h in r.highlights[:3]:
                lines.append(f"> {h}")
        lines.append(f"**Authority:** {tier_emoji} Tier {r.domainTier} | **Score:** {r.score:.0f}/100")
        if r.publishedDate:
            lines.append(f"**Date:** {r.publishedDate}")
        lines.append("")

    if additional_queries:
        lines.append("---")
        lines.append(f"*Additional queries used: {', '.join(additional_queries)}*")

    return "\n".join(lines)

async def web_search_advanced(
    query: str,
    type: Optional[str] = None,
    numResults: int = 10,
    category: Optional[str] = None,
    includeDomains: Optional[list[str]] = None,
    excludeDomains: Optional[list[str]] = None,
    startPublishedDate: Optional[str] = None,
    endPublishedDate: Optional[str] = None,
    startCrawlDate: Optional[str] = None,
    endCrawlDate: Optional[str] = None,
    includeText: Optional[list[str]] = None,
    excludeText: Optional[list[str]] = None,
    userLocation: Optional[dict] = None,
    safesearch: Optional[int] = None,
    enableHighlights: bool = True,
    highlight_sentences: int = 3,
    enableSummary: bool = False,
    additionalQueries: bool = True,
) -> str:
    if type is None:
        type = get_server_config().default_search_type

    logger.info(f"web_search_advanced: query={query!r}, type={type}, numResults={numResults}")

    type_config = SEARCH_TYPE_CONFIG.get(type, SEARCH_TYPE_CONFIG["auto"])
    category_engines = CATEGORY_ENGINES.get(category) if category else None

    config = get_searxng_config()
    effective_safesearch = safesearch if safesearch is not None else int(config.safesearch)

    try:
        raw_results = await _execute_search(
            query=query,
            search_type=type,
            num_results=numResults,
            category=category,
            engines=category_engines,
            timeout=config.timeout,
            safesearch=effective_safesearch,
        )
    except httpx.ConnectError:
        return "## Connection Error\nCannot connect to SearxNG."
    except httpx.TimeoutException:
        return "## Timeout\nSearch timed out."
    except httpx.HTTPStatusError as e:
        return f"## HTTP Error\n{e.response.status_code}"
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        return f"## Error\n{str(e)}"

    raw_results = _apply_domain_filters(raw_results, includeDomains, excludeDomains)
    raw_results = _apply_date_filters(raw_results, startPublishedDate, endPublishedDate)

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
    for raw in deduplicated[:numResults * 3]:
        sr = _build_advanced_result(
            raw, query,
            highlight_sentences=highlight_sentences if enableHighlights else 0,
            enable_summary=enableSummary and type_config.enable_summary,
        )
        scored_results.append(sr)

    scored_results.sort(key=lambda x: -x.score)

    variation_names = [v["query"] for v in _expander.expand(query, type)][:type_config.query_variations]
    additional_q: list[str] = [str(x) for x in variation_names[1:]] if len(variation_names) > 1 else []

    response_text = _format_advanced_response(
        query=query,
        results=scored_results[:numResults],
        search_type=type,
        total_found=len(raw_results),
        additional_queries=additional_q,
    )

    return response_text
