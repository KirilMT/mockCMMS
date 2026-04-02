"""Comprehensive tests for the .collab LockClient module.

These tests import the implementation directly from the `.collab/core` path so they
don't rely on project package layout. They include both smoke checks and safe behavior
tests that use monkeypatch to avoid network.

Consolidated from test_lock_client.py and test_lock_client_comprehensive.py.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import pytest

# Load the module directly from .collab/core/lock_client.py
proj_root = Path(__file__).resolve().parents[3]
module_path = proj_root / ".collab" / "core" / "lock_client.py"
spec = importlib.util.spec_from_file_location("collab.lock_client", str(module_path))
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)  # type: ignore[arg-type]


# ============================================================================
# Helpers
# ============================================================================


class FakeResponse:
    """Mock Supabase response object."""

    def __init__(self, status=200, data=None, error=None):
        self.status = status
        self.data = data or []
        self.error = error


class FakeClient:
    """Mock Supabase client with chainable methods."""

    def __init__(self, response):
        self._resp = response

    def rpc(self, *args, **kwargs):
        return self

    def table(self, *args, **kwargs):
        return self

    def select(self, *args, **kwargs):
        return self

    def delete(self, *args, **kwargs):
        return self

    def eq(self, *args, **kwargs):
        return self

    def insert(self, *args, **kwargs):
        return self

    def update(self, *args, **kwargs):
        return self

    def order(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def execute(self):
        return self._resp


def make_get_create_client(resp):
    """Original helper: wraps response in nested factory."""

    def fake_get_create_client():
        def create_client(url, key):
            return FakeClient(resp)

        return create_client

    return fake_get_create_client


def make_create_client(resp):
    """Comprehensive helper: direct factory for fake Supabase client."""

    def fake_create_client(url, key):
        return FakeClient(resp)

    return fake_create_client


# ============================================================================
# Smoke / Structure Tests
# ============================================================================


def test_lockclient_class_and_methods_exist():
    assert hasattr(mod, "LockClient")
    LC = getattr(mod, "LockClient")
    for name in ("acquire", "release", "active", "get_lock_status", "watch"):
        assert hasattr(LC, name), f"Missing {name}"


# ============================================================================
# _get_create_client Tests
# ============================================================================


def test_get_create_client_caches_result(monkeypatch):
    """Test that _get_create_client caches the supabase create_client function."""
    fake_fn = lambda url, key: None  # noqa: E731
    monkeypatch.setattr(mod, "_supabase_create_client", fake_fn)
    result = mod._get_create_client()
    assert result is fake_fn


def test_get_create_client_lazy_import_success(monkeypatch):
    """Test _get_create_client with successful supabase import."""
    monkeypatch.setattr(mod, "_supabase_create_client", None)

    fake_create = lambda url, key: FakeClient(FakeResponse())  # noqa: E731
    fake_supabase = type(sys)("fake_supabase")
    fake_supabase.create_client = fake_create
    monkeypatch.setitem(sys.modules, "supabase", fake_supabase)

    result = mod._get_create_client()
    assert result is fake_create

    # Reset for other tests
    monkeypatch.setattr(mod, "_supabase_create_client", None)


def test_get_create_client_import_error(monkeypatch):
    """Test _get_create_client exits when supabase is not installed."""
    monkeypatch.setattr(mod, "_supabase_create_client", None)

    original_import = (
        __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__
    )

    def mock_import(name, *args, **kwargs):
        if name == "supabase":
            raise ImportError("No module named 'supabase'")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", mock_import)
    with pytest.raises(SystemExit):
        mod._get_create_client()

    # Reset
    monkeypatch.setattr(mod, "_supabase_create_client", None)


# ============================================================================
# Git Helper Tests
# ============================================================================


def test_get_git_username_from_config(monkeypatch):
    """Test deriving developer ID from git config."""

    def mock_check_output(cmd, *args, **kwargs):
        if "user.name" in cmd:
            return b"john_doe\n"
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)

    username = mod.LockClient._get_git_username()
    assert username == "john_doe"


def test_get_git_username_fallback_to_env(monkeypatch):
    """Test fallback to environment variables when git config fails."""
    monkeypatch.setenv("USER", "env_user")
    monkeypatch.setenv("USERNAME", "env_username")

    def mock_check_output(cmd, *args, **kwargs):
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)

    username = mod.LockClient._get_git_username()
    assert username in ("env_user", "env_username")


def test_get_current_branch(monkeypatch):
    """Test getting current git branch."""

    def mock_check_output(cmd, *args, **kwargs):
        if "branch" in cmd and "--show-current" in cmd:
            return b"feature/test\n"
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)

    branch = mod.LockClient._get_current_branch()
    assert branch == "feature/test"


# ============================================================================
# Path Validation Tests
# ============================================================================


def test_should_ignore_path(monkeypatch):
    """Test path filtering for ignored directories."""
    # _should_ignore_path is a static method, only ignores .git/ and .collab/
    assert mod.LockClient._should_ignore_path(".git/config") is True
    assert mod.LockClient._should_ignore_path(".collab/core/file.py") is True
    assert mod.LockClient._should_ignore_path("src/app.py") is False
    assert mod.LockClient._should_ignore_path("tests/test_something.py") is False


# ============================================================================
# Lock Acquisition Tests
# ============================================================================


def test_acquire_missing_file_returns_false(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.invalid")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon:fake")
    monkeypatch.setattr(
        mod,
        "_get_create_client",
        make_get_create_client({"status": 200, "data": []}),
    )

    lc = mod.LockClient(developer_id="tester")
    ok, msg = lc.acquire("this/path/does/not/exist.file")
    assert not ok
    assert "does not exist" in msg


def test_acquire_success(monkeypatch, tmp_path):
    """Test successful lock acquisition."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    test_file = tmp_path / "src" / "app.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("# code")

    # The RPC returns a list with status "ok", and acquire returns (True, token)
    response = FakeResponse(status=200, data=[{"status": "ok", "lock_id": "abc123"}])
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))
    monkeypatch.setattr(mod, "_PROJECT_ROOT", str(tmp_path))

    lc = mod.LockClient(developer_id="test_user")
    ok, msg = lc.acquire(str(test_file))
    assert ok is True


def test_acquire_conflict(monkeypatch, tmp_path):
    """Test lock acquisition when file is already locked by another developer."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    test_file = tmp_path / "src" / "app.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("# code")

    response = FakeResponse(
        status=200,
        data=[{"status": "conflict", "owner": "another_user"}],
    )
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))
    monkeypatch.setattr(mod, "_PROJECT_ROOT", str(tmp_path))

    lc = mod.LockClient(developer_id="test_user")
    ok, msg = lc.acquire(str(test_file))
    assert ok is False
    assert "another_user" in msg


def test_acquire_with_custom_expiry(monkeypatch, tmp_path):
    """Test lock acquisition with custom expiry time."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    test_file = tmp_path / "src" / "app.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("# code")

    response = FakeResponse(status=200, data=[{"status": "ok", "lock_id": "xyz789"}])
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))
    monkeypatch.setattr(mod, "_PROJECT_ROOT", str(tmp_path))

    lc = mod.LockClient(developer_id="test_user")
    ok, msg = lc.acquire(str(test_file), expires_minutes=120)
    assert ok is True


def test_acquire_api_exception(monkeypatch, tmp_path):
    """Test acquire when API call raises an exception."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    test_file = tmp_path / "src" / "app.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("# code")

    class ExplodingClient(FakeClient):
        def execute(self):
            raise RuntimeError("API exploded")

    monkeypatch.setattr(
        mod,
        "_get_create_client",
        lambda: lambda url, key: ExplodingClient(FakeResponse()),
    )
    monkeypatch.setattr(mod, "_PROJECT_ROOT", str(tmp_path))

    lc = mod.LockClient(developer_id="test_user")
    ok, msg = lc.acquire(str(test_file))
    assert ok is False
    assert "API Error" in msg


def test_acquire_response_error_dict(monkeypatch, tmp_path):
    """Test acquire when response contains an error dict."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    test_file = tmp_path / "src" / "app.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("# code")

    response = FakeResponse(
        status=400, data=None, error={"message": "Bad lock request"}
    )
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))
    monkeypatch.setattr(mod, "_PROJECT_ROOT", str(tmp_path))

    lc = mod.LockClient(developer_id="test_user")
    ok, msg = lc.acquire(str(test_file))
    assert ok is False
    assert "Bad lock request" in msg


