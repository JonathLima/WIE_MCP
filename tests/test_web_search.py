import pytest
from unittest.mock import patch, AsyncMock
from src.tools.web_search import web_search, _format_error, _normalize_unresponsive_engines
from src.models import ToolErrorResponse


class TestFormatError:
    """Verify _format_error is defined and produces valid markdown."""

    def test_format_error_returns_markdown(self):
        error = ToolErrorResponse(
            error_code="TEST_ERROR",
            message="Something went wrong",
            retry_guidance="Try again",
            markdown="",
        )
        result = _format_error(error)
        assert "TEST_ERROR" in result
        assert "Something went wrong" in result
        assert "Try again" in result

    def test_format_error_no_name_error(self):
        """Regression: _format_error was previously undefined, causing NameError."""
        error = ToolErrorResponse(
            error_code="SEARCH_VALIDATION_ERROR",
            message="bad params",
            retry_guidance="fix them",
            markdown="",
        )
        # Should NOT raise NameError
        result = _format_error(error)
        assert isinstance(result, str)


class TestWebSearchValidation:
    """Validation of search parameters via Pydantic."""

    @pytest.mark.asyncio
    async def test_empty_query_returns_validation_error(self):
        result = await web_search(query="", limit=10)
        assert "SEARCH_VALIDATION_ERROR" in result

    @pytest.mark.asyncio
    async def test_overlimit_returns_validation_error(self):
        result = await web_search(query="test", limit=999)
        assert "SEARCH_VALIDATION_ERROR" in result

    @pytest.mark.asyncio
    async def test_valid_params_reach_search(self):
        with patch("src.tools.web_search.fetch_search_payload", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {"results": [], "unresponsive_engines": []}
            result = await web_search(query="python release", limit=5)
            assert isinstance(result, str)
            assert "No Results" in result or "Search Results" in result


class TestNormalizeUnresponsiveEngines:
    """SearXNG returns [[engine, reason], ...]; we flatten to 'engine: reason'."""

    def test_flattens_pairs(self):
        assert _normalize_unresponsive_engines([["brave", "too many requests"], ["duckduckgo", "CAPTCHA"]]) == [
            "brave: too many requests",
            "duckduckgo: CAPTCHA",
        ]

    def test_handles_mixed(self):
        assert _normalize_unresponsive_engines([["google", "CAPTCHA"], "mwmbl", ["qwant", "access denied"]]) == [
            "google: CAPTCHA",
            "mwmbl",
            "qwant: access denied",
        ]

    def test_empty(self):
        assert _normalize_unresponsive_engines([]) == []


class TestWebSearchSuccess:
    """Basic success path with mocked SearXNG."""

    @pytest.mark.asyncio
    async def test_returns_formatted_markdown(self):
        fake_results = [
            {
                "title": "Python 3.12",
                "url": "https://python.org/3.12",
                "content": "New features in Python 3.12",
                "engines": ["google"],
            }
        ]
        with patch("src.tools.web_search.fetch_search_payload", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {"results": fake_results, "unresponsive_engines": []}
            result = await web_search(query="python 3.12", limit=5)
            assert "Python 3.12" in result
            assert "python.org" in result

    @pytest.mark.asyncio
    async def test_unresponsive_engines_pairs_do_not_raise(self):
        """Regression: SearXNG sends unresponsive_engines as [[engine, reason]]; must not crash web_search."""
        fake_results = [{"title": "X", "url": "https://x.dev", "content": "x", "engines": ["mwmbl"]}]
        with patch("src.tools.web_search.fetch_search_payload", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                "results": fake_results,
                "unresponsive_engines": [["brave", "too many requests"], ["duckduckgo", "CAPTCHA"]],
            }
            result = await web_search(query="test", limit=5)
            assert isinstance(result, str)
