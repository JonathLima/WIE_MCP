# Design Document: AIHawk Stealth Browser Integration into WIE_MCP

**Date:** 2026-09-14  
**Status:** Approved  
**Author:** Antigravity & Jonathan Lima  

---

## 1. Overview & Objectives

### 1.1 Context
WIE (Web Investigator Engine) is an MCP server providing web search (via SearXNG) and content extraction (`fetch_page`, `get_contents`, `site_search`). When fetching target pages, WIE currently relies on `curl_cffi` for TLS fingerprint impersonation, an optional external binary (`obscura`), and `httpx` as a fallback. However, modern websites with dynamic JavaScript Single-Page Applications (SPAs), Cloudflare Turnstile, Datadome, Akamai, or bot mitigation mechanisms frequently block pure HTTP clients or deliver blank placeholder markup.

Meanwhile, **AIHawk** leverages `invisible-playwright`—a specialized browser engine that patches Firefox at the C++ level (fingerprinting, canvas, WebGL, WebRTC, fonts, and humanized input curves)—to browse undetected and defeat bot mitigations.

### 1.2 Goal
Integrate AIHawk's core stealth browsing capabilities into WIE_MCP under a **hybrid architecture**:
1. **Transparent Dynamic Scraping:** Enhance `fetch_page` and `get_contents` with an intelligent, pure-Python fallback using `invisible-playwright` when anti-bot challenges or dynamic JS walls are encountered.
2. **Interactive Autonomous Agent Tools:** Expose a dedicated suite of FastMCP tools (`browser_navigate`, `browser_snapshot`, `browser_click`, `browser_type`, `browser_take_screenshot`, `browser_evaluate`, `browser_close`) allowing AI clients (Claude, Cursor, Gemini) to autonomously interact with complex web applications.

---

## 2. Architecture & Components

```
                      +------------------------------------------+
                      |               MCP Clients                |
                      |        (Claude, Cursor, Gemini)          |
                      +--------------------+---------------------+
                                           |
                                           v
+------------------------------------------------------------------------------------+
|                                    FastMCP (WIE)                                   |
|                                                                                    |
|   [Search Tools]            [Extraction Tools]          [Interactive Browser Tools]|
|   - web_search              - fetch_page                - browser_navigate         |
|   - web_search_advanced     - get_contents              - browser_click            |
|   - site_search             (Intelligent Fallback)      - browser_type             |
|                                     │                   - browser_snapshot         |
|                                     │                   - browser_take_screenshot  |
|                                     ▼                   - browser_evaluate         |
|                       +──────────────────────────+      - browser_close            |
|                       |   src/browser/engine.py   | <──────────────────────────────+
|                       |   (StealthBrowserEngine) |
|                       +─────────────┬────────────+
+─────────────────────────────────────┼──────────────────────────────────────────────+
                                      │
                                      ▼
                      +──────────────────────────────────+
                      |       invisible-playwright       |
                      |   (Patched Firefox + C++ Engine) |
                      +──────────────────────────────────+
```

### 2.1 Component Breakdown

1. **`src/browser/config.py`**:
   - Manages stealth browser configuration: headless mode, proxy URL, timeout settings, persistent user profile directory (to preserve sessions and cookies), and fingerprint seed.
   - Integrated into WIE's Pydantic `BaseSettings` architecture.

2. **`src/browser/engine.py`**:
   - Manages the singleton lifecycle of `invisible-playwright`.
   - Implements lazy startup (browser is only launched when first needed) and asynchronous graceful shutdown via FastAPI/FastMCP lifespan handlers.
   - Provides a dedicated context for one-shot page scraping without polluting interactive session history.

3. **`src/browser/session.py`**:
   - Manages the active interactive browsing session for autonomous agent tasks.
   - Encapsulates human-like mouse movements (Bézier curves), natural typing cadence with jitter, and scroll behavior.

4. **`src/browser/snapshot.py`**:
   - Extracts an accessible interactive element tree (IDs, CSS selectors, role labels, and coordinates) formatted in compact Markdown so LLMs can easily decide which element to interact with.

