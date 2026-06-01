import pytest
from unittest.mock import patch, AsyncMock
from src.tools.get_contents import get_contents

@pytest.mark.asyncio
async def test_get_contents_returns_markdown():
    with patch("src.tools.get_contents._fetch_single_url") as mock_fetch:
        mock_fetch.return_value = {
            "url": "https://example.com",
            "status_code": 200,
            "title": "Example",
            "content": "Page content",
            "highlights": [],
            "summary": None,
        }
        result = await get_contents(urls=["https://example.com"])
        assert isinstance(result, str)
        assert "example.com" in result

@pytest.mark.asyncio
async def test_get_contents_highlights():
    with patch("src.tools.get_contents._fetch_single_url") as mock_fetch:
        mock_fetch.return_value = {
            "url": "https://python.org",
            "status_code": 200,
            "title": "Python",
            "content": "Python is a programming language.",
            "highlights": ["Python is a programming language."],
            "summary": None,
        }
        result = await get_contents(
            urls=["https://python.org"],
            highlight_query="Python",
        )
        assert isinstance(result, str)