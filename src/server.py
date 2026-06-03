from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

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


@mcp.tool()
async def web_search(
    query: str,
    time_range: str | None = None,
    categories: str | None = None,
    safesearch: str | None = None,
    limit: int = 10,
) -> str:
    return await do_web_search(
        query=query,
        time_range=time_range,
        categories=categories,
        safesearch=safesearch,
        limit=limit,
    )

@mcp.tool()
async def site_search(
    query: str,
    site: str,
    time_range: str | None = None,
    limit: int = 5,
) -> str:
    return await do_site_search(
        query=query,
        site=site,
        time_range=time_range,
        limit=limit,
    )

@mcp.tool()
async def fetch_page(url: str, max_tokens: int | None = None) -> str:
    return await do_fetch_page(url=url, max_tokens=max_tokens)

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

@mcp.tool()
async def answer(query: str, urls: list[str]) -> str:
    return await do_answer(query=query, urls=urls)

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
