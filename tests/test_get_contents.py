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


@pytest.mark.asyncio
async def test_get_contents_validation_error():
    # Empty URL list should fail validation
    result = await get_contents(urls=[])
    assert "VALIDATION_ERROR" in result

    # Invalid max_tokens should fail validation
    result = await get_contents(urls=["https://example.com"], max_tokens=10)
    assert "VALIDATION_ERROR" in result


@pytest.mark.asyncio
async def test_get_contents_propagates_fetch_blocked_error():
    from src.errors import FetchBlockedError
    with patch("src.tools.get_contents._fetch_page_structured", new_callable=AsyncMock) as mock_structured:
        mock_structured.side_effect = FetchBlockedError("Blocked by Cloudflare (HTTP 403)")
        
        result = await get_contents(urls=["https://blocked.com"])
        assert "**Status:** 403" in result
        assert "Error: Blocked by Cloudflare (HTTP 403)" in result


@pytest.mark.asyncio
async def test_get_contents_propagates_fetch_http_error():
    from src.errors import FetchHTTPError
    with patch("src.tools.get_contents._fetch_page_structured", new_callable=AsyncMock) as mock_structured:
        mock_structured.side_effect = FetchHTTPError("HTTP 502 from server", status_code=502)
        
        result = await get_contents(urls=["https://error-site.com"])
        assert "**Status:** 502" in result
        assert "Error: HTTP 502 from server" in result