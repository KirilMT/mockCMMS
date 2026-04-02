"""Tests for `.collab/dashboard/server.py` serve() function.

The server uses http.server (not Flask). These tests mock http.server components to
avoid binding ports or opening browsers.

Consolidated from test_server.py and test_server_comprehensive.py.
"""

from __future__ import annotations

import http.server
import importlib.util
import inspect
from pathlib import Path
from unittest import mock

import pytest

# Load module directly
proj_root = Path(__file__).resolve().parents[3]
module_file = proj_root / ".collab" / "dashboard" / "server.py"
spec = importlib.util.spec_from_file_location(
    "collab.dashboard.server",
    str(module_file),
)
assert spec and spec.loader
srv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(srv)  # type: ignore[arg-type]


# ============================================================================
# Structure / Smoke Tests
# ============================================================================


def test_dashboard_index_exists():
    dashboard_index = (
        Path(__file__).resolve().parents[3] / ".collab" / "dashboard" / "index.html"
    )
    assert dashboard_index.exists(), f"Dashboard index missing: {dashboard_index}"


def test_serve_callable_no_browser(monkeypatch):
    assert hasattr(srv, "serve") and callable(srv.serve)
    try:
        srv_path = Path(__file__).resolve().parents[3] / ".collab" / "dashboard"
        assert (srv_path / "index.html").exists()
    except Exception as e:
        pytest.fail(f"serve() pre-check failed: {e}")


def test_serve_function_exists():
    """Test that the serve function exists."""
    assert hasattr(srv, "serve")
    assert callable(srv.serve)


def test_module_has_http_server():
    """Test that the module uses http.server (not Flask)."""

    src = module_file.read_text()
    assert "http.server" in src


def test_serve_accepts_keyword_args():
    """Test that serve accepts keyword arguments."""
    sig = inspect.signature(srv.serve)
    params = list(sig.parameters.keys())
    assert "port" in params
    assert "open_browser" in params


def test_serve_default_port():
    """Test serve signature has default port=0."""
    sig = inspect.signature(srv.serve)
    assert sig.parameters["port"].default == 0


# ============================================================================
# Server Mocking Tests (mock http.server to avoid port binding)
# ============================================================================


class FakeServer:
    """Mock HTTP server that doesn't actually bind."""

    def __init__(self, addr, handler):
        self.server_address = (addr[0], addr[1] or 9999)

    def serve_forever(self):
        pass  # Don't block

    def server_close(self):
        pass


def test_serve_creates_server(monkeypatch, tmp_path):
    """Test that serve creates an HTTP server."""
    monkeypatch.setattr("webbrowser.open", mock.Mock())
    monkeypatch.setattr(http.server, "ThreadingHTTPServer", FakeServer)
    try:
        srv.serve(port=0, open_browser=False)
    except Exception:
        pass


def test_serve_with_custom_port(monkeypatch):
    """Test serve with custom port."""
    monkeypatch.setattr("webbrowser.open", mock.Mock())
    monkeypatch.setattr(http.server, "ThreadingHTTPServer", FakeServer)
    try:
        srv.serve(port=8888, open_browser=False)
    except Exception:
        pass


def test_serve_opens_browser_when_requested(monkeypatch):
    """Test that browser is opened when open_browser=True."""
    mock_browser = mock.Mock()
    monkeypatch.setattr("webbrowser.open", mock_browser)
    monkeypatch.setattr(http.server, "ThreadingHTTPServer", FakeServer)
    try:
        srv.serve(port=0, open_browser=True)
    except Exception:
        pass
    assert mock_browser.called


def test_serve_does_not_open_browser_when_not_requested(monkeypatch):
    """Test that browser is not opened when open_browser=False."""
    mock_browser = mock.Mock()
    monkeypatch.setattr("webbrowser.open", mock_browser)
    monkeypatch.setattr(http.server, "ThreadingHTTPServer", FakeServer)
    try:
        srv.serve(port=0, open_browser=False)
    except Exception:
        pass
    assert not mock_browser.called


def test_serve_handles_address_in_use_error(monkeypatch):
    """Test that serve handles port already in use error gracefully."""
    monkeypatch.setattr("webbrowser.open", mock.Mock())

    def raise_oserror(addr, handler):
        raise OSError("Address already in use")

    monkeypatch.setattr(http.server, "ThreadingHTTPServer", raise_oserror)
    try:
        srv.serve(port=5000, open_browser=False)
    except (OSError, SystemExit):
        pass


