import pytest
from unittest.mock import AsyncMock, patch
from src.tools.fetch_page import _build_fetch_response
from src.models import FetchRequest
from src.config import FetchConfig


@pytest.mark.asyncio
async def test_fetch_page_stealth_fallback_when_challenge_detected():
    config = FetchConfig()
    request = FetchRequest(url="https://example.com/protected")

    with patch("src.tools.fetch_page.validate_url", return_value=(True, "")), \
         patch("src.tools.fetch_page._throttle", new_callable=AsyncMock), \
         patch("src.tools.fetch_page._fetch_with_curl_cffi", new_callable=AsyncMock) as mock_curl, \
         patch("src.tools.fetch_page._fetch_with_stealth_browser", new_callable=AsyncMock) as mock_stealth:

        # curl_cffi gets cloudflare challenge
        mock_curl.return_value = (
            "<html><title>Just a moment...</title>cf-browser-verification</html>",
            403,
            "text/html",
        )
        # stealth browser returns clean rendered DOM
        mock_stealth.return_value = (
            "<html><title>Clean Article</title><body><p>Legitimate content on page.</p></body></html>",
            200,
            "text/html",
        )

        resp = await _build_fetch_response(request, config)
        assert resp.title == "Clean Article"
        assert "Legitimate content on page" in resp.content
        mock_stealth.assert_awaited_once()
