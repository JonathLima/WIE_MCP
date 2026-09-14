from src.browser.snapshot import parse_interactive_snapshot

SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head><title>Login Page</title></head>
<body>
    <header><h1>Welcome Back</h1></header>
    <main>
        <form action="/login" method="post">
            <label for="username">Username</label>
            <input type="text" id="username" name="user" placeholder="Enter username" />
            
            <label for="password">Password</label>
            <input type="password" id="password" name="pass" />
            
            <button type="submit" id="submit-btn">Sign In</button>
            <a href="/forgot" class="link-forgot">Forgot Password?</a>
        </form>
    </main>
</body>
</html>
"""

def test_parse_interactive_snapshot():
    snapshot = parse_interactive_snapshot(SAMPLE_HTML, title="Login Page", url="https://example.com/login")
    assert "# Page Snapshot: Login Page" in snapshot
    assert "https://example.com/login" in snapshot
    assert '<input' in snapshot
    assert 'id="username"' in snapshot
    assert '<button' in snapshot
    assert 'Sign In' in snapshot
    assert '<a' in snapshot
    assert 'Forgot Password?' in snapshot

def test_parse_interactive_snapshot_empty():
    snapshot = parse_interactive_snapshot("<html><body><p>Hello world without buttons</p></body></html>")
    assert "No interactive elements found on page" in snapshot
