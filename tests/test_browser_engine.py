import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.browser.engine import StealthBrowserEngine
from src.browser.config import BrowserConfig

@pytest.mark.asyncio
async def test_engine_is_available_flag():
    with patch("src.browser.engine.PLAYWRIGHT_AVAILABLE", False):
        engine = StealthBrowserEngine(BrowserConfig())
        assert engine.is_available() is False

@pytest.mark.asyncio
async def test_engine_one_shot_fetch_html():
    engine = StealthBrowserEngine(BrowserConfig())
    
    mock_page = AsyncMock()
    mock_page.content = AsyncMock(return_value="<html><body>Rendered DOM</body></html>")
    mock_page.title = AsyncMock(return_value="Rendered Title")
    mock_page.goto = AsyncMock()
    mock_page.wait_for_timeout = AsyncMock()
    mock_page.close = AsyncMock()
    
    mock_context = AsyncMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)
    
    mock_browser = AsyncMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    
    mock_pw = AsyncMock()
    mock_pw.firefox.launch = AsyncMock(return_value=mock_browser)
    
    engine._playwright = mock_pw
    engine._browser = mock_browser
    engine._context = mock_context
    engine._is_started = True
    
    html, title = await engine.fetch_page_html("https://example.com")
    assert html == "<html><body>Rendered DOM</body></html>"
    assert title == "Rendered Title"
    mock_page.goto.assert_awaited_once()
    mock_page.close.assert_awaited_once()
