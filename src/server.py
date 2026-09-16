from __future__ import annotations

import asyncio
import logging

from mcp.server.fastmcp import FastMCP, Image
from mcp.types import ToolAnnotations

from src.browser.engine import StealthBrowserEngine
from src.browser.session import BrowserSession
from src.browser.actions import BrowserActions

from src.config import get_server_config
from src.tools.web_search import web_search as do_web_search
from src.tools.fetch_page import fetch_page as do_fetch_page
from src.tools.site_search import site_search as do_site_search
from src.tools.web_search_advanced import web_search_advanced as do_web_search_advanced
from src.tools.get_contents import get_contents as do_get_contents
from src.tools.answer import answer as do_answer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

server_config = get_server_config()

mcp = FastMCP(
    name="WIE",
    host=server_config.host,
    port=server_config.port,
)


@mcp.tool(annotations=ToolAnnotations(title="Web Search", readOnlyHint=True))
async def web_search(
    query: str,
    time_range: str | None = None,
    categories: str | None = None,
    safesearch: str | None = None,
    limit: int = 10,
    language: str = "auto",
) -> str:
    return await do_web_search(
        query=query,
        time_range=time_range,
        categories=categories,
        safesearch=safesearch,
        limit=limit,
        language=language,
    )

@mcp.tool(annotations=ToolAnnotations(title="Site Search", readOnlyHint=True))
async def site_search(
    query: str,
    site: str,
    time_range: str | None = None,
    limit: int = 5,
    language: str = "auto",
) -> str:
    return await do_site_search(
        query=query,
        site=site,
        time_range=time_range,
        limit=limit,
        language=language,
    )

@mcp.tool(annotations=ToolAnnotations(title="Fetch Page", readOnlyHint=True))
async def fetch_page(url: str, max_tokens: int | None = None, language: str = "auto") -> str:
    return await do_fetch_page(url=url, max_tokens=max_tokens, language=language)

@mcp.tool(annotations=ToolAnnotations(title="Web Search Advanced", readOnlyHint=True))
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
    language: str = "auto",
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
        language=language,
    )

@mcp.tool(annotations=ToolAnnotations(title="Get Contents", readOnlyHint=True))
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

@mcp.tool(annotations=ToolAnnotations(title="Answer", readOnlyHint=True))
async def answer(query: str, urls: list[str]) -> str:
    return await do_answer(query=query, urls=urls)

_active_session: BrowserSession | None = None
_active_actions: BrowserActions | None = None
_session_lock = asyncio.Lock()


async def get_active_browser_actions() -> BrowserActions:
    global _active_session, _active_actions
    async with _session_lock:
        if _active_actions is None:
            engine = await StealthBrowserEngine.get_instance()
            if not engine.is_available():
                raise RuntimeError("Stealth browser engine is not available or disabled.")
            if not engine._is_started:
                await engine.start()
            page = await engine._context.new_page()
            _active_session = BrowserSession(page)
            _active_actions = BrowserActions(_active_session)
        return _active_actions


async def reset_active_browser_actions() -> None:
    global _active_session, _active_actions
    async with _session_lock:
        if _active_actions:
            try:
                await _active_actions.close()
            except Exception:
                pass
            _active_session = None
            _active_actions = None


@mcp.tool(annotations=ToolAnnotations(title="Browser Navigate", readOnlyHint=False))
async def browser_navigate(url: str, wait_until: str = "load", timeout_seconds: float = 30.0) -> str:
    """Navigate the stealth browser to a URL, bypassing anti-bot challenges and rendering dynamic JavaScript."""
    actions = await get_active_browser_actions()
    return await actions.navigate(url=url, wait_until=wait_until, timeout_seconds=timeout_seconds)


@mcp.tool(annotations=ToolAnnotations(title="Browser Snapshot", readOnlyHint=True))
async def browser_snapshot(interactive_only: bool = True) -> str:
    """Capture an interactive snapshot of the current page DOM and accessibility tree with element IDs and selectors."""
    actions = await get_active_browser_actions()
    return await actions.snapshot(interactive_only=interactive_only)


@mcp.tool(annotations=ToolAnnotations(title="Browser Click", readOnlyHint=False))
async def browser_click(selector: str | None = None, text: str | None = None) -> str:
    """Click an element matching a CSS selector or visible text using humanized cursor movement."""
    actions = await get_active_browser_actions()
    return await actions.click(selector=selector, text=text)


@mcp.tool(annotations=ToolAnnotations(title="Browser Type", readOnlyHint=False))
async def browser_type(selector: str, text: str, press_enter: bool = False, clear_first: bool = True) -> str:
    """Type text into an input or textarea element with natural human typing intervals."""
    actions = await get_active_browser_actions()
    return await actions.type_text(selector=selector, text=text, press_enter=press_enter, clear_first=clear_first)


@mcp.tool(annotations=ToolAnnotations(title="Browser Take Screenshot", readOnlyHint=True))
async def browser_take_screenshot() -> Image:
    """Take a screenshot of the current page viewport."""
    actions = await get_active_browser_actions()
    png_bytes = await actions.take_screenshot()
    return Image(data=png_bytes, format="png")


@mcp.tool(annotations=ToolAnnotations(title="Browser Evaluate", readOnlyHint=True))
async def browser_evaluate(expression: str) -> str:
    """Evaluate a read-only JavaScript expression in the context of the active page."""
    actions = await get_active_browser_actions()
    return await actions.evaluate(expression=expression)


@mcp.tool(annotations=ToolAnnotations(title="Browser Close", readOnlyHint=False))
async def browser_close() -> str:
    """Close the active interactive browser session."""
    global _active_actions
    if _active_actions is None:
        return "No active browser session to close."
    await reset_active_browser_actions()
    return "Browser session closed successfully."


def run_http() -> None:
    """Run server in Streamable HTTP mode (for remote clients - Zed compatible)."""
    logger.info(
        "MCP server starting on %s:%d (Streamable HTTP)",
        server_config.host,
        server_config.port,
    )
    mcp.run(transport="streamable-http")


def run_stdio() -> None:
    """Run server in STDIO mode (for Claude Desktop, Cursor, Zed, etc.)."""
    logger.info("MCP server starting in STDIO mode")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "http"

    if mode == "http" or mode == "sse":
        run_http()
    elif mode == "stdio":
        run_stdio()
    else:
        run_http()
