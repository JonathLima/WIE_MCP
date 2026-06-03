import pytest
from src.config import (
    SearxngConfig,
    FetchConfig,
    ServerConfig,
    get_searxng_config,
    get_fetch_config,
    get_server_config,
)

@pytest.fixture(autouse=True)
def clear_config_caches():
    get_searxng_config.cache_clear()
    get_fetch_config.cache_clear()
    get_server_config.cache_clear()
    yield
    get_searxng_config.cache_clear()
    get_fetch_config.cache_clear()
    get_server_config.cache_clear()

def test_searxng_config_aliases(monkeypatch):
    monkeypatch.setenv("SEARXNG_HOST", "http://my-searxng:1234")
    monkeypatch.setenv("SEARXNG_ENGINES", "google,bing")
    monkeypatch.setenv("SEARCH_DEFAULT_LIMIT", "15")
    monkeypatch.setenv("SEARCH_TIMEOUT_SECONDS", "8.5")

    # Clear cache by creating a new instance
    cfg = SearxngConfig()
    assert cfg.host == "http://my-searxng:1234"
    assert cfg.engines == "google,bing"
    assert cfg.default_limit == 15
    assert cfg.timeout == 8.5

def test_fetch_config_aliases(monkeypatch):
    monkeypatch.setenv("FETCH_TIMEOUT_SECONDS", "12.0")
    monkeypatch.setenv("FETCH_MAX_CONTENT_LENGTH", "5000")
    monkeypatch.setenv("FETCH_TOKEN_BUDGET", "4000")

    cfg = FetchConfig()
    assert cfg.timeout == 12.0
    assert cfg.max_content_length == 5000
    assert cfg.token_budget == 4000

def test_server_config_aliases(monkeypatch):
    monkeypatch.setenv("MCP_SERVER_HOST", "127.0.0.1")
    monkeypatch.setenv("MCP_SERVER_PORT", "9000")
    monkeypatch.setenv("API_KEY", "secret-test-key")
    monkeypatch.setenv("SEARCH_DEFAULT_TYPE", "deep")

    cfg = ServerConfig()
    assert cfg.host == "127.0.0.1"
    assert cfg.port == 9000
    assert cfg.api_key == "secret-test-key"
    assert cfg.default_search_type == "deep"
