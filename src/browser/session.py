from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class BrowserSession:
    """Manages an active tab/page session for agentic browsing."""

    def __init__(self, page) -> None:
        self.page = page

    async def current_url(self) -> str:
        return self.page.url

    async def current_title(self) -> str:
        return await self.page.title()

    async def get_html(self) -> str:
        return await self.page.content()

    async def close(self) -> None:
        try:
            await self.page.close()
        except Exception as exc:
            logger.debug("Error closing page: %s", exc)