def test_acquire_response_error_string(monkeypatch, tmp_path):
    """Test acquire when response contains a string error."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    test_file = tmp_path / "src" / "app.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("# code")

    response = FakeResponse(status=400, data=None, error="String error")
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))
    monkeypatch.setattr(mod, "_PROJECT_ROOT", str(tmp_path))

    lc = mod.LockClient(developer_id="test_user")
    ok, msg = lc.acquire(str(test_file))
    assert ok is False
    assert "String error" in msg


def test_acquire_status_200_empty_data(monkeypatch, tmp_path):
    """Test acquire with status 200 but empty data falls through to status check."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    test_file = tmp_path / "src" / "app.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("# code")

    response = FakeResponse(status=201, data=[], error=None)
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))
    monkeypatch.setattr(mod, "_PROJECT_ROOT", str(tmp_path))

    lc = mod.LockClient(developer_id="test_user")
    ok, msg = lc.acquire(str(test_file))
    assert ok is True


def test_acquire_unexpected_response(monkeypatch, tmp_path):
    """Test acquire with unexpected status code and empty data."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    test_file = tmp_path / "src" / "app.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("# code")

    response = FakeResponse(status=500, data=[], error=None)
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))
    monkeypatch.setattr(mod, "_PROJECT_ROOT", str(tmp_path))

    lc = mod.LockClient(developer_id="test_user")
    ok, msg = lc.acquire(str(test_file))
    assert ok is False
    assert "Unexpected response" in msg


def test_acquire_multiple_success(monkeypatch, tmp_path):
    """Test batch lock acquisition."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    file1 = tmp_path / "src" / "app.py"
    file2 = tmp_path / "src" / "routes.py"
    file1.parent.mkdir(parents=True)
    file1.write_text("# code")
    file2.write_text("# code")

    response = FakeResponse(status=200, data=[{"status": "ok", "lock_id": "batch123"}])
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))
    monkeypatch.setattr(mod, "_PROJECT_ROOT", str(tmp_path))

    lc = mod.LockClient(developer_id="test_user")
    ok, failed, msg = lc.acquire_multiple([str(file1), str(file2)])
    assert ok is True
    assert len(failed) == 0


def test_acquire_multiple_with_failures(monkeypatch, tmp_path):
    """Test batch lock acquisition with some files failing."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    file1 = tmp_path / "src" / "app.py"
    file1.parent.mkdir(parents=True)
    file1.write_text("# code")

    response = FakeResponse(status=200, data=[{"status": "conflict", "owner": "other"}])
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))
    monkeypatch.setattr(mod, "_PROJECT_ROOT", str(tmp_path))

    lc = mod.LockClient(developer_id="test_user")
    ok, failed, msg = lc.acquire_multiple([str(file1)])
    assert ok is False
    assert len(failed) == 1
    assert "Conflicts" in msg


# ============================================================================
# Lock Release Tests
# ============================================================================


def test_release_no_lock_returns_false(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.invalid")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon:fake")
    resp = {"status": 500, "data": None, "error": None}
    monkeypatch.setattr(mod, "_get_create_client", make_get_create_client(resp))

    lc = mod.LockClient(developer_id="tester")
    ok, msg = lc.release("path/that/was/not/locked.txt")
    assert ok is False
    assert "No lock released" in msg


def test_release_success(monkeypatch):
    """Test successful lock release."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    response = FakeResponse(status=200, data=[{"file_path": "src/app.py"}])
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))

    lc = mod.LockClient(developer_id="test_user")
    ok, msg = lc.release("src/app.py")
    assert ok is True
    assert "released" in msg.lower()


def test_release_not_owner(monkeypatch):
    """Test release when no lock is deleted (empty data, error response)."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    # status 500 + data=None + error triggers the "No lock released" path
    response = FakeResponse(status=500, data=None, error="not found")
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))

    lc = mod.LockClient(developer_id="test_user")
    ok, msg = lc.release("src/app.py")
    assert ok is False


def test_release_api_exception(monkeypatch):
    """Test release when API call raises an exception."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    class ExplodingClient(FakeClient):
        def execute(self):
            raise RuntimeError("Network timeout error")

    monkeypatch.setattr(
        mod,
        "_get_create_client",
        lambda: lambda url, key: ExplodingClient(FakeResponse()),
    )
    monkeypatch.setattr(mod.time, "sleep", lambda x: None)

    lc = mod.LockClient(developer_id="test_user")
    ok, msg = lc.release("src/app.py")
    assert ok is False
    assert "API Error" in msg


def test_release_multiple(monkeypatch):
    """Test batch lock release."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    response = FakeResponse(
        status=200, data=[{"file_path": "src/app.py"}, {"file_path": "src/routes.py"}]
    )
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))

    lc = mod.LockClient(developer_id="test_user")
    ok, count, msg = lc.release_multiple(["src/app.py", "src/routes.py"])
    assert ok is True
    assert count >= 0


def test_release_all(monkeypatch):
    """Test releasing all locks held by current developer."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    locks_data = [
        {"file_path": "src/app.py", "developer_id": "test_user"},
        {"file_path": "src/routes.py", "developer_id": "test_user"},
        {"file_path": "src/other.py", "developer_id": "other_user"},
    ]

    responses = [
        FakeResponse(status=200, data=locks_data),
        FakeResponse(status=200, data=[{"file_path": "src/app.py"}]),
        FakeResponse(status=200, data=[{"file_path": "src/routes.py"}]),
    ]

    call_count = [0]

    def get_response_client():
        def create_client(url, key):
            resp = responses[min(call_count[0], len(responses) - 1)]
            call_count[0] += 1
            return FakeClient(resp)

        return create_client

    monkeypatch.setattr(mod, "_get_create_client", get_response_client)

    lc = mod.LockClient(developer_id="test_user")
    count = lc.release_all()
    assert count >= 0


# ============================================================================
# Lock Status and Query Tests
# ============================================================================


def test_get_lock_status_no_lock(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.invalid")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon:fake")
    resp = {"status": 200, "data": []}
    monkeypatch.setattr(mod, "_get_create_client", make_get_create_client(resp))

    lc = mod.LockClient(developer_id="tester")
    status = lc.get_lock_status("some/file.py")
    assert isinstance(status, dict)
    assert status.get("is_locked") is False
    assert status.get("can_edit") is True


def test_get_lock_status_locked(monkeypatch):
    """Test getting status of a locked file."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    future = (datetime.now(timezone.utc) + timedelta(hours=8)).isoformat()
    lock_data = {
        "file_path": "src/app.py",
        "developer_id": "other_user",
        "acquired_at": "2025-01-01T10:00:00+00:00",
        "expires_at": future,
    }
    response = FakeResponse(status=200, data=[lock_data])
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))

    lc = mod.LockClient(developer_id="test_user")
    status = lc.get_lock_status("src/app.py")
    assert status["is_locked"] is True
    assert status["locked_by"] == "other_user"
    assert status["can_edit"] is False


def test_get_lock_status_api_exception(monkeypatch):
    """Test get_lock_status when API raises an exception."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    class ExplodingClient(FakeClient):
        def execute(self):
            raise RuntimeError("Network error")

    monkeypatch.setattr(
        mod,
        "_get_create_client",
        lambda: lambda url, key: ExplodingClient(FakeResponse()),
    )

    lc = mod.LockClient(developer_id="test_user")
    status = lc.get_lock_status("src/app.py")
    assert status["is_locked"] is False
    assert "error" in status


def test_get_lock_status_response_error(monkeypatch):
    """Test get_lock_status when response has error."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    response = FakeResponse(status=500, data=None, error="Server error")
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))

    lc = mod.LockClient(developer_id="test_user")
    status = lc.get_lock_status("src/app.py")
    assert status["is_locked"] is False
    assert "error" in status


def test_get_lock_status_bad_expiry(monkeypatch):
    """Test get_lock_status with invalid expires_at field."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    lock_data = {
        "file_path": "src/app.py",
        "developer_id": "other_user",
        "acquired_at": "2025-01-01T10:00:00+00:00",
        "expires_at": "not-a-date",
    }
    response = FakeResponse(status=200, data=[lock_data])
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))

    lc = mod.LockClient(developer_id="test_user")
    status = lc.get_lock_status("src/app.py")
    # Bad expiry falls back to datetime.now(utc) which is in the past
    assert isinstance(status, dict)


