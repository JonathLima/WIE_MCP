from __future__ import annotations

import asyncio
import logging
from typing import Optional

from src.browser.config import BrowserConfig, get_browser_config

logger = logging.getLogger(__name__)

try:
    from invisible_playwright.async_api import InvisiblePlaywright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    InvisiblePlaywright = None
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("invisible-playwright not installed; browser engine unavailable")


class StealthBrowserEngine:
    _instance: Optional[StealthBrowserEngine] = None
    _lock = asyncio.Lock()

    def __init__(self, config: Optional[BrowserConfig] = None) -> None:
        self.config = config or get_browser_config()
        self._ipw = None
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
        if not PLAYWRIGHT_AVAILABLE or not self.config.enabled:
            return False
        try:
            import invisible_playwright._engine as _eng
            return _eng.resolve_executable(None) is not None
        except Exception:
            return False

    async def start(self) -> None:
        if self._is_started or not self.is_available():
            return

        async with self._lock:
            if self._is_started:
                return
            logger.info("Initializing stealth browser engine (InvisiblePlaywright Firefox)...")
            try:
                launch_kwargs = {
                    "headless": self.config.headless,
                }
                if self.config.proxy:
                    launch_kwargs["proxy"] = {"server": self.config.proxy}
                if self.config.profile_dir:
                    launch_kwargs["profile_dir"] = self.config.profile_dir

                self._ipw = InvisiblePlaywright(**launch_kwargs)
                target = await self._ipw.__aenter__()

                if hasattr(target, "new_context"):
                    self._browser = target
                    self._context = await self._browser.new_context(
                        viewport={"width": self.config.viewport_width, "height": self.config.viewport_height}
                    )
                else:
                    self._browser = None
                    self._context = target

                self._is_started = True
                logger.info("Stealth browser engine ready.")
            except Exception as exc:
                logger.error("Failed to launch stealth browser: %s", exc)
                await self.stop()
                raise

    async def stop(self) -> None:
        async with self._lock:
            if self._context and self._browser:
                try:
                    await self._context.close()
                except Exception:
                    pass
                self._context = None

            if self._ipw:
                try:
                    await self._ipw.__aexit__(None, None, None)
                except Exception:
                    pass
                self._ipw = None

            self._browser = None
            self._context = None
            self._is_started = False
            logger.info("Stealth browser engine stopped.")

    async def fetch_page_html(
        self,
        url: str,
        wait_until: str = "load",
        timeout_seconds: Optional[float] = None,
    ) -> tuple[str, str]:
        """One-shot page fetch for scraping fallback without keeping an interactive tab open."""
        if not self.is_available():
            raise RuntimeError("Stealth browser is not available or disabled.")

        if not self._is_started:
            await self.start()

        timeout = (timeout_seconds or self.config.timeout) * 1000
        page = await self._context.new_page()
        try:
            await page.goto(url, wait_until=wait_until, timeout=timeout)
            # Short stabilization pause for anti-bot interstitials and dynamic DOM hydration
            await page.wait_for_timeout(1500)
            content = await page.content()
            title = await page.title()
            return content, title
        finally:
            await page.close()
