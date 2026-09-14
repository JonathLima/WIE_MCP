from src.browser.config import BrowserConfig

def test_browser_config_defaults():
    config = BrowserConfig()
    assert config.enabled is True
    assert config.headless is True
    assert config.timeout == 30.0
    assert config.proxy == ""
    assert config.profile_dir == ""
    assert config.viewport_width == 1280
    assert config.viewport_height == 800

def test_browser_config_env_override(monkeypatch):
    monkeypatch.setenv("BROWSER_ENABLED", "false")
    monkeypatch.setenv("BROWSER_HEADLESS", "false")
    monkeypatch.setenv("BROWSER_TIMEOUT_SECONDS", "45.0")
    monkeypatch.setenv("BROWSER_PROXY", "http://127.0.0.1:8080")
    monkeypatch.setenv("BROWSER_PROFILE_DIR", "/tmp/profiles")
    monkeypatch.setenv("BROWSER_VIEWPORT_WIDTH", "1920")
    monkeypatch.setenv("BROWSER_VIEWPORT_HEIGHT", "1080")
    
    config = BrowserConfig()
    assert config.enabled is False
    assert config.headless is False
    assert config.timeout == 45.0
    assert config.proxy == "http://127.0.0.1:8080"
    assert config.profile_dir == "/tmp/profiles"
    assert config.viewport_width == 1920
    assert config.viewport_height == 1080
