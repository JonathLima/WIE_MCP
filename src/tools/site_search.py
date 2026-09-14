from __future__ import annotations

import logging
from src.tools.web_search import web_search as do_web_search

logger = logging.getLogger(__name__)

async def site_search(
    query: str,
    site: str,
    time_range: str | None = None,
    limit: int = 5,
    language: str = "auto",
) -> str:
    site_query = f"site:{site} {query}"
    logger.info("site_search called: site=%s, query=%s", site, query)
    
    return await do_web_search(
        query=site_query,
        time_range=time_range,
        limit=limit,
        language=language,
    )
