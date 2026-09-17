import http.server
import threading
import pytest
from src.server import (
    browser_navigate,
    browser_snapshot,
    browser_click,
    browser_type,
    browser_take_screenshot,
    browser_evaluate,
    browser_close,
)
from src.tools.fetch_page import fetch_page


class MockHTMLHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        html = """<!DOCTYPE html>
<html>
<head><title>E2E Local Test Page</title></head>
<body>
    <h1>Welcome to E2E Testing</h1>
    <form id="login-form">
        <label for="username">Username</label>
        <input type="text" id="username" name="username" placeholder="Enter username" />
        <button type="button" id="btn-submit" onclick="document.title = 'Clicked: ' + document.getElementById('username').value">Submit</button>
        <a href="#more" id="link-more">Learn More</a>
    </form>
</body>
</html>"""
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        pass  # Quiet logging


@pytest.fixture(scope="module")
def local_server():
    server = http.server.HTTPServer(("127.0.0.1", 0), MockHTMLHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


@pytest.mark.asyncio
async def test_e2e_live_browser_full_interaction_suite(local_server):
    """End-to-end test running the real stealth Firefox against a local page:
    navigate -> snapshot -> typing -> clicking -> JS eval -> screenshot -> clean close."""
    try:
        # 1. Navigate
        nav_res = await browser_navigate(local_server, wait_until="load", timeout_seconds=15.0)
        assert "Successfully navigated to:" in nav_res
        assert "E2E Local Test Page" in nav_res

        # 2. Snapshot
        snapshot = await browser_snapshot(interactive_only=True)
        assert "# Page Snapshot: E2E Local Test Page" in snapshot
        assert "username" in snapshot
        assert "btn-submit" in snapshot
        assert "Learn More" in snapshot

        # 3. Type text into input with humanized intervals
        type_res = await browser_type(
            selector="input#username",
            text="AIHawk_Agent",
            press_enter=False,
            clear_first=True,
        )
        assert 'Typed "AIHawk_Agent" into selector "input#username"' in type_res

        # 4. Click button using humanized cursor movement
        click_res = await browser_click(selector="button#btn-submit")
        assert "Clicked element" in click_res

        # 5. Evaluate JavaScript to confirm the DOM state changed after click
        eval_res = await browser_evaluate("document.title")
        assert "Clicked: AIHawk_Agent" in eval_res

        # 6. Capture live screenshot
        screenshot = await browser_take_screenshot()
        assert screenshot._format == "png"
        assert screenshot.data.startswith(b"\x89PNG\r\n\x1a\n")
        assert len(screenshot.data) > 1000
    finally:
        # 7. Clean close
        close_res = await browser_close()
        assert "closed successfully" in close_res


@pytest.mark.asyncio
async def test_e2e_fetch_page_with_stealth_engine():
    """End-to-end test verifying fetch_page returns formatted markdown with readability and structure."""
    res = await fetch_page("https://example.com")
    assert "Example Domain" in res
    assert "Content" in res or "Page Content" in res
