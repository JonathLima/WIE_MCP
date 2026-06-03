import pytest
from unittest.mock import patch, AsyncMock
from src.tools.fetch_page import fetch_page


class TestFetchPageValidation:
    """URL validation before any fetch attempt."""

    @pytest.mark.asyncio
    async def test_invalid_url_returns_error(self):
        result = await fetch_page(url="not-a-url")
        assert "Invalid" in result or "Error" in result

    @pytest.mark.asyncio
    async def test_empty_url_returns_error(self):
        result = await fetch_page(url="")
        assert "Invalid" in result or "Error" in result


class TestFetchPageFallbackDiscard:
    """Status codes 403/429/5xx should discard html_content so next fallback is tried."""

    @pytest.mark.asyncio
    async def test_curl_cffi_403_triggers_fallback(self):
        """When curl_cffi returns 403, it should be discarded and next method tried."""
        with patch("src.tools.fetch_page.CURL_CFFI_AVAILABLE", True), \
             patch("src.tools.fetch_page.NODRIVER_AVAILABLE", False), \
             patch("src.tools.fetch_page._fetch_with_curl_cffi", new_callable=AsyncMock) as mock_curl, \
             patch("src.tools.fetch_page._fetch_with_httpx_fallback", new_callable=AsyncMock) as mock_httpx:

            mock_curl.return_value = ("<html>blocked</html>", 403, "text/html")
            mock_httpx.return_value = ("<html><body>real content</body></html>", 200, "text/html")

            result = await fetch_page(url="https://example.com")
            # curl_cffi 403 should be discarded, httpx fallback should be called
            mock_httpx.assert_called_once()

    @pytest.mark.asyncio
    async def test_curl_cffi_500_triggers_fallback(self):
        """When curl_cffi returns 500, it should be discarded."""
        with patch("src.tools.fetch_page.CURL_CFFI_AVAILABLE", True), \
             patch("src.tools.fetch_page.NODRIVER_AVAILABLE", False), \
             patch("src.tools.fetch_page._fetch_with_curl_cffi", new_callable=AsyncMock) as mock_curl, \
             patch("src.tools.fetch_page._fetch_with_httpx_fallback", new_callable=AsyncMock) as mock_httpx:

            mock_curl.return_value = ("<html>error</html>", 500, "text/html")
            mock_httpx.return_value = ("<html><body>ok</body></html>", 200, "text/html")

            result = await fetch_page(url="https://example.com")
            # httpx fallback should have been called since curl returned 500
            mock_httpx.assert_called_once()


class TestFetchPageBlockedError:
    """Final 403/429 after all fallbacks should raise FetchBlockedError, formatted as markdown."""

    @pytest.mark.asyncio
    async def test_final_403_returns_blocked_error(self):
        with patch("src.tools.fetch_page.CURL_CFFI_AVAILABLE", False), \
             patch("src.tools.fetch_page.NODRIVER_AVAILABLE", False), \
             patch("src.tools.fetch_page._fetch_with_httpx_fallback", new_callable=AsyncMock) as mock_httpx:

            mock_httpx.return_value = ("<html>forbidden</html>", 403, "text/html")
            result = await fetch_page(url="https://blocked-site.com")
            assert "FETCH_BLOCKED_ERROR" in result

    @pytest.mark.asyncio
    async def test_final_429_returns_blocked_error(self):
        with patch("src.tools.fetch_page.CURL_CFFI_AVAILABLE", False), \
             patch("src.tools.fetch_page.NODRIVER_AVAILABLE", False), \
             patch("src.tools.fetch_page._fetch_with_httpx_fallback", new_callable=AsyncMock) as mock_httpx:

            mock_httpx.return_value = ("<html>rate limited</html>", 429, "text/html")
            result = await fetch_page(url="https://ratelimited.com")
            assert "FETCH_BLOCKED_ERROR" in result


class TestFetchPageHTTPError:
    """Non-blocked HTTP errors (4xx except 403/429) should raise FetchHTTPError."""

    @pytest.mark.asyncio
    async def test_404_returns_http_error(self):
        with patch("src.tools.fetch_page.CURL_CFFI_AVAILABLE", False), \
             patch("src.tools.fetch_page.NODRIVER_AVAILABLE", False), \
             patch("src.tools.fetch_page._fetch_with_httpx_fallback", new_callable=AsyncMock) as mock_httpx:

            mock_httpx.return_value = ("<html>not found</html>", 404, "text/html")
            result = await fetch_page(url="https://example.com/missing")
            assert "FETCH_HTTP_ERROR" in result


class TestFetchPageConnectionFailure:
    """When all methods fail with connection errors, should return FetchConnectionError."""

    @pytest.mark.asyncio
    async def test_all_methods_fail_returns_connection_error(self):
        with patch("src.tools.fetch_page.CURL_CFFI_AVAILABLE", False), \
             patch("src.tools.fetch_page.NODRIVER_AVAILABLE", False), \
             patch("src.tools.fetch_page._fetch_with_httpx_fallback", new_callable=AsyncMock) as mock_httpx:

            mock_httpx.side_effect = ConnectionError("refused")
            result = await fetch_page(url="https://down-site.com")
            assert "FETCH_CONNECTION_ERROR" in result

    @pytest.mark.asyncio
    async def test_timeout_returns_timeout_error(self):
        import httpx
        with patch("src.tools.fetch_page.CURL_CFFI_AVAILABLE", False), \
             patch("src.tools.fetch_page.NODRIVER_AVAILABLE", False), \
             patch("src.tools.fetch_page._fetch_with_httpx_fallback", new_callable=AsyncMock) as mock_httpx:

            mock_httpx.side_effect = httpx.ReadTimeout("timed out")
            result = await fetch_page(url="https://slow-site.com")
            assert "FETCH_TIMEOUT_ERROR" in result