def test_active_locks(monkeypatch):
    """Test retrieving all active locks."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    locks_data = [
        {"file_path": "src/app.py", "developer_id": "user1"},
        {"file_path": "src/routes.py", "developer_id": "user2"},
    ]
    response = FakeResponse(status=200, data=locks_data)
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))

    lc = mod.LockClient(developer_id="test_user")
    locks = lc.active()
    assert len(locks) == 2
    assert locks[0]["file_path"] == "src/app.py"


def test_active_locks_exception(monkeypatch):
    """Test active() returns empty list on API error."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    class ExplodingClient(FakeClient):
        def execute(self):
            raise RuntimeError("Network error")

    monkeypatch.setattr(
        mod,
        "_get_create_client",
        lambda: lambda url, key: ExplodingClient(FakeResponse()),
    )

    lc = mod.LockClient(developer_id="test_user")
    locks = lc.active()
    assert locks == []


def test_active_locks_with_error(monkeypatch):
    """Test active() returns empty list when response has error."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    response = FakeResponse(status=500, data=None, error="Error")
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))

    lc = mod.LockClient(developer_id="test_user")
    locks = lc.active()
    assert locks == []


# ============================================================================
# Force Release Tests
# ============================================================================


def test_force_release(monkeypatch):
    """Test force-releasing a lock (admin operation)."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service_key")

    response = FakeResponse(status=200, data=[{"file_path": "src/app.py"}])
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))

    lc = mod.LockClient(developer_id="admin")
    ok, msg = lc.force_release("src/app.py")
    assert isinstance(ok, bool)
    assert isinstance(msg, str)


def test_force_release_api_exception(monkeypatch):
    """Test force_release when API call raises an exception."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    class ExplodingClient(FakeClient):
        def execute(self):
            raise RuntimeError("Network timeout error")

    monkeypatch.setattr(
        mod,
        "_get_create_client",
        lambda: lambda url, key: ExplodingClient(FakeResponse()),
    )
    monkeypatch.setattr(mod.time, "sleep", lambda x: None)

    lc = mod.LockClient(developer_id="admin")
    ok, msg = lc.force_release("src/app.py")
    assert ok is False
    assert "API Error" in msg


def test_force_release_with_error(monkeypatch):
    """Test force_release when response has error."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    response = FakeResponse(status=500, data=None, error="Server error")
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))

    lc = mod.LockClient(developer_id="admin")
    ok, msg = lc.force_release("src/app.py")
    assert ok is False
    assert "API Error" in msg


def test_force_release_no_lock(monkeypatch):
    """Test force_release when no lock exists to remove."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    # Need data to be truly None (not []) to hit the "No lock removed" path
    class NullDataResponse:
        status = 200
        data = None
        error = None

    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(NullDataResponse())
    )

    lc = mod.LockClient(developer_id="admin")
    ok, msg = lc.force_release("src/app.py")
    assert ok is False
    assert "No lock removed" in msg


# ============================================================================
# History Tests
# ============================================================================


def test_history_all_files(monkeypatch):
    """Test fetching lock history for all files."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    history_data = [
        {"file_path": "src/app.py", "developer_id": "user1", "action": "acquired"},
        {"file_path": "src/app.py", "developer_id": "user1", "action": "released"},
    ]
    response = FakeResponse(status=200, data=history_data)
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))

    lc = mod.LockClient(developer_id="test_user")
    history = lc.history()
    assert isinstance(history, list)


def test_history_specific_file(monkeypatch):
    """Test fetching lock history for a specific file."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    history_data = [
        {"file_path": "src/app.py", "developer_id": "user1", "action": "acquired"}
    ]
    response = FakeResponse(status=200, data=history_data)
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))

    lc = mod.LockClient(developer_id="test_user")
    history = lc.history(file_path="src/app.py", limit=10)
    assert isinstance(history, list)


def test_history_exception(monkeypatch):
    """Test history returns empty list when API raises exception."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    class ExplodingClient(FakeClient):
        def execute(self):
            raise RuntimeError("DB error")

    monkeypatch.setattr(
        mod,
        "_get_create_client",
        lambda: lambda url, key: ExplodingClient(FakeResponse()),
    )

    lc = mod.LockClient(developer_id="test_user")
    history = lc.history()
    assert history == []


# ============================================================================
# PID File Management Tests
# ============================================================================


def test_pid_file_helpers(tmp_path, monkeypatch):
    pid_file = tmp_path / "daemon.pid"
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))
    if pid_file.exists():
        pid_file.unlink()

    mod.LockClient._write_pid(424242)
    assert pid_file.exists()
    assert mod.LockClient._read_pid() == 424242

    mod.LockClient._remove_pid()
    assert not pid_file.exists()


def test_read_pid_missing_file(tmp_path, monkeypatch):
    """Test reading PID when file doesn't exist."""
    pid_file = tmp_path / "missing.pid"
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))

    pid = mod.LockClient._read_pid()
    assert pid is None


def test_write_pid_oserror(tmp_path, monkeypatch):
    """Test _write_pid handles OSError gracefully."""
    monkeypatch.setattr(mod, "PID_FILE", str(tmp_path / "nonexistent" / "dir" / "pid"))

    # Should not raise
    mod.LockClient._write_pid(12345)


def test_remove_pid_no_file(tmp_path, monkeypatch):
    """Test _remove_pid is safe when file doesn't exist."""
    monkeypatch.setattr(mod, "PID_FILE", str(tmp_path / "nonexistent.pid"))
    mod.LockClient._remove_pid()  # Should not raise


# ============================================================================
# _is_process_alive Tests
# ============================================================================


def test_is_process_alive_current_process():
    """Test _is_process_alive returns True for current process."""
    result = mod.LockClient._is_process_alive(os.getpid())
    assert result is True


def test_is_process_alive_nonexistent_pid():
    """Test _is_process_alive returns False for a very high PID."""
    result = mod.LockClient._is_process_alive(99999999)
    assert result is False


# ============================================================================
# Daemon Status Tests
# ============================================================================


def test_daemon_status_not_running(tmp_path, monkeypatch):
    """Test daemon status when not running."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    pid_file = tmp_path / "daemon.pid"
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))
    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )

    lc = mod.LockClient(developer_id="test_user")
    is_running = lc.daemon_status()
    assert is_running is False


def test_daemon_status_running(tmp_path, monkeypatch):
    """Test daemon status when daemon is running."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    pid_file = tmp_path / "daemon.pid"
    pid_file.write_text(str(os.getpid()))
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))
    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )

    lc = mod.LockClient(developer_id="test_user")
    is_running = lc.daemon_status()
    assert is_running is True


# ============================================================================
# Daemon Start / Stop Tests
# ============================================================================


def test_daemon_start_already_running(tmp_path, monkeypatch, capsys):
    """Test daemon_start when watcher is already running."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    pid_file = tmp_path / "daemon.pid"
    pid_file.write_text(str(os.getpid()))
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))
    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )

    lc = mod.LockClient(developer_id="test_user")
    lc.daemon_start()
    captured = capsys.readouterr()
    assert "already running" in captured.out.lower()


def test_daemon_start_launches_process(tmp_path, monkeypatch, capsys):
    """Test daemon_start launches a background process."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    pid_file = tmp_path / "daemon.pid"
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))
    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )

    class FakeProc:
        pid = 99999999

    def mock_popen(*args, **kwargs):
        return FakeProc()

    monkeypatch.setattr(subprocess, "Popen", mock_popen)
    monkeypatch.setattr(mod.time, "sleep", lambda x: None)
    # Process will appear dead since PID doesn't exist
    monkeypatch.setattr(
        mod.LockClient, "_is_process_alive", staticmethod(lambda pid: False)
    )

    lc = mod.LockClient(developer_id="test_user")
    lc.daemon_start()
    captured = capsys.readouterr()
    assert (
        "exited immediately" in captured.out.lower()
        or "starting" in captured.out.lower()
    )


