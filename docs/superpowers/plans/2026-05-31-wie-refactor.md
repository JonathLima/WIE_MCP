# WIE Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix naming inconsistencies, eliminate the agent search loop, consolidate duplicate code, and rewrite the READMEs — without changing search logic or external tool names.

**Architecture:** Single shared `searxng_client.py` for all SearXNG HTTP calls. Domain tier lists live only in `constants.py`. Tool outputs are purely descriptive (no behavioral directives). All public parameters use snake_case. Server identity is unified as `"WIE"`.

**Tech Stack:** Python 3.11+, FastMCP, httpx, pydantic v2, flashrank (optional), curl_cffi (optional), nodriver (optional)

**Spec:** `docs/superpowers/specs/2026-05-31-wie-refactor-design.md`

---

## File Map

| Action | File | Reason |
|---|---|---|
| Modify | `src/constants.py` | Merge duplicate domain tier lists; single source of truth |
| Modify | `src/config.py` | Rename `SearchCategory` to `SearxngCategory` |
| Modify | `src/models.py` | All fields to snake_case |
| Create | `src/searxng_client.py` | Shared SearXNG HTTP fetch, replaces duplication |
| Create | `src/utils/text.py` | Shared `split_into_sentences()` |
| Modify | `src/utils/dedup.py` | Import tiers from constants, remove duplicate lists |
| Modify | `src/utils/highlights.py` | Import from utils/text.py |
| Modify | `src/utils/summarizer.py` | Import from utils/text.py |
| Modify | `src/tools/web_search.py` | Use searxng_client, new output format (no directives) |
| Modify | `src/tools/web_search_advanced.py` | snake_case params, use searxng_client, new output format |
| Rename+Modify | `src/tools/web_fetch.py` to `src/tools/fetch_page.py` | Filename matches tool name; add `_fetch_page_structured()` |
| Modify | `src/tools/get_contents.py` | Use `_fetch_page_structured()`, no markdown parsing |
| Modify | `src/tools/answer.py` | Cleaner output with sources quality indicator |
| Modify | `src/tools/site_search.py` | Import path update if needed |
| Modify | `src/server.py` | name="WIE", snake_case params, import fetch_page.py |
| Modify | `configs/*.json` | Key "investigator" to "wie" |
| Modify | `mcp_config.json` | Key "investigator" to "wie" |
| Overwrite | `README.md` | Corrected examples, snake_case, underscore search types |
| Overwrite | `README.pt-br.md` | Same corrections in Portuguese |
| Modify | `tests/test_constants.py` | Updated imports |
| Modify | `tests/test_models.py` | Updated field names |
| Modify | `tests/test_web_search_advanced.py` | Updated param names |
| Modify | `tests/test_highlights.py` | Updated imports |
| Modify | `tests/test_summarizer.py` | Updated imports |

---

## Task 1: Consolidate Domain Tiers in constants.py

**Files:**
- Modify: `src/constants.py`
- Test: `tests/test_constants.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_constants.py — add to existing file
from src.constants import TIER1_DOMAINS, TIER1_SUFFIXES, TIER2_DOMAINS, TIER3_DOMAINS

def test_tier1_domains_is_frozenset():
    assert isinstance(TIER1_DOMAINS, frozenset)
    assert "github.com" in TIER1_DOMAINS

def test_tier1_suffixes_tuple():
    assert isinstance(TIER1_SUFFIXES, tuple)
    assert ".gov" in TIER1_SUFFIXES

def test_tier2_domains_is_frozenset():
    assert "wikipedia.org" in TIER2_DOMAINS

def test_tier3_domains_is_frozenset():
    assert "medium.com" in TIER3_DOMAINS
```

- [ ] **Step 2: Run test to verify it fails**

```
pytest tests/test_constants.py::test_tier1_domains_is_frozenset -v
```

Expected: FAIL with `ImportError: cannot import name 'TIER1_DOMAINS' from 'src.constants'`

- [ ] **Step 3: Add unified tier definitions to constants.py**

At the top of `src/constants.py`, before the `SearchTypeConfig` dataclass, add:

```python
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
```

Then remove the old `DOMAIN_TIER_1_LIST`, `DOMAIN_TIER_2_LIST`, `DOMAIN_TIER_3_LIST` variables entirely from `src/constants.py`.

