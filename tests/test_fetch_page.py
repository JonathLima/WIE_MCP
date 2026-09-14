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
             patch("src.tools.fetch_page.OBSCURA_AVAILABLE", False), \
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
             patch("src.tools.fetch_page.OBSCURA_AVAILABLE", False), \
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
             patch("src.tools.fetch_page.OBSCURA_AVAILABLE", False), \
             patch("src.tools.fetch_page.validate_url", return_value=(True, "")), \
             patch("src.tools.fetch_page._fetch_with_httpx_fallback", new_callable=AsyncMock) as mock_httpx:

            mock_httpx.return_value = ("<html>forbidden</html>", 403, "text/html")
            result = await fetch_page(url="https://blocked-site.com")
            assert "FETCH_BLOCKED_ERROR" in result

    @pytest.mark.asyncio
    async def test_final_429_returns_blocked_error(self):
        with patch("src.tools.fetch_page.CURL_CFFI_AVAILABLE", False), \
             patch("src.tools.fetch_page.OBSCURA_AVAILABLE", False), \
             patch("src.tools.fetch_page._fetch_with_httpx_fallback", new_callable=AsyncMock) as mock_httpx:

            mock_httpx.return_value = ("<html>rate limited</html>", 429, "text/html")
            result = await fetch_page(url="https://ratelimited.com")
            assert "FETCH_BLOCKED_ERROR" in result


class TestFetchPageHTTPError:
    """Non-blocked HTTP errors (4xx except 403/429) should raise FetchHTTPError."""

    @pytest.mark.asyncio
    async def test_404_returns_http_error(self):
        with patch("src.tools.fetch_page.CURL_CFFI_AVAILABLE", False), \
             patch("src.tools.fetch_page.OBSCURA_AVAILABLE", False), \
             patch("src.tools.fetch_page._fetch_with_httpx_fallback", new_callable=AsyncMock) as mock_httpx:

            mock_httpx.return_value = ("<html>not found</html>", 404, "text/html")
            result = await fetch_page(url="https://example.com/missing")
            assert "FETCH_HTTP_ERROR" in result


class TestFetchPageConnectionFailure:
    """When all methods fail with connection errors, should return FetchConnectionError."""

    @pytest.mark.asyncio
    async def test_all_methods_fail_returns_connection_error(self):
        with patch("src.tools.fetch_page.CURL_CFFI_AVAILABLE", False), \
             patch("src.tools.fetch_page.OBSCURA_AVAILABLE", False), \
             patch("src.tools.fetch_page.validate_url", return_value=(True, "")), \
             patch("src.tools.fetch_page._fetch_with_httpx_fallback", new_callable=AsyncMock) as mock_httpx:

            mock_httpx.side_effect = ConnectionError("refused")
            result = await fetch_page(url="https://down-site.com")
            assert "FETCH_CONNECTION_ERROR" in result

    @pytest.mark.asyncio
    async def test_timeout_returns_timeout_error(self):
        import httpx
        with patch("src.tools.fetch_page.CURL_CFFI_AVAILABLE", False), \
             patch("src.tools.fetch_page.OBSCURA_AVAILABLE", False), \
             patch("src.tools.fetch_page._fetch_with_httpx_fallback", new_callable=AsyncMock) as mock_httpx:

            mock_httpx.side_effect = httpx.ReadTimeout("timed out")
            result = await fetch_page(url="https://slow-site.com")
            assert "FETCH_TIMEOUT_ERROR" in result


class TestCurlCffiFetch:
    """Verify _fetch_with_curl_cffi passes allow_redirects=True (not follow_redirects)."""

    @pytest.mark.asyncio
    async def test_curl_cffi_uses_allow_redirects(self):
        from src.tools.fetch_page import _fetch_with_curl_cffi
        from src.config import FetchConfig
        from unittest.mock import MagicMock

        mock_resp = MagicMock()
        mock_resp.text = "<html>Hello</html>"
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "text/html"}

        mock_session_instance = AsyncMock()
        mock_session_instance.get.return_value = mock_resp

        mock_session_cm = AsyncMock()
        mock_session_cm.__aenter__.return_value = mock_session_instance
        mock_session_cm.__aexit__.return_value = None

        with patch("src.tools.fetch_page.CURL_CFFI_AVAILABLE", True), \
             patch("src.tools.fetch_page.AsyncSession", return_value=mock_session_cm):

            html, status, content_type = await _fetch_with_curl_cffi("https://example.com", FetchConfig())
            assert status == 200
            assert html == "<html>Hello</html>"
            mock_session_instance.get.assert_called_once()
            _, kwargs = mock_session_instance.get.call_args
            assert kwargs.get("allow_redirects") is True
            assert "follow_redirects" not in kwargs


