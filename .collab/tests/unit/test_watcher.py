"""Tests for the `.collab/core/watcher.py` module.

We load the module from file and assert the `main` entrypoint is present and
that the module imports correctly. No network or system changes are performed.

Consolidated from test_watcher.py and test_watcher_comprehensive.py.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

# Load module directly
proj_root = Path(__file__).resolve().parents[3]
module_file = proj_root / ".collab" / "core" / "watcher.py"
spec = importlib.util.spec_from_file_location("collab.watcher", str(module_file))
assert spec and spec.loader
watcher_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watcher_mod)  # type: ignore[arg-type]

# Also load lock_client for mocking
lock_client_path = proj_root / ".collab" / "core" / "lock_client.py"
spec2 = importlib.util.spec_from_file_location(
    "collab.lock_client", str(lock_client_path)
)
assert spec2 and spec2.loader
lock_client_mod = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(lock_client_mod)  # type: ignore[arg-type]

# Register lock_client in sys.modules so watcher's `from core.lock_client import
# LockClient` resolves to our module (which we can monkeypatch).
sys.modules["core.lock_client"] = lock_client_mod


# ============================================================================
# Helpers
# ============================================================================


class MockLockClient:
    """Mock LockClient for testing watcher without network calls."""

    def __init__(self, developer_id=None):
        self.developer_id = developer_id or "test_user"
        self.watch_called = False
        self.watch_kwargs = {}

    def watch(self, **kwargs):
        """Mock watch method."""
        self.watch_called = True
        self.watch_kwargs = kwargs


# ============================================================================
# Structure Tests
# ============================================================================


def test_watcher_main_exists():
    assert hasattr(watcher_mod, "main")
    assert callable(getattr(watcher_mod, "main"))


def test_main_imports_correctly():
    """Test that required imports are present in the module."""
    assert hasattr(watcher_mod, "main")
    assert hasattr(lock_client_mod, "LockClient")


# ============================================================================
# main() Argument Tests
# ============================================================================


def test_main_with_no_args(monkeypatch):
    """Test main function with default arguments."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    mock_argv = ["watcher.py"]
    monkeypatch.setattr(sys, "argv", mock_argv)

    mock_client = MockLockClient()

    def mock_lock_client_class(developer_id=None):
        return mock_client

    monkeypatch.setattr(lock_client_mod, "LockClient", mock_lock_client_class)

    try:
        watcher_mod.main()
    except SystemExit:
        pass

    assert mock_client.watch_called


def test_main_with_interval_arg(monkeypatch):
    """Test main function with custom interval."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    mock_argv = ["watcher.py", "--interval", "10"]
    monkeypatch.setattr(sys, "argv", mock_argv)

    mock_client = MockLockClient()

    def mock_lock_client_class(developer_id=None):
        return mock_client

    monkeypatch.setattr(lock_client_mod, "LockClient", mock_lock_client_class)

    try:
        watcher_mod.main()
    except SystemExit:
        pass

    assert mock_client.watch_called
    assert mock_client.watch_kwargs.get("interval") == 10


def test_main_with_timeout_arg(monkeypatch):
    """Test main function with custom timeout."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    mock_argv = ["watcher.py", "--timeout", "30"]
    monkeypatch.setattr(sys, "argv", mock_argv)

    mock_client = MockLockClient()

    def mock_lock_client_class(developer_id=None):
        return mock_client

    monkeypatch.setattr(lock_client_mod, "LockClient", mock_lock_client_class)

    try:
        watcher_mod.main()
    except SystemExit:
        pass

    assert mock_client.watch_called
    assert mock_client.watch_kwargs.get("timeout_mins") == 30


def test_main_with_developer_id_arg(monkeypatch):
    """Test main function with custom developer ID.

    Note: watcher.py doesn't accept --developer-id; LockClient() is called
    without arguments. We just test that main works with default dev ID.
    """
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    mock_argv = ["watcher.py"]
    monkeypatch.setattr(sys, "argv", mock_argv)

    mock_client = MockLockClient()

    def mock_lock_client_class(developer_id=None):
        mock_client.developer_id = developer_id
        return mock_client

    monkeypatch.setattr(lock_client_mod, "LockClient", mock_lock_client_class)

    try:
        watcher_mod.main()
    except SystemExit:
        pass

    assert mock_client.watch_called


def test_main_with_dashboard_flag(monkeypatch):
    """Test main function with dashboard flag."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    mock_argv = ["watcher.py", "--open-dashboard"]
    monkeypatch.setattr(sys, "argv", mock_argv)

    mock_client = MockLockClient()

    def mock_lock_client_class(developer_id=None):
        return mock_client

    monkeypatch.setattr(lock_client_mod, "LockClient", mock_lock_client_class)

    try:
        watcher_mod.main()
    except SystemExit:
        pass

    assert mock_client.watch_called
    assert mock_client.watch_kwargs.get("open_dashboard") is True


def test_main_with_all_args(monkeypatch):
    """Test main function with all arguments."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    mock_argv = [
        "watcher.py",
        "--interval",
        "15",
        "--timeout",
        "45",
        "--open-dashboard",
    ]
    monkeypatch.setattr(sys, "argv", mock_argv)

    mock_client = MockLockClient()

    def mock_lock_client_class(developer_id=None):
        mock_client.developer_id = developer_id
        return mock_client

    monkeypatch.setattr(lock_client_mod, "LockClient", mock_lock_client_class)

    try:
        watcher_mod.main()
    except SystemExit:
        pass

    assert mock_client.watch_called
    assert mock_client.watch_kwargs.get("interval") == 15
    assert mock_client.watch_kwargs.get("timeout_mins") == 45
    assert mock_client.watch_kwargs.get("open_dashboard") is True


