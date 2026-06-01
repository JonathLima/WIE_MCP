# WIE Refactor — Design Spec
**Date:** 2026-05-31  
**Scope:** Naming fixes, loop fix, code consolidation, README rewrite  
**Approach:** Output-First Refactor (Approach 2)

---

## 1. Goal

Fix three reported problems without changing the external behavior of the system:

1. **Agent loop** — the LLM keeps calling `web_search` repeatedly because the tool output contains directives that instruct more actions
2. **Naming inconsistency** — mix of camelCase and snake_case across public tool parameters, duplicate domain tier lists, `SearchCategory` name collision, `type` as parameter name (Python reserved word)
3. **README errors** — wrong parameter names in examples, inconsistent hyphen vs underscore in search type names, undocumented or incorrect config keys

---

## 2. Identity

| Layer | Before | After |
|---|---|---|
| `FastMCP(name=...)` | `"Web Search & Fetch MCP"` | `"WIE"` |
| Config key in all JSON files | `"investigator"` | `"wie"` |

All config files under `configs/` and `mcp_config.json` at root use `"wie"` as the MCP server key.

---

## 3. Naming Conventions

**Rule:** all public tool parameters use `snake_case`. No exceptions.

### 3.1 Tool parameter renames (server.py)

| Before | After |
|---|---|
| `type` | `search_type` |
| `numResults` | `num_results` |
| `enableHighlights` | `enable_highlights` |
| `enableSummary` | `enable_summary` |
| `additionalQueries` | `additional_queries` |
| `includeDomains` | `include_domains` |
| `excludeDomains` | `exclude_domains` |
| `startPublishedDate` | `start_published_date` |
| `endPublishedDate` | `end_published_date` |
| `startCrawlDate` | `start_crawl_date` |
| `endCrawlDate` | `end_crawl_date` |
| `includeText` | `include_text` |
| `excludeText` | `exclude_text` |
| `userLocation` | `user_location` |
| `highlight_sentences` | unchanged (already snake_case) |

### 3.2 Model field renames (models.py)

All fields in `SearchRequestAdvanced`, `SearchResultAdvanced`, `SearchResponseAdvanced` migrate to snake_case:

| Before | After |
|---|---|
| `numResults` | `num_results` |
| `includeDomains` | `include_domains` |
| `excludeDomains` | `exclude_domains` |
| `startPublishedDate` | `start_published_date` |
| `endPublishedDate` | `end_published_date` |
| `startCrawlDate` | `start_crawl_date` |
| `endCrawlDate` | `end_crawl_date` |
| `includeText` | `include_text` |
| `excludeText` | `exclude_text` |
| `userLocation` | `user_location` |
| `enableHighlights` | `enable_highlights` |
| `enableSummary` | `enable_summary` |
| `additionalQueries` | `additional_queries` |
| `domainTier` | `domain_tier` |
| `wordCount` | `word_count` |
| `publishedDate` | `published_date` |
| `searchType` | `search_type` |
| `totalFound` | `total_found` |
| `additionalQueriesUsed` | `additional_queries_used` |
| `incompleteResults` | `incomplete_results` |
| `statusCode` | `status_code` |
| `wordCount` | `word_count` |

### 3.3 Name collision resolution

`SearchCategory` in `config.py` (a `Literal[...]` of SearXNG categories) is renamed to `SearxngCategory` to avoid collision with the `SearchCategory` enum in `models.py`.

### 3.4 Domain tier list consolidation

`TIER1_DOMAINS`, `TIER2_DOMAINS`, `TIER3_DOMAINS` in `dedup.py` and `DOMAIN_TIER_1_LIST`, `DOMAIN_TIER_2_LIST`, `DOMAIN_TIER_3_LIST` in `constants.py` are merged into a single set of names in `constants.py`. `dedup.py` imports from `constants.py`. No duplication.

---

## 4. Output Reform (Loop Fix)

### 4.1 Root cause

The `web_search` tool appends `OPERATIONAL GUIDELINES FOR THE RESEARCHER` to every response. This block contains imperative instructions (`NEVER trust a snippet`, `Always use fetch_page`, `try site_search`) that the LLM reads as a directive, causing it to call more tools in a loop.

### 4.2 Fix

Remove all behavioral directives from tool outputs. Tool outputs must **describe** findings only. They must never **prescribe** what the model should do next.

### 4.3 New output format (web_search and web_search_advanced)

```
## Search Results — {n} results
Query: `{query}`

### 1. {title}
URL: {url}
Source: {tier_emoji} {domain} · Score: {score}
Snippet: {snippet}
[Highlights:]
> {highlight}
[Published: {date}]

---
```

- Tier emoji only: 🟢 🔵 🟡 ⚪ (no verbose label)
- No guidelines block
- No "IMPORTANT: verify with fetch_page" banner
- Highlights shown inline when enabled, not as a separate section

### 4.4 get_contents fix

`get_contents` currently calls `fetch_page()` (which returns a markdown string) and then parses that string with fragile heuristics (`if "## " in content`). This breaks when heading format changes.

**Fix:** Create an internal `_fetch_page_structured()` function in `fetch_page.py` that returns a `FetchResponse` object. `get_contents` calls this directly and reads structured fields (`title`, `content`, `word_count`), bypassing markdown parsing entirely.

The public `fetch_page()` tool keeps returning markdown (unchanged for external callers). Only `get_contents` uses the structured internal function.

### 4.5 answer output

Add a clear "Sources used" section with per-source extraction quality indicator so the model knows the answer is complete and can stop.

---

## 5. Code Consolidation

### 5.1 New file: src/searxng_client.py

`_fetch_from_searxng()` is currently duplicated in `web_search.py` and `web_search_advanced.py`. Both implementations are nearly identical.

Extract to `src/searxng_client.py`:

```python
async def fetch_search_results(params: dict, timeout: float) -> list[dict]:
    """Single source of truth for all SearXNG HTTP calls."""
```

Both `web_search.py` and `web_search_advanced.py` import from here.

### 5.2 File rename: web_fetch.py → fetch_page.py

`web_fetch.py` contains the `fetch_page` tool. The filename should match the tool name. Rename to `fetch_page.py`. All imports updated accordingly.

### 5.3 _split_into_sentences deduplication

`_split_into_sentences()` is defined identically in both `highlights.py` and `summarizer.py`. Extract to a shared `utils/text.py` module. Both files import from there.

---

## 6. README Rewrite

Both `README.md` (EN) and `README.pt-br.md` (PT-BR) are rewritten with:

- All search type names use underscore: `deep_lite`, `deep_reasoning` (not `deep-lite`, `deep-reasoning`)
- All parameter examples use snake_case
- Config examples show `"wie"` as the server key
- `start_crawl_date` / `end_crawl_date` documented as "reserved, not yet supported by SearXNG backend"
- Speed table completed (was missing Rerank and Best For columns)
- Quick Start instructions verified against actual code

---

## 7. What Does NOT Change

- Search logic (query expansion, variations, semaphore concurrency)
- FlashRank reranking
- nodriver / curl_cffi fetch fallback chain
- Scoring algorithm (tier + age + engine reliability + specific data)
- All existing tool names (`web_search`, `web_search_advanced`, `site_search`, `fetch_page`, `get_contents`, `answer`)
- Docker / docker-compose setup
- SearXNG settings
- Test file structure (tests updated to match new param names only)