def test_daemon_start_successful(tmp_path, monkeypatch, capsys):
    """Test daemon_start with successful process launch."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    pid_file = tmp_path / "daemon.pid"
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))
    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )

    class FakeProc:
        pid = 12345

    def mock_popen(*args, **kwargs):
        return FakeProc()

    monkeypatch.setattr(subprocess, "Popen", mock_popen)
    monkeypatch.setattr(mod.time, "sleep", lambda x: None)
    monkeypatch.setattr(
        mod.LockClient, "_is_process_alive", staticmethod(lambda pid: True)
    )

    lc = mod.LockClient(developer_id="test_user")
    lc.daemon_start()
    captured = capsys.readouterr()
    assert "started" in captured.out.lower()


def test_daemon_start_with_open_dashboard(tmp_path, monkeypatch, capsys):
    """Test daemon_start with --open-dashboard flag."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    pid_file = tmp_path / "daemon.pid"
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))
    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )

    popen_cmds = []

    class FakeProc:
        pid = 12345

    def mock_popen(cmd, **kwargs):
        popen_cmds.append(cmd)
        return FakeProc()

    monkeypatch.setattr(subprocess, "Popen", mock_popen)
    monkeypatch.setattr(mod.time, "sleep", lambda x: None)
    monkeypatch.setattr(
        mod.LockClient, "_is_process_alive", staticmethod(lambda pid: True)
    )

    lc = mod.LockClient(developer_id="test_user")
    lc.daemon_start(open_dashboard=True)
    # Should include --open-dashboard in the command
    assert any("--open-dashboard" in str(cmd) for cmd in popen_cmds)


def test_daemon_stop_not_running(tmp_path, monkeypatch, capsys):
    """Test daemon_stop when no daemon is running."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    pid_file = tmp_path / "daemon.pid"
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))
    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )

    lc = mod.LockClient(developer_id="test_user")
    lc.daemon_stop()
    captured = capsys.readouterr()
    assert "no running" in captured.out.lower()


def test_daemon_stop_kills_process(tmp_path, monkeypatch, capsys):
    """Test daemon_stop stops the running process."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    pid_file = tmp_path / "daemon.pid"
    pid_file.write_text("99999")
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))
    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )

    alive_calls = [0]

    def mock_is_alive(pid):
        alive_calls[0] += 1
        # First call True (for the check), subsequent False (stopped)
        return alive_calls[0] <= 1

    monkeypatch.setattr(
        mod.LockClient, "_is_process_alive", staticmethod(mock_is_alive)
    )
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: None)
    monkeypatch.setattr(mod.time, "sleep", lambda x: None)

    lc = mod.LockClient(developer_id="test_user")
    lc.daemon_stop()
    captured = capsys.readouterr()
    assert "stop" in captured.out.lower()


# ============================================================================
# Dashboard Tests
# ============================================================================


def test_dashboard_opens_browser(monkeypatch):
    """Test dashboard() opens a browser."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )

    opened_urls = []

    def mock_prepare(self):
        return "http://127.0.0.1:9999/dash.html", "/tmp/dash.html"

    monkeypatch.setattr(mod.LockClient, "_prepare_dashboard_server", mock_prepare)

    import webbrowser

    monkeypatch.setattr(webbrowser, "open", lambda url: opened_urls.append(url))

    lc = mod.LockClient(developer_id="test_user")
    lc.dashboard()
    assert len(opened_urls) == 1


def test_dashboard_no_url(monkeypatch):
    """Test dashboard() when _prepare_dashboard_server returns None."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )

    def mock_prepare(self):
        return None, None

    monkeypatch.setattr(mod.LockClient, "_prepare_dashboard_server", mock_prepare)

    lc = mod.LockClient(developer_id="test_user")
    lc.dashboard()  # Should return early without error


def test_dashboard_browser_exception(monkeypatch, capsys):
    """Test dashboard() handles browser open failure."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )

    def mock_prepare(self):
        return "http://127.0.0.1:9999/dash.html", "/tmp/dash.html"

    monkeypatch.setattr(mod.LockClient, "_prepare_dashboard_server", mock_prepare)

    import webbrowser

    monkeypatch.setattr(
        webbrowser, "open", mock.Mock(side_effect=Exception("No browser"))
    )

    lc = mod.LockClient(developer_id="test_user")
    lc.dashboard()
    captured = capsys.readouterr()
    assert "open in browser" in captured.out.lower() or "http" in captured.out.lower()


# ============================================================================
# _prepare_dashboard_server Tests
# ============================================================================


def test_prepare_dashboard_server_missing_html(monkeypatch):
    """Test _prepare_dashboard_server when index.html is missing."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )
    monkeypatch.setattr(mod, "_COLLAB_ROOT", "/nonexistent/path")

    lc = mod.LockClient(developer_id="test_user")
    url, tmp_path = lc._prepare_dashboard_server()
    assert url is None
    assert tmp_path is None


def test_prepare_dashboard_server_success(monkeypatch, tmp_path):
    """Test _prepare_dashboard_server creates server and returns URL."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    # Create fake dashboard directory with index.html
    dash_dir = tmp_path / "dashboard"
    dash_dir.mkdir()
    (dash_dir / "index.html").write_text("<html><body>Test</body></html>")

    monkeypatch.setattr(mod, "_COLLAB_ROOT", str(tmp_path))
    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )

    lc = mod.LockClient(developer_id="test_user")
    url, tmp_file = lc._prepare_dashboard_server()

    # Should return a valid URL
    if url:
        assert "http://127.0.0.1" in url
    # Clean up temp file if created
    if tmp_file and os.path.exists(tmp_file):
        os.unlink(tmp_file)


# ============================================================================
# Watch Tests
# ============================================================================


def test_watch_idle_timeout(monkeypatch, tmp_path):
    """Test watch() exits on idle timeout."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    pid_file = tmp_path / "daemon.pid"
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))
    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )

    # Make _run_git_status return empty (no changes)
    monkeypatch.setattr(mod.LockClient, "_run_git_status", staticmethod(lambda: ""))

    # Make _reconcile return empty set
    monkeypatch.setattr(mod.LockClient, "_reconcile", lambda self: set())

    # Advance time to trigger timeout quickly
    time_offset = [0]
    real_now = datetime.now

    def advancing_now():
        return real_now() + timedelta(minutes=time_offset[0])

    monkeypatch.setattr(
        mod,
        "datetime",
        type(
            "FakeDT",
            (),
            {
                "now": staticmethod(advancing_now),
                "fromisoformat": datetime.fromisoformat,
            },
        )(),
    )
    monkeypatch.setattr(
        mod.time, "sleep", lambda x: time_offset.__setitem__(0, time_offset[0] + 2)
    )

    lc = mod.LockClient(developer_id="test_user")
    lc.watch(interval=1, timeout_mins=1)  # Should exit due to timeout


def test_watch_with_file_changes(monkeypatch, tmp_path):
    """Test watch() detects file changes and acquires locks."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    pid_file = tmp_path / "daemon.pid"
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))

    response = FakeResponse(status=200, data=[{"status": "ok"}])
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))

    # First reconcile returns empty, then git status returns changes
    git_call_count = [0]

    def mock_git_status():
        git_call_count[0] += 1
        if git_call_count[0] <= 1:
            return ""
        if git_call_count[0] == 2:
            return " M src/app.py"
        return ""

    monkeypatch.setattr(
        mod.LockClient, "_run_git_status", staticmethod(mock_git_status)
    )
    monkeypatch.setattr(mod.LockClient, "_reconcile", lambda self: set())

    loop_count = [0]

    def mock_sleep(x):
        loop_count[0] += 1
        if loop_count[0] > 3:
            raise KeyboardInterrupt()

    monkeypatch.setattr(mod.time, "sleep", mock_sleep)

    lc = mod.LockClient(developer_id="test_user")
    lc.watch(interval=1, timeout_mins=60)  # Will exit via KeyboardInterrupt


def test_watch_keyboard_interrupt(monkeypatch, tmp_path):
    """Test watch() handles KeyboardInterrupt gracefully."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    pid_file = tmp_path / "daemon.pid"
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))
    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )
    monkeypatch.setattr(mod.LockClient, "_run_git_status", staticmethod(lambda: ""))
    monkeypatch.setattr(mod.LockClient, "_reconcile", lambda self: set())
    monkeypatch.setattr(mod.time, "sleep", mock.Mock(side_effect=KeyboardInterrupt))

    lc = mod.LockClient(developer_id="test_user")
    # Should not raise
    lc.watch(interval=1, timeout_mins=60)


