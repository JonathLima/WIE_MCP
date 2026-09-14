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
