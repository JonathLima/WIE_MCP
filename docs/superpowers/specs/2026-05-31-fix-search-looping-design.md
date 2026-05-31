# Design Spec: Fix Search Looping & Env Config Issues in WIE_MCP

## Context & Problem Statement
When an AI agent uses the WIE_MCP server for search queries, it occasionally enters an infinite loop of search attempts without producing any results. This looping behavior is caused by three underlying issues:
1. **Silent Suppression of Exceptions**: In [web_search_advanced.py](file:///C:/Users/JonathanLima/Documents/WIE_MCP/src/tools/web_search_advanced.py), the `_execute_search` function catches and silences exceptions from query variations. If all variations fail (due to connection errors or timeouts), it returns an empty list, yielding a tool response of `## No Results Found`. The AI agent interprets this as a successful search with zero matches, leading it to continuously rephrase the query and retry in an infinite loop.
2. **Missing Environment Mapping in Config**: The Pydantic Settings classes in [config.py](file:///C:/Users/JonathanLima/Documents/WIE_MCP/src/config.py) do not map fields to prefixed environment variables (e.g. `SEARXNG_HOST`, `SEARCH_TIMEOUT_SECONDS`, etc.) defined in `.env`. Consequently, local settings are ignored, causing connections to fall back to the default `http://searxng:8080`, which is unreachable outside Docker.
3. **Python 3.14 Compatibility Issue**: The `nodriver` library contains a non-UTF-8 symbol in its CDP module, raising a `SyntaxError` on import in Python 3.14. Because [web_fetch.py](file:///C:/Users/JonathanLima/Documents/WIE_MCP/src/tools/web_fetch.py) only caught `ImportError`, this crash prevented the server from starting or responding.

---

## Proposed Changes

### 1. Robust Import Safeguard (Done)
Catch `SyntaxError` alongside `ImportError` when importing `nodriver` in `web_fetch.py` to ensure compatibility under Python 3.14.

### 2. Pydantic Settings Environment Mapping
Modify `src/config.py` using Pydantic's `AliasChoices` validation aliases to map configuration fields to their respective environment variables.
- **SearxngConfig**:
  - `host` -> `AliasChoices("SEARXNG_HOST", "host")`
  - `engines` -> `AliasChoices("SEARXNG_ENGINES", "engines")`
  - `default_category` -> `AliasChoices("SEARXNG_DEFAULT_CATEGORY", "default_category")`
  - `safesearch` -> `AliasChoices("SEARXNG_SAFESEARCH", "safesearch")`
  - `default_limit` -> `AliasChoices("SEARCH_DEFAULT_LIMIT", "default_limit")`
  - `timeout` -> `AliasChoices("SEARCH_TIMEOUT_SECONDS", "timeout")`
- **FetchConfig**:
  - `timeout` -> `AliasChoices("FETCH_TIMEOUT_SECONDS", "timeout")`
  - `max_content_length` -> `AliasChoices("FETCH_MAX_CONTENT_LENGTH", "max_content_length")`
  - `token_budget` -> `AliasChoices("FETCH_TOKEN_BUDGET", "token_budget")`
- **ServerConfig**:
  - `host` -> `AliasChoices("MCP_SERVER_HOST", "host")`
  - `port` -> `AliasChoices("MCP_SERVER_PORT", "port")`
  - `api_key` -> `AliasChoices("API_KEY", "api_key")`
  - `default_search_type` -> `AliasChoices("SEARCH_DEFAULT_TYPE", "default_search_type")`

### 3. Propagate Systematic Search Failures in Advanced Search
Refactor `_execute_search` in `web_search_advanced.py` to:
- Capture both results and exceptions from each variation task.
- If **all** variations raise exceptions (meaning the search backend is entirely unreachable/offline), raise the last exception.
- If at least one variation succeeds, return the successful results and log any partial failures.

---

## Verification Plan

### Automated Tests
1. **Config Verification**: Add tests in a new file `tests/test_config.py` to assert that:
   - Configuration is correctly parsed from environment variables (mocked using `monkeypatch`).
   - Default fallbacks are maintained when variables are unset.
2. **Error Propagation Verification**: Update `tests/test_web_search_advanced.py` to mock `_fetch_from_searxng` raising connection or timeout errors. Verify that calling `web_search_advanced` correctly returns markdown error responses instead of "No Results Found".
3. **Execution**: Run `venv/Scripts/pytest.exe` to ensure all tests pass.