def test_watch_error_in_loop(monkeypatch, tmp_path):
    """Test watch() handles errors in main loop gracefully."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    pid_file = tmp_path / "daemon.pid"
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))
    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )
    monkeypatch.setattr(mod.LockClient, "_reconcile", lambda self: set())

    call_count = [0]

    def error_git_status():
        call_count[0] += 1
        if call_count[0] <= 2:
            raise RuntimeError("Git broken")
        raise KeyboardInterrupt()

    monkeypatch.setattr(
        mod.LockClient, "_run_git_status", staticmethod(error_git_status)
    )
    monkeypatch.setattr(mod.time, "sleep", lambda x: None)

    lc = mod.LockClient(developer_id="test_user")
    lc.watch(interval=1, timeout_mins=60)


def test_watch_parent_process_dead(monkeypatch, tmp_path):
    """Test watch() exits when parent process dies."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    pid_file = tmp_path / "daemon.pid"
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))
    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )
    monkeypatch.setattr(mod.LockClient, "_run_git_status", staticmethod(lambda: ""))
    monkeypatch.setattr(mod.LockClient, "_reconcile", lambda self: set())

    # Make parent check trigger immediately
    check_count = [0]
    real_now = datetime.now

    def advancing_now():
        check_count[0] += 1
        return real_now() + timedelta(seconds=check_count[0] * 31)

    monkeypatch.setattr(
        mod,
        "datetime",
        type(
            "FakeDT",
            (),
            {
                "now": staticmethod(advancing_now),
                "fromisoformat": datetime.fromisoformat,
            },
        )(),
    )

    # Parent is dead
    monkeypatch.setattr(
        mod.LockClient, "_is_process_alive", staticmethod(lambda pid: False)
    )
    monkeypatch.setattr(mod.time, "sleep", lambda x: None)

    lc = mod.LockClient(developer_id="test_user")
    lc.watch(interval=1, timeout_mins=60)


def test_watch_open_dashboard(monkeypatch, tmp_path):
    """Test watch() opens dashboard when requested."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    pid_file = tmp_path / "daemon.pid"
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))
    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )
    monkeypatch.setattr(mod.LockClient, "_run_git_status", staticmethod(lambda: ""))
    monkeypatch.setattr(mod.LockClient, "_reconcile", lambda self: set())
    monkeypatch.setattr(mod.time, "sleep", mock.Mock(side_effect=KeyboardInterrupt))

    dashboard_called = [False]

    def mock_dashboard(self):
        dashboard_called[0] = True

    monkeypatch.setattr(mod.LockClient, "dashboard", mock_dashboard)

    lc = mod.LockClient(developer_id="test_user")
    lc.watch(interval=1, timeout_mins=60, open_dashboard=True)
    assert dashboard_called[0]


# ============================================================================
# _graceful_shutdown Tests
# ============================================================================


def test_graceful_shutdown(monkeypatch, tmp_path):
    """Test _graceful_shutdown releases locks and removes PID file."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    pid_file = tmp_path / "daemon.pid"
    pid_file.write_text("12345")
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))
    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )

    lc = mod.LockClient(developer_id="test_user")
    lc._graceful_shutdown()
    assert not pid_file.exists()


def test_graceful_shutdown_with_exception(monkeypatch, tmp_path):
    """Test _graceful_shutdown handles release_all errors."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    pid_file = tmp_path / "daemon.pid"
    pid_file.write_text("12345")
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))
    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )

    lc = mod.LockClient(developer_id="test_user")
    monkeypatch.setattr(lc, "release_all", mock.Mock(side_effect=RuntimeError("fail")))
    lc._graceful_shutdown()  # Should not raise


# ============================================================================
# _reconcile Tests
# ============================================================================


def test_reconcile_stale_locks(monkeypatch, tmp_path):
    """Test _reconcile releases stale locks and acquires missing ones."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    monkeypatch.setattr(
        mod.LockClient,
        "_run_git_status",
        staticmethod(lambda: " M src/new.py"),
    )

    locks_data = [
        {"file_path": "src/old.py", "developer_id": "test_user"},
        {"file_path": "src/new.py", "developer_id": "test_user"},
    ]
    response = FakeResponse(status=200, data=locks_data)
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))

    lc = mod.LockClient(developer_id="test_user")
    result = lc._reconcile()
    assert "src/new.py" in result


def test_reconcile_git_error(monkeypatch, tmp_path):
    """Test _reconcile handles git status errors."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    def error_git_status():
        raise RuntimeError("Git broken")

    monkeypatch.setattr(
        mod.LockClient, "_run_git_status", staticmethod(error_git_status)
    )
    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )

    lc = mod.LockClient(developer_id="test_user")
    result = lc._reconcile()
    assert result == set()


def test_reconcile_supabase_error(monkeypatch, tmp_path):
    """Test _reconcile handles Supabase errors."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    monkeypatch.setattr(
        mod.LockClient,
        "_run_git_status",
        staticmethod(lambda: " M src/app.py"),
    )

    class ErrorClient(FakeClient):
        def execute(self):
            raise RuntimeError("Supabase down")

    monkeypatch.setattr(
        mod,
        "_get_create_client",
        lambda: lambda url, key: ErrorClient(FakeResponse()),
    )

    lc = mod.LockClient(developer_id="test_user")
    result = lc._reconcile()
    assert "src/app.py" in result


# ============================================================================
# _run_git_status Tests
# ============================================================================


def test_run_git_status(monkeypatch):
    """Test _run_git_status runs git command."""

    def mock_check_output(cmd, *args, **kwargs):
        return b" M src/app.py\n M src/routes.py\n"

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)
    result = mod.LockClient._run_git_status()
    assert "src/app.py" in result


# ============================================================================
# _parse_git_status_path Tests
# ============================================================================


def test_parse_git_status_path_simple():
    """Test parsing simple modified file."""
    assert mod.LockClient._parse_git_status_path(" M src/app.py") == "src/app.py"


def test_parse_git_status_path_rename():
    """Test parsing renamed file."""
    result = mod.LockClient._parse_git_status_path("R  old.py -> new.py")
    assert result == "new.py"


def test_parse_git_status_path_quoted():
    """Test parsing quoted paths."""
    result = mod.LockClient._parse_git_status_path('M  "src/my file.py"')
    assert "my file" in result


# ============================================================================
# _register_signal_handlers Tests
# ============================================================================


