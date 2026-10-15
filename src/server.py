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
    instructions=(
        "WIE (Web Intelligence Engine) is a local, privacy-first search and content extraction service. "
        "Use web_search or web_search_advanced whenever you need real-time facts, current news, online documentation, or internet research. "
        "Use fetch_page or get_contents to extract and read full markdown content from specific web URLs. "
        "Use site_search to find information restricted to a single domain. "
        "For bot-protected, Cloudflare, or dynamic JavaScript-heavy sites, use the browser_* tools."
    ),
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
    """Search the web for up-to-date information, news, documentation, and real-time facts across multiple engines with deduplication, domain scoring, and ranking.

    Use this tool whenever you need current information from the internet, facts beyond knowledge cutoff, or reference sources.

    Args:
        query: The search query string.
        time_range: Optional filter for recent results: 'day', 'week', 'month', or 'year'.
        categories: Optional category filter: 'general', 'news', 'science', 'it', etc.
        safesearch: SafeSearch filtering level ('0'=off, '1'=moderate, '2'=strict).
        limit: Maximum number of results to return (1-20, default: 10).
        language: Two-letter language code or 'auto' (e.g. 'en', 'pt-BR', 'auto').
    """
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
    """Search specifically within a single target domain or website (e.g. github.com, python.org, docs.rs).

    Use this tool when looking for documentation, code, issues, or articles restricted to a specific domain.

    Args:
        query: The search terms.
        site: The target domain or host (e.g. 'github.com', 'developer.mozilla.org').
        time_range: Optional time range: 'day', 'week', 'month', 'year'.
        limit: Maximum number of results to return (default: 5).
        language: Two-letter language code or 'auto'.
    """
    return await do_site_search(
        query=query,
        site=site,
        time_range=time_range,
        limit=limit,
        language=language,
    )

@mcp.tool(annotations=ToolAnnotations(title="Fetch Page", readOnlyHint=True))
async def fetch_page(url: str, max_tokens: int | None = None, language: str = "auto") -> str:
    """Fetch and extract readable content, tables, structured metadata, and links from a web URL as clean Markdown.

    Includes stealth anti-bot protection (TLS fingerprint impersonation and stealth browser fallback)
    for protected sites like Cloudflare, Reddit, or single-page apps.
    Use this tool whenever you need to read the full text or inspect details of a specific URL.

    Args:
        url: The web page URL to fetch.
        max_tokens: Optional token budget limit for truncation.
        language: Language preference header for localized content (default: 'auto').
    """
    return await do_fetch_page(url=url, max_tokens=max_tokens, language=language)

@mcp.tool(annotations=ToolAnnotations(title="Web Search Advanced", readOnlyHint=True))
async def web_search_advanced(
    query: str,
    search_type: str = "deep",
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
    """Perform an advanced deep web search with query expansion, domain filtering, date ranges, content highlights, and extractive summarization.

    Use this tool for comprehensive or complex research tasks requiring multi-engine queries, strict date filters, or domain exclusions.

    Args:
        query: The primary search query.
        search_type: Search depth preset: 'fast', 'auto', 'deep', or 'deep_lite' (default: 'deep').
        num_results: Number of results to return (default: 10).
        category: Optional search category ('general', 'news', 'science', 'it', etc.).
        include_domains: Whitelist of domains to include in results.
        exclude_domains: Blacklist of domains to exclude from results.
        start_published_date: Filter results published on or after date (YYYY-MM-DD).
        end_published_date: Filter results published on or before date (YYYY-MM-DD).
        start_crawl_date: Filter results crawled on or after date (YYYY-MM-DD).
        end_crawl_date: Filter results crawled on or before date (YYYY-MM-DD).
        include_text: Keywords that must be present in content snippet.
        exclude_text: Keywords that must not appear in content snippet.
        user_location: Optional dict with location hints (country, city).
        safesearch: SafeSearch level (0=off, 1=moderate, 2=strict).
        enable_highlights: Whether to extract keyword sentence highlights (default: True).
        highlight_sentences: Number of highlight sentences to show (default: 3).
        enable_summary: Whether to generate an extractive summary (default: False).
        additional_queries: Whether to run automatic query expansions (default: True).
        language: Search language code or 'auto'.
    """
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
    """Batch fetch and extract clean markdown content from multiple URLs concurrently.

    Use this tool when you have multiple URLs (e.g. from search results) and need to read them all in parallel.

    Args:
        urls: List of web page URLs to fetch concurrently.
        highlight_query: Optional search query to highlight relevant sentences.
        highlight_sentences: Number of highlight sentences per match (default: 3).
        enable_summary: Whether to generate an extractive summary per URL (default: False).
        max_tokens: Maximum total tokens for the combined output (default: 8000).
    """
    return await do_get_contents(
        urls=urls,
        highlight_query=highlight_query,
        highlight_sentences=highlight_sentences,
        enable_summary=enable_summary,
        max_tokens=max_tokens,
    )

@mcp.tool(annotations=ToolAnnotations(title="Answer", readOnlyHint=True))
async def answer(query: str, urls: list[str]) -> str:
    """Extract evidence from multiple URLs and synthesize a direct, cited answer to a specific question.

    Use this tool when you have a question and a list of candidate source URLs to extract the answer from.

    Args:
        query: The question or inquiry to answer.
        urls: List of URLs to fetch and analyze for the answer.
    """
    return await do_answer(query=query, urls=urls)

_active_session: BrowserSession | None = None
_active_actions: BrowserActions | None = None
_session_lock = asyncio.Lock()


async def get_active_browser_actions() -> BrowserActions:
    global _active_session, _active_actions
    async with _session_lock:
        if _active_actions is not None and _active_session is not None:
            if hasattr(_active_session.page, "is_closed") and _active_session.page.is_closed():
                _active_actions = None
                _active_session = None

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