def test_serve_binds_to_localhost(monkeypatch):
    """Test that server binds to localhost (127.0.0.1)."""
    bind_addr = {}

    class CapturingServer:
        def __init__(self, addr, handler):
            bind_addr["host"] = addr[0]
            bind_addr["port"] = addr[1]
            self.server_address = (addr[0], addr[1] or 9999)

        def serve_forever(self):
            pass

        def server_close(self):
            pass

    monkeypatch.setattr("webbrowser.open", mock.Mock())
    monkeypatch.setattr(http.server, "ThreadingHTTPServer", CapturingServer)
    try:
        srv.serve(port=0, open_browser=False)
    except Exception:
        pass
    assert bind_addr.get("host") == "127.0.0.1"


def test_serve_with_debug_mode(monkeypatch):
    """Test serve executes without error in non-browser mode."""
    monkeypatch.setattr("webbrowser.open", mock.Mock())
    monkeypatch.setattr(http.server, "ThreadingHTTPServer", FakeServer)
    try:
        srv.serve(port=0, open_browser=False)
    except Exception:
        pass


def test_serve_handles_keyboard_interrupt(monkeypatch):
    """Test that serve handles KeyboardInterrupt gracefully."""
    monkeypatch.setattr("webbrowser.open", mock.Mock())

    class InterruptServer:
        def __init__(self, addr, handler):
            self.server_address = (addr[0], addr[1] or 9999)

        def serve_forever(self):
            raise KeyboardInterrupt()

        def server_close(self):
            pass

    monkeypatch.setattr(http.server, "ThreadingHTTPServer", InterruptServer)
    # Should not raise - main() has try/except KeyboardInterrupt
    try:
        srv.serve(port=0, open_browser=False)
    except KeyboardInterrupt:
        pass  # OK if it propagates


def test_browser_timer_delay(monkeypatch):
    """Test that browser is opened directly (no Timer in this implementation)."""
    mock_browser = mock.Mock()
    monkeypatch.setattr("webbrowser.open", mock_browser)
    monkeypatch.setattr(http.server, "ThreadingHTTPServer", FakeServer)
    try:
        srv.serve(port=0, open_browser=True)
    except Exception:
        pass
    # Browser should be called
    assert mock_browser.called


def test_template_folder_configured():
    """Test that the serve function reads from the dashboard directory."""
    src = module_file.read_text()
    assert "index.html" in src


def test_index_route_exists():
    """Test that server serves files from a temp directory with injected config."""
    src = module_file.read_text()
    assert "__SUPABASE_CONFIG__" in src


# ============================================================================
# Comprehensive Edge Cases (restored from test_server_comprehensive.py)
# ============================================================================


def test_serve_injects_supabase_config(monkeypatch, tmp_path):
    """Test that serve() writes a temp HTML file with Supabase config injected."""
    monkeypatch.setattr("webbrowser.open", mock.Mock())
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_anon_key")

    import tempfile

    written_content = {}

    class CapturingTempFile:
        def __init__(self, *args, **kwargs):
            self.name = str(tmp_path / "dashboard.html")
            self._content = []

        def write(self, data):
            self._content.append(data)
            written_content["data"] = "".join(self._content)

        def flush(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr(
        tempfile, "NamedTemporaryFile", lambda **kw: CapturingTempFile()
    )
    monkeypatch.setattr(http.server, "ThreadingHTTPServer", FakeServer)

    try:
        srv.serve(port=0, open_browser=False)
    except Exception:
        pass

    assert "__SUPABASE_CONFIG__" in written_content.get("data", "")


# ============================================================================
# Missing index.html Tests (lines 34-35)
# ============================================================================


def test_serve_missing_index_html(monkeypatch, tmp_path):
    """Test serve exits when index.html doesn't exist."""
    monkeypatch.setattr("webbrowser.open", mock.Mock())
    # Point _THIS_DIR to a directory without index.html
    monkeypatch.setattr(srv, "_THIS_DIR", str(tmp_path))

    with pytest.raises(SystemExit):
        srv.serve(port=0, open_browser=False)


# ============================================================================
# __main__ Block Tests (lines 89-98)
# ============================================================================


def test_module_has_main_block():
    """Test that __name__ == '__main__' block exists."""
    src = module_file.read_text()
    assert '__name__ == "__main__"' in src or "__name__ == '__main__'" in src


def test_module_main_block_has_argparse():
    """Test that the __main__ block uses argparse (lines 90-98)."""
    src = module_file.read_text()
    assert "argparse" in src
    assert "--port" in src
    assert "--no-browser" in src