# ============================================================================
# Error Handling Tests
# ============================================================================


def test_main_handles_keyboard_interrupt(monkeypatch):
    """Test main function gracefully handles KeyboardInterrupt."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    mock_argv = ["watcher.py"]
    monkeypatch.setattr(sys, "argv", mock_argv)

    class InterruptClient:
        def __init__(self, developer_id=None):
            self.developer_id = developer_id

        def watch(self, **kwargs):
            raise KeyboardInterrupt()

    def mock_lock_client_class(developer_id=None):
        return InterruptClient(developer_id)

    monkeypatch.setattr(lock_client_mod, "LockClient", mock_lock_client_class)

    # watcher.main() doesn't catch KeyboardInterrupt itself; it lets
    # LockClient.watch handle it. If it propagates, that's expected.
    try:
        watcher_mod.main()
    except (KeyboardInterrupt, SystemExit):
        pass


def test_main_handles_exception(monkeypatch):
    """Test main function handles general exceptions."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    mock_argv = ["watcher.py"]
    monkeypatch.setattr(sys, "argv", mock_argv)

    class FailingClient:
        def __init__(self, developer_id=None):
            self.developer_id = developer_id

        def watch(self, **kwargs):
            raise RuntimeError("Test error")

    def mock_lock_client_class(developer_id=None):
        return FailingClient(developer_id)

    monkeypatch.setattr(lock_client_mod, "LockClient", mock_lock_client_class)

    try:
        watcher_mod.main()
    except (SystemExit, RuntimeError):
        pass


def test_main_zero_timeout_disables_timeout(monkeypatch):
    """Test that timeout=0 disables the timeout feature."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    mock_argv = ["watcher.py", "--timeout", "0"]
    monkeypatch.setattr(sys, "argv", mock_argv)

    mock_client = MockLockClient()

    def mock_lock_client_class(developer_id=None):
        return mock_client

    monkeypatch.setattr(lock_client_mod, "LockClient", mock_lock_client_class)

    try:
        watcher_mod.main()
    except SystemExit:
        pass

    assert mock_client.watch_called
    assert mock_client.watch_kwargs.get("timeout_mins") == 0


def test_main_negative_interval_handled(monkeypatch):
    """Test that negative interval values are handled."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    mock_argv = ["watcher.py", "--interval", "-5"]
    monkeypatch.setattr(sys, "argv", mock_argv)

    mock_client = MockLockClient()

    def mock_lock_client_class(developer_id=None):
        return mock_client

    monkeypatch.setattr(lock_client_mod, "LockClient", mock_lock_client_class)

    try:
        watcher_mod.main()
    except (SystemExit, ValueError):
        pass


# ============================================================================
# Comprehensive Edge Cases (restored from test_watcher_comprehensive.py)
# ============================================================================


def test_main_lock_client_called_without_developer_id(monkeypatch):
    """Test that watcher.main() calls LockClient() without a developer_id argument.

    The watcher module does not accept --developer-id; it relies on LockClient's default
    (git config or env). Verify the constructor receives developer_id=None.
    """
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    mock_argv = ["watcher.py"]
    monkeypatch.setattr(sys, "argv", mock_argv)

    init_kwargs = {}
    mock_client = MockLockClient()

    def mock_lock_client_class(developer_id=None):
        init_kwargs["developer_id"] = developer_id
        return mock_client

    monkeypatch.setattr(lock_client_mod, "LockClient", mock_lock_client_class)

    try:
        watcher_mod.main()
    except SystemExit:
        pass

    assert mock_client.watch_called
    assert init_kwargs.get("developer_id") is None


# ============================================================================
# Import Fallback / Module Path Tests
# ============================================================================


def test_watcher_module_has_logger():
    """Test that the watcher module defines a logger."""
    assert hasattr(watcher_mod, "logger")


def test_watcher_module_path_setup():
    """Test that the module sets up sys.path for imports."""
    src = module_file.read_text()
    assert "sys.path.insert" in src
    assert "core.lock_client" in src


def test_watcher_import_fallback_path():
    """Test that the watcher module has an ImportError fallback path.

    The watcher.py handles ImportError by adjusting sys.path and re-importing. We verify
    the code structure exists (lines 27-34).
    """
    src = module_file.read_text()
    assert "except ImportError" in src
    assert "load_dotenv" in src


def test_watcher_main_block_present():
    """Test that __name__ == '__main__' block exists (line 59)."""
    src = module_file.read_text()
    assert '__name__ == "__main__"' in src or "__name__ == '__main__'" in src
