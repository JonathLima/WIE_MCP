# AIHawk Stealth Browser Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate AIHawk's invisible-playwright stealth browser into WIE_MCP as both an automatic fallback for scraping protected/dynamic pages and an interactive browser toolset for autonomous agents.

**Architecture:** A native Python module `src/browser/` manages lazy initialization of `invisible-playwright` (stealth-patched Firefox). It integrates into `src/tools/fetch_page.py` as a Tier 2 anti-bot / SPA fallback and into `src/server.py` exposing atomic FastMCP tools (`browser_navigate`, `browser_snapshot`, `browser_click`, `browser_type`, `browser_take_screenshot`, `browser_evaluate`, `browser_close`).

**Tech Stack:** Python 3.11+, invisible-playwright >= 0.15.0, FastMCP, pydantic-settings, pytest, pytest-asyncio.

---

### Task 1: Dependencies and Browser Configuration

**Files:**
- Modify: `requirements.txt`
- Create: `src/browser/__init__.py`
- Create: `src/browser/config.py`
- Modify: `src/config.py`
- Create: `tests/test_browser_config.py`

- [ ] **Step 1: Write the failing test for browser configuration**

```python
# tests/test_browser_config.py
from src.browser.config import BrowserConfig

def test_browser_config_defaults():
    config = BrowserConfig()
    assert config.enabled is True
    assert config.headless is True
    assert config.timeout == 30.0
    assert config.proxy == ""
    assert config.profile_dir == ""
    assert config.viewport_width == 1280
    assert config.viewport_height == 800

def test_browser_config_env_override(monkeypatch):
    monkeypatch.setenv("BROWSER_ENABLED", "false")
    monkeypatch.setenv("BROWSER_HEADLESS", "false")
    monkeypatch.setenv("BROWSER_TIMEOUT_SECONDS", "45.0")
    monkeypatch.setenv("BROWSER_PROXY", "http://127.0.0.1:8080")
    
    config = BrowserConfig()
    assert config.enabled is False
    assert config.headless is False
    assert config.timeout == 45.0
    assert config.proxy == "http://127.0.0.1:8080"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `rtk ./venv/Scripts/python -m pytest tests/test_browser_config.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'src.browser'`

- [ ] **Step 3: Update dependencies and implement `BrowserConfig`**

Add `invisible-playwright>=0.15.0` to `requirements.txt`.

Create `src/browser/__init__.py`:
```python
"""Stealth browser automation module for WIE_MCP based on invisible-playwright."""
```

Create `src/browser/config.py`:
```python
from __future__ import annotations

from functools import lru_cache
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict

class BrowserConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("BROWSER_ENABLED", "browser_enabled"),
        description="Enable stealth browser support for scraping and agent navigation",
    )
    headless: bool = Field(
        default=True,
        validation_alias=AliasChoices("BROWSER_HEADLESS", "browser_headless"),
        description="Run the stealth browser in headless mode",
    )
    timeout: float = Field(
        default=30.0,
        gt=0,
        validation_alias=AliasChoices("BROWSER_TIMEOUT_SECONDS", "browser_timeout"),
        description="Default timeout in seconds for browser operations",
    )
    proxy: str = Field(
        default="",
        validation_alias=AliasChoices("BROWSER_PROXY", "browser_proxy"),
        description="Optional proxy URL (http:// or socks5://)",
    )
    profile_dir: str = Field(
        default="",
        validation_alias=AliasChoices("BROWSER_PROFILE_DIR", "browser_profile_dir"),
        description="Optional persistent profile directory to retain cookies and logins",
    )
    viewport_width: int = Field(
        default=1280,
        ge=320,
        validation_alias=AliasChoices("BROWSER_VIEWPORT_WIDTH", "viewport_width"),
        description="Browser viewport width",
    )
    viewport_height: int = Field(
        default=800,
        ge=240,
        validation_alias=AliasChoices("BROWSER_VIEWPORT_HEIGHT", "viewport_height"),
        description="Browser viewport height",
    )

@lru_cache(maxsize=1)
def get_browser_config() -> BrowserConfig:
    return BrowserConfig()
