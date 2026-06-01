import pytest
from src.constants import (
    SEARCH_TYPE_CONFIG, CATEGORY_DOMAINS, CATEGORY_ENGINES,
    TIER1_DOMAINS, TIER1_SUFFIXES, TIER2_DOMAINS, TIER3_DOMAINS,
    VAGUE_PHRASES, SPECIFIC_DATA_PATTERNS,
)

def test_search_type_config_has_all_types():
    expected = {"auto", "fast", "instant", "deep_lite", "deep", "deep_reasoning"}
    assert set(SEARCH_TYPE_CONFIG.keys()) == expected

def test_search_type_config_deep_has_variations():
    cfg = SEARCH_TYPE_CONFIG["deep"]
    assert cfg.query_variations == 5
    assert cfg.enable_rerank is True
    assert cfg.enable_summary is True

def test_category_domains_has_all_categories():
    expected = {"news", "research_paper", "company", "people", "financial_report",
                "product", "personal_site", "code", "video", "image", "general"}
    assert set(CATEGORY_DOMAINS.keys()) == expected

def test_tier1_includes_official_domains():
    assert "github.com" in TIER1_DOMAINS
    assert "arxiv.org" in TIER1_DOMAINS

def test_tier1_is_frozenset():
    assert isinstance(TIER1_DOMAINS, frozenset)

def test_tier1_suffixes_contains_gov_and_edu():
    assert ".gov" in TIER1_SUFFIXES
    assert ".edu" in TIER1_SUFFIXES
    assert ".gov.br" in TIER1_SUFFIXES
    assert ".edu.br" in TIER1_SUFFIXES

def test_tier1_suffixes_is_tuple():
    assert isinstance(TIER1_SUFFIXES, tuple)

def test_tier2_includes_stackoverflow():
    assert "stackoverflow.com" in TIER2_DOMAINS
    assert "wikipedia.org" in TIER2_DOMAINS

def test_tier2_is_frozenset():
    assert isinstance(TIER2_DOMAINS, frozenset)

def test_tier3_includes_blogs():
    assert "medium.com" in TIER3_DOMAINS

def test_tier3_is_frozenset():
    assert isinstance(TIER3_DOMAINS, frozenset)

def test_tiers_are_disjoint():
    assert TIER1_DOMAINS.isdisjoint(TIER2_DOMAINS), "TIER1 and TIER2 should not overlap"
    assert TIER1_DOMAINS.isdisjoint(TIER3_DOMAINS), "TIER1 and TIER3 should not overlap"
    assert TIER2_DOMAINS.isdisjoint(TIER3_DOMAINS), "TIER2 and TIER3 should not overlap"