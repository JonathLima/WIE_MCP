import pytest
from unittest.mock import patch, AsyncMock
from src.tools.answer import answer

@pytest.mark.asyncio
async def test_answer_returns_string():
    with patch("src.tools.answer._fetch_and_extract") as mock:
        mock.return_value = "Python is a programming language created by Guido van Rossum."
        result = await answer(
            query="What is Python?",
            urls=["https://python.org"]
        )
        assert isinstance(result, str)
        assert "Python" in result


@pytest.mark.asyncio
async def test_answer_validation_error():
    # Empty query should fail validation
    result = await answer(query="", urls=["https://example.com"])
    assert "VALIDATION_ERROR" in result

    # Empty urls list should fail validation
    result = await answer(query="What is Python?", urls=[])
    assert "VALIDATION_ERROR" in result

    # Too many urls should fail validation
    result = await answer(query="What is Python?", urls=["https://example.com"] * 21)
    assert "VALIDATION_ERROR" in result
