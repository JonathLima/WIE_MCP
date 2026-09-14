from __future__ import annotations

from typing import Any, Union

WeightValue = Union[str, float]

QUERY_VARIATION_STRATEGIES = {
    "instant": ["original"],
    "fast": ["original"],
    "auto": ["original"],
    "deep_lite": ["original", "broader", "narrower"],
    "deep": ["original", "broader", "narrower", "related_topic", "different_viewpoint"],
    "deep_reasoning": ["original", "broader", "narrower", "related_topic", "different_viewpoint",
                       "cause_effect", "history", "future"],
}

BROADER_PATTERNS = [
    "{query} overview",
    "{query} guide",
    "introduction to {query}",
    "what is {query}",
    "about {query}",
]

RELATED_PATTERNS = [
    "{query} alternatives",
    "{query} compared to",
    "{query} vs",
    "{query} related",
]

CAUSE_EFFECT_PATTERNS = [
    "{query} why", "{query} causes",
    "{query} results in", "{query} impact",
    "{query} effect on", "how {query} works",
]

HISTORY_PATTERNS = [
    "{query} history", "{query} origin",
    "{query} when", "{query} evolution",
    "history of {query}", "{query} timeline",
]

FUTURE_PATTERNS = [
    "{query} future", "{query} roadmap",
    "{query} upcoming", "{query} next version",
    "{query} prediction", "{query} trends",
]

VIEWPOINT_PATTERNS = [
    "{query} criticism", "{query} problems",
    "{query} limitations", "{query} disadvantages",
    "{query} controversy", "{query} debate",
]

def _generate_variations(query: str, purpose: str) -> list[str]:
    if purpose == "original":
        return [query]

    q = query.strip()
    variations: list[str] = []

    if purpose == "broader":
        for pattern in BROADER_PATTERNS[:2]:
            variations.append(pattern.format(query=q))
    elif purpose == "narrower":
        variations.append(f"{q} detailed")
        variations.append(f"{q} documentation")
        variations.append(f"{q} tutorial")
    elif purpose == "related_topic":
        for pattern in RELATED_PATTERNS[:2]:
            variations.append(pattern.format(query=q))
    elif purpose == "different_viewpoint":
        for pattern in VIEWPOINT_PATTERNS[:2]:
            variations.append(pattern.format(query=q))
    elif purpose == "cause_effect":
        for pattern in CAUSE_EFFECT_PATTERNS[:2]:
            variations.append(pattern.format(query=q))
    elif purpose == "history":
        for pattern in HISTORY_PATTERNS[:2]:
            variations.append(pattern.format(query=q))
    elif purpose == "future":
        for pattern in FUTURE_PATTERNS[:2]:
            variations.append(pattern.format(query=q))

    return variations[:2]

class QueryExpander:
    def __init__(self):
        self._cache: dict[tuple[str, str, str], list[Any]] = {}

    def expand(self, query: str, search_type: str, language: str = "auto") -> list[Any]:
        cache_key = (query, search_type, language)
        if cache_key in self._cache:
            return self._cache[cache_key]

        result = expand_query(query, search_type, language=language)
        self._cache[cache_key] = result
        return result

    def clear_cache(self):
        self._cache.clear()

def expand_query(query: str, search_type: str, language: str = "auto") -> list[Any]:
    # For explicit non-English queries, skip expansion to avoid mixing languages
    # auto keeps the existing EN-biased expansion behaviour (documented)
    if language != "auto" and language != "en":
        return [{"query": query, "purpose": "original", "weight": 1.0}]

    strategies = QUERY_VARIATION_STRATEGIES.get(search_type, ["original"])
    weight_map = {
        "original": 1.0,
        "broader": 0.9,
        "narrower": 0.9,
        "related_topic": 0.8,
        "different_viewpoint": 0.7,
        "cause_effect": 0.7,
        "history": 0.7,
        "future": 0.7,
    }

    all_variations: list[dict[str, str | float]] = []
    for strategy in strategies:
        variations = _generate_variations(query, strategy)
        weight = weight_map.get(strategy, 0.5)
        for var in variations:
            all_variations.append({
                "query": var,
                "purpose": strategy,
                "weight": weight,
            })

    if search_type == "deep_reasoning":
        chain_patterns = [
            f"explain {query} step by step",
            f"{query} how does it work",
            f"{query} problems and solutions",
        ]
        for pattern in chain_patterns:
            all_variations.append({
                "query": pattern,
                "purpose": "chain_step",
                "weight": 0.6,
            })

    deduplicated: dict[str, Any] = {}
    for v in all_variations:
        key = v["query"].lower().strip()
        weight_val = float(v["weight"])  # type: ignore[arg-type]
        if key not in deduplicated or weight_val > float(deduplicated[key]["weight"]):  # type: ignore[index]
            deduplicated[key] = v

    final = list(deduplicated.values())
    final.sort(key=lambda x: -float(x["weight"]))  # type: ignore[arg-type]
    return final