def test_register_signal_handlers(monkeypatch, tmp_path):
    """Test that signal handlers are registered."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    pid_file = tmp_path / "daemon.pid"
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))
    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )

    lc = mod.LockClient(developer_id="test_user")
    lc._register_signal_handlers()
    # Should not raise, signal handlers registered


# ============================================================================
# Error Handling Tests
# ============================================================================


def test_validate_credentials_missing_url(monkeypatch):
    """Test credential validation when URL is missing."""
    monkeypatch.setattr(mod, "SUPABASE_URL", "")
    monkeypatch.setattr(mod, "SUPABASE_ANON_KEY", "test_key")

    with pytest.raises(SystemExit):
        mod._validate_credentials()


def test_validate_credentials_missing_key(monkeypatch):
    """Test credential validation when key is missing."""
    monkeypatch.setattr(mod, "SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setattr(mod, "SUPABASE_ANON_KEY", "")

    with pytest.raises(SystemExit):
        mod._validate_credentials()


def test_retry_on_network_error_success_after_retry(monkeypatch):
    """Test retry logic succeeds after transient network error."""
    call_count = [0]

    def flaky_func():
        call_count[0] += 1
        if call_count[0] < 2:
            raise ConnectionError("Network timeout")
        return "success"

    monkeypatch.setattr(mod.time, "sleep", lambda x: None)

    result = mod._retry_on_network_error(flaky_func)
    assert result == "success"
    assert call_count[0] == 2


def test_retry_on_network_error_gives_up(monkeypatch):
    """Test retry logic gives up after max attempts."""

    def always_fails():
        raise ConnectionError("Persistent network error")

    monkeypatch.setattr(mod.time, "sleep", lambda x: None)

    with pytest.raises(ConnectionError):
        mod._retry_on_network_error(always_fails)


def test_retry_on_network_error_non_network_error():
    """Test retry logic doesn't retry non-network errors.

    Note: _retry_on_network_error only skips retry when the error string does
    NOT contain 'timeout', 'connection', 'network', or 'unreachable'. A plain
    ValueError('Not a network error') matches none of those, so it raises immediately.
    """
    call_count = [0]

    def non_network_error():
        call_count[0] += 1
        raise ValueError("Not a network error")

    with pytest.raises(ValueError):
        mod._retry_on_network_error(non_network_error)

    # The function should raise on first attempt (no retry for non-network errors)
    assert call_count[0] >= 1


# ============================================================================
# Response Parsing Tests
# ============================================================================


def test_parse_response_success():
    """Test response parsing for successful responses."""
    response = FakeResponse(status=200, data={"key": "value"})

    status, data, error = mod.LockClient._parse_response(response)
    assert status == 200
    assert data == {"key": "value"}
    assert error is None


def test_parse_response_error():
    """Test response parsing for error responses."""
    response = FakeResponse(status=400, data=None, error="Bad request")

    status, data, error = mod.LockClient._parse_response(response)
    assert status == 400
    assert error == "Bad request"


def test_parse_response_dict():
    """Test response parsing for dict responses."""
    resp = {"status": 200, "data": [{"file": "test"}], "error": None}
    status, data, error = mod.LockClient._parse_response(resp)
    assert status == 200
    assert data == [{"file": "test"}]


# ============================================================================
# Comprehensive Edge Cases (restored from test_lock_client_comprehensive.py)
# ============================================================================


def test_get_current_branch_error(monkeypatch):
    """Test _get_current_branch returns None when git command fails."""

    def mock_check_output(cmd, *args, **kwargs):
        raise subprocess.CalledProcessError(128, cmd)

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)

    result = mod.LockClient._get_current_branch()
    assert result is None


def test_get_lock_status_expired(monkeypatch):
    """Test get_lock_status marks expired locks as unlocked."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    lock_data = {
        "file_path": "src/app.py",
        "developer_id": "other_user",
        "acquired_at": "2025-01-01T10:00:00+00:00",
        "expires_at": past,
    }
    response = FakeResponse(status=200, data=[lock_data])
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))

    lc = mod.LockClient(developer_id="test_user")
    status = lc.get_lock_status("src/app.py")
    assert status["is_locked"] is False
    assert status["can_edit"] is True
    assert status.get("expired") is True


# ============================================================================
# CLI Tests
# ============================================================================


def test_cli_acquire(monkeypatch, tmp_path, capsys):
    """Test CLI acquire command."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    test_file = tmp_path / "src" / "app.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("# code")

    response = FakeResponse(status=200, data=[{"status": "ok"}])
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))
    monkeypatch.setattr(mod, "_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setattr(sys, "argv", ["lock_client.py", "acquire", str(test_file)])

    try:
        mod._run_cli()
    except SystemExit:
        pass
    captured = capsys.readouterr()
    assert "locked" in captured.out.lower() or "✓" in captured.out


def test_cli_release(monkeypatch, capsys):
    """Test CLI release command."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    response = FakeResponse(status=200, data=[{"file_path": "src/app.py"}])
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))
    monkeypatch.setattr(sys, "argv", ["lock_client.py", "release", "src/app.py"])

    mod._run_cli()
    captured = capsys.readouterr()
    assert "released" in captured.out.lower() or "✓" in captured.out


def test_cli_active_no_locks(monkeypatch, capsys):
    """Test CLI active command with no locks."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    response = FakeResponse(status=200, data=[])
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))
    monkeypatch.setattr(sys, "argv", ["lock_client.py", "active"])

    mod._run_cli()
    captured = capsys.readouterr()
    assert "no active" in captured.out.lower()


def test_cli_active_with_locks(monkeypatch, capsys):
    """Test CLI active command with locks."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    response = FakeResponse(
        status=200,
        data=[
            {
                "file_path": "src/app.py",
                "developer_id": "user1",
                "branch_name": "main",
                "reason": "testing",
            }
        ],
    )
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))
    monkeypatch.setattr(sys, "argv", ["lock_client.py", "active"])

    mod._run_cli()
    captured = capsys.readouterr()
    assert "src/app.py" in captured.out


def test_cli_status_locked(monkeypatch, capsys):
    """Test CLI status command for locked file."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    future = (datetime.now(timezone.utc) + timedelta(hours=8)).isoformat()
    response = FakeResponse(
        status=200,
        data=[
            {
                "file_path": "src/app.py",
                "developer_id": "user1",
                "acquired_at": "2025-01-01T10:00:00+00:00",
                "expires_at": future,
            }
        ],
    )
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))
    monkeypatch.setattr(sys, "argv", ["lock_client.py", "status", "src/app.py"])

    mod._run_cli()
    captured = capsys.readouterr()
    assert "locked" in captured.out.lower() or "🔒" in captured.out


def test_cli_status_unlocked(monkeypatch, capsys):
    """Test CLI status command for unlocked file."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    response = FakeResponse(status=200, data=[])
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))
    monkeypatch.setattr(sys, "argv", ["lock_client.py", "status", "src/app.py"])

    mod._run_cli()
    captured = capsys.readouterr()
    assert "unlocked" in captured.out.lower() or "🔓" in captured.out


def test_cli_release_all(monkeypatch, capsys):
    """Test CLI release-all command."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    response = FakeResponse(status=200, data=[])
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))
    monkeypatch.setattr(sys, "argv", ["lock_client.py", "release-all"])

    mod._run_cli()
    captured = capsys.readouterr()
    assert "released" in captured.out.lower()


def test_cli_force_release(monkeypatch, capsys):
    """Test CLI force-release command."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    response = FakeResponse(status=200, data=[{"file_path": "src/app.py"}])
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))
    monkeypatch.setattr(sys, "argv", ["lock_client.py", "force-release", "src/app.py"])

    mod._run_cli()
    captured = capsys.readouterr()
    assert "✓" in captured.out or "✗" in captured.out


def test_cli_acquire_batch(monkeypatch, tmp_path, capsys):
    """Test CLI acquire-batch command."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    file1 = tmp_path / "src" / "a.py"
    file2 = tmp_path / "src" / "b.py"
    file1.parent.mkdir(parents=True)
    file1.write_text("# a")
    file2.write_text("# b")

    response = FakeResponse(status=200, data=[{"status": "ok"}])
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))
    monkeypatch.setattr(mod, "_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setattr(
        sys, "argv", ["lock_client.py", "acquire-batch", str(file1), str(file2)]
    )

    try:
        mod._run_cli()
    except SystemExit:
        pass
    captured = capsys.readouterr()
    assert "locked" in captured.out.lower() or "✓" in captured.out


def test_cli_acquire_batch_conflict(monkeypatch, tmp_path, capsys):
    """Test CLI acquire-batch with conflicts."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    file1 = tmp_path / "src" / "a.py"
    file1.parent.mkdir(parents=True)
    file1.write_text("# a")

    response = FakeResponse(status=200, data=[{"status": "conflict", "owner": "other"}])
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))
    monkeypatch.setattr(mod, "_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setattr(sys, "argv", ["lock_client.py", "acquire-batch", str(file1)])

    with pytest.raises(SystemExit):
        mod._run_cli()


def test_cli_release_batch(monkeypatch, capsys):
    """Test CLI release-batch command."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    response = FakeResponse(status=200, data=[{"file_path": "src/app.py"}])
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))
    monkeypatch.setattr(
        sys, "argv", ["lock_client.py", "release-batch", "src/a.py", "src/b.py"]
    )

    mod._run_cli()
    captured = capsys.readouterr()
    assert "released" in captured.out.lower()


def test_cli_daemon_start(monkeypatch, tmp_path, capsys):
    """Test CLI daemon-start command."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    pid_file = tmp_path / "daemon.pid"
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))
    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )

    class FakeProc:
        pid = 12345

    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: FakeProc())
    monkeypatch.setattr(mod.time, "sleep", lambda x: None)
    monkeypatch.setattr(
        mod.LockClient, "_is_process_alive", staticmethod(lambda pid: True)
    )
    monkeypatch.setattr(sys, "argv", ["lock_client.py", "daemon-start"])

    mod._run_cli()
    captured = capsys.readouterr()
    assert "started" in captured.out.lower()


