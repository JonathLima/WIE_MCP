from __future__ import annotations

import json
import logging
from typing import Optional

from src.browser.session import BrowserSession
from src.browser.snapshot import parse_interactive_snapshot

logger = logging.getLogger(__name__)


class BrowserActions:
    """Executes high-level agentic browser actions against an active session."""

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

    async def type_text(
        self,
        selector: str,
        text: str,
        press_enter: bool = False,
        clear_first: bool = True,
    ) -> str:
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

    async def close(self) -> str:
        await self.session.close()
        return "Browser session closed."
