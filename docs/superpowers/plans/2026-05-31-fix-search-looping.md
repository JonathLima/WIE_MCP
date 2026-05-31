# Fix Search Looping & Env Config Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the infinite looping issue in internet searches by propagating search errors, mapping environment variables properly in the configuration, and keeping the README files updated.

**Architecture:** Use Pydantic Settings' validation aliases to load configurations from `.env`. Track search variation results/exceptions in advanced search, raising an exception if all variations fail to prevent infinite looping of LLM query rephrasing.

**Tech Stack:** Python, Pydantic Settings, HTTPX, Pytest, Markdown.

---

### Task 1: Update Configuration Mappings
**Files:**
- Modify: `src/config.py`

- [ ] **Step 1: Write changes to `src/config.py` to add `AliasChoices` for environment variables.**

Add the import for `AliasChoices` and configure the validation aliases for all fields in `SearxngConfig`, `FetchConfig`, and `ServerConfig`.

```python
# target in src/config.py
from pydantic import Field, field_validator, AliasChoices
```

Complete `SearxngConfig` with aliases:
```python
class SearxngConfig(BaseSettings):
    host: str = Field(
        default="http://searxng:8080",
        validation_alias=AliasChoices("SEARXNG_HOST", "host"),
    )
    engines: str = Field(
        default="google,duckduckgo,bing,wikipedia,startpage",
        validation_alias=AliasChoices("SEARXNG_ENGINES", "engines"),
    )
    default_category: SearchCategory = Field(
        default="general",
        validation_alias=AliasChoices("SEARXNG_DEFAULT_CATEGORY", "default_category"),
    )
    safesearch: SafeSearchLevel = Field(
        default="0",
        validation_alias=AliasChoices("SEARXNG_SAFESEARCH", "safesearch"),
    )
    default_limit: int = Field(
        default=10,
        ge=1,
        le=20,
        validation_alias=AliasChoices("SEARCH_DEFAULT_LIMIT", "default_limit"),
    )
    timeout: float = Field(
        default=10.0,
        gt=0,
        validation_alias=AliasChoices("SEARCH_TIMEOUT_SECONDS", "timeout"),
    )
```

Complete `FetchConfig` with aliases:
```python
class FetchConfig(BaseSettings):
    timeout: float = Field(
        default=15.0,
        gt=0,
        validation_alias=AliasChoices("FETCH_TIMEOUT_SECONDS", "timeout"),
    )
    max_content_length: int = Field(
        default=10000,
        ge=1000,
        le=100000,
        validation_alias=AliasChoices("FETCH_MAX_CONTENT_LENGTH", "max_content_length"),
    )
    token_budget: int = Field(
        default=8000,
        ge=1000,
        le=128000,
        validation_alias=AliasChoices("FETCH_TOKEN_BUDGET", "token_budget"),
    )
    max_redirects: int = Field(default=5, ge=0, le=10)
    max_concurrent_browsers: int = Field(default=2, ge=1, le=10)
```

Complete `ServerConfig` with aliases:
```python
class ServerConfig(BaseSettings):
    host: str = Field(
        default="0.0.0.0",
        validation_alias=AliasChoices("MCP_SERVER_HOST", "host"),
    )
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        validation_alias=AliasChoices("MCP_SERVER_PORT", "port"),
    )
    api_key: str = Field(
        default="",
        validation_alias=AliasChoices("API_KEY", "api_key"),
    )
    default_search_type: str = Field(
        default="auto",
        validation_alias=AliasChoices("SEARCH_DEFAULT_TYPE", "default_search_type"),
    )
```

- [ ] **Step 2: Commit Task 1**

```bash
git add src/config.py
git commit -m "feat: add validation aliases for configuration settings"
```

---

### Task 2: Create Configuration Loading Tests
**Files:**
- Create: `tests/test_config.py`

- [ ] **Step 1: Write test file `tests/test_config.py` to assert that settings map correctly.**