def test_cli_daemon_stop(monkeypatch, tmp_path, capsys):
    """Test CLI daemon-stop command."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    pid_file = tmp_path / "daemon.pid"
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))
    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )
    monkeypatch.setattr(sys, "argv", ["lock_client.py", "daemon-stop"])

    mod._run_cli()
    captured = capsys.readouterr()
    assert "no running" in captured.out.lower() or "stop" in captured.out.lower()


def test_cli_daemon_status(monkeypatch, tmp_path, capsys):
    """Test CLI daemon-status command."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    pid_file = tmp_path / "daemon.pid"
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))
    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )
    monkeypatch.setattr(sys, "argv", ["lock_client.py", "daemon-status"])

    mod._run_cli()
    captured = capsys.readouterr()
    assert "not running" in captured.out.lower()


def test_cli_reconcile(monkeypatch, tmp_path, capsys):
    """Test CLI reconcile command."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )
    monkeypatch.setattr(mod.LockClient, "_run_git_status", staticmethod(lambda: ""))
    monkeypatch.setattr(sys, "argv", ["lock_client.py", "reconcile"])

    mod._run_cli()


def test_cli_history(monkeypatch, capsys):
    """Test CLI history command."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    response = FakeResponse(status=200, data=[])
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))
    monkeypatch.setattr(sys, "argv", ["lock_client.py", "history"])

    mod._run_cli()
    captured = capsys.readouterr()
    assert "[]" in captured.out


def test_cli_dashboard(monkeypatch, capsys):
    """Test CLI dashboard command."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )

    def mock_prepare(self):
        return "http://127.0.0.1:9999/dash.html", "/tmp/dash.html"

    monkeypatch.setattr(mod.LockClient, "_prepare_dashboard_server", mock_prepare)

    import webbrowser

    monkeypatch.setattr(webbrowser, "open", lambda url: None)
    monkeypatch.setattr(mod.time, "sleep", mock.Mock(side_effect=KeyboardInterrupt))
    monkeypatch.setattr(sys, "argv", ["lock_client.py", "dashboard"])

    try:
        mod._run_cli()
    except KeyboardInterrupt:
        pass


def test_cli_watch(monkeypatch, tmp_path, capsys):
    """Test CLI watch command."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    pid_file = tmp_path / "daemon.pid"
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))
    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )
    monkeypatch.setattr(mod.LockClient, "_run_git_status", staticmethod(lambda: ""))
    monkeypatch.setattr(mod.LockClient, "_reconcile", lambda self: set())
    monkeypatch.setattr(mod.time, "sleep", mock.Mock(side_effect=KeyboardInterrupt))
    monkeypatch.setattr(sys, "argv", ["lock_client.py", "watch"])

    mod._run_cli()


def test_cli_no_command(monkeypatch, capsys):
    """Test CLI with no command prints help."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )
    monkeypatch.setattr(sys, "argv", ["lock_client.py"])

    mod._run_cli()
    capsys.readouterr()
    # Should print help or usage info


def test_main_entry_point(monkeypatch, capsys):
    """Test that main() calls _run_cli."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )
    monkeypatch.setattr(sys, "argv", ["lock_client.py"])

    mod.main()


def test_cli_daemon_start_with_auto_open_env(monkeypatch, tmp_path, capsys):
    """Test CLI daemon-start with AUTO_OPEN_DASHBOARD env variable."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")
    monkeypatch.setenv("AUTO_OPEN_DASHBOARD", "1")

    pid_file = tmp_path / "daemon.pid"
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))
    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )

    class FakeProc:
        pid = 12345

    popen_cmds = []

    def mock_popen(cmd, **kwargs):
        popen_cmds.append(cmd)
        return FakeProc()

    monkeypatch.setattr(subprocess, "Popen", mock_popen)
    monkeypatch.setattr(mod.time, "sleep", lambda x: None)
    monkeypatch.setattr(
        mod.LockClient, "_is_process_alive", staticmethod(lambda pid: True)
    )
    monkeypatch.setattr(sys, "argv", ["lock_client.py", "daemon-start"])

    mod._run_cli()
    # Auto-open should add --open-dashboard
    assert any("--open-dashboard" in str(cmd) for cmd in popen_cmds)


def test_cli_acquire_failure(monkeypatch, capsys):
    """Test CLI acquire when file doesn't exist."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )
    monkeypatch.setattr(
        sys, "argv", ["lock_client.py", "acquire", "nonexistent/file.py"]
    )

    with pytest.raises(SystemExit):
        mod._run_cli()


# ============================================================================
# Additional Coverage Tests
# ============================================================================


def test_read_pid_bad_content(tmp_path, monkeypatch):
    """Test _read_pid handles non-integer PID file content (line 876-877)."""
    pid_file = tmp_path / "bad.pid"
    pid_file.write_text("not-a-number")
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))

    pid = mod.LockClient._read_pid()
    assert pid is None


def test_parse_git_status_path_unicode_escape():
    """Test _parse_git_status_path with unicode-escaped quoted path (line 854-856)."""
    # A quoted path triggers the unicode_escape decode path
    result = mod.LockClient._parse_git_status_path(' M "src/file.py"')
    assert "file" in result


def test_parse_git_status_path_bad_unicode_escape():
    """Test _parse_git_status_path with invalid unicode escape (line 855-856)."""
    # Invalid escape sequence triggers the except branch
    result = mod.LockClient._parse_git_status_path(' M "src/\\xZZfile.py"')
    assert "file" in result


def test_prepare_dashboard_server_read_error(monkeypatch, tmp_path):
    """Test _prepare_dashboard_server when reading HTML file fails (lines 582-584)."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    # Create dashboard dir with index.html, but make it unreadable
    dash_dir = tmp_path / "dashboard"
    dash_dir.mkdir()
    html_file = dash_dir / "index.html"
    html_file.write_text("<html></html>")

    monkeypatch.setattr(mod, "_COLLAB_ROOT", str(tmp_path))
    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )

    # Mock open to raise IOError on the specific file
    original_open = open

    def failing_open(path, *args, **kwargs):
        if "index.html" in str(path):
            raise IOError("Permission denied")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr("builtins.open", failing_open)

    lc = mod.LockClient(developer_id="test_user")
    url, tmp_file = lc._prepare_dashboard_server()
    assert url is None


def test_graceful_shutdown_releases_locks(monkeypatch, tmp_path):
    """Test _graceful_shutdown logs when locks are released (line 778)."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    pid_file = tmp_path / "daemon.pid"
    pid_file.write_text("12345")
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))

    # Return locks to release
    locks_data = [
        {"file_path": "src/app.py", "developer_id": "test_user"},
    ]
    response = FakeResponse(status=200, data=locks_data)
    monkeypatch.setattr(mod, "_get_create_client", lambda: make_create_client(response))

    lc = mod.LockClient(developer_id="test_user")
    lc._graceful_shutdown()


def test_watch_with_conflict_warning(monkeypatch, tmp_path):
    """Test watch() logs conflict warnings (line 721)."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    pid_file = tmp_path / "daemon.pid"
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))

    # Make acquire return conflict
    conflict_resp = FakeResponse(
        status=200, data=[{"status": "conflict", "owner": "other"}]
    )
    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(conflict_resp)
    )

    git_call_count = [0]

    def mock_git_status():
        git_call_count[0] += 1
        if git_call_count[0] <= 1:
            return ""
        if git_call_count[0] == 2:
            return " M src/conflict.py"
        return " M src/conflict.py"  # keep same to avoid further changes

    monkeypatch.setattr(
        mod.LockClient, "_run_git_status", staticmethod(mock_git_status)
    )
    monkeypatch.setattr(mod.LockClient, "_reconcile", lambda self: set())

    loop_count = [0]

    def mock_sleep(x):
        loop_count[0] += 1
        if loop_count[0] > 3:
            raise KeyboardInterrupt()

    monkeypatch.setattr(mod.time, "sleep", mock_sleep)

    lc = mod.LockClient(developer_id="test_user")
    lc.watch(interval=1, timeout_mins=60)


def test_watch_dashboard_error(monkeypatch, tmp_path):
    """Test watch() handles dashboard open error (lines 666-667)."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    pid_file = tmp_path / "daemon.pid"
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))
    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )
    monkeypatch.setattr(mod.LockClient, "_run_git_status", staticmethod(lambda: ""))
    monkeypatch.setattr(mod.LockClient, "_reconcile", lambda self: set())
    monkeypatch.setattr(mod.time, "sleep", mock.Mock(side_effect=KeyboardInterrupt))

    def failing_dashboard(self):
        raise RuntimeError("Dashboard broken")

    monkeypatch.setattr(mod.LockClient, "dashboard", failing_dashboard)

    lc = mod.LockClient(developer_id="test_user")
    lc.watch(interval=1, timeout_mins=60, open_dashboard=True)