class TestChallengeDetection:
    """_is_challenge_html classifies anti-bot interstitials."""

    def test_cloudflare_challenge(self):
        from src.tools.fetch_page import _is_challenge_html
        assert _is_challenge_html("<html>Just a moment... checking your browser</html>") == "cloudflare"

    def test_recaptcha_challenge(self):
        from src.tools.fetch_page import _is_challenge_html
        assert _is_challenge_html('<div class="g-recaptcha"></div>') == "recaptcha"

    def test_hcaptcha_challenge(self):
        from src.tools.fetch_page import _is_challenge_html
        assert _is_challenge_html('<div class="h-captcha"></div>') == "hcaptcha"

    def test_generic_verify(self):
        from src.tools.fetch_page import _is_challenge_html
        assert _is_challenge_html("<p>verify you are human</p>") == "generic"

    def test_case_insensitive_matching(self):
        from src.tools.fetch_page import _is_challenge_html
        # lowercase-only matching, no case sensitivity surprises
        assert _is_challenge_html("<html><body>g-RECAPTCHA</body></html>") == "recaptcha"

    def test_article_about_captcha_not_flagged(self):
        from src.tools.fetch_page import _is_challenge_html
        html = "<html><head><title>Understanding CAPTCHA systems</title></head><body>This article explains how captcha and recaptcha work.</body></html>"
        assert _is_challenge_html(html) is None

    def test_long_article_with_challenge_terms_not_flagged(self):
        from src.tools.fetch_page import _is_challenge_html
        body = "This survey discusses g-recaptcha, hcaptcha.com, and just a moment challenge flows. " * 600
        html = f"<html><head><title>CAPTCHA Systems Review</title></head><body>{body}</body></html>"
        assert len(html) > 20000
        assert _is_challenge_html(html) is None

    def test_http_error_title_detected(self):
        from src.tools.fetch_page import _is_challenge_html
        assert _is_challenge_html("<html><head><title>403 Forbidden</title></head><body></body></html>") == "http-error"

    def test_http_error_title_404(self):
        from src.tools.fetch_page import _is_challenge_html
        assert _is_challenge_html("<html><head><title>404 Not Found</title></head></html>") == "http-error"

    def test_no_challenge(self):
        from src.tools.fetch_page import _is_challenge_html
        assert _is_challenge_html("<html><body>normal article</body></html>") is None

    def test_empty_body(self):
        from src.tools.fetch_page import _is_challenge_html
        assert _is_challenge_html("") is None


class TestObscuraFetch:
    """_fetch_with_obscura builds the right CLI and returns rendered HTML."""

    @pytest.mark.asyncio
    async def test_builds_stealth_args_and_returns_html(self):
        from src.tools.fetch_page import _fetch_with_obscura
        from src.config import FetchConfig

        stdout_bytes = "<html><body>rendered</body></html>".encode()

        class FakeProc:
            returncode = 0
            async def communicate(self):
                return stdout_bytes, b""

        with patch("src.tools.fetch_page.OBSCURA_AVAILABLE", True), \
             patch("src.tools.fetch_page.asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = FakeProc()
            config = FetchConfig(obscura_stealth=True, obscura_proxy="socks5://127.0.0.1:9050")
            html, status, ct = await _fetch_with_obscura("https://example.com", config)
            assert status == 200
            assert "rendered" in html
            args = mock_exec.call_args[0]
            assert "--stealth" in args
            assert "--dump" in args and "html" in args
            assert "--proxy" in args and "socks5://127.0.0.1:9050" in args
