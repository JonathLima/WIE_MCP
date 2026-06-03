from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from src.models import SearchResult

logger = logging.getLogger(__name__)

from src.constants import TIER1_DOMAINS, TIER1_SUFFIXES, TIER2_DOMAINS, TIER3_DOMAINS

def get_domain_tier(url: str) -> int:
    try:
        hostname = urlparse(url).hostname or ""
        hostname = hostname.lower()
    except Exception:
        return 4

    if any(hostname.endswith(suffix) for suffix in TIER1_SUFFIXES):
        return 1

    for domain in TIER1_DOMAINS:
        if hostname == domain or hostname.endswith("." + domain):
            return 1

    for domain in TIER2_DOMAINS:
        if hostname == domain or hostname.endswith("." + domain):
            return 2

    for domain in TIER3_DOMAINS:
        if hostname == domain or hostname.endswith("." + domain):
            return 3

    return 4

VAGUE_LANGUAGE = {
    "approximately", "around", "typically", "usually", "generally",
    "often", "sometimes", "may", "might", "could", "varies",
    "about", "roughly", "estimated", "likely", "possibly",
}

def has_vague_language(text: str) -> bool:
    if not text:
        return False
    words = text.lower().split()
    return any(word in VAGUE_LANGUAGE for word in words)

_SPECIFIC_DATA_PATTERNS = [
    re.compile(r"\d+\.\d+\.\d+"),           # versions: 3.13.2
    re.compile(r"\$[\d,]+"),                  # prices: $1,299
    re.compile(r"\d{1,2}/\d{1,2}/\d{4}"),    # dates: 12/25/2025
    re.compile(r"\d{4}-\d{2}-\d{2}"),        # ISO dates: 2025-12-25
    re.compile(r"\d+%"),                      # percentages: 45%
    re.compile(r"v\d+\.\d+"),                # versions: v2.1
]

def has_specific_data(text: str) -> bool:
    if not text:
        return False
    return any(pattern.search(text) for pattern in _SPECIFIC_DATA_PATTERNS)

ENGINE_RELIABILITY: dict[str, float] = {
    "google": 1.2,
    "bing": 1.0,
    "duckduckgo": 1.0,
    "startpage": 1.1,
    "brave": 1.1,
    "wikipedia": 1.5,
    "qwant": 0.9,
    "yahoo": 0.9,
    "unknown": 0.8,
}

RELIABLE_ENGINES = {"google", "bing", "duckduckgo"}

def _get_age_days(published_date: str | None) -> int | None:
    if not published_date:
        return None

    for fmt in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%B %d, %Y",
        "%b %d, %Y",
    ):
        try:
            dt = datetime.strptime(published_date.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            return max(0, (now - dt).days)
        except (ValueError, TypeError):
            continue

    return None

def normalize_url(url: str) -> str:
    try:
        parsed = urlparse(url)
    except Exception:
        return url

    scheme = parsed.scheme.lower()
    netloc = parsed.hostname.lower() if parsed.hostname else parsed.netloc.lower()

    port = parsed.port
    if port:
        if (scheme == "http" and port == 80) or (scheme == "https" and port == 443):
            netloc = parsed.hostname.lower() if parsed.hostname else ""

    if parsed.query:
        params = parse_qs(parsed.query, keep_blank_values=True)
        tracking_prefixes = ("utm_", "ref", "fbclid", "gclid", "mc_eid")
        filtered = {
            k: v
            for k, v in params.items()
            if not k.lower().startswith(tuple(tracking_prefixes))
        }
        query = urlencode(sorted(filtered.items()), doseq=True)
    else:
        query = ""

    canonical = urlunparse((scheme, netloc, parsed.path.rstrip("/"), parsed.params, query, ""))
    return canonical or url

def score_result(raw: dict) -> dict:
    score = 0.0
    url = raw.get("url", "")
    snippet = raw.get("content", "")
    engine = raw.get("engine", "unknown")
    published = raw.get("publishedDate")

    tier = get_domain_tier(url)
    tier_scores = {1: 40, 2: 25, 3: 15, 4: 5}
    score += tier_scores.get(tier, 5)

    specific = has_specific_data(snippet)
    vague = has_vague_language(snippet)
    if specific:
        score += 30
    elif not vague:
        score += 15

    age_days = _get_age_days(published)
    if age_days is not None:
        if age_days < 7:
            score += 20
        elif age_days < 30:
            score += 15
        elif age_days < 365:
            score += 10

    engine_lower = engine.lower()
    if engine_lower in RELIABLE_ENGINES:
        score += 10
    elif engine_lower in ENGINE_RELIABILITY:
        score += int(ENGINE_RELIABILITY[engine_lower] * 7)

    return {
        "score": round(score, 1),
        "domain_tier": tier,
        "has_specific_data": specific,
        "vagueness_detected": vague,
    }

def deduplicate_and_score(results: list[dict], engines_queried: list[str]) -> list[SearchResult]:
    seen_urls: set[str] = set()
    scored: list[SearchResult] = []
    total = len(results)

    for raw in results:
        url = raw.get("url", "").strip()
        if not url:
            continue

        canonical = normalize_url(url)
        if canonical in seen_urls:
            logger.debug("Deduplicated duplicate URL: %s", canonical)
            continue
        seen_urls.add(canonical)

        title = raw.get("title", "").strip()
        snippet = raw.get("content", "").strip()
        engine = raw.get("engine", "unknown")

        scoring = score_result(raw)

        idx = len(scored)  # Use position as ID for FlashRank reranking
        
        try:
            result = SearchResult(
                id=idx,
                title=title or canonical,
                url=url,  # Keep original URL for display
                snippet=snippet,
                score=scoring["score"],
                engine=engine,
                published_date=raw.get("publishedDate"),
                has_specific_data=scoring["has_specific_data"],
                vagueness_detected=scoring["vagueness_detected"],
                domain_tier=scoring["domain_tier"],
            )
        except Exception as exc:
            logger.warning("Skipping result with invalid URL '%s': %s", url, exc)
            continue

        scored.append(result)

    scored.sort(key=lambda r: r.score, reverse=True)

    for i, r in enumerate(scored):
        r.id = i

    logger.info(
        "Deduplication: %d raw results → %d unique (queried: %s)",
        total,
        len(scored),
        engines_queried,
    )

    return scored
