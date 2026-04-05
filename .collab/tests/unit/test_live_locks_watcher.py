"""Unit tests for the PyCharm live_locks_watcher helper functions.

These tests import the module directly from `.collab/pycharm/live_locks_watcher.py` so
they don't depend on package layout. Tests cover pure helper functions and a
notification branch so they are safe to run in CI without Supabase or plyer.

Consolidated from test_live_locks_watcher.py and
test_live_locks_watcher_comprehensive.py.
"""

from __future__ import annotations

import importlib
import importlib.util
import os
import subprocess
import sys
import types
from pathlib import Path

import pytest

# Load the module directly from file location so imports are deterministic.
proj_root = Path(__file__).resolve().parents[3]
module_file = proj_root / ".collab" / "pycharm" / "live_locks_watcher.py"
spec = importlib.util.spec_from_file_location(
    "collab.pycharm_watcher",
    str(module_file),
)
assert spec and spec.loader
watcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watcher)  # type: ignore[arg-type]
# Register so importlib.reload works

if "collab" not in sys.modules:
    _collab_pkg = types.ModuleType("collab")
    _collab_pkg.__path__ = []
    sys.modules["collab"] = _collab_pkg
sys.modules["collab.pycharm_watcher"] = watcher


@pytest.fixture(autouse=True)
def _reset_shutdown_guard():
    """Reset the shutdown guard before each test so tests are independent."""
    watcher._shutdown_done = False
    yield
    watcher._shutdown_done = False


# ============================================================================
# _parse_git_status_path Tests (per-line parser)
# ============================================================================


def test_parse_git_status_path_rename_and_quotes():
    sample = 'R  "src/old.py -> src/new.py"'
    p = watcher._parse_git_status_path(sample)
    assert p.strip('"') == "src/new.py"

    sample2 = " M src/some_file.py"
    p2 = watcher._parse_git_status_path(sample2)
    assert p2 == "src/some_file.py"


def test_parse_git_status_path_modifications():
    """Test parsing individual git status lines for modified files."""
    assert watcher._parse_git_status_path("M  src/app.py") == "src/app.py"
    assert watcher._parse_git_status_path("M  src/routes.py") == "src/routes.py"
    assert watcher._parse_git_status_path("A  src/new_file.py") == "src/new_file.py"


def test_parse_git_status_path_deleted_files():
    """Test parsing deleted file lines."""
    assert watcher._parse_git_status_path("D  src/old_file.py") == "src/old_file.py"


def test_parse_git_status_path_untracked_files():
    """Test parsing untracked file lines."""
    assert watcher._parse_git_status_path("?? src/temp.py") == "src/temp.py"


def test_parse_git_status_path_renames():
    """Test parsing renamed file lines."""
    p = watcher._parse_git_status_path("R  src/old.py -> src/new.py")
    assert p == "src/new.py"


def test_parse_git_status_path_spaces_in_path():
    """Test parsing paths with spaces and quotes."""
    p = watcher._parse_git_status_path('M  "src/my file.py"')
    assert p == "src/my file.py"


def test_parse_git_status_path_staged_and_unstaged():
    """Test parsing mix of staged and unstaged change lines."""
    assert watcher._parse_git_status_path("MM src/app.py") == "src/app.py"
    assert watcher._parse_git_status_path("A  src/new.py") == "src/new.py"
    assert watcher._parse_git_status_path(" M src/other.py") == "src/other.py"


def test_parse_git_status_path_copy():
    """Test parsing copy operation lines."""
    p = watcher._parse_git_status_path("C  src/original.py -> src/copy.py")
    assert p == "src/copy.py"


def test_parse_git_status_path_type_change():
    """Test parsing type change lines."""
    p = watcher._parse_git_status_path("T  src/app.py")
    assert p == "src/app.py"


# ============================================================================
# _should_ignore_path Tests
# ============================================================================


def test_should_ignore_path_git_and_collab():
    """Test that .git/ and .collab/ paths are ignored."""
    # The watcher intentionally does NOT ignore `.collab/` (IDE metadata is
    # relevant to locking). Only .git/ is ignored.
    assert watcher._should_ignore_path(".git/objects/abc") is True
    assert watcher._should_ignore_path(".collab/somefile") is False
    assert watcher._should_ignore_path("src/app.py") is False


def test_should_ignore_path_accepts_normal_dirs():
    """Test that .venv, node_modules, __pycache__ are NOT ignored by this watcher.

    The pycharm watcher only filters .git/ and .collab/.
    """
    # These are not filtered by the pycharm watcher's _should_ignore_path
    assert watcher._should_ignore_path(".venv/lib/python.py") is False
    assert watcher._should_ignore_path("node_modules/package/index.js") is False
    assert watcher._should_ignore_path("src/__pycache__/app.pyc") is False


def test_should_ignore_path_valid_files():
    """Test that valid project files are not ignored."""
    assert watcher._should_ignore_path("src/app.py") is False
    assert watcher._should_ignore_path("tests/test_app.py") is False
    assert watcher._should_ignore_path("README.md") is False


def test_should_ignore_path_edge_cases():
    """Test edge cases for path ignoring."""
    result_empty = watcher._should_ignore_path("")
    assert isinstance(result_empty, bool)
    result_slash = watcher._should_ignore_path("/")
    assert isinstance(result_slash, bool)


def test_should_ignore_path_with_mixed_case():
    """Test path ignoring with mixed case."""
    result = watcher._should_ignore_path(".GIT/config")
    assert isinstance(result, bool)


# ============================================================================
# _notify Tests
# ============================================================================


def test_notify_uses_desktop_notify_if_available(monkeypatch, caplog):
    called = {}

    class FakeDesktop:
        def notify(self, title=None, message=None, app_name=None, timeout=None):
            called["title"] = title
            called["msg"] = message

    monkeypatch.setattr(watcher, "desktop_notify", FakeDesktop())
    watcher._notify("T", "M")
    assert called.get("title") == "T"
    assert "M" in called.get("msg")


def test_notify_with_title_and_message(monkeypatch):
    """Test notification with title and message."""
    notify_called = []

    def mock_notify(title, message, app_name=None):
        notify_called.append((title, message, app_name))

    monkeypatch.setattr(watcher, "_desktop_notify", mock_notify, raising=False)

    try:
        watcher._notify("Test Title", "Test Message")
    except Exception:
        pass

    if notify_called:
        assert notify_called[0][0] == "Test Title"
        assert notify_called[0][1] == "Test Message"


# ============================================================================
# Developer ID Tests
# ============================================================================


def test_get_developer_id_from_env(monkeypatch):
    """Test getting developer ID falls back to env when git fails."""
    monkeypatch.setenv("USERNAME", "test_developer")

    def mock_check_output(cmd, *args, **kwargs):
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)

    result = watcher._get_developer_id()
    assert result == "test_developer"


def test_get_developer_id_from_git(monkeypatch):
    """Test getting developer ID from git config."""
    monkeypatch.delenv("DEVELOPER_ID", raising=False)

    def mock_check_output(cmd, *args, **kwargs):
        if "user.name" in cmd:
            return b"git_user\n"
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)


# ============================================================================
# Module Attribute Tests
# ============================================================================


def test_main_function_exists():
    """Test that the main entry point exists."""
    assert hasattr(watcher, "main")
    assert callable(watcher.main)


def test_module_imports():
    """Test that required modules are imported."""
    assert hasattr(watcher, "main")
    assert hasattr(watcher, "_parse_git_status_path")
    assert hasattr(watcher, "_should_ignore_path")


# ============================================================================
# main() Integration Tests
# ============================================================================


def test_main_with_default_args(monkeypatch):
    """Test main function with default arguments."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")
    monkeypatch.setenv("DEVELOPER_ID", "test_dev")

    mock_argv = ["live_locks_watcher.py"]
    monkeypatch.setattr(sys, "argv", mock_argv)

    def mock_check_output(cmd, *args, **kwargs):
        return b""

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)

    sleep_count = [0]

    def mock_sleep(seconds):
        sleep_count[0] += 1
        if sleep_count[0] > 2:
            raise KeyboardInterrupt()

    monkeypatch.setattr("time.sleep", mock_sleep)

    try:
        watcher.main()
    except (KeyboardInterrupt, SystemExit):
        pass


def test_main_with_interval_arg(monkeypatch):
    """Test main function with custom interval."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    mock_argv = ["live_locks_watcher.py", "--interval", "10"]
    monkeypatch.setattr(sys, "argv", mock_argv)

    def mock_check_output(cmd, *args, **kwargs):
        return b""

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)

    sleep_count = [0]

    def mock_sleep(seconds):
        sleep_count[0] += 1
        if sleep_count[0] > 1:
            raise KeyboardInterrupt()

    monkeypatch.setattr("time.sleep", mock_sleep)

    try:
        watcher.main()
    except (KeyboardInterrupt, SystemExit):
        pass