```

Export `get_browser_config` and `BrowserConfig` in `src/config.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `rtk ./venv/Scripts/python -m pytest tests/test_browser_config.py -v`  
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
rtk git add requirements.txt src/browser/__init__.py src/browser/config.py src/config.py tests/test_browser_config.py
rtk git commit -m "feat(browser): add browser config and requirements"
```

---

### Task 2: Page Snapshot Utility

**Files:**
- Create: `src/browser/snapshot.py`
- Create: `tests/test_browser_snapshot.py`

- [ ] **Step 1: Write the failing test for DOM snapshot generation**

```python
# tests/test_browser_snapshot.py
from src.browser.snapshot import parse_interactive_snapshot

SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head><title>Login Page</title></head>
<body>
    <header><h1>Welcome Back</h1></header>
    <main>
        <form action="/login" method="post">
            <label for="username">Username</label>
            <input type="text" id="username" name="user" placeholder="Enter username" />
            
            <label for="password">Password</label>
            <input type="password" id="password" name="pass" />
            
            <button type="submit" id="submit-btn">Sign In</button>
            <a href="/forgot" class="link-forgot">Forgot Password?</a>
        </form>
    </main>
</body>
</html>
"""

def test_parse_interactive_snapshot():
    snapshot = parse_interactive_snapshot(SAMPLE_HTML, title="Login Page", url="https://example.com/login")
    assert "# Page Snapshot: Login Page" in snapshot
    assert "https://example.com/login" in snapshot
    assert '[1] <input type="text" id="username" name="user">' in snapshot
    assert '[2] <input type="password" id="password" name="pass">' in snapshot
    assert '[3] <button id="submit-btn">Sign In</button>' in snapshot
    assert '[4] <a class="link-forgot" href="/forgot">Forgot Password?</a>' in snapshot
```

- [ ] **Step 2: Run test to verify it fails**

Run: `rtk ./venv/Scripts/python -m pytest tests/test_browser_snapshot.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'src.browser.snapshot'`

- [ ] **Step 3: Implement `src/browser/snapshot.py`**

```python
from __future__ import annotations

from bs4 import BeautifulSoup

INTERACTIVE_TAGS = {"a", "button", "input", "select", "textarea"}
INTERACTIVE_ROLES = {"button", "link", "checkbox", "radio", "textbox", "menuitem", "tab"}

def parse_interactive_snapshot(html: str, title: str = "", url: str = "") -> str:
    soup = BeautifulSoup(html, "html.parser")
    lines: list[str] = []
    
    lines.append(f"# Page Snapshot: {title or 'Untitled Page'}")
    if url:
        lines.append(f"**URL:** {url}")
    lines.append("")
    lines.append("## Interactive Elements")
    
    count = 0
    for el in soup.find_all(True):
        tag_name = el.name.lower()
        role = el.get("role", "").lower()
        is_clickable = el.get("onclick") or el.get("cursor") == "pointer"
        
        if tag_name not in INTERACTIVE_TAGS and role not in INTERACTIVE_ROLES and not is_clickable:
            continue
            
        count += 1
        attrs = []
        if el.get("id"):
            attrs.append(f'id="{el["id"]}"')
        if el.get("name"):
            attrs.append(f'name="{el["name"]}"')
        if el.get("type"):
            attrs.append(f'type="{el["type"]}"')
        if el.get("class"):
            classes = " ".join(el["class"]) if isinstance(el["class"], list) else str(el["class"])
            attrs.append(f'class="{classes}"')
        if el.get("href"):
            attrs.append(f'href="{el["href"]}"')
            
        attr_str = " " + " ".join(attrs) if attrs else ""
        text = el.get_text(strip=True)
        if len(text) > 60:
            text = text[:57] + "..."
            
        if tag_name in ("input", "img"):
            label = f' Label: "{el.get("placeholder", "") or el.get("aria-label", "") or el.get("value", "")}"' if (el.get("placeholder") or el.get("aria-label") or el.get("value")) else ""
            lines.append(f"- [{count}] <{tag_name}{attr_str}>{label}")
        else:
            lines.append(f"- [{count}] <{tag_name}{attr_str}>{text}</{tag_name}>")
            
    if count == 0:
        lines.append("_No interactive elements found on page._")
        
    return "\n".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `rtk ./venv/Scripts/python -m pytest tests/test_browser_snapshot.py -v`  
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
rtk git add src/browser/snapshot.py tests/test_browser_snapshot.py
rtk git commit -m "feat(browser): add interactive DOM snapshot parser"
```

---

### Task 3: Stealth Browser Engine Lifecycle

**Files:**
- Create: `src/browser/engine.py`
- Create: `tests/test_browser_engine.py`

- [ ] **Step 1: Write unit tests for `StealthBrowserEngine`**

```python
# tests/test_browser_engine.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.browser.engine import StealthBrowserEngine
from src.browser.config import BrowserConfig

@pytest.mark.asyncio
async def test_engine_is_available_flag():
    with patch("src.browser.engine.PLAYWRIGHT_AVAILABLE", False):
        engine = StealthBrowserEngine(BrowserConfig())
        assert engine.is_available() is False

@pytest.mark.asyncio
async def test_engine_one_shot_fetch_html():
    engine = StealthBrowserEngine(BrowserConfig())
    
    mock_page = AsyncMock()
    mock_page.content = AsyncMock(return_value="<html><body>Rendered DOM</body></html>")
    mock_page.title = AsyncMock(return_value="Rendered Title")
    mock_page.goto = AsyncMock()
    mock_page.close = AsyncMock()
    
    mock_context = AsyncMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)
    
    mock_browser = AsyncMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    
    mock_pw = AsyncMock()
    mock_pw.firefox.launch = AsyncMock(return_value=mock_browser)
    
    engine._playwright = mock_pw
    engine._browser = mock_browser
    
    html, title = await engine.fetch_page_html("https://example.com")
    assert html == "<html><body>Rendered DOM</body></html>"
    assert title == "Rendered Title"
    mock_page.goto.assert_awaited_once()
    mock_page.close.assert_awaited_once()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `rtk ./venv/Scripts/python -m pytest tests/test_browser_engine.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'src.browser.engine'`

- [ ] **Step 3: Implement `src/browser/engine.py`**

```python
from __future__ import annotations

import asyncio
import logging
from typing import Optional

from src.browser.config import BrowserConfig, get_browser_config

logger = logging.getLogger(__name__)

try:
    from invisible_playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    try:
        from playwright.async_api import async_playwright
        PLAYWRIGHT_AVAILABLE = True
    except ImportError:
        PLAYWRIGHT_AVAILABLE = False
        logger.warning("invisible-playwright not installed; browser engine unavailable")

class StealthBrowserEngine:
    _instance: Optional[StealthBrowserEngine] = None
    _lock = asyncio.Lock()

    def __init__(self, config: Optional[BrowserConfig] = None) -> None:
        self.config = config or get_browser_config()
        self._playwright = None
        self._browser = None
        self._context = None
        self._is_started = False

    @classmethod
    async def get_instance(cls, config: Optional[BrowserConfig] = None) -> StealthBrowserEngine:
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(config)
        return cls._instance

    def is_available(self) -> bool:
        return PLAYWRIGHT_AVAILABLE and self.config.enabled

    async def start(self) -> None:
        if self._is_started or not self.is_available():
            return

        async with self._lock:
            if self._is_started:
                return
            logger.info("Initializing stealth browser engine (Firefox)...")
            try:
                self._playwright = await async_playwright().start()
                launch_args = {}
                if self.config.proxy:
                    launch_args["proxy"] = {"server": self.config.proxy}

                self._browser = await self._playwright.firefox.launch(
                    headless=self.config.headless,
                    **launch_args,
                )
                self._context = await self._browser.new_context(
                    viewport={"width": self.config.viewport_width, "height": self.config.viewport_height}
                )
                self._is_started = True
                logger.info("Stealth browser engine ready.")
            except Exception as exc:
                logger.error("Failed to launch stealth browser: %s", exc)
                await self.stop()
                raise

    async def stop(self) -> None:
        async with self._lock:
            if self._context:
                try:
                    await self._context.close()
                except Exception:
                    pass
                self._context = None

            if self._browser:
                try:
                    await self._browser.close()
                except Exception:
                    pass
                self._browser = None

            if self._playwright:
                try:
                    await self._playwright.stop()
                except Exception:
                    pass
                self._playwright = None

            self._is_started = False
            logger.info("Stealth browser engine stopped.")

    async def fetch_page_html(self, url: str, wait_until: str = "load", timeout_seconds: Optional[float] = None) -> tuple[str, str]:
        if not self.is_available():
            raise RuntimeError("Stealth browser is not available or disabled.")

        if not self._is_started:
            await self.start()

        timeout = (timeout_seconds or self.config.timeout) * 1000
        page = await self._context.new_page()
        try:
            await page.goto(url, wait_until=wait_until, timeout=timeout)
            # Short stabilization pause for anti-bot interstitials and dynamic hydration
            await page.wait_for_timeout(1500)
            content = await page.content()
            title = await page.title()
            return content, title
        finally:
            await page.close()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `rtk ./venv/Scripts/python -m pytest tests/test_browser_engine.py -v`  
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
rtk git add src/browser/engine.py tests/test_browser_engine.py
rtk git commit -m "feat(browser): implement stealth browser engine lifecycle"
```

---

### Task 4: Interactive Session and Browser Actions

**Files:**
- Create: `src/browser/session.py`
- Create: `src/browser/actions.py`
- Create: `tests/test_browser_actions.py`

- [ ] **Step 1: Write unit tests for interactive browser actions**

```python
# tests/test_browser_actions.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.browser.session import BrowserSession
from src.browser.actions import BrowserActions

@pytest.mark.asyncio
async def test_session_navigate():
    mock_page = AsyncMock()
    mock_page.goto = AsyncMock()
    mock_page.title = AsyncMock(return_value="Target Page")
    mock_page.url = "https://example.com/target"
    mock_page.content = AsyncMock(return_value="<html><body>Content</body></html>")
    
    session = BrowserSession(mock_page)
    actions = BrowserActions(session)
    
    result = await actions.navigate("https://example.com/target")
    assert "Navigated to: https://example.com/target" in result
    assert "Title: Target Page" in result
    mock_page.goto.assert_awaited_once()

@pytest.mark.asyncio
async def test_session_type():
    mock_page = AsyncMock()
    mock_page.fill = AsyncMock()
    mock_page.press = AsyncMock()
    
    session = BrowserSession(mock_page)
    actions = BrowserActions(session)
    
    result = await actions.type_text("#input", "hello", press_enter=True)
    assert 'Typed "hello" into selector "#input"' in result
    mock_page.fill.assert_awaited_once_with("#input", "hello")
    mock_page.press.assert_awaited_once_with("#input", "Enter")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `rtk ./venv/Scripts/python -m pytest tests/test_browser_actions.py -v`  
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement `src/browser/session.py` and `src/browser/actions.py`**

Create `src/browser/session.py`:
```python
from __future__ import annotations

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class BrowserSession:
    def __init__(self, page) -> None:
        self.page = page

    async def current_url(self) -> str:
        return self.page.url

    async def current_title(self) -> str:
        return await self.page.title()

    async def get_html(self) -> str:
        return await self.page.content()
```

Create `src/browser/actions.py`:
```python
from __future__ import annotations

import json
import logging
from typing import Optional

from src.browser.session import BrowserSession
from src.browser.snapshot import parse_interactive_snapshot

logger = logging.getLogger(__name__)

class BrowserActions:
    def __init__(self, session: BrowserSession) -> None:
        self.session = session
        self.page = session.page

    async def navigate(self, url: str, wait_until: str = "load", timeout_seconds: float = 30.0) -> str:
        timeout_ms = timeout_seconds * 1000
        await self.page.goto(url, wait_until=wait_until, timeout=timeout_ms)
        await self.page.wait_for_timeout(1000)
        title = await self.session.current_title()
        current_url = await self.session.current_url()
        return f"Successfully navigated to: {current_url}\n**Title:** {title}"

    async def snapshot(self, interactive_only: bool = True) -> str:
        html = await self.session.get_html()
        title = await self.session.current_title()
        url = await self.session.current_url()
        return parse_interactive_snapshot(html, title=title, url=url)

    async def click(self, selector: Optional[str] = None, text: Optional[str] = None) -> str:
        if not selector and not text:
            raise ValueError("Either selector or text must be provided to click.")

        target = selector if selector else f"text={text}"
        await self.page.click(target)
        await self.page.wait_for_timeout(1000)
        current_url = await self.session.current_url()
        title = await self.session.current_title()
        return f'Clicked element "{target}".\nCurrent page: {title} ({current_url})'

    async def type_text(self, selector: str, text: str, press_enter: bool = False, clear_first: bool = True) -> str:
        if clear_first:
            await self.page.fill(selector, text)
        else:
            await self.page.type(selector, text)

        if press_enter:
            await self.page.press(selector, "Enter")
            await self.page.wait_for_timeout(1000)

        return f'Typed "{text}" into selector "{selector}" (press_enter={press_enter}).'

    async def take_screenshot(self) -> bytes:
        return await self.page.screenshot(type="png", full_page=False)

    async def evaluate(self, expression: str) -> str:
        result = await self.page.evaluate(expression)
        return json.dumps(result, ensure_ascii=False, indent=2)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `rtk ./venv/Scripts/python -m pytest tests/test_browser_actions.py -v`  
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
rtk git add src/browser/session.py src/browser/actions.py tests/test_browser_actions.py
rtk git commit -m "feat(browser): add interactive browser session and actions"
```

---

### Task 5: Integrate Stealth Browser Fallback in `fetch_page`

**Files:**
- Modify: `src/tools/fetch_page.py`
- Modify: `tests/test_fetch_page.py`

- [ ] **Step 1: Write test for stealth browser fallback trigger in `fetch_page`**

```python
# tests/test_fetch_page_stealth.py
import pytest
from unittest.mock import AsyncMock, patch
from src.tools.fetch_page import _build_fetch_response
from src.models import FetchRequest
from src.config import FetchConfig

@pytest.mark.asyncio
async def test_fetch_page_stealth_fallback_when_challenge_detected():
    config = FetchConfig()
    request = FetchRequest(url="https://protected.example.com")

    with patch("src.tools.fetch_page._fetch_with_curl_cffi", new_callable=AsyncMock) as mock_curl, \
         patch("src.tools.fetch_page._fetch_with_stealth_browser", new_callable=AsyncMock) as mock_stealth:
        
        # curl_cffi gets cloudflare challenge
        mock_curl.return_value = ("<html><title>Just a moment...</title>cf-browser-verification</html>", 403, "text/html")
        # stealth browser returns clear rendered DOM
        mock_stealth.return_value = ("<html><title>Clean Article</title><body><h1>Real Article</h1><p>Legitimate content.</p></body></html>", 200, "text/html")

        resp = await _build_fetch_response(request, config)
        assert "Clean Article" in resp.title
        assert "Real Article" in resp.content
        mock_stealth.assert_awaited_once()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `rtk ./venv/Scripts/python -m pytest tests/test_fetch_page_stealth.py -v`  
Expected: FAIL

- [ ] **Step 3: Update `src/tools/fetch_page.py` with `_fetch_with_stealth_browser`**

Add helper function in `src/tools/fetch_page.py`:
```python
from src.browser.engine import StealthBrowserEngine

async def _fetch_with_stealth_browser(url: str, config: FetchConfig) -> tuple[str, int, str]:
    engine = await StealthBrowserEngine.get_instance()
    if not engine.is_available():
        raise RuntimeError("Stealth browser engine is not available")
    html, title = await engine.fetch_page_html(url, timeout_seconds=config.timeout)
    return html, 200, "text/html"
```

In `_build_fetch_response`, place `_fetch_with_stealth_browser` after `_fetch_with_curl_cffi` whenever `html_content is None` or a challenge is detected:
```python
    if html_content is None or _is_challenge_html(html_content):
        engine = await StealthBrowserEngine.get_instance()
        if engine.is_available():
            try:
                logger.info("Attempting fetch with stealth browser (invisible-playwright): %s", url_str)
                html_content, status_code, content_type = await _fetch_with_stealth_browser(url_str, config)
                fetch_method = "stealth_browser"
                if _should_discard_status(status_code) or _is_challenge_html(html_content):
                    html_content = None
            except Exception as exc:
                logger.warning("Stealth browser fetch failed for %s: %s", url_str, exc)
                html_content = None
```

- [ ] **Step 4: Run test suite to verify all fetch tests pass**

Run: `rtk ./venv/Scripts/python -m pytest tests/test_fetch_page.py tests/test_fetch_page_stealth.py -v`  
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
rtk git add src/tools/fetch_page.py tests/test_fetch_page_stealth.py
rtk git commit -m "feat(fetch): add invisible-playwright stealth browser fallback"
```

---

### Task 6: Expose Interactive Stealth Browser Tools in FastMCP Server

**Files:**
- Modify: `src/server.py`
- Create: `tests/test_server_browser_tools.py`

- [ ] **Step 1: Write integration tests for server browser tools**

```python
# tests/test_server_browser_tools.py
import pytest
from unittest.mock import AsyncMock, patch
from src.server import browser_navigate, browser_snapshot, browser_click, browser_type, browser_evaluate

@pytest.mark.asyncio
async def test_server_browser_navigate():
    with patch("src.server.get_active_browser_actions", new_callable=AsyncMock) as mock_get_actions:
        mock_actions = AsyncMock()
        mock_actions.navigate = AsyncMock(return_value="Successfully navigated to: https://example.com")
        mock_get_actions.return_value = mock_actions

        res = await browser_navigate("https://example.com")
        assert "Successfully navigated" in res
```

- [ ] **Step 2: Run test to verify it fails**

Run: `rtk ./venv/Scripts/python -m pytest tests/test_server_browser_tools.py -v`  
Expected: FAIL with `ImportError: cannot import name 'browser_navigate' from 'src.server'`

- [ ] **Step 3: Register interactive tools in `src/server.py`**

In `src/server.py`:
- Add session holder:
```python
from mcp.types import Image
from src.browser.engine import StealthBrowserEngine
from src.browser.session import BrowserSession
from src.browser.actions import BrowserActions

_active_session: BrowserSession | None = None
_active_actions: BrowserActions | None = None

async def get_active_browser_actions() -> BrowserActions:
    global _active_session, _active_actions
    if _active_actions is None:
        engine = await StealthBrowserEngine.get_instance()
        await engine.start()
        page = await engine._context.new_page()
        _active_session = BrowserSession(page)
        _active_actions = BrowserActions(_active_session)
    return _active_actions
```

- Expose FastMCP tools:
  - `@mcp.tool(...) async def browser_navigate(url: str, wait_until: str = "load", timeout_seconds: float = 30.0) -> str`
  - `@mcp.tool(...) async def browser_snapshot(interactive_only: bool = True) -> str`
  - `@mcp.tool(...) async def browser_click(selector: str | None = None, text: str | None = None) -> str`
  - `@mcp.tool(...) async def browser_type(selector: str, text: str, press_enter: bool = False, clear_first: bool = True) -> str`
  - `@mcp.tool(...) async def browser_take_screenshot() -> Image`
  - `@mcp.tool(...) async def browser_evaluate(expression: str) -> str`
  - `@mcp.tool(...) async def browser_close() -> str`

- Register clean shutdown on server lifespan.

- [ ] **Step 4: Run test to verify it passes**

Run: `rtk ./venv/Scripts/python -m pytest tests/test_server_browser_tools.py -v`  
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
rtk git add src/server.py tests/test_server_browser_tools.py
rtk git commit -m "feat(server): expose interactive stealth browser tools in FastMCP"
```

---

### Task 7: Full Test Suite Verification & Documentation

**Files:**
- Modify: `README.md`
- Modify: `README.pt-br.md`

- [ ] **Step 1: Run the full test suite**

Run: `rtk ./venv/Scripts/python -m pytest`  
Expected: All tests PASS (>95 tests)

- [ ] **Step 2: Update documentation**

Document the new stealth browser engine, setup command (`python -m invisible_playwright fetch`), configuration variables, and the new MCP tools in both `README.md` and `README.pt-br.md`.

- [ ] **Step 3: Commit documentation updates**

```bash
rtk git add README.md README.pt-br.md
rtk git commit -m "docs: document stealth browser integration and interactive tools"
```
