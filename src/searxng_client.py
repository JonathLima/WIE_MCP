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