5. **`src/browser/actions.py`**:
   - Houses the core implementations of browser actions: navigation with challenge-waiting, clicking, typing, evaluating JS, taking screenshots, and closing tabs.

---

## 3. Fallback Pipeline in `fetch_page`

When `fetch_page` or `get_contents` requests a URL:
1. **Tier 1 (Fast Static Fetch):** Execute request via `curl_cffi` with randomized Chrome TLS impersonation.
2. **Challenge & Status Detection:** Inspect the response status code and body. If HTTP 403, 429, or recognized anti-bot challenges (Cloudflare Turnstile, Datadome, Akamai, empty JS SPA skeleton) are detected:
3. **Tier 2 (Stealth Dynamic Fetch):** Dispatch request to `StealthBrowserEngine`. Launch/reuse stealth Firefox, navigate to URL, wait for challenge resolution and DOM network-idle, and extract the rendered HTML.
4. **Tier 3 (HTTP Fallback):** If `invisible-playwright` is not installed or encounters an unrecoverable failure, fall back to standard `httpx`.
5. **Readability & Formatting:** The extracted HTML from any tier is passed to WIE's existing `extract_readability_content` and markdown formatter for unified output.

---

## 4. MCP Tool Specifications

### 4.1 `browser_navigate`
- **Arguments:**
  - `url: str`: Target web address.
  - `wait_until: str = "load"`: Navigation condition (`"load"`, `"domcontentloaded"`, or `"networkidle"`).
  - `timeout_seconds: float = 30.0`: Max time to wait.
- **Returns:** Markdown summary of current page: landed URL, status code, title, and initial page overview.

### 4.2 `browser_snapshot`
- **Arguments:**
  - `interactive_only: bool = True`: If True, limits results to actionable elements (`<button>`, `<a>`, `<input>`, `<select>`, `<textarea>`, clickable ARIA roles).
- **Returns:** Compact Markdown list of actionable elements with index numbers and unique CSS selectors.

### 4.3 `browser_click`
- **Arguments:**
  - `selector: str | None = None`: CSS selector of target element.
  - `text: str | None = None`: Visible text of element to click if selector is omitted.
- **Returns:** Confirmation message with target clicked and any subsequent navigation/URL changes.

### 4.4 `browser_type`
- **Arguments:**
  - `selector: str`: CSS selector of the input field.
  - `text: str`: Text to type.
  - `press_enter: bool = False`: Whether to submit with Enter key after typing.
  - `clear_first: bool = True`: Whether to clear existing text before typing.
- **Returns:** Status message confirming input.

### 4.5 `browser_take_screenshot`
- **Arguments:** None.
- **Returns:** FastMCP `Image(data=png_bytes, format="png")` representing the current viewport.

### 4.6 `browser_evaluate`
- **Arguments:**
  - `expression: str`: JavaScript expression to evaluate.
- **Returns:** JSON serialized string of the evaluated result.

### 4.7 `browser_close`
- **Arguments:** None.
- **Returns:** Confirmation that the active browser session was closed.

---

## 5. Dependencies & Environmental Setup

- **`invisible-playwright>=0.15.0`**: Core stealth browser engine.
- **Binary Fetch:** Requires one-time download of the patched Firefox engine:
  ```bash
  python -m invisible_playwright fetch
  ```
- **Requirements Update:** Add `invisible-playwright>=0.15.0` to `requirements.txt`.

---

## 6. Verification & Quality Assurance

1. **Unit Tests:**
   - Test configuration defaults and environment overrides in `src/browser/config.py`.
   - Test snapshot generation on mock HTML pages in `tests/test_browser_snapshot.py`.
   - Test fallback trigger logic in `tests/test_fetch_page_stealth.py`.
2. **Integration Tests:**
   - Test `StealthBrowserEngine` startup, navigation, snapshotting, and cleanup on local mock servers or public safe endpoints (`tests/test_browser_engine.py`).
3. **End-to-End Verification:**
   - Execute WIE MCP server and verify tools are registered and responsive.
   - Run `fetch_page` against dynamic / protected targets to verify automatic stealth resolution.