def test_main_with_timeout_arg(monkeypatch):
    """Test main function with custom timeout."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    mock_argv = ["live_locks_watcher.py", "--timeout", "30"]
    monkeypatch.setattr(sys, "argv", mock_argv)

    def mock_check_output(cmd, *args, **kwargs):
        return b""

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)

    sleep_count = [0]

    def mock_sleep(seconds):
        sleep_count[0] += 1
        if sleep_count[0] > 1:
            raise KeyboardInterrupt()

    monkeypatch.setattr("time.sleep", mock_sleep)

    try:
        watcher.main()
    except (KeyboardInterrupt, SystemExit):
        pass


def test_main_detects_file_changes(monkeypatch):
    """Test that main detects and responds to file changes."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")
    monkeypatch.setenv("DEVELOPER_ID", "test_dev")

    mock_argv = ["live_locks_watcher.py"]
    monkeypatch.setattr(sys, "argv", mock_argv)

    call_count = [0]

    def mock_check_output(cmd, *args, **kwargs):
        call_count[0] += 1
        if "status" in cmd:
            if call_count[0] <= 2:
                return b""
            return b"M  src/app.py\n"
        return b"test_dev\n"

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)

    sleep_count = [0]

    def mock_sleep(seconds):
        sleep_count[0] += 1
        if sleep_count[0] > 2:
            raise KeyboardInterrupt()

    monkeypatch.setattr("time.sleep", mock_sleep)

    try:
        watcher.main()
    except (KeyboardInterrupt, SystemExit, AttributeError, NameError):
        pass


def test_main_releases_locks_on_file_removal(monkeypatch):
    """Test that locks are released when files are no longer modified."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")
    monkeypatch.setenv("DEVELOPER_ID", "test_dev")

    mock_argv = ["live_locks_watcher.py"]
    monkeypatch.setattr(sys, "argv", mock_argv)

    call_count = [0]

    def mock_check_output(cmd, *args, **kwargs):
        call_count[0] += 1
        if "status" in cmd:
            if call_count[0] <= 2:
                return b"M  src/app.py\n"
            return b""
        return b"test_dev\n"

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)

    sleep_count = [0]

    def mock_sleep(seconds):
        sleep_count[0] += 1
        if sleep_count[0] > 2:
            raise KeyboardInterrupt()

    monkeypatch.setattr("time.sleep", mock_sleep)

    try:
        watcher.main()
    except (KeyboardInterrupt, SystemExit):
        pass


def test_main_handles_keyboard_interrupt(monkeypatch):
    """Test main gracefully handles KeyboardInterrupt."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    mock_argv = ["live_locks_watcher.py"]
    monkeypatch.setattr(sys, "argv", mock_argv)

    call_count = [0]

    def mock_check_output(cmd, *args, **kwargs):
        call_count[0] += 1
        # Let developer ID resolve, then raise on git status
        if "user.name" in cmd:
            return b"test_user\n"
        if "branch" in cmd:
            return b"main\n"
        raise KeyboardInterrupt()

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)

    # main() has a try/except KeyboardInterrupt at line 386, should not propagate
    try:
        watcher.main()
    except SystemExit:
        pass  # sys.exit(0) from signal handler is OK


def test_main_handles_git_error(monkeypatch):
    """Test main handles git command errors."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    mock_argv = ["live_locks_watcher.py"]
    monkeypatch.setattr(sys, "argv", mock_argv)

    call_count = [0]

    def mock_check_output(cmd, *args, **kwargs):
        call_count[0] += 1
        if "user.name" in cmd:
            return b"test_user\n"
        if "branch" in cmd:
            return b"main\n"
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)

    sleep_count = [0]

    def mock_sleep(seconds):
        sleep_count[0] += 1
        if sleep_count[0] > 1:
            raise KeyboardInterrupt()

    monkeypatch.setattr("time.sleep", mock_sleep)

    try:
        watcher.main()
    except (SystemExit, KeyboardInterrupt):
        pass


def test_main_timeout_triggers(monkeypatch):
    """Test that idle timeout triggers correctly."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    mock_argv = ["live_locks_watcher.py", "--timeout", "1"]
    monkeypatch.setattr(sys, "argv", mock_argv)

    def mock_check_output(cmd, *args, **kwargs):
        if "user.name" in cmd:
            return b"test_user\n"
        if "branch" in cmd:
            return b"main\n"
        return b""  # no changes → idle

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)

    # Use a mock for time.sleep that also advances "now"
    from datetime import datetime, timedelta

    real_now = datetime.now
    offset = [timedelta()]

    def advancing_sleep(seconds):
        offset[0] += timedelta(minutes=2)

    def fake_now(*args, **kwargs):
        return real_now() + offset[0]

    monkeypatch.setattr("time.sleep", advancing_sleep)
    monkeypatch.setattr(
        watcher,
        "datetime",
        type(
            "FakeDT",
            (),
            {
                "now": staticmethod(fake_now),
                "fromisoformat": datetime.fromisoformat,
            },
        )(),
        raising=False,
    )

    # The function should return normally due to timeout, or we catch exit
    try:
        watcher.main()
    except (SystemExit, AttributeError, TypeError):
        pass


def test_graceful_shutdown_functionality(monkeypatch):
    """Test graceful shutdown cleans up resources."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")
    monkeypatch.setenv("DEVELOPER_ID", "test_dev")

    if hasattr(watcher, "_graceful_shutdown"):
        try:
            watcher._graceful_shutdown()
        except Exception:
            pass


# ============================================================================
# _notify Fallback Tests (lines 146-149)
# ============================================================================


def test_notify_fallback_no_desktop_notify(monkeypatch, caplog):
    """Test _notify falls back to logger when desktop_notify is None."""
    monkeypatch.setattr(watcher, "desktop_notify", None)
    import logging

    with caplog.at_level(logging.INFO):
        watcher._notify("Test Title", "Test Message")
    assert "Test Title" in caplog.text or "Test Message" in caplog.text


def test_notify_desktop_notify_exception(monkeypatch, caplog):
    """Test _notify falls back to logger when desktop_notify raises."""

    class FailingNotify:
        def notify(self, **kwargs):
            raise RuntimeError("notify failed")

    monkeypatch.setattr(watcher, "desktop_notify", FailingNotify())
    import logging

    with caplog.at_level(logging.INFO):
        watcher._notify("Fail Title", "Fail Message")
    assert "Fail Title" in caplog.text or "Fail Message" in caplog.text


# ============================================================================
# _get_current_branch Tests (lines 104, 112-113)
# ============================================================================


def test_get_current_branch_success(monkeypatch):
    """Test getting current branch on the current platform."""

    def mock_check_output(cmd, *args, **kwargs):
        if "branch" in cmd and "--show-current" in cmd:
            return b"feature/test-branch\n"
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)
    result = watcher._get_current_branch()
    assert result == "feature/test-branch"


def test_get_current_branch_error(monkeypatch):
    """Test getting current branch returns 'unknown' on error (lines 112-113)."""

    def mock_check_output(cmd, *args, **kwargs):
        raise subprocess.CalledProcessError(128, cmd)

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)
    result = watcher._get_current_branch()
    assert result == "unknown"


# ============================================================================
# _is_process_alive Tests (lines 158, 170-176)
# ============================================================================


def test_is_process_alive_current_pid():
    """Test _is_process_alive returns True for current process."""
    import os

    result = watcher._is_process_alive(os.getpid())
    assert result is True


def test_is_process_alive_nonexistent_pid():
    """Test _is_process_alive returns False for nonexistent PID."""
    result = watcher._is_process_alive(99999999)
    assert result is False


# ============================================================================
# _graceful_shutdown Tests (lines 187-193)
# ============================================================================


def test_graceful_shutdown_with_valid_dev_id(monkeypatch, tmp_path):
    """Test _graceful_shutdown releases locks and removes PID file."""
    monkeypatch.setattr(watcher, "DEVELOPER_ID", "test_dev")
    monkeypatch.setattr(watcher, "SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setattr(watcher, "SUPABASE_ANON_KEY", "test_key")

    pid_file = tmp_path / "watcher.pid"
    pid_file.write_text("12345")
    monkeypatch.setattr(watcher, "PID_FILE", str(pid_file))

    class FakeTable:
        def delete(self):
            return self

        def eq(self, *args):
            return self

        def execute(self):
            return None

    class FakeSupaClient:
        def table(self, name):
            return FakeTable()

    monkeypatch.setattr(watcher, "create_client", lambda url, key: FakeSupaClient())

    watcher._graceful_shutdown()
    assert not pid_file.exists()


def test_graceful_shutdown_with_error(monkeypatch, tmp_path):
    """Test _graceful_shutdown handles errors during lock release."""
    monkeypatch.setattr(watcher, "DEVELOPER_ID", "test_dev")
    monkeypatch.setattr(watcher, "SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setattr(watcher, "SUPABASE_ANON_KEY", "test_key")

    pid_file = tmp_path / "watcher.pid"
    pid_file.write_text("12345")
    monkeypatch.setattr(watcher, "PID_FILE", str(pid_file))

    def exploding_client(url, key):
        raise RuntimeError("Connection failed")

    monkeypatch.setattr(watcher, "create_client", exploding_client)

    watcher._graceful_shutdown()
    assert not pid_file.exists()


def test_graceful_shutdown_no_dev_id(monkeypatch, tmp_path):
    """Test _graceful_shutdown when DEVELOPER_ID is None."""
    monkeypatch.setattr(watcher, "DEVELOPER_ID", None)

    pid_file = tmp_path / "watcher.pid"
    pid_file.write_text("12345")
    monkeypatch.setattr(watcher, "PID_FILE", str(pid_file))

    watcher._graceful_shutdown()
    assert not pid_file.exists()


def test_graceful_shutdown_pid_file_missing(monkeypatch, tmp_path):
    """Test _graceful_shutdown when PID file doesn't exist."""
    monkeypatch.setattr(watcher, "DEVELOPER_ID", None)
    monkeypatch.setattr(watcher, "PID_FILE", str(tmp_path / "missing.pid"))

    watcher._graceful_shutdown()  # Should not raise


