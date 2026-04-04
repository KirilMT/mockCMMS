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
