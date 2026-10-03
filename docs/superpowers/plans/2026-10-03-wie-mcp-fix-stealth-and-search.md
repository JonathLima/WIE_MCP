# WIE-MCP Fix: Stealth Browser, Anti-Bot Bypass, and Deep Search Optimization

**Goal:** Fix WIE-MCP's stealth browser and scraping reliability, resolve Cloudflare/Turnstile anti-bot blocks, tune SearXNG to top search engines, and establish Deep Search by default.

---

### Task 1: Dockerfile & Xvfb Entrypoint Infrastructure
- **Files:**
  - Create: `entrypoint.sh`
  - Modify: `Dockerfile`
- **Steps:**
  1. Add Linux system packages to `Dockerfile`: `xvfb`, `libgtk-3-0`, `libasound2`, `libdbus-glib-1-2`, `libx11-xcb1`, `libxtst6`, `fonts-liberation`, `procps`.
  2. Add `RUN python -m invisible_playwright fetch` in `Dockerfile` to bake the patched Firefox browser into the image.
  3. Create `entrypoint.sh` to start `Xvfb :99 -screen 0 1280x1024x24 -ac +extension GLX +render -noreset &` and export `DISPLAY=:99`.
  4. Update `Dockerfile` `ENTRYPOINT` or `CMD` to execute via `entrypoint.sh`.

### Task 2: Active Turnstile & Cloudflare Challenge Resolution in StealthBrowserEngine
- **Files:**
  - Modify: `src/browser/engine.py`
  - Modify: `tests/test_browser_engine.py`
- **Steps:**
  1. Implement `_handle_turnstile_challenge(page, timeout_seconds=8.0)` in `StealthBrowserEngine`.
  2. In `fetch_page_html`, check if the page presents a challenge (`_is_challenge_html`).
  3. If challenge detected, wait for proof-of-work auto-resolution, and if Turnstile iframe/checkbox is present, find and click it with humanized mouse movement.
  4. Ensure session cleanup and proper lock handling.

### Task 3: Realistic Chrome Navigation Headers in `curl_cffi`
- **Files:**
  - Modify: `src/tools/fetch_page.py`
- **Steps:**
  1. Update `_fetch_with_curl_cffi` to send realistic browser navigation headers (`Sec-Ch-Ua`, `Sec-Fetch-Dest: document`, `Sec-Fetch-Mode: navigate`, `Sec-Fetch-Site: none`, `Sec-Fetch-User: ?1`, `Upgrade-Insecure-Requests: 1`, `Accept`).
  2. Prevent immediate bot flags from Reddit / Cloudflare on direct HTTP requests.

### Task 4: SearXNG Tuning & Deep Search Configuration
- **Files:**
  - Modify: `searxng/settings.yml`
  - Modify: `.env`
  - Modify: `src/config.py`
- **Steps:**
  1. In `searxng/settings.yml`, prune engine list to high-performance market leaders (`google`, `bing`, `duckduckgo`, `brave`, `qwant`, `github`, `hackernews`, `arxiv`).
  2. Set `SEARCH_DEFAULT_TYPE=deep` in `.env` and `src/config.py`.
  3. Increase `SEARCH_TIMEOUT_SECONDS=25` and `FETCH_TIMEOUT_SECONDS=30`.

### Task 5: Docker Container Rebuild and Integration Verification
- **Steps:**
  1. Run local pytest suite.
  2. Rebuild Docker container: `docker compose build mcp-server`.
  3. Restart services: `docker compose up -d mcp-server`.
  4. Verify live MCP tools (`web_search`, `fetch_page`, `browser_navigate`).
