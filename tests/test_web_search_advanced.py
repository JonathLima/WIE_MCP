import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.tools.web_search_advanced import web_search_advanced

@pytest.mark.asyncio
async def test_web_search_advanced_returns_markdown():
    with patch("src.tools.web_search_advanced._execute_search") as mock_exec:
        mock_exec.return_value = []
        result = await web_search_advanced(query="test", search_type="auto")
        assert isinstance(result, str)
        assert "Search Results" in result or "No Results" in result

@pytest.mark.asyncio
async def test_web_search_advanced_respects_type():
    with patch("src.tools.web_search_advanced._execute_search") as mock_exec:
        mock_exec.return_value = []
        await web_search_advanced(query="python", search_type="fast", num_results=5)
        call_args = mock_exec.call_args
        assert call_args[1]["search_type"] == "fast"

@pytest.mark.asyncio
async def test_web_search_advanced_propagates_connection_error():
    import httpx
    with patch("src.tools.web_search_advanced._execute_search") as mock_exec:
        mock_exec.side_effect = httpx.ConnectError("Cannot connect")
        result = await web_search_advanced(query="test", search_type="deep_lite")
        assert "Connection Error" in result

@pytest.mark.asyncio
async def test_web_search_advanced_propagates_timeout():
    import httpx
    with patch("src.tools.web_search_advanced._execute_search") as mock_exec:
        mock_exec.side_effect = httpx.TimeoutException("Timed out")
        result = await web_search_advanced(query="test", search_type="deep_lite")
        assert "Timeout" in result