```python
import pytest
from src.config import SearxngConfig, FetchConfig, ServerConfig

def test_searxng_config_aliases(monkeypatch):
    monkeypatch.setenv("SEARXNG_HOST", "http://my-searxng:1234")
    monkeypatch.setenv("SEARXNG_ENGINES", "google,bing")
    monkeypatch.setenv("SEARCH_DEFAULT_LIMIT", "15")
    monkeypatch.setenv("SEARCH_TIMEOUT_SECONDS", "8.5")

    # Clear cache by creating a new instance
    cfg = SearxngConfig()
    assert cfg.host == "http://my-searxng:1234"
    assert cfg.engines == "google,bing"
    assert cfg.default_limit == 15
    assert cfg.timeout == 8.5

def test_fetch_config_aliases(monkeypatch):
    monkeypatch.setenv("FETCH_TIMEOUT_SECONDS", "12.0")
    monkeypatch.setenv("FETCH_MAX_CONTENT_LENGTH", "5000")
    monkeypatch.setenv("FETCH_TOKEN_BUDGET", "4000")

    cfg = FetchConfig()
    assert cfg.timeout == 12.0
    assert cfg.max_content_length == 5000
    assert cfg.token_budget == 4000

def test_server_config_aliases(monkeypatch):
    monkeypatch.setenv("MCP_SERVER_HOST", "127.0.0.1")
    monkeypatch.setenv("MCP_SERVER_PORT", "9000")
    monkeypatch.setenv("API_KEY", "secret-test-key")
    monkeypatch.setenv("SEARCH_DEFAULT_TYPE", "deep")

    cfg = ServerConfig()
    assert cfg.host == "127.0.0.1"
    assert cfg.port == 9000
    assert cfg.api_key == "secret-test-key"
    assert cfg.default_search_type == "deep"
```

- [ ] **Step 2: Run configuration tests and verify they pass**

Run: `venv\Scripts\pytest.exe tests/test_config.py`
Expected: PASS (3 tests passed)

- [ ] **Step 3: Commit Task 2**

```bash
git add tests/test_config.py
git commit -m "test: add configuration environment mapping tests"
```

---

### Task 3: Error Propagation in Advanced Search
**Files:**
- Modify: `src/tools/web_search_advanced.py`

- [ ] **Step 1: Update `_execute_search` function to propagate systematic failures.**

Change `_execute_search` so that it returns results and errors, and raises if all fail:

```python
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

    tasks = []
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
    
    all_results = []
    errors = []
    for vr, err in variation_results:
        if err:
            errors.append(err)
        else:
            all_results.extend(vr)

    # If all variations failed, raise the last exception
    if len(errors) == len(tasks) and errors:
        raise errors[-1]

    return all_results
```

- [ ] **Step 2: Commit Task 3**

```bash
git add src/tools/web_search_advanced.py
git commit -m "feat: propagate exceptions in web_search_advanced when all variations fail"
```

---

### Task 4: Test Advanced Search Error Handling
**Files:**
- Modify: `tests/test_web_search_advanced.py`

- [ ] **Step 1: Write error propagation tests in `tests/test_web_search_advanced.py`**

Add tests that verify connection error and timeout propagation:

```python
# Append to tests/test_web_search_advanced.py

@pytest.mark.asyncio
async def test_web_search_advanced_propagates_connection_error():
    import httpx
    with patch("src.tools.web_search_advanced._fetch_from_searxng") as mock_fetch:
        mock_fetch.side_effect = httpx.ConnectError("Cannot connect")
        result = await web_search_advanced(query="test", type="deep_lite")
        assert "Connection Error" in result
        assert "Cannot connect" in result or "SearxNG" in result

@pytest.mark.asyncio
async def test_web_search_advanced_propagates_timeout():
    import httpx
    with patch("src.tools.web_search_advanced._fetch_from_searxng") as mock_fetch:
        mock_fetch.side_effect = httpx.TimeoutException("Timed out")
        result = await web_search_advanced(query="test", type="deep_lite")
        assert "Timeout" in result
```

- [ ] **Step 2: Run all tests in test suite and ensure they pass.**

Run: `venv\Scripts\pytest.exe`
Expected: PASS (35 tests passed)

- [ ] **Step 3: Commit Task 4**

```bash
git add tests/test_web_search_advanced.py
git commit -m "test: add connection and timeout error propagation tests for advanced search"
```

---

### Task 5: Update README files
**Files:**
- Modify: `README.md`
- Modify: `README.pt-br.md`

- [ ] **Step 1: Update `README.md` to document the Pydantic configuration load and search modes.**
- [ ] **Step 2: Update `README.pt-br.md` similarly.**

- [ ] **Step 3: Commit Task 5**

```bash
git add README.md README.pt-br.md
git commit -m "docs: update english and portuguese readmes with config mapping and error behavior details"
```

---

### Task 6: Final Verification
- [ ] **Step 1: Run pytest to ensure everything works without regression.**
- [ ] **Step 2: Commit final status.**
