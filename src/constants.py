from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class SearchTypeConfig:
    query_variations: int
    enable_rerank: bool
    enable_summary: bool
    enable_highlights: bool
    highlight_sentences: int
    engines: Optional[list[str]] = None
    timeout_multiplier: float = 1.0

SEARCH_TYPE_CONFIG: dict[str, SearchTypeConfig] = {
    "instant": SearchTypeConfig(
        query_variations=1,
        enable_rerank=False,
        enable_summary=False,
        enable_highlights=False,
        highlight_sentences=0,
        engines=["google"],
        timeout_multiplier=0.5,
    ),
    "fast": SearchTypeConfig(
        query_variations=1,
        enable_rerank=False,
        enable_summary=False,
        enable_highlights=False,
        highlight_sentences=0,
        engines=["google"],
        timeout_multiplier=0.75,
    ),
    "auto": SearchTypeConfig(
        query_variations=1,
        enable_rerank=True,
        enable_summary=False,
        enable_highlights=True,
        highlight_sentences=2,
        timeout_multiplier=1.0,
    ),
    "deep_lite": SearchTypeConfig(
        query_variations=3,
        enable_rerank=True,
        enable_summary=True,
        enable_highlights=True,
        highlight_sentences=3,
        timeout_multiplier=1.5,
    ),
    "deep": SearchTypeConfig(
        query_variations=5,
        enable_rerank=True,
        enable_summary=True,
        enable_highlights=True,
        highlight_sentences=5,
        timeout_multiplier=2.0,
    ),
    "deep_reasoning": SearchTypeConfig(
        query_variations=7,
        enable_rerank=True,
        enable_summary=True,
        enable_highlights=True,
        highlight_sentences=5,
        timeout_multiplier=3.0,
    ),
}

# === Domain Authority Tiers ===
# Single source of truth. dedup.py and web_search_advanced.py import from here.

TIER1_DOMAINS: frozenset[str] = frozenset({
    "github.com", "gitlab.com", "bitbucket.org",
    "docs.python.org", "doc.rust-lang.org", "docs.oracle.com",
    "developer.mozilla.org", "developer.apple.com", "developer.android.com",
    "learn.microsoft.com", "cloud.google.com", "aws.amazon.com",
    "nodejs.org", "python.org", "rust-lang.org", "golang.org", "go.dev",
    "react.dev", "vuejs.org", "angular.io", "svelte.dev",
    "pytorch.org", "tensorflow.org", "keras.io",
    "readthedocs.io", "readthedocs.org",
    "arxiv.org", "openreview.net", "papers.nips.cc",
    "pypi.org", "npmjs.com", "crates.io", "packagist.org", "rubygems.org",
})

TIER1_SUFFIXES: tuple[str, ...] = (".gov", ".edu", ".gov.br", ".edu.br", ".gov.uk", ".ac.uk")

TIER2_DOMAINS: frozenset[str] = frozenset({
    "wikipedia.org", "en.wikipedia.org", "pt.wikipedia.org",
    "stackoverflow.com", "stackexchange.com", "superuser.com",
    "serverfault.com", "askubuntu.com",
    "nature.com", "science.org", "ieee.org", "acm.org",
    "theverge.com", "arstechnica.com", "infoq.com", "techcrunch.com",
    "wired.com", "zdnet.com", "engadget.com",
    "imdb.com", "metacritic.com",
    "kaggle.com", "huggingface.co",
})

TIER3_DOMAINS: frozenset[str] = frozenset({
    "medium.com", "dev.to", "css-tricks.com", "smashingmagazine.com",
    "freecodecamp.org", "digitalocean.com", "hashnode.dev",
    "blog.google", "engineering.fb.com", "netflixtechblog.com",
    "bbc.com", "reuters.com", "apnews.com", "nytimes.com",
    "theguardian.com", "washingtonpost.com", "wsj.com", "ft.com",
    "news.ycombinator.com",
    "producthunt.com", "indiehackers.com",
    "khanacademy.org", "coursera.org", "udemy.com", "edx.org",
})

CATEGORY_DOMAINS: dict[str, list[str]] = {
    "research_paper": ["arxiv.org", "openreview.net", "papers.nips.cc", "nature.com",
                       "science.org", "ieee.org", "acm.org", "jstor.org", "sciencedirect.com"],
    "company": ["linkedin.com", "bloomberg.com", "reuters.com", "crunchbase.com",
                "owler.com", "zoominfo.com"],
    "people": ["linkedin.com", "twitter.com", "github.com", "scholar.google.com"],
    "financial_report": ["sec.gov", "edgar.com", "annualreports.com"],
    "product": ["producthunt.com", "g2.com", "capterra.com", "trustpilot.com"],
    "personal_site": ["medium.com", "dev.to", "substack.com", "ghost.org"],
    "code": ["github.com", "gitlab.com", "stackoverflow.com", "stackblitz.com",
             "codesandbox.io", "replit.com", "codepen.io"],
    "news": ["bbc.com", "reuters.com", "apnews.com", "nytimes.com", "theguardian.com"],
    "video": ["youtube.com", "vimeo.com", "ted.com", "twitch.tv"],
    "image": ["flickr.com", "unsplash.com", "pexels.com", "imgur.com"],
    "general": [],
}

CATEGORY_ENGINES: dict[str, list[str] | None] = {
    "research_paper": ["google", "bing", "duckduckgo"],
    "company": ["google", "bing"],
    "people": ["google", "bing"],
    "financial_report": ["google", "bing"],
    "product": ["google", "bing", "duckduckgo"],
    "personal_site": ["google", "duckduckgo"],
    "code": ["google", "bing"],
    "news": ["google", "bing", "news"],
    "video": ["google", "bing"],
    "image": ["google", "bing"],
    "general": None,
}

VAGUE_PHRASES = {
    "approximately", "around", "typically", "usually", "generally",
    "often", "sometimes", "may", "might", "could", "varies",
    "about", "roughly", "estimated", "likely", "possibly",
    "somewhat", "relatively", "fairly", "pretty much", "in some cases",
}

SPECIFIC_DATA_PATTERNS = {
    "version": r"\d+\.\d+\.\d+",
    "price": r"\$[\d,]+\.?\d*",
    "date": r"\d{4}-\d{2}-\d{2}",
    "percentage": r"\d+%",
    "semver": r"v\d+\.\d+",
    "date_short": r"\d{1,2}/\d{1,2}/\d{4}",
}