- [ ] **Step 4: Run tests**

```
pytest tests/test_constants.py -v
```

Expected: all pass.

- [ ] **Step 5: Commit**

```
git add src/constants.py tests/test_constants.py
git commit -m "refactor: consolidate domain tiers into constants.py as single source of truth"
```

---

## Task 2: Fix Name Collision in config.py

**Files:**
- Modify: `src/config.py`

- [ ] **Step 1: Rename SearchCategory to SearxngCategory**

In `src/config.py`, change the type alias:

```python
# Before
SearchCategory = Literal[
    "general", "news", "images", "videos",
    "music", "it", "science", "files", "social media",
]
```

```python
# After
SearxngCategory = Literal[
    "general", "news", "images", "videos",
    "music", "it", "science", "files", "social media",
]
```

Update the `SearxngConfig.default_category` field type:

```python
default_category: SearxngCategory = Field(
    default="general",
    validation_alias=AliasChoices("SEARXNG_DEFAULT_CATEGORY", "default_category"),
    description="Default search category when none specified",
)
```

- [ ] **Step 2: Verify no import errors**

```
python -c "from src.config import get_searxng_config, SearxngCategory; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```
git add src/config.py
git commit -m "refactor: rename SearchCategory to SearxngCategory to avoid collision with models.py"
```

---

## Task 3: Migrate models.py to Full snake_case

**Files:**
- Modify: `src/models.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_models.py — add to existing file
from src.models import SearchResultAdvanced, SearchRequestAdvanced, ContentItem

def test_search_result_advanced_snake_case():
    r = SearchResultAdvanced(
        title="Test",
        url="https://example.com",
        domain_tier=1,
        score=80.0,
    )
    assert r.domain_tier == 1
    assert r.word_count == 0
    assert r.published_date is None

def test_search_request_advanced_snake_case():
    req = SearchRequestAdvanced(query="test")
    assert req.num_results == 10
    assert req.enable_highlights is True
    assert req.search_type.value == "auto"

def test_content_item_snake_case():
    item = ContentItem(url="https://example.com")
    assert item.status_code == 200
    assert item.word_count == 0
