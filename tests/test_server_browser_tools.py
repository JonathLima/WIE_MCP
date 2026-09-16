import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.server import (
    browser_navigate,
    browser_snapshot,
    browser_click,
    browser_type,
    browser_take_screenshot,
    browser_evaluate,
    browser_close,
)


@pytest.mark.asyncio
async def test_server_browser_navigate():
    with patch("src.server.get_active_browser_actions", new_callable=AsyncMock) as mock_get_actions:
        mock_actions = AsyncMock()
        mock_actions.navigate = AsyncMock(return_value="Successfully navigated to: https://example.com\n**Title:** Example")
        mock_get_actions.return_value = mock_actions

        res = await browser_navigate("https://example.com")
        assert "Successfully navigated" in res
        mock_actions.navigate.assert_awaited_once_with(url="https://example.com", wait_until="load", timeout_seconds=30.0)


@pytest.mark.asyncio
async def test_server_browser_snapshot():
    with patch("src.server.get_active_browser_actions", new_callable=AsyncMock) as mock_get_actions:
        mock_actions = AsyncMock()
        mock_actions.snapshot = AsyncMock(return_value="# Page Snapshot: Test\n- [1] <button>Click</button>")
        mock_get_actions.return_value = mock_actions

        res = await browser_snapshot()
        assert "Page Snapshot" in res
        mock_actions.snapshot.assert_awaited_once_with(interactive_only=True)


@pytest.mark.asyncio
async def test_server_browser_click():
    with patch("src.server.get_active_browser_actions", new_callable=AsyncMock) as mock_get_actions:
        mock_actions = AsyncMock()
        mock_actions.click = AsyncMock(return_value='Clicked element "button#btn"')
        mock_get_actions.return_value = mock_actions

        res = await browser_click(selector="button#btn")
        assert "Clicked element" in res
        mock_actions.click.assert_awaited_once_with(selector="button#btn", text=None)


@pytest.mark.asyncio
async def test_server_browser_type():
    with patch("src.server.get_active_browser_actions", new_callable=AsyncMock) as mock_get_actions:
        mock_actions = AsyncMock()
        mock_actions.type_text = AsyncMock(return_value='Typed "query" into selector "#search"')
        mock_get_actions.return_value = mock_actions

        res = await browser_type(selector="#search", text="query", press_enter=True)
        assert "Typed" in res
        mock_actions.type_text.assert_awaited_once_with(
            selector="#search",
            text="query",
            press_enter=True,
            clear_first=True,
        )


@pytest.mark.asyncio
async def test_server_browser_evaluate():
    with patch("src.server.get_active_browser_actions", new_callable=AsyncMock) as mock_get_actions:
        mock_actions = AsyncMock()
        mock_actions.evaluate = AsyncMock(return_value='{\n  "title": "Hello"\n}')
        mock_get_actions.return_value = mock_actions

        res = await browser_evaluate("document.title")
        assert "Hello" in res
        mock_actions.evaluate.assert_awaited_once_with(expression="document.title")


@pytest.mark.asyncio
async def test_server_browser_take_screenshot():
    with patch("src.server.get_active_browser_actions", new_callable=AsyncMock) as mock_get_actions:
        mock_actions = AsyncMock()
        mock_actions.take_screenshot = AsyncMock(return_value=b"\x89PNG\r\n\x1a\nfakeimagebytes")
        mock_get_actions.return_value = mock_actions

        img = await browser_take_screenshot()
        assert img._format == "png"
        assert img.data == b"\x89PNG\r\n\x1a\nfakeimagebytes"


@pytest.mark.asyncio
async def test_server_browser_close():
    with patch("src.server._active_actions", MagicMock()):
        with patch("src.server.reset_active_browser_actions", new_callable=AsyncMock):
            res = await browser_close()
            assert "closed" in res.lower()