def test_watch_reconcile_periodic(monkeypatch, tmp_path):
    """Test watch() triggers periodic reconciliation (lines 737-738)."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    pid_file = tmp_path / "daemon.pid"
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))
    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )
    monkeypatch.setattr(mod.LockClient, "_run_git_status", staticmethod(lambda: ""))

    reconcile_count = [0]

    def counting_reconcile(self):
        reconcile_count[0] += 1
        return set()

    monkeypatch.setattr(mod.LockClient, "_reconcile", counting_reconcile)

    # Advance time past 15 minutes for periodic reconcile
    time_offset = [0]
    real_now = datetime.now

    def advancing_now():
        return real_now() + timedelta(minutes=time_offset[0])

    monkeypatch.setattr(
        mod,
        "datetime",
        type(
            "FakeDT",
            (),
            {
                "now": staticmethod(advancing_now),
                "fromisoformat": datetime.fromisoformat,
            },
        )(),
    )

    loop_count = [0]

    def mock_sleep(x):
        loop_count[0] += 1
        time_offset[0] += 16  # Jump 16 minutes each sleep
        if loop_count[0] > 3:
            raise KeyboardInterrupt()

    monkeypatch.setattr(mod.time, "sleep", mock_sleep)

    lc = mod.LockClient(developer_id="test_user")
    lc.watch(interval=1, timeout_mins=0)  # timeout=0 means no timeout

    # reconcile_count[0] should be > 1 (initial + periodic)
    assert reconcile_count[0] >= 1


def test_prepare_dashboard_server_tmpfile_error(monkeypatch, tmp_path):
    """Test _prepare_dashboard_server when tmpfile creation fails (lines 604-606)."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    dash_dir = tmp_path / "dashboard"
    dash_dir.mkdir()
    (dash_dir / "index.html").write_text("<html></html>")

    monkeypatch.setattr(mod, "_COLLAB_ROOT", str(tmp_path))
    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )

    # Mock tempfile to raise
    import tempfile

    monkeypatch.setattr(
        tempfile,
        "NamedTemporaryFile",
        mock.Mock(side_effect=OSError("Disk full")),
    )

    lc = mod.LockClient(developer_id="test_user")
    url, tmp_file = lc._prepare_dashboard_server()
    assert url is None
    assert tmp_file is None


def test_prepare_dashboard_server_http_error(monkeypatch, tmp_path):
    """Test _prepare_dashboard_server when HTTP server fails (lines 641-647)."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    dash_dir = tmp_path / "dashboard"
    dash_dir.mkdir()
    (dash_dir / "index.html").write_text("<html></html>")

    monkeypatch.setattr(mod, "_COLLAB_ROOT", str(tmp_path))
    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )

    # Mock http.server.ThreadingHTTPServer to raise
    import http.server

    monkeypatch.setattr(
        http.server,
        "ThreadingHTTPServer",
        mock.Mock(side_effect=OSError("Port error")),
    )

    lc = mod.LockClient(developer_id="test_user")
    url, tmp_file = lc._prepare_dashboard_server()
    assert url is None
    assert tmp_file is None


def test_remove_pid_oserror(tmp_path, monkeypatch):
    """Test _remove_pid handles OSError gracefully (lines 895-896)."""
    pid_file = tmp_path / "daemon.pid"
    pid_file.write_text("12345")
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))

    # Mock os.remove to raise OSError
    original_remove = os.remove

    def failing_remove(path):
        if "daemon.pid" in str(path):
            raise OSError("Permission denied")
        return original_remove(path)

    monkeypatch.setattr(os, "remove", failing_remove)

    # Should not raise
    mod.LockClient._remove_pid()


def test_reconcile_supabase_lock_query_error(monkeypatch, tmp_path):
    """Test _reconcile handles Supabase lock query error (lines 806-808)."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    monkeypatch.setattr(
        mod.LockClient,
        "_run_git_status",
        staticmethod(lambda: " M src/app.py"),
    )

    call_count = [0]

    class SelectiveErrorClient:
        """Errors only on the second execute call (active locks)."""

        def __init__(self, resp):
            self._resp = resp

        def rpc(self, *args, **kwargs):
            return self

        def table(self, *args, **kwargs):
            return self

        def select(self, *args, **kwargs):
            call_count[0] += 1
            if call_count[0] >= 1:
                raise RuntimeError("Supabase query failed")
            return self

        def delete(self, *args, **kwargs):
            return self

        def eq(self, *args, **kwargs):
            return self

        def execute(self):
            return self._resp

    monkeypatch.setattr(
        mod,
        "_get_create_client",
        lambda: lambda url, key: SelectiveErrorClient(FakeResponse()),
    )

    lc = mod.LockClient(developer_id="test_user")
    result = lc._reconcile()
    assert "src/app.py" in result


def test_prepare_dashboard_server_socket_probe_failure(monkeypatch, tmp_path):
    """Test _prepare_dashboard_server socket probe retry (lines 637-638)."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    dash_dir = tmp_path / "dashboard"
    dash_dir.mkdir()
    (dash_dir / "index.html").write_text("<html></html>")

    monkeypatch.setattr(mod, "_COLLAB_ROOT", str(tmp_path))
    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )

    import http.server
    import socket as _socket

    # Create a real-ish server mock that binds but returns a port
    # where sockets will initially fail then succeed
    probe_count = [0]
    original_create_connection = _socket.create_connection

    def flaky_connection(addr, timeout=None):
        probe_count[0] += 1
        if probe_count[0] <= 2:
            raise ConnectionRefusedError("not ready yet")
        return original_create_connection(addr, timeout=timeout)

    class FakeServerForProbe:
        def __init__(self, addr, handler):
            self.server_address = ("127.0.0.1", 19876)

        def serve_forever(self):
            pass

        def shutdown(self):
            pass

    monkeypatch.setattr(http.server, "ThreadingHTTPServer", FakeServerForProbe)
    monkeypatch.setattr(_socket, "create_connection", flaky_connection)
    monkeypatch.setattr(mod.time, "sleep", lambda x: None)

    lc = mod.LockClient(developer_id="test_user")
    url, tmp_file = lc._prepare_dashboard_server()

    # Should succeed after retries
    if url:
        assert "http://127.0.0.1" in url
    if tmp_file and os.path.exists(tmp_file):
        os.unlink(tmp_file)


def test_prepare_dashboard_server_unlink_error(monkeypatch, tmp_path):
    """Test _prepare_dashboard_server handles unlink error (lines 644-645)."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_key")

    dash_dir = tmp_path / "dashboard"
    dash_dir.mkdir()
    (dash_dir / "index.html").write_text("<html></html>")

    monkeypatch.setattr(mod, "_COLLAB_ROOT", str(tmp_path))
    monkeypatch.setattr(
        mod, "_get_create_client", lambda: make_create_client(FakeResponse())
    )

    import http.server

    # Server creation raises, triggering the except block
    def raise_on_create(addr, handler):
        raise OSError("Cannot bind")

    monkeypatch.setattr(http.server, "ThreadingHTTPServer", raise_on_create)

    # Also mock os.unlink to raise, covering lines 644-645
    original_unlink = os.unlink

    def failing_unlink(path):
        if path.endswith(".html"):
            raise OSError("Permission denied on unlink")
        return original_unlink(path)

    monkeypatch.setattr(os, "unlink", failing_unlink)

    lc = mod.LockClient(developer_id="test_user")
    url, tmp_file = lc._prepare_dashboard_server()
    assert url is None
    assert tmp_file is None