```

- [ ] **Step 2: Run to verify they fail**

```
pytest tests/test_models.py::test_search_result_advanced_snake_case -v
```

Expected: FAIL with `ValidationError` or `AttributeError`

- [ ] **Step 3: Update models.py**

Replace the `SearchRequestAdvanced` class:

```python
class SearchRequestAdvanced(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    search_type: SearchType = Field(default=SearchType.AUTO)
    num_results: int = Field(default=10, ge=1, le=100)
    category: Optional[SearchCategory] = None
    include_domains: Optional[list[str]] = None
    exclude_domains: Optional[list[str]] = None
    start_published_date: Optional[str] = None
    end_published_date: Optional[str] = None
    start_crawl_date: Optional[str] = None
    end_crawl_date: Optional[str] = None
    include_text: Optional[list[str]] = None
    exclude_text: Optional[list[str]] = None
    user_location: Optional[UserLocation] = None
    safesearch: Optional[int] = Field(default=0, ge=0, le=2)
    enable_highlights: bool = Field(default=True)
    highlight_sentences: int = Field(default=3, ge=1, le=10)
    enable_summary: bool = Field(default=False)
    additional_queries: bool = Field(default=True)
```

Replace `SearchResultAdvanced`:

```python
class SearchResultAdvanced(BaseModel):
    title: str
    url: HttpUrl
    snippet: str = ""
    published_date: Optional[str] = None
    author: Optional[str] = None
    domain: str = ""
    domain_tier: int = Field(ge=1, le=4)
    score: float = Field(ge=0.0)
    highlights: list[str] = Field(default_factory=list)
    summary: Optional[str] = None
    word_count: int = 0
```

Replace `SearchResponseAdvanced`:

```python
class SearchResponseAdvanced(BaseModel):
    query: str
    results: list[SearchResultAdvanced]
    search_type: str
    total_found: int
    additional_queries_used: list[str] = Field(default_factory=list)
    incomplete_results: bool = False
```

Replace `ContentItem`:

```python
class ContentItem(BaseModel):
    url: str
    status_code: int = 200
    title: str = ""
    author: Optional[str] = None
    published_date: Optional[str] = None
    word_count: int = 0
    content: str = ""
    highlights: list[str] = Field(default_factory=list)
    summary: Optional[str] = None
    raw: Optional[str] = None
```

- [ ] **Step 4: Run tests**

```
pytest tests/test_models.py -v
```

Expected: all pass.

- [ ] **Step 5: Commit**

```
git add src/models.py tests/test_models.py
git commit -m "refactor: migrate all models to snake_case field names"
```

---

## Task 4: Create src/searxng_client.py and src/utils/text.py

**Files:**
- Create: `src/searxng_client.py`
- Create: `src/utils/text.py`

- [ ] **Step 1: Create src/utils/text.py**

```python
# src/utils/text.py
from __future__ import annotations

import re

_SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+')


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentences on . ! ? boundaries."""
    return [s.strip() for s in _SENTENCE_SPLIT.split(text) if s.strip()]
```

- [ ] **Step 2: Create src/searxng_client.py**

```python
# src/searxng_client.py
from __future__ import annotations

import logging

import httpx

from src.config import get_searxng_config

logger = logging.getLogger(__name__)


async def fetch_search_results(params: dict, timeout: float) -> list[dict]:
    """Execute a single HTTP GET to SearXNG and return the raw results list.

    Args:
        params: SearXNG query parameters (q, format, engines, safesearch, etc.)
        timeout: HTTP timeout in seconds.

    Returns:
        List of raw result dicts from SearXNG. Empty list on empty response.

    Raises:
        httpx.ConnectError: SearXNG is unreachable.
        httpx.TimeoutException: Request exceeded timeout.
        httpx.HTTPStatusError: SearXNG returned a non-2xx status.
    """
    config = get_searxng_config()
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(config.search_url, params=params)
        response.raise_for_status()
        data = response.json()

    results: list[dict] = data.get("results", [])
    logger.debug(
        "searxng_client: %d results for q=%r", len(results), params.get("q")
    )
    return results
```

- [ ] **Step 3: Verify both imports work**

```
python -c "from src.searxng_client import fetch_search_results; from src.utils.text import split_into_sentences; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```
git add src/searxng_client.py src/utils/text.py
git commit -m "feat: add shared searxng_client and utils/text modules"
```

---

## Task 5: Update dedup.py, highlights.py, summarizer.py

**Files:**
- Modify: `src/utils/dedup.py`
- Modify: `src/utils/highlights.py`
- Modify: `src/utils/summarizer.py`

- [ ] **Step 1: Update dedup.py**

Remove the `TIER1_DOMAINS`, `TIER1_SUFFIXES`, `TIER2_DOMAINS`, `TIER3_DOMAINS` constant blocks from `src/utils/dedup.py` and replace with one import line:

```python
from src.constants import TIER1_DOMAINS, TIER1_SUFFIXES, TIER2_DOMAINS, TIER3_DOMAINS
```

Keep `get_domain_tier()`, `normalize_url()`, `deduplicate_and_score()`, and all other functions exactly as they are.

- [ ] **Step 2: Update highlights.py**

In `src/utils/highlights.py`, remove the `_split_into_sentences` function definition and `import re` (if only used for that). Add at the top:

```python
from src.utils.text import split_into_sentences as _split_into_sentences
```

Ensure the rest of `highlights.py` (the `_score_sentence` and `extract_highlights` functions) is unchanged.

- [ ] **Step 3: Update summarizer.py**

In `src/utils/summarizer.py`, remove the `_split_into_sentences` function definition and `import re` (if only used for that). Add:

```python
from src.utils.text import split_into_sentences as _split_into_sentences
```

Keep `extractive_summary` unchanged.

- [ ] **Step 4: Run tests**

```
pytest tests/test_highlights.py tests/test_summarizer.py tests/test_constants.py -v
```

Expected: all pass.

- [ ] **Step 5: Commit**

```
git add src/utils/dedup.py src/utils/highlights.py src/utils/summarizer.py
git commit -m "refactor: remove duplicate code, import from shared constants and text modules"
```

---

## Task 6: Reform Tool Outputs and Fix the Agent Loop

**Files:**
- Modify: `src/tools/web_search.py`
- Modify: `src/tools/web_search_advanced.py`
- Test: `tests/test_web_search_advanced.py`

This task eliminates the root cause of the agent loop: behavioral directives in tool output.

- [ ] **Step 1: Update web_search.py**

Add `from urllib.parse import urlparse` at the top.

Replace the `_fetch_from_searxng` function with an import:

```python
from src.searxng_client import fetch_search_results
```

Replace `_format_search_response` with:

```python
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
```

Remove `_format_error` and replace the exception handlers in `web_search()` with inline concise strings:

```python
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
```

Inside `web_search()`, replace the `_fetch_from_searxng` call:

```python
    raw_results = await fetch_search_results(params, timeout=config.timeout)
    engines_list = [e.strip() for e in params.get("engines", "").split(",") if e.strip()]
```

Remove the `_TIER_LABELS` dict (no longer used).

- [ ] **Step 2: Update web_search_advanced.py**

Add `from src.searxng_client import fetch_search_results` and remove the local `_fetch_from_searxng` function.

Replace `_format_advanced_response`:

```python
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
```

Update `web_search_advanced()` signature to snake_case:

```python
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
```

Update `_execute_search` to accept `search_type` instead of `type`, and update all internal references (`numResults` to `num_results`, `enableHighlights` to `enable_highlights`, `includeDomains` to `include_domains`, etc.).

Update `_build_advanced_result` to use snake_case model fields (`domain_tier`, `word_count`, `published_date`).

Update the `_format_advanced_response` call in the main function body.

- [ ] **Step 3: Update tests/test_web_search_advanced.py**

Replace all camelCase parameter names with snake_case in every test call. Example:

```python
# Before
result = await web_search_advanced(query="python", numResults=5, enableHighlights=False)

# After
result = await web_search_advanced(query="python", num_results=5, enable_highlights=False)
```

- [ ] **Step 4: Run tests**

```
pytest tests/ -v --tb=short
```

Expected: all pass.

- [ ] **Step 5: Commit**

```
git add src/tools/web_search.py src/tools/web_search_advanced.py tests/test_web_search_advanced.py
git commit -m "fix: remove behavioral directives from outputs, fix agent search loop"
```

---

## Task 7: Rename web_fetch.py and Fix get_contents

**Files:**
- Rename+Modify: `src/tools/web_fetch.py` to `src/tools/fetch_page.py`
- Modify: `src/tools/get_contents.py`
- Modify: `src/tools/answer.py`

- [ ] **Step 1: Rename the file**

```
git mv src/tools/web_fetch.py src/tools/fetch_page.py
```

- [ ] **Step 2: Refactor fetch_page.py to expose _fetch_page_structured()**

Extract the body of `fetch_page()` into a new private `_build_fetch_response()` function. The public `fetch_page()` calls it and formats the result as markdown. The new `_fetch_page_structured()` calls it and returns the raw object.

Add at the end of `src/tools/fetch_page.py`:

```python
async def _build_fetch_response(request: FetchRequest, config: FetchConfig) -> FetchResponse:
    """Core fetch logic. Returns a FetchResponse. Called by both fetch_page() and _fetch_page_structured()."""
    # Move everything from fetch_page() between request validation and "return response.markdown" here.
    # Return the FetchResponse object directly instead of response.markdown.
    ...


async def fetch_page(url: str, max_tokens: int | None = None) -> str:
    config = get_fetch_config()
    token_budget = max_tokens or config.token_budget
    try:
        request = FetchRequest(url=url, max_tokens=token_budget)
    except Exception as exc:
        return f"## Invalid URL\n{exc}"
    try:
        response = await _build_fetch_response(request, config)
        return response.markdown
    except Exception as exc:
        logger.error("fetch_page error for %s: %s", url, exc, exc_info=True)
        return f"## Fetch Error\n{exc}"


async def _fetch_page_structured(url: str, max_tokens: int | None = None) -> FetchResponse | None:
    """Internal-only. Returns FetchResponse directly. Used by get_contents to skip markdown parsing."""
    config = get_fetch_config()
    token_budget = max_tokens or config.token_budget
    try:
        request = FetchRequest(url=url, max_tokens=token_budget)
        return await _build_fetch_response(request, config)
    except Exception as exc:
        logger.warning("_fetch_page_structured failed for %s: %s", url, exc)
        return None
```

- [ ] **Step 3: Update get_contents.py**

Replace `_fetch_single_url` entirely:

```python
from src.tools.fetch_page import _fetch_page_structured


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
```

Update the output section in `get_contents()` to use `status_code` (snake_case):

```python
lines.append(f"**Status:** {item['status_code']}")
```

Also update `enable_summary` parameter name (was `enableSummary`):

```python
async def get_contents(
    urls: list[str],
    highlight_query: Optional[str] = None,
    highlight_sentences: int = 3,
    enable_summary: bool = False,
    max_tokens: int = 8000,
) -> str:
```

- [ ] **Step 4: Update answer.py output**

Replace the output block in `answer()`:

```python
    lines = [f'## Answer: "{query}"', ""]
    lines.append(answer_text)
    lines.append("")
    lines.append("---")
    lines.append(f"Sources ({len(urls)}):")
    for url in urls:
        lines.append(f"- {url}")

    return "\n".join(lines)
```

- [ ] **Step 5: Run full tests**

```
pytest tests/ -v --tb=short
```

Expected: all pass.

- [ ] **Step 6: Commit**

```
git add src/tools/fetch_page.py src/tools/get_contents.py src/tools/answer.py
git commit -m "refactor: rename web_fetch to fetch_page, fix get_contents to use structured response"
```

---

## Task 8: Update server.py and All Config Files

**Files:**
- Modify: `src/server.py`
- Modify: `configs/claude-desktop.json`
- Modify: `configs/cursor.json`
- Modify: `configs/http-remote.json`
- Modify: `configs/lm-studio.json`
- Modify: `configs/vscode-cline.json`
- Modify: `configs/windsurf.json`
- Modify: `configs/zed.json`
- Modify: `mcp_config.json`

- [ ] **Step 1: Update server.py**

Change:

```python
from src.tools.web_fetch import fetch_page as do_fetch_page
```

to:

```python
from src.tools.fetch_page import fetch_page as do_fetch_page
```

Change the FastMCP instantiation:

```python
mcp = FastMCP(
    name="WIE",
    host=server_config.host,
    port=server_config.port,
)
```

Update the `web_search_advanced` tool registration to snake_case parameters:

```python
@mcp.tool()
async def web_search_advanced(
    query: str,
    search_type: str = "auto",
    num_results: int = 10,
    category: str | None = None,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    start_published_date: str | None = None,
    end_published_date: str | None = None,
    start_crawl_date: str | None = None,
    end_crawl_date: str | None = None,
    include_text: list[str] | None = None,
    exclude_text: list[str] | None = None,
    user_location: dict | None = None,
    safesearch: int | None = None,
    enable_highlights: bool = True,
    highlight_sentences: int = 3,
    enable_summary: bool = False,
    additional_queries: bool = True,
) -> str:
    return await do_web_search_advanced(
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
```

Update `get_contents` tool registration (`enableSummary` to `enable_summary`):

```python
@mcp.tool()
async def get_contents(
    urls: list[str],
    highlight_query: str | None = None,
    highlight_sentences: int = 3,
    enable_summary: bool = False,
    max_tokens: int = 8000,
) -> str:
    return await do_get_contents(
        urls=urls,
        highlight_query=highlight_query,
        highlight_sentences=highlight_sentences,
        enable_summary=enable_summary,
        max_tokens=max_tokens,
    )
```

- [ ] **Step 2: Update all config JSON files**

`configs/claude-desktop.json`:
```json
{
  "mcpServers": {
    "wie": {
      "command": "python",
      "args": ["-m", "src.server", "stdio"]
    }
  }
}
```

`configs/cursor.json`, `configs/vscode-cline.json`, `configs/windsurf.json`, `configs/zed.json` — change only the key from `"investigator"` to `"wie"`, preserving everything else in each file.

`configs/http-remote.json`:
```json
{
  "mcpServers": {
    "wie": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

`configs/lm-studio.json`:
```json
{
  "mcpServers": {
    "wie": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

`mcp_config.json` (root):
```json
{
  "mcpServers": {
    "wie": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

- [ ] **Step 3: Verify server starts in stdio mode**

```
python -m src.server stdio
```

Expected output: `MCP server starting in STDIO mode`  
Press Ctrl+C to stop.

- [ ] **Step 4: Run full test suite**

```
pytest tests/ -v --tb=short
```

Expected: all pass.

- [ ] **Step 5: Commit**

```
git add src/server.py configs/ mcp_config.json
git commit -m "feat: rename server to WIE, all configs use wie key, snake_case tool params"
```

---

## Task 9: Rewrite README.md and README.pt-br.md

**Files:**
- Overwrite: `README.md`
- Overwrite: `README.pt-br.md`

- [ ] **Step 1: Rewrite README.md**

Use this exact structure. Every example must reflect the actual code as it stands after all previous tasks.

```markdown
# WIE — Web Investigator Engine

> Privacy-first, self-hosted, zero-cost web search for AI agents

[![AGPLv3 License](badge)] [![Python 3.11+](badge)]

[Brief one-paragraph description of what WIE is]

🇧🇷 [Versão em Português](./README.pt-br.md)

---

## Why WIE?
[Comparison table vs Exa Search — same as existing but verified]

## Architecture
[ASCII diagram — update web_fetch.py to fetch_page.py]

## Search Types
[Table with correct underscore names: instant, fast, auto, deep_lite, deep, deep_reasoning]

## Quick Start

### 1. Clone and configure
git clone ...
cp .env.example .env
# Edit .env

### 2. Start with Docker
docker compose up -d

### 3. Add to your AI client
[Show configs/claude-desktop.json with "wie" key]

## Configuration (.env)
[Full table of all env vars]

## Tools Reference

### web_search
Parameters: query, time_range, categories, safesearch, limit
[Example with snake_case only]

### web_search_advanced
Parameters: query, search_type, num_results, category, include_domains,
  exclude_domains, start_published_date, end_published_date,
  start_crawl_date (reserved, not yet filtered by SearXNG backend),
  end_crawl_date (reserved), include_text, exclude_text, user_location,
  safesearch, enable_highlights, highlight_sentences, enable_summary, additional_queries
[Example with snake_case only]

### site_search
Parameters: query, site, time_range, limit

### fetch_page
Parameters: url, max_tokens

### get_contents
Parameters: urls, highlight_query, highlight_sentences, enable_summary, max_tokens

### answer
Parameters: query, urls

## Client Setup
[claude-desktop, cursor, zed, windsurf, vscode-cline — all with "wie" key]

## Development
[pytest commands, contributing guide]
```

- [ ] **Step 2: Rewrite README.pt-br.md**

Same structure and corrections as README.md, translated into Brazilian Portuguese.

- [ ] **Step 3: Commit**

```
git add README.md README.pt-br.md
git commit -m "docs: rewrite READMEs — correct params, search types, WIE identity"
```

---

## Task 10: Final Verification

- [ ] **Step 1: Run full test suite**

```
pytest tests/ -v
```

Expected: all pass, zero import errors.

- [ ] **Step 2: Verify server starts**

```
python -m src.server http
```

Expected: `MCP server starting on 0.0.0.0:8000 (Streamable HTTP)`  
Ctrl+C to stop.

- [ ] **Step 3: Verify no old camelCase param names remain in src/**

```
grep -rn "numResults\|enableHighlights\|enableSummary\|additionalQueries\|includeDomains\|excludeDomains\|startPublishedDate\|endPublishedDate" src/
```

Expected: no matches.

- [ ] **Step 4: Verify no old identifiers remain**

```
grep -rn "web_fetch\|DOMAIN_TIER_1_LIST\|DOMAIN_TIER_2_LIST\|Web Search & Fetch MCP\|\"investigator\"" src/ configs/ mcp_config.json
```

Expected: no matches.

- [ ] **Step 5: Verify no duplicate _split_into_sentences**

```
grep -rn "def _split_into_sentences\|def split_into_sentences" src/
```

Expected: only in `src/utils/text.py`.

- [ ] **Step 6: Final commit**

```
git add -A
git commit -m "chore: WIE refactor complete — naming, loop fix, consolidation, docs"
```
