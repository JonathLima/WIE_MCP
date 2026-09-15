import pytest
from unittest.mock import AsyncMock, MagicMock
from src.browser.session import BrowserSession
from src.browser.actions import BrowserActions

@pytest.mark.asyncio
async def test_session_navigate():
    mock_page = AsyncMock()
    mock_page.goto = AsyncMock()
    mock_page.wait_for_timeout = AsyncMock()
    mock_page.title = AsyncMock(return_value="Target Page")
    mock_page.url = "https://example.com/target"
    mock_page.content = AsyncMock(return_value="<html><body>Content</body></html>")
    
    session = BrowserSession(mock_page)
    actions = BrowserActions(session)
    
    result = await actions.navigate("https://example.com/target")
    assert "Successfully navigated to: https://example.com/target" in result
    assert "**Title:** Target Page" in result
    mock_page.goto.assert_awaited_once()

@pytest.mark.asyncio
async def test_session_type():
    mock_page = AsyncMock()
    mock_page.fill = AsyncMock()
    mock_page.press = AsyncMock()
    mock_page.wait_for_timeout = AsyncMock()
    
    session = BrowserSession(mock_page)
    actions = BrowserActions(session)
    
    result = await actions.type_text("#input", "hello", press_enter=True)
    assert 'Typed "hello" into selector "#input"' in result
    mock_page.fill.assert_awaited_once_with("#input", "hello")
    mock_page.press.assert_awaited_once_with("#input", "Enter")

@pytest.mark.asyncio
async def test_session_click():
    mock_page = AsyncMock()
    mock_page.click = AsyncMock()
    mock_page.wait_for_timeout = AsyncMock()
    mock_page.title = AsyncMock(return_value="After Click Page")
    mock_page.url = "https://example.com/after-click"
    
    session = BrowserSession(mock_page)
    actions = BrowserActions(session)
    
    result = await actions.click(selector="button#submit")
    assert 'Clicked element "button#submit"' in result
    assert "After Click Page" in result
    mock_page.click.assert_awaited_once_with("button#submit")

@pytest.mark.asyncio
async def test_session_evaluate():
    mock_page = AsyncMock()
    mock_page.evaluate = AsyncMock(return_value={"count": 42})
    
    session = BrowserSession(mock_page)
    actions = BrowserActions(session)
    
    result = await actions.evaluate("document.title")
    assert '"count": 42' in result
    mock_page.evaluate.assert_awaited_once_with("document.title")