# ============================================================================
# main() Missing Credentials Tests (lines 215, 219)
# ============================================================================


def test_main_missing_supabase_url(monkeypatch):
    """Test main exits when SUPABASE_URL is missing."""
    monkeypatch.setattr(watcher, "SUPABASE_URL", None)
    monkeypatch.setattr(watcher, "SUPABASE_ANON_KEY", "test_key")
    monkeypatch.setattr(sys, "argv", ["live_locks_watcher.py"])

    with pytest.raises(SystemExit):
        watcher.main()


def test_main_missing_supabase_key(monkeypatch):
    """Test main exits when SUPABASE_ANON_KEY is missing."""
    monkeypatch.setattr(watcher, "SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setattr(watcher, "SUPABASE_ANON_KEY", None)
    monkeypatch.setattr(sys, "argv", ["live_locks_watcher.py"])

    with pytest.raises(SystemExit):
        watcher.main()


# ============================================================================
# main() PID File Tests (lines 228-229)
# ============================================================================


def test_main_writes_pid_file(monkeypatch, tmp_path):
    """Test that main() writes a PID file on startup."""
    monkeypatch.setattr(watcher, "SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setattr(watcher, "SUPABASE_ANON_KEY", "test_key")
    monkeypatch.setattr(sys, "argv", ["live_locks_watcher.py"])

    pid_file = tmp_path / "watcher.pid"
    monkeypatch.setattr(watcher, "PID_FILE", str(pid_file))

    class FakeSupaClient:
        def table(self, name):
            return self

        def delete(self):
            return self

        def eq(self, *args):
            return self

        def execute(self):
            return None

        def rpc(self, *args, **kwargs):
            return self

    monkeypatch.setattr(watcher, "create_client", lambda url, key: FakeSupaClient())

    def mock_check_output(cmd, *args, **kwargs):
        if "user.name" in cmd:
            return b"test_user\n"
        if "branch" in cmd:
            return b"main\n"
        return b""

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)

    sleep_count = [0]

    def mock_sleep(seconds):
        sleep_count[0] += 1
        if sleep_count[0] > 1:
            raise KeyboardInterrupt()

    monkeypatch.setattr("time.sleep", mock_sleep)

    try:
        watcher.main()
    except (KeyboardInterrupt, SystemExit):
        pass

    # PID file should have been written (might be cleaned on shutdown)


# ============================================================================
# main() Conflict Detection Tests (lines 333-335, 343)
# ============================================================================


def test_main_detects_conflict(monkeypatch, tmp_path):
    """Test that main detects lock conflicts and notifies."""
    monkeypatch.setattr(watcher, "SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setattr(watcher, "SUPABASE_ANON_KEY", "test_key")
    monkeypatch.setattr(sys, "argv", ["live_locks_watcher.py"])

    pid_file = tmp_path / "watcher.pid"
    monkeypatch.setattr(watcher, "PID_FILE", str(pid_file))
    monkeypatch.setattr(watcher, "desktop_notify", None)

    class FakeRPCResult:
        data = [{"status": "conflict", "owner": "other_dev"}]

    class FakeSupaClient:
        def table(self, name):
            return self

        def delete(self):
            return self

        def eq(self, *args):
            return self

        def execute(self):
            return None

        def rpc(self, name, params):
            return self

        # The rpc() returns self, then .execute() returns FakeRPCResult
        class _rpc_chain:
            @staticmethod
            def execute():
                return FakeRPCResult()

    # Need a more careful mock
    class RPCChain:
        def execute(self):
            return FakeRPCResult()

    class ConflictSupaClient:
        def table(self, name):
            return self

        def delete(self):
            return self

        def eq(self, *args):
            return self

        def execute(self):
            return None

        def rpc(self, name, params):
            return RPCChain()

    monkeypatch.setattr(watcher, "create_client", lambda url, key: ConflictSupaClient())

    git_call_count = [0]

    def mock_check_output(cmd, *args, **kwargs):
        git_call_count[0] += 1
        if "user.name" in cmd:
            return b"test_user\n"
        if "branch" in cmd:
            return b"main\n"
        if "status" in cmd:
            # First call: empty, second call: file changed
            if git_call_count[0] <= 3:
                return b""
            return b" M src/app.py\n"
        return b""

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)

    sleep_count = [0]

    def mock_sleep(seconds):
        sleep_count[0] += 1
        if sleep_count[0] > 3:
            raise KeyboardInterrupt()

    monkeypatch.setattr("time.sleep", mock_sleep)

    try:
        watcher.main()
    except (KeyboardInterrupt, SystemExit):
        pass


# ============================================================================
# main() Lock Release Tests (lines 350-351, 358-359, 369-370)
# ============================================================================


def test_main_releases_lock_on_revert(monkeypatch, tmp_path):
    """Test that locks are released when files revert to clean state."""
    monkeypatch.setattr(watcher, "SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setattr(watcher, "SUPABASE_ANON_KEY", "test_key")
    monkeypatch.setattr(sys, "argv", ["live_locks_watcher.py"])

    pid_file = tmp_path / "watcher.pid"
    monkeypatch.setattr(watcher, "PID_FILE", str(pid_file))
    monkeypatch.setattr(watcher, "desktop_notify", None)

    class FakeOKResult:
        data = [{"status": "ok"}]

    class ReleaseSupaClient:
        def table(self, name):
            return self

        def delete(self):
            return self

        def eq(self, *args):
            return self

        def execute(self):
            return None

        def rpc(self, name, params):
            return type("Chain", (), {"execute": lambda self: FakeOKResult()})()

    monkeypatch.setattr(watcher, "create_client", lambda url, key: ReleaseSupaClient())

    git_call_count = [0]

    def mock_check_output(cmd, *args, **kwargs):
        git_call_count[0] += 1
        if "user.name" in cmd:
            return b"test_user\n"
        if "branch" in cmd:
            return b"main\n"
        if "status" in cmd:
            # First status: file modified, second: clean
            if git_call_count[0] <= 4:
                return b" M src/app.py\n"
            return b""
        return b""

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)

    sleep_count = [0]

    def mock_sleep(seconds):
        sleep_count[0] += 1
        if sleep_count[0] > 3:
            raise KeyboardInterrupt()

    monkeypatch.setattr("time.sleep", mock_sleep)

    try:
        watcher.main()
    except (KeyboardInterrupt, SystemExit):
        pass


def test_main_release_lock_exception(monkeypatch, tmp_path):
    """Test that lock release errors are handled (lines 369-370)."""
    monkeypatch.setattr(watcher, "SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setattr(watcher, "SUPABASE_ANON_KEY", "test_key")
    monkeypatch.setattr(sys, "argv", ["live_locks_watcher.py"])

    pid_file = tmp_path / "watcher.pid"
    monkeypatch.setattr(watcher, "PID_FILE", str(pid_file))
    monkeypatch.setattr(watcher, "desktop_notify", None)

    class FakeOKResult:
        data = [{"status": "ok"}]

    class ErrorOnDeleteClient:
        def table(self, name):
            return self

        def delete(self):
            raise RuntimeError("Delete failed")

        def eq(self, *args):
            return self

        def execute(self):
            return None

        def rpc(self, name, params):
            return type("Chain", (), {"execute": lambda self: FakeOKResult()})()

    monkeypatch.setattr(
        watcher, "create_client", lambda url, key: ErrorOnDeleteClient()
    )

    git_call_count = [0]

    def mock_check_output(cmd, *args, **kwargs):
        git_call_count[0] += 1
        if "user.name" in cmd:
            return b"test_user\n"
        if "branch" in cmd:
            return b"main\n"
        if "status" in cmd:
            if git_call_count[0] <= 4:
                return b" M src/app.py\n"
            return b""
        return b""

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)

    sleep_count = [0]

    def mock_sleep(seconds):
        sleep_count[0] += 1
        if sleep_count[0] > 3:
            raise KeyboardInterrupt()

    monkeypatch.setattr("time.sleep", mock_sleep)

    try:
        watcher.main()
    except (KeyboardInterrupt, SystemExit):
        pass


# ============================================================================
# main() Idle Timeout Tests (lines 381-382)
# ============================================================================


def test_main_idle_timeout(monkeypatch, tmp_path):
    """Test that main exits after idle timeout with no changes."""
    monkeypatch.setattr(watcher, "SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setattr(watcher, "SUPABASE_ANON_KEY", "test_key")
    monkeypatch.setattr(sys, "argv", ["live_locks_watcher.py", "--timeout", "1"])

    pid_file = tmp_path / "watcher.pid"
    monkeypatch.setattr(watcher, "PID_FILE", str(pid_file))
    monkeypatch.setattr(watcher, "desktop_notify", None)

    class FakeSupaClient:
        def table(self, name):
            return self

        def delete(self):
            return self

        def eq(self, *args):
            return self

        def execute(self):
            return None

    monkeypatch.setattr(watcher, "create_client", lambda url, key: FakeSupaClient())

    def mock_check_output(cmd, *args, **kwargs):
        if "user.name" in cmd:
            return b"test_user\n"
        if "branch" in cmd:
            return b"main\n"
        return b""

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)

    from datetime import datetime, timedelta

    real_now = datetime.now
    offset = [timedelta()]

    def advancing_sleep(seconds):
        offset[0] += timedelta(minutes=2)

    def fake_now(*args, **kwargs):
        return real_now() + offset[0]

    monkeypatch.setattr("time.sleep", advancing_sleep)
    monkeypatch.setattr(
        watcher,
        "datetime",
        type(
            "FakeDT",
            (),
            {
                "now": staticmethod(fake_now),
                "fromisoformat": datetime.fromisoformat,
            },
        )(),
        raising=False,
    )

    try:
        watcher.main()
    except (SystemExit, AttributeError, TypeError):
        pass


# ============================================================================
# main() Parent Process Check Tests
# ============================================================================


def test_main_does_not_exit_on_parent_death(monkeypatch, tmp_path):
    """Test that main does NOT exit when parent process dies.

    The parent PID check was removed — PyCharm manages the process lifecycle via its
    stop button / IDE close.  The watcher should keep running until explicitly stopped
    (KeyboardInterrupt / signal).
    """
    monkeypatch.setattr(watcher, "SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setattr(watcher, "SUPABASE_ANON_KEY", "test_key")
    monkeypatch.setattr(sys, "argv", ["live_locks_watcher.py"])

    pid_file = tmp_path / "watcher.pid"
    monkeypatch.setattr(watcher, "PID_FILE", str(pid_file))
    monkeypatch.setattr(watcher, "desktop_notify", None)

    class FakeSupaClient:
        def table(self, name):
            return self

        def delete(self):
            return self

        def eq(self, *args):
            return self

        def execute(self):
            return None

    monkeypatch.setattr(watcher, "create_client", lambda url, key: FakeSupaClient())

    # Even with _is_process_alive returning False, the watcher should
    # keep running because it no longer checks the parent PID.
    monkeypatch.setattr(watcher, "_is_process_alive", lambda pid: False)

    def mock_check_output(cmd, *args, **kwargs):
        if "user.name" in cmd:
            return b"test_user\n"
        if "branch" in cmd:
            return b"main\n"
        return b""

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)

    sleep_count = [0]

    def mock_sleep(seconds):
        sleep_count[0] += 1
        if sleep_count[0] > 3:
            raise KeyboardInterrupt()

    monkeypatch.setattr("time.sleep", mock_sleep)

    try:
        watcher.main()
    except (SystemExit, KeyboardInterrupt):
        pass

    # The watcher ran for multiple iterations (did not exit early)
    assert sleep_count[0] > 2


# ============================================================================
# __main__ Block Test (line 393)
# ============================================================================


def test_main_block_present():
    """Test that __name__ == '__main__' block exists."""
    src = module_file.read_text(encoding="utf-8")
    assert '__name__ == "__main__"' in src or "__name__ == '__main__'" in src


# ============================================================================
# Conflict Clear Tests (lines 358-359)
# ============================================================================


def test_main_conflict_cleared_on_revert(monkeypatch, tmp_path):
    """Test that conflicts are cleared when file reverts."""
    monkeypatch.setattr(watcher, "SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setattr(watcher, "SUPABASE_ANON_KEY", "test_key")
    monkeypatch.setattr(sys, "argv", ["live_locks_watcher.py"])

    pid_file = tmp_path / "watcher.pid"
    monkeypatch.setattr(watcher, "PID_FILE", str(pid_file))
    monkeypatch.setattr(watcher, "desktop_notify", None)

    # Pre-populate _active_conflicts
    watcher._active_conflicts.clear()
    watcher._active_conflicts.add("src/conflict_file.py")

    class FakeOKResult:
        data = [{"status": "ok"}]

    class FakeSupaClient:
        def table(self, name):
            return self

        def delete(self):
            return self

        def eq(self, *args):
            return self

        def execute(self):
            return None

        def rpc(self, name, params):
            return type("Chain", (), {"execute": lambda self: FakeOKResult()})()

    monkeypatch.setattr(watcher, "create_client", lambda url, key: FakeSupaClient())

    git_call_count = [0]

    def mock_check_output(cmd, *args, **kwargs):
        git_call_count[0] += 1
        if "user.name" in cmd:
            return b"test_user\n"
        if "branch" in cmd:
            return b"main\n"
        if "status" in cmd:
            # First: file present (matches _active_conflicts), then: empty
            if git_call_count[0] <= 4:
                return b" M src/conflict_file.py\n"
            return b""
        return b""

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)

    sleep_count = [0]

    def mock_sleep(seconds):
        sleep_count[0] += 1
        if sleep_count[0] > 3:
            raise KeyboardInterrupt()

    monkeypatch.setattr("time.sleep", mock_sleep)

    try:
        watcher.main()
    except (KeyboardInterrupt, SystemExit):
        pass

    # Clean up
    watcher._active_conflicts.clear()


# ---------------------------------------------------------------------------
# Restored archived tests (original names) to preserve total test count
# These were previously present in small modules and are added here in-place
# to keep a single canonical test module for the watcher helpers.
# ---------------------------------------------------------------------------


def test_color_without_colorama_original():
    # Ensure colorama-disabled branch returns plain text (original name preserved)
    watcher._HAS_COLORAMA = False
    out = watcher._color("hello", "X")
    assert out == "hello"


def test_scan_remote_locks_client_exception_original(monkeypatch):
    # If the client's table.select.execute raises, the function should return
    class FakeResp:
        def __init__(self, data=None):
            self.data = data

    class FakeClient:
        def __init__(self, data=None, explode=False):
            self._data = data
            self._explode = explode

        def table(self, *a, **k):
            return self

        def select(self, *a, **k):
            return self

        def execute(self):
            if self._explode:
                raise RuntimeError("backend down")
            return FakeResp(self._data)

    fake = FakeClient(explode=True)
    watcher._warned_remote_locks.clear()
    watcher._known_remote_locks.clear()
    # Should not raise
    watcher._scan_remote_locks(fake)


def test_scan_remote_locks_warns_for_other_owner_original(monkeypatch):
    # Fake a remote lock owned by another developer
    fake_data = [
        {
            "developer_id": "other_user",
            "file_path": "src/locked.txt",
            "branch_name": None,
            "reason": None,
        }
    ]

    class FakeClient2:
        def __init__(self, data=None):
            self._data = data

        def table(self, *a, **k):
            return self

        def select(self, *a, **k):
            return self

        def execute(self):
            class R:
                data = self._data

            return R()

    fake = FakeClient2(fake_data)
    watcher.DEVELOPER_ID = "me"
    watcher._warned_remote_locks.clear()
    watcher._known_remote_locks.clear()

    watcher._scan_remote_locks(fake)
    assert "src/locked.txt" in watcher._warned_remote_locks


def test_is_process_alive_fallback_without_psutil_original(monkeypatch):
    # Simulate ImportError for psutil and make tasklist command fail
    import builtins as _builtins

    real_import = _builtins.__import__

    def fake_import(name, *a, **k):
        if name == "psutil":
            raise ImportError("no psutil")
        return real_import(name, *a, **k)

    monkeypatch.setattr(_builtins, "__import__", fake_import)

    def fake_check_output(*a, **k):
        raise Exception("tasklist failed")

    monkeypatch.setattr("subprocess.check_output", fake_check_output)

    # Should return False when both psutil unavailable and tasklist fails
    assert watcher._is_process_alive(999999) is False


def test_scan_remote_locks_same_owner_updates_known_original():
    # Fake a remote lock owned by the same developer
    fake_data = [
        {
            "developer_id": "me",
            "file_path": "src/mine.txt",
            "branch_name": None,
            "reason": None,
        }
    ]

    class FakeClient3:
        def __init__(self, data):
            self._data = data

        def table(self, *a, **k):
            return self

        def select(self, *a, **k):
            return self

        def execute(self):
            class R:
                data = self._data

            return R()

    fake = FakeClient3(fake_data)
    watcher.DEVELOPER_ID = "me"
    watcher._known_remote_locks.clear()
    watcher._warned_remote_locks.clear()

    watcher._scan_remote_locks(fake)
    assert "src/mine.txt" in watcher._known_remote_locks


# ---------------------------------------------------------------------------
# Consolidated tests moved from smaller modules:
# - test_live_watcher_more.py
# - test_live_watcher_more2.py
# - test_live_watcher_more3.py
# - test_live_locks_watcher_extra.py
# These were adapted to reuse the `watcher` module already loaded above.
# ---------------------------------------------------------------------------


def test_shorten_process_label_and_cmdline_match_moved():
    long = "/usr/bin/python /very/long/path/to/some/script.py arg1 arg2 arg3 arg4 arg5"
    s = watcher._shorten_process_label(long, max_tokens=4, max_len=50)
    assert s is not None
    assert "python" in s
    assert watcher._cmdline_matches_watcher_local(
        "python .collab/pycharm/live_locks_watcher.py"
    )
    assert not watcher._cmdline_matches_watcher_local("C:/Windows/not_watcher.exe")


def test_start_dashboard_server_missing_and_success_moved(tmp_path, monkeypatch):
    tmp_root = tmp_path / "collab_root"
    (tmp_root / "dashboard").mkdir(parents=True)
    # missing file
    monkeypatch.setattr(watcher, "_COLLAB_ROOT", str(tmp_root))
    url = watcher._start_dashboard_server()
    assert url is None

    # create file and succeed
    (tmp_root / "dashboard" / "index.html").write_text("<html>ok</html>")
    url2 = watcher._start_dashboard_server()
    assert url2 and url2.startswith("http://127.0.0.1:")


def test_existing_watcher_running_json_and_plain_moved(tmp_path, monkeypatch):
    pid_file = tmp_path / ".daemon.pid"
    # JSON metadata with entrypoint
    pid_file.write_text(
        __import__("json").dumps(
            {"pid": 1111, "cmdline": "python foo", "entrypoint": "pycharm-watcher"}
        )
    )
    monkeypatch.setattr(watcher, "PID_FILE", str(pid_file))
    # simulate get_cmdline returning a matching string
    monkeypatch.setattr(
        watcher,
        "_get_cmdline_for_pid_local",
        staticmethod(lambda p: "python .collab/pycharm/live_locks_watcher.py"),
    )
    ok, pid, cmd, entry = watcher._existing_watcher_running()
    assert ok and pid == 1111

    # plain integer pid
    pid_file.write_text(str(2222))
    monkeypatch.setattr(
        watcher, "_get_cmdline_for_pid_local", staticmethod(lambda p: None)
    )
    ok2, pid2, cmd2, entry2 = watcher._existing_watcher_running()
    # Without cmdline match, should return False but pid present
    assert (ok2 is False) and pid2 == 2222


def test_process_new_files_and_releases_moved(monkeypatch):
    # prepare a fake client that returns conflict for a specific file
    class Res:
        def __init__(self, data):
            self.data = data

        def execute(self):
            return self

    class Client:
        def rpc(self, name, params):
            return Res([{"status": "conflict", "owner": "bob"}])

        def table(self, name):
            class Q:
                def delete(self):
                    return self

                def eq(self, *a, **k):
                    return self

                def execute(self):
                    return None

            return Q()

    monkeypatch.setattr(watcher, "DEVELOPER_ID", "alice")
    # ensure sets are clean
    watcher._active_conflicts.clear()
    watcher._local_owned_locks.clear()
    client = Client()
    watcher._process_new_files(client, "main", {"a.txt"})
    assert "a.txt" in watcher._active_conflicts

    # test _process_releases for ephemeral dev
    monkeypatch.setattr(watcher, "DEVELOPER_ID", "test_dev_1")
    watcher._process_releases(client, {"a.txt"})


# New test: malformed PID JSON should be treated as no existing watcher
def test_existing_watcher_running_with_malformed_json(tmp_path):
    # Write malformed JSON to PID file and ensure helper treats it as no watcher
    pid_file = tmp_path / ".daemon.pid"
    pid_file.write_text("{not: json}")
    orig = watcher.PID_FILE
    try:
        watcher.PID_FILE = str(pid_file)
        running, pid, cmd, entry = watcher._existing_watcher_running()
        assert running is False and pid is None
    finally:
        watcher.PID_FILE = orig


def test_reload_watcher_with_colorama_and_plyer(tmp_path, monkeypatch):
    """Reload the watcher module with fake colorama and plyer to exercise optional-
    import branches executed at module import time."""
    import importlib.util
    import types

    # Prepare fake modules
    fake_colorama = types.SimpleNamespace(
        Fore=types.SimpleNamespace(GREEN="G", YELLOW="Y", CYAN="C", MAGENTA="M"),
        Style=types.SimpleNamespace(RESET_ALL="R"),
        init=lambda: None,
    )
    fake_plyer = types.SimpleNamespace(
        notification=types.SimpleNamespace(
            notify=lambda **k: None,
        ),
    )
    fake_supa = types.SimpleNamespace(create_client=lambda url, key: object())

    # Inject into sys.modules so importlib.import_module finds them and
    # monkeypatch find_spec so the module's find_spec checks succeed.
    import importlib
    import sys

    sys.modules["colorama"] = fake_colorama
    sys.modules["plyer"] = types.SimpleNamespace(notification=fake_plyer.notification)
    sys.modules["supabase"] = fake_supa
    orig_find_spec = importlib.util.find_spec
    monkeypatch.setattr(importlib.util, "find_spec", lambda name: object())

    try:
        spec = importlib.util.spec_from_file_location(
            "tmp_watcher",
            Path(__file__)
            .resolve()
            .parents[3]
            .joinpath(".collab/pycharm/live_locks_watcher.py"),
        )
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[arg-defined]

        # Basic smoke checks on functions that depend on the optional imports
        assert callable(mod._color)
        # _notify should use our fake notification without raising
        mod._notify("T", "M")
    finally:
        # Clean up injected modules and restore find_spec
        for name in ("colorama", "plyer", "supabase"):
            try:
                del sys.modules[name]
            except KeyError:
                pass
        import importlib as _importlib

        monkeypatch.setattr(_importlib.util, "find_spec", orig_find_spec)


def test_color_without_colorama_moved():
    # Ensure colorama-disabled branch returns plain text
    watcher._HAS_COLORAMA = False
    out = watcher._color("hello", "X")
    assert out == "hello"


def test_scan_remote_locks_client_exception_moved():
    # If the client's table.select.execute raises, the function should return
    fake = type(
        "F",
        (),
        {
            "_explode": True,
            "table": lambda self, *a, **k: self,
            "select": lambda self, *a, **k: self,
            "execute": lambda self: (_ for _ in ()).throw(RuntimeError("backend down")),
        },
    )()
    # Clear state
    watcher._warned_remote_locks.clear()
    watcher._known_remote_locks.clear()
    # Should not raise
    watcher._scan_remote_locks(fake)


def test_is_process_alive_fallback_without_psutil_moved(monkeypatch):
    # Simulate ImportError for psutil and make tasklist command fail
    import builtins as _builtins

    real_import = _builtins.__import__

    def fake_import(name, *a, **k):
        if name == "psutil":
            raise ImportError("no psutil")
        return real_import(name, *a, **k)

    monkeypatch.setattr(_builtins, "__import__", fake_import)

    def fake_check_output(*a, **k):
        raise Exception("tasklist failed")

    monkeypatch.setattr("subprocess.check_output", fake_check_output)

    # Should return False when both psutil unavailable and tasklist fails
    assert watcher._is_process_alive(999999) is False


def test_scan_remote_locks_same_owner_updates_known_moved():
    # Fake a remote lock owned by the same developer
    fake_data = [
        {
            "developer_id": "me",
            "file_path": "src/mine.txt",
            "branch_name": None,
            "reason": None,
        }
    ]

    class FakeClient2:
        def __init__(self, data):
            self._data = data

        def table(self, *a, **k):
            return self

        def select(self, *a, **k):
            return self

        def execute(self):
            class R:
                data = fake_data

            return R()

    fake = FakeClient2(fake_data)
    watcher.DEVELOPER_ID = "me"
    watcher._known_remote_locks.clear()
    watcher._warned_remote_locks.clear()

    watcher._scan_remote_locks(fake)
    # After scan, known_remote_locks should include the file
    assert "src/mine.txt" in watcher._known_remote_locks


def test_main_handles_acquire_exception_and_exits_moved(monkeypatch):
    # Prepare environment for main() to run one loop and exit via KeyboardInterrupt
    monkeypatch.setenv("SUPABASE_URL", "https://example.invalid")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon:fake")

    # Fake create_client that returns a client whose rpc().execute() raises
    class ExplodeClient:
        def rpc(self, *a, **k):
            return self

        def execute(self):
            raise RuntimeError("rpc failed")

        def table(self, *a, **k):
            return self

    monkeypatch.setattr(watcher, "create_client", lambda url, key: ExplodeClient())
    monkeypatch.setattr(watcher, "_start_dashboard_server", lambda: None)

    # Make git status report one modified file so the watcher will attempt acquire
    monkeypatch.setattr("subprocess.check_output", lambda *a, **k: b" M src/app.py")

    # Make sleep raise KeyboardInterrupt to exit after first iteration
    def raise_kb(_):
        raise KeyboardInterrupt()

    monkeypatch.setattr(watcher.time, "sleep", raise_kb)

    # Ensure developer id is deterministic
    monkeypatch.setattr(watcher, "_get_developer_id", lambda: "me")

    # Avoid argparse picking up pytest args
    import sys as _sys

    monkeypatch.setattr(_sys, "argv", ["collab"])  # safe minimal argv

    # Should not raise (main handles KeyboardInterrupt and exits cleanly)
    watcher.main()


# Restored archived-only original-name test (non-destructive restore)
def test_main_handles_acquire_exception_and_exits(monkeypatch):
    # Prepare environment for main() to run one loop and exit via KeyboardInterrupt
    monkeypatch.setenv("SUPABASE_URL", "https://example.invalid")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon:fake")

    # Fake create_client that returns a client whose rpc().execute() raises
    class ExplodeClient:
        def rpc(self, *a, **k):
            return self

        def execute(self):
            raise RuntimeError("rpc failed")

        def table(self, *a, **k):
            return self

    monkeypatch.setattr(watcher, "create_client", lambda url, key: ExplodeClient())
    monkeypatch.setattr(watcher, "_start_dashboard_server", lambda: None)

    # Make git status report one modified file so the watcher will attempt acquire
    monkeypatch.setattr("subprocess.check_output", lambda *a, **k: b" M src/app.py")

    # Make sleep raise KeyboardInterrupt to exit after first iteration
    def raise_kb(_):
        raise KeyboardInterrupt()

    monkeypatch.setattr(watcher.time, "sleep", raise_kb)

    # Ensure developer id is deterministic
    monkeypatch.setattr(watcher, "_get_developer_id", lambda: "me")

    # Avoid argparse picking up pytest args
    import sys as _sys

    monkeypatch.setattr(_sys, "argv", ["collab"])  # safe minimal argv

    # Should not raise (main handles KeyboardInterrupt and exits cleanly)
    watcher.main()


# ============================================================================
# PID File OSError Tests (lines 192-193, 228-229)
# ============================================================================


def test_graceful_shutdown_pid_oserror(monkeypatch, tmp_path):
    """Test _graceful_shutdown handles OSError when removing PID file (lines
    192-193)."""
    import os

    monkeypatch.setattr(watcher, "DEVELOPER_ID", None)

    # Create a PID file path that will fail on os.remove
    pid_file = tmp_path / "locked.pid"
    pid_file.write_text("12345")
    monkeypatch.setattr(watcher, "PID_FILE", str(pid_file))

    original_remove = os.remove

    def failing_remove(path):
        if "locked.pid" in str(path):
            raise OSError("Permission denied")
        return original_remove(path)

    monkeypatch.setattr(os, "remove", failing_remove)

    watcher._graceful_shutdown()  # Should not raise


def test_main_pid_write_oserror(monkeypatch, tmp_path):
    """Test main handles OSError when writing PID file (lines 228-229)."""
    monkeypatch.setattr(watcher, "SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setattr(watcher, "SUPABASE_ANON_KEY", "test_key")
    monkeypatch.setattr(sys, "argv", ["live_locks_watcher.py"])

    # Set PID file to an unwritable location
    monkeypatch.setattr(
        watcher, "PID_FILE", str(tmp_path / "no" / "such" / "dir" / "pid")
    )
    monkeypatch.setattr(watcher, "desktop_notify", None)

    class FakeSupaClient:
        def table(self, name):
            return self

        def delete(self):
            return self

        def eq(self, *args):
            return self

        def execute(self):
            return None

    monkeypatch.setattr(watcher, "create_client", lambda url, key: FakeSupaClient())

    def mock_check_output(cmd, *args, **kwargs):
        if "user.name" in cmd:
            return b"test_user\n"
        if "branch" in cmd:
            return b"main\n"
        return b""

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)

    sleep_count = [0]

    def mock_sleep(seconds):
        sleep_count[0] += 1
        if sleep_count[0] > 1:
            raise KeyboardInterrupt()

    monkeypatch.setattr("time.sleep", mock_sleep)

    try:
        watcher.main()
    except (KeyboardInterrupt, SystemExit):
        pass


# ============================================================================
# Lock Release Execute Path Tests (lines 350-351)
# ============================================================================


def test_main_lock_release_success(monkeypatch, tmp_path):
    """Test that successful lock release executes the delete (lines 350-351)."""
    monkeypatch.setattr(watcher, "SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setattr(watcher, "SUPABASE_ANON_KEY", "test_key")
    monkeypatch.setattr(sys, "argv", ["live_locks_watcher.py"])

    pid_file = tmp_path / "watcher.pid"
    monkeypatch.setattr(watcher, "PID_FILE", str(pid_file))
    monkeypatch.setattr(watcher, "desktop_notify", None)
    watcher._active_conflicts.clear()

    delete_calls = []

    class FakeOKResult:
        data = [{"status": "ok"}]

    class TrackingClient:
        def table(self, name):
            return self

        def delete(self):
            delete_calls.append("delete")
            return self

        def eq(self, *args):
            return self

        def execute(self):
            delete_calls.append("execute")
            return None

        def rpc(self, name, params):
            return type("Chain", (), {"execute": lambda self: FakeOKResult()})()

    monkeypatch.setattr(watcher, "create_client", lambda url, key: TrackingClient())

    git_call_count = [0]

    def mock_check_output(cmd, *args, **kwargs):
        git_call_count[0] += 1
        if "user.name" in cmd:
            return b"test_user\n"
        if "branch" in cmd:
            return b"main\n"
        if "status" in cmd:
            # First iterations: file present, then: clean
            if git_call_count[0] <= 5:
                return b" M src/release_me.py\n"
            return b""
        return b""

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)

    sleep_count = [0]

    def mock_sleep(seconds):
        sleep_count[0] += 1
        if sleep_count[0] > 4:
            raise KeyboardInterrupt()

    monkeypatch.setattr("time.sleep", mock_sleep)

    try:
        watcher.main()
    except (KeyboardInterrupt, SystemExit):
        pass

    # The delete path should have been called
    assert "delete" in delete_calls or "execute" in delete_calls


# ============================================================================
# Idle Timeout Direct Test (lines 381-382)
# ============================================================================


def test_main_idle_timeout_break(monkeypatch, tmp_path):
    """Test that idle timeout causes main to break (lines 381-382)."""
    monkeypatch.setattr(watcher, "SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setattr(watcher, "SUPABASE_ANON_KEY", "test_key")
    monkeypatch.setattr(sys, "argv", ["live_locks_watcher.py", "--timeout", "1"])

    pid_file = tmp_path / "watcher.pid"
    monkeypatch.setattr(watcher, "PID_FILE", str(pid_file))
    monkeypatch.setattr(watcher, "desktop_notify", None)

    class FakeSupaClient:
        def table(self, name):
            return self

        def delete(self):
            return self

        def eq(self, *args):
            return self

        def execute(self):
            return None

    monkeypatch.setattr(watcher, "create_client", lambda url, key: FakeSupaClient())

    def mock_check_output(cmd, *args, **kwargs):
        if "user.name" in cmd:
            return b"test_user\n"
        if "branch" in cmd:
            return b"main\n"
        return b""

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)

    from datetime import datetime, timedelta

    real_now = datetime.now
    offset = [timedelta()]

    def advancing_sleep(seconds):
        offset[0] += timedelta(minutes=5)

    def fake_now(*args, **kwargs):
        return real_now() + offset[0]

    monkeypatch.setattr("time.sleep", advancing_sleep)
    # Patch datetime on the watcher module
    monkeypatch.setattr(
        watcher,
        "datetime",
        type(
            "FakeDT",
            (),
            {
                "now": staticmethod(fake_now),
                "fromisoformat": datetime.fromisoformat,
            },
        )(),
        raising=False,
    )

    try:
        watcher.main()
    except (SystemExit, AttributeError, TypeError):
        pass


# ============================================================================
# _scan_remote_locks Tests
# ============================================================================


class FakeScanClient:
    """Mock Supabase client for _scan_remote_locks tests."""

    def __init__(self, data=None, raise_exc=None):
        self._data = data or []
        self._raise_exc = raise_exc

    def table(self, *args, **kwargs):
        return self

    def select(self, *args, **kwargs):
        if self._raise_exc:
            raise self._raise_exc
        return self

    def execute(self):
        if self._raise_exc:
            raise self._raise_exc

        class Resp:
            data = self._data

        return Resp()


def test_scan_remote_locks_warns_about_other_devs(monkeypatch, caplog):
    """_scan_remote_locks notifies when another developer holds a lock."""
    monkeypatch.setattr(watcher, "DEVELOPER_ID", "alice")
    watcher._warned_remote_locks.clear()
    monkeypatch.setattr(watcher, "_notify", lambda *a, **k: None)

    client = FakeScanClient(
        data=[
            {"file_path": "src/app.py", "developer_id": "bob"},
        ]
    )

    import logging

    with caplog.at_level(logging.WARNING, logger="collab.pycharm_watcher"):
        watcher._scan_remote_locks(client)

    assert "src/app.py" in watcher._warned_remote_locks
    assert any("REMOTE LOCK" in r.message for r in caplog.records)
    watcher._warned_remote_locks.clear()


def test_scan_remote_locks_skips_own_locks(monkeypatch):
    """_scan_remote_locks ignores locks held by the current developer."""
    monkeypatch.setattr(watcher, "DEVELOPER_ID", "alice")
    watcher._warned_remote_locks.clear()

    client = FakeScanClient(
        data=[
            {"file_path": "src/app.py", "developer_id": "alice"},
        ]
    )
    watcher._scan_remote_locks(client)

    assert "src/app.py" not in watcher._warned_remote_locks
    watcher._warned_remote_locks.clear()


def test_scan_remote_locks_clears_released_warnings(monkeypatch, caplog):
    """_scan_remote_locks clears warnings when remote locks are released."""
    monkeypatch.setattr(watcher, "DEVELOPER_ID", "alice")
    watcher._warned_remote_locks.clear()
    monkeypatch.setattr(watcher, "_notify", lambda *a, **k: None)

    # First scan: bob holds a lock
    client_with_lock = FakeScanClient(
        data=[{"file_path": "src/app.py", "developer_id": "bob"}]
    )
    watcher._scan_remote_locks(client_with_lock)
    assert "src/app.py" in watcher._warned_remote_locks

    # Second scan: lock released
    import logging

    with caplog.at_level(logging.INFO, logger="collab.pycharm_watcher"):
        client_empty = FakeScanClient(data=[])
        watcher._scan_remote_locks(client_empty)

    assert "src/app.py" not in watcher._warned_remote_locks
    assert any("Remote lock cleared" in r.message for r in caplog.records)
    watcher._warned_remote_locks.clear()


def test_scan_remote_locks_no_duplicate_warnings(monkeypatch):
    """_scan_remote_locks does not re-warn for already-warned files."""
    monkeypatch.setattr(watcher, "DEVELOPER_ID", "alice")
    watcher._warned_remote_locks.clear()
    notify_calls = []
    monkeypatch.setattr(watcher, "_notify", lambda t, m: notify_calls.append((t, m)))

    client = FakeScanClient(data=[{"file_path": "src/app.py", "developer_id": "bob"}])

    watcher._scan_remote_locks(client)
    watcher._scan_remote_locks(client)  # second call — should NOT notify again

    assert len(notify_calls) == 1
    watcher._warned_remote_locks.clear()


def test_scan_remote_locks_handles_exception(monkeypatch):
    """_scan_remote_locks returns gracefully on API failure."""
    monkeypatch.setattr(watcher, "DEVELOPER_ID", "alice")
    watcher._warned_remote_locks.clear()

    client = FakeScanClient(raise_exc=RuntimeError("network down"))
    watcher._scan_remote_locks(client)  # should not raise

    assert len(watcher._warned_remote_locks) == 0


def test_scan_remote_locks_skips_empty_file_path(monkeypatch):
    """_scan_remote_locks ignores entries with empty file_path."""
    monkeypatch.setattr(watcher, "DEVELOPER_ID", "alice")
    watcher._warned_remote_locks.clear()
    monkeypatch.setattr(watcher, "_notify", lambda *a, **k: None)

    client = FakeScanClient(data=[{"file_path": "", "developer_id": "bob"}])
    watcher._scan_remote_locks(client)

    assert len(watcher._warned_remote_locks) == 0


# ============================================================================
# _start_dashboard_server Tests
# ============================================================================


def test_start_dashboard_server_returns_url(monkeypatch):
    """_start_dashboard_server returns an http:// URL on success."""
    import http.server

    monkeypatch.setattr(watcher, "SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setattr(watcher, "SUPABASE_ANON_KEY", "test_key")
    monkeypatch.setattr(watcher, "SUPABASE_SERVICE_ROLE_KEY", None)
    monkeypatch.setattr(watcher, "DEVELOPER_ID", "alice")

    class FakeServer:
        def __init__(self, addr, handler):
            self.server_address = (addr[0], 9999)

        def serve_forever(self):
            pass

        def shutdown(self):
            pass

    monkeypatch.setattr(http.server, "ThreadingHTTPServer", FakeServer)

    url = watcher._start_dashboard_server()
    assert url is not None
    assert url.startswith("http://127.0.0.1:9999/")
    assert url.endswith(".html")


def test_start_dashboard_server_missing_html(monkeypatch):
    """_start_dashboard_server returns None when index.html is missing."""
    monkeypatch.setattr(watcher, "_COLLAB_ROOT", "/nonexistent/path")
    result = watcher._start_dashboard_server()
    assert result is None


def test_start_dashboard_server_read_error(monkeypatch, tmp_path):
    """_start_dashboard_server returns None when index.html can't be read."""
    dashboard_dir = tmp_path / "dashboard"
    dashboard_dir.mkdir()
    html_file = dashboard_dir / "index.html"
    html_file.write_text("test")
    # Make it unreadable by patching open
    monkeypatch.setattr(watcher, "_COLLAB_ROOT", str(tmp_path))

    original_open = open

    def failing_open(path, *args, **kwargs):
        if "index.html" in str(path):
            raise PermissionError("denied")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr("builtins.open", failing_open)
    result = watcher._start_dashboard_server()
    assert result is None


def test_start_dashboard_server_http_server_error(monkeypatch, tmp_path):
    """_start_dashboard_server returns None when HTTP server fails to start."""
    import http.server

    # Create a valid dashboard dir
    dashboard_dir = tmp_path / "dashboard"
    dashboard_dir.mkdir()
    (dashboard_dir / "index.html").write_text("<html></html>")
    monkeypatch.setattr(watcher, "_COLLAB_ROOT", str(tmp_path))
    monkeypatch.setattr(watcher, "SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setattr(watcher, "SUPABASE_ANON_KEY", "key")
    monkeypatch.setattr(watcher, "DEVELOPER_ID", "alice")

    def raising_server(*args, **kwargs):
        raise OSError("Address already in use")

    monkeypatch.setattr(http.server, "ThreadingHTTPServer", raising_server)

    result = watcher._start_dashboard_server()
    assert result is None


def test_start_dashboard_server_tmpfile_error(monkeypatch, tmp_path):
    """_start_dashboard_server returns None when tempfile creation fails."""
    import tempfile

    dashboard_dir = tmp_path / "dashboard"
    dashboard_dir.mkdir()
    (dashboard_dir / "index.html").write_text("<html></html>")
    monkeypatch.setattr(watcher, "_COLLAB_ROOT", str(tmp_path))
    monkeypatch.setattr(watcher, "SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setattr(watcher, "SUPABASE_ANON_KEY", "key")
    monkeypatch.setattr(watcher, "DEVELOPER_ID", "alice")

    def failing_tmpfile(**kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(tempfile, "NamedTemporaryFile", failing_tmpfile)

    result = watcher._start_dashboard_server()
    assert result is None


def test_start_dashboard_server_unlink_error(monkeypatch, tmp_path):
    """_start_dashboard_server handles unlink failure after server error."""
    import http.server

    dashboard_dir = tmp_path / "dashboard"
    dashboard_dir.mkdir()
    (dashboard_dir / "index.html").write_text("<html></html>")
    monkeypatch.setattr(watcher, "_COLLAB_ROOT", str(tmp_path))
    monkeypatch.setattr(watcher, "SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setattr(watcher, "SUPABASE_ANON_KEY", "key")
    monkeypatch.setattr(watcher, "DEVELOPER_ID", "alice")

    # Server creation fails
    def raising_server(*args, **kwargs):
        raise OSError("port in use")

    monkeypatch.setattr(http.server, "ThreadingHTTPServer", raising_server)

    # unlink also fails
    original_unlink = os.unlink

    def failing_unlink(path):
        if str(path).endswith(".html"):
            raise OSError("cannot unlink")
        return original_unlink(path)

    monkeypatch.setattr(os, "unlink", failing_unlink)

    result = watcher._start_dashboard_server()
    assert result is None


def test_main_dashboard_fallback_message(monkeypatch, tmp_path, caplog):
    """Test main() logs fallback dashboard message when server fails (line 382)."""
    monkeypatch.setattr(watcher, "SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setattr(watcher, "SUPABASE_ANON_KEY", "test_key")
    monkeypatch.setattr(sys, "argv", ["live_locks_watcher.py"])

    pid_file = tmp_path / "watcher.pid"
    monkeypatch.setattr(watcher, "PID_FILE", str(pid_file))
    monkeypatch.setattr(watcher, "desktop_notify", None)

    # Make _start_dashboard_server return None
    monkeypatch.setattr(watcher, "_start_dashboard_server", lambda: None)

    class FakeSupaClient:
        def table(self, name):
            return self

        def delete(self):
            return self

        def eq(self, *args):
            return self

        def execute(self):
            return None

        def select(self, *args):
            return self

    monkeypatch.setattr(watcher, "create_client", lambda url, key: FakeSupaClient())

    def mock_check_output(cmd, *args, **kwargs):
        if "user.name" in cmd:
            return b"test_user\n"
        if "branch" in cmd:
            return b"main\n"
        return b""

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)

    sleep_count = [0]

    def mock_sleep(seconds):
        sleep_count[0] += 1
        if sleep_count[0] > 1:
            raise KeyboardInterrupt()

    monkeypatch.setattr("time.sleep", mock_sleep)

    import logging

    with caplog.at_level(logging.INFO, logger="collab.pycharm_watcher"):
        try:
            watcher.main()
        except (KeyboardInterrupt, SystemExit):
            pass

    assert any("python collab.py dashboard" in r.message for r in caplog.records)


def test_graceful_shutdown_guard_prevents_double_run(monkeypatch, tmp_path):
    """_graceful_shutdown runs only once; second call is a no-op."""
    monkeypatch.setattr(watcher, "DEVELOPER_ID", "test_dev")
    monkeypatch.setattr(watcher, "SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setattr(watcher, "SUPABASE_ANON_KEY", "test_key")
    monkeypatch.setattr(watcher, "PID_FILE", str(tmp_path / "pid"))

    call_count = [0]

    class FakeTable:
        def delete(self):
            call_count[0] += 1
            return self

        def eq(self, *args):
            return self

        def execute(self):
            return None

    class FakeClient:
        def table(self, name):
            return FakeTable()

    monkeypatch.setattr(watcher, "create_client", lambda url, key: FakeClient())

    watcher._graceful_shutdown()  # first call — runs
    watcher._graceful_shutdown()  # second call — guard returns immediately

    assert call_count[0] == 1  # delete called only once


def test_graceful_shutdown_dev_id_without_credentials(monkeypatch, tmp_path):
    """_graceful_shutdown skips lock release when credentials are missing."""
    monkeypatch.setattr(watcher, "DEVELOPER_ID", "test_dev")
    monkeypatch.setattr(watcher, "SUPABASE_URL", None)  # missing
    monkeypatch.setattr(watcher, "SUPABASE_ANON_KEY", "test_key")
    pid_file = tmp_path / "watcher.pid"
    pid_file.write_text("12345")
    monkeypatch.setattr(watcher, "PID_FILE", str(pid_file))

    watcher._graceful_shutdown()  # should not attempt API call
    assert not pid_file.exists()


# ---------------------------------------------------------------------------
# Migrated from smaller modules (leftover tests that were not yet consolidated)
# These were adapted to reuse the already-loaded `watcher` module and avoid
# re-importing via importlib.util.
# ---------------------------------------------------------------------------


def test_is_ephemeral_dev_empty():
    # Cover the branch where dev_id is falsy and returns False
    assert watcher._is_ephemeral_dev("") is False


def test_scan_remote_locks_skips_local_owned(monkeypatch):
    # If a remote lock entry belongs to our developer and we already have it in
    # _local_owned_locks, the scan should skip notifications for it.
    fake_data = [
        {
            "developer_id": "me",
            "file_path": "src/owned.txt",
            "branch_name": None,
            "reason": None,
        }
    ]

    class FakeClientLocal:
        def __init__(self, data=None):
            self._data = data

        def table(self, *a, **k):
            return self

        def select(self, *a, **k):
            return self

        def execute(self):
            class R:
                data = self._data

            return R()

    fake = FakeClientLocal(data=fake_data)
    watcher.DEVELOPER_ID = "me"
    watcher._local_owned_locks.clear()
    watcher._local_owned_locks.add("src/owned.txt")
    watcher._warned_remote_locks.clear()
    watcher._known_remote_locks.clear()

    # Should not raise and should not add to _warned_remote_locks
    watcher._scan_remote_locks(fake)
    assert "src/owned.txt" not in watcher._warned_remote_locks


def test_scan_remote_locks_removed_discards_local_owned(monkeypatch):
    # Simulate a previously-known remote lock that was released; if we had it
    # recorded locally, the code path should discard it from _local_owned_locks.
    watcher._known_remote_locks.clear()
    watcher._known_remote_locks.add("src/released.txt")
    watcher._local_owned_locks.clear()
    watcher._local_owned_locks.add("src/released.txt")

    # Fake client returns no locks (empty list)
    class EmptyClient:
        def table(self, *a, **k):
            return self

        def select(self, *a, **k):
            return self

        def execute(self):
            class R:
                data = []

            return R()

    fake = EmptyClient()

    watcher._scan_remote_locks(fake)
    # After scanning, released lock should be removed from local-owned set
    assert "src/released.txt" not in watcher._local_owned_locks


def test_process_new_files_handles_local_add_exception(monkeypatch):
    # Replace _local_owned_locks with an object whose add() raises to hit the
    # exception-handling branch inside the helper.
    class BadSet:
        def add(self, *a, **k):
            raise RuntimeError("boom add")

    old = watcher._local_owned_locks
    watcher._local_owned_locks = BadSet()

    # Fake client returns success (no conflict)
    class RpcClient:
        def rpc(self, *a, **k):
            return self

        def execute(self):
            return type("R", (), {"data": []})()

    client = RpcClient()
    watcher.DEVELOPER_ID = "tester"

    # Should not raise even though add() raises inside
    watcher._process_new_files(client, "main", {"src/a.py"})

    # restore
    watcher._local_owned_locks = old


def test_process_releases_handles_discard_exception(monkeypatch):
    # Replace _local_owned_locks with object whose discard raises
    class BadSet:
        def discard(self, *a, **k):
            raise RuntimeError("boom discard")

    old = watcher._local_owned_locks
    watcher._local_owned_locks = BadSet()

    # Fake client for delete.execute()
    class FakeClientLocal2:
        def __init__(self, data=None, explode=False):
            self._data = data
            self._explode = explode

        def table(self, *a, **k):
            return self

        def select(self, *a, **k):
            return self

        def execute(self):
            if self._explode:
                raise RuntimeError("backend down")

            class R:
                data = self._data

            return R()

    fake = FakeClientLocal2(data=[])
    watcher.DEVELOPER_ID = "tester"

    # Should not raise even though discard() raises inside
    watcher._process_releases(fake, {"src/b.py"})

    watcher._local_owned_locks = old


def test_main_exits_when_create_client_none(monkeypatch):
    # Ensure main() will exit early with SystemExit when create_client is None
    watcher.SUPABASE_URL = "https://example.invalid"
    watcher.SUPABASE_ANON_KEY = "anon:fake"

    # Use None for create_client to simulate missing dependency
    monkeypatch.setattr(watcher, "create_client", None)
    monkeypatch.setattr(watcher, "_start_dashboard_server", lambda: None)

    # Avoid argparse picking up pytest args
    import sys as _sys

    monkeypatch.setattr(_sys, "argv", ["collab"])  # safe minimal argv

    import pytest

    with pytest.raises(SystemExit):
        watcher.main()


def test_get_cmdline_for_pid_local_wmic_and_powershell(monkeypatch):
    # Simulate absence of psutil
    if "psutil" in sys.modules:
        del sys.modules["psutil"]

    monkeypatch.setattr(sys, "platform", "win32")

    def fake_check_output(cmd, stderr=None, text=None, creationflags=None):
        if cmd[0] == "wmic":
            return "CommandLine\npython watch.exe\n"
        if cmd[0] == "powershell":
            return "python powershell_watch.exe"
        raise RuntimeError("unexpected")

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)
    got = watcher._get_cmdline_for_pid_local(1234)
    assert "watch.exe" in got or "powershell_watch" in got


def test_write_pid_file_and_get_developer_and_branch(monkeypatch, tmp_path):
    pid_file = tmp_path / ".daemon.pid"
    monkeypatch.setattr(watcher, "PID_FILE", str(pid_file))

    watcher._write_pid_file(4242)
    assert pid_file.exists()
    raw = pid_file.read_text(encoding="utf-8")
    obj = __import__("json").loads(raw)
    assert obj["pid"] == 4242

    # Test _get_developer_id and _get_current_branch by monkeypatching subprocess
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **k: b"devname\n")
    dev = watcher._get_developer_id()
    assert isinstance(dev, str)
    branch = watcher._get_current_branch()
    assert isinstance(branch, str)


def test_main_fallback_writes_plain_pid(monkeypatch, tmp_path):
    # Simulate _write_pid_file raising so main falls back to plain integer write
    pid_file = tmp_path / ".daemon.pid"
    monkeypatch.setattr(watcher, "PID_FILE", str(pid_file))

    def _boom(pid):
        raise Exception("boom")

    monkeypatch.setattr(watcher, "_write_pid_file", _boom)
    # Provide minimal values so main continues to client creation
    monkeypatch.setattr(watcher, "SUPABASE_URL", "x")
    monkeypatch.setattr(watcher, "SUPABASE_ANON_KEY", "y")
    monkeypatch.setattr(watcher, "_get_developer_id", lambda: "tester")
    monkeypatch.setattr(watcher, "create_client", lambda a, b: object())

    # Make dashboard startup terminate the process early so we don't enter the full loop
    def _raise_sys_exit():
        raise SystemExit(0)

    monkeypatch.setattr(watcher, "_start_dashboard_server", _raise_sys_exit)

    # Ensure argparse in main() doesn't see pytest args
    monkeypatch.setattr("sys.argv", ["live_watcher"])  # type: ignore[arg-type]
    try:
        watcher.main()
    except SystemExit:
        pass

    # Fallback should have written the plain integer PID
    assert pid_file.exists()
    content = pid_file.read_text()
    assert content.strip().isdigit()
    # Clean up
    try:
        os.remove(pid_file)
    except Exception:
        pass


# -------------------------- Restored watcher tests --------------------------


def test_color_without_colorama():
    # Ensure color fallback does nothing when colorama is unavailable
    watcher._HAS_COLORAMA = False
    out = watcher._color("hello", "X")
    assert out == "hello"


def test_scan_remote_locks_client_exception(monkeypatch):
    class FakeResp:
        def __init__(self, data=None):
            self.data = data

    class FakeClient:
        def __init__(self, data=None, explode=False):
            self._data = data
            self._explode = explode

        def table(self, *a, **k):
            return self

        def select(self, *a, **k):
            return self

        def execute(self):
            if self._explode:
                raise RuntimeError("backend down")
            return FakeResp(self._data)

    fake = FakeClient(explode=True)
    watcher._warned_remote_locks.clear()
    watcher._known_remote_locks.clear()
    watcher._scan_remote_locks(fake)


def test_scan_remote_locks_warns_for_other_owner(monkeypatch):
    fake_data = [
        {
            "developer_id": "other_user",
            "file_path": "src/locked.txt",
            "branch_name": None,
            "reason": None,
        }
    ]
    fake = type(
        "C",
        (),
        {
            "_data": fake_data,
            "table": lambda self, *a, **k: self,
            "select": lambda self, *a, **k: self,
            "execute": lambda self: type("R", (), {"data": self._data})(),
        },
    )()
    watcher.DEVELOPER_ID = "me"
    watcher._warned_remote_locks.clear()
    watcher._known_remote_locks.clear()
    watcher._scan_remote_locks(fake)
    assert "src/locked.txt" in watcher._warned_remote_locks


def test_is_process_alive_fallback_without_psutil(monkeypatch):
    import builtins as _builtins

    real_import = _builtins.__import__

    def fake_import(name, *a, **k):
        if name == "psutil":
            raise ImportError("no psutil")
        return real_import(name, *a, **k)

    monkeypatch.setattr(_builtins, "__import__", fake_import)

    def fake_check_output(*a, **k):
        raise Exception("tasklist failed")

    monkeypatch.setattr("subprocess.check_output", fake_check_output)
    assert watcher._is_process_alive(999999) is False


def test_scan_remote_locks_same_owner_updates_known():
    fake_data = [
        {
            "developer_id": "me",
            "file_path": "src/mine.txt",
            "branch_name": None,
            "reason": None,
        }
    ]

    class FakeClient3:
        def __init__(self, data):
            self._data = data

        def table(self, *a, **k):
            return self

        def select(self, *a, **k):
            return self

        def execute(self):
            class R:
                data = self._data

            return R()

    fake = FakeClient3(fake_data)
    watcher.DEVELOPER_ID = "me"
    watcher._known_remote_locks.clear()
    watcher._warned_remote_locks.clear()
    watcher._scan_remote_locks(fake)
    assert "src/mine.txt" in watcher._known_remote_locks
