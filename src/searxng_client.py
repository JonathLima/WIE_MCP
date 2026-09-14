# src/searxng_client.py
from __future__ import annotations

import logging

import httpx

from src.config import get_searxng_config

logger = logging.getLogger(__name__)


async def fetch_search_payload(params: dict, timeout: float) -> dict:
    """Execute a single HTTP GET to SearXNG and return the full JSON payload.

    Args:
        params: SearXNG query parameters (q, format, engines, safesearch, etc.)
        timeout: HTTP timeout in seconds.

    Returns:
        Full JSON response dict from SearXNG (includes 'results', 'unresponsive_engines', etc.).

    Raises:
        httpx.ConnectError: SearXNG is unreachable.
        httpx.TimeoutException: Request exceeded timeout.
        httpx.HTTPStatusError: SearXNG returned a non-2xx status.
    """
    config = get_searxng_config()
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(config.search_url, params=params)
        response.raise_for_status()
        data: dict = response.json()

    logger.debug(
        "searxng_client: %d results for q=%r", len(data.get("results", [])), params.get("q")
    )
    return data


async def fetch_search_results(params: dict, timeout: float) -> list[dict]:
    """Wrapper around fetch_search_payload that returns only the results list.

    Kept for backward compatibility with existing call sites and mocks.
    """
    payload = await fetch_search_payload(params, timeout)
    return payload.get("results", [])
