from __future__ import annotations

import importlib.util
import os
from pathlib import Path

# Load lock_client module from file so tests are deterministic
proj_root = Path(__file__).resolve().parents[3]
module_path = proj_root / ".collab" / "core" / "lock_client.py"
spec = importlib.util.spec_from_file_location("collab.lock_client", str(module_path))
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)  # type: ignore[arg-type]


def test_ephemeral_developer_short_circuits_acquire_and_release(tmp_path, monkeypatch):
    # Create a file to lock
    test_file = tmp_path / "src" / "file.txt"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("hello")

    # Ensure credentials present so LockClient init passes
    monkeypatch.setenv("SUPABASE_URL", "https://example.invalid")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon")

    # Ensure module will not exit trying to import supabase; provide a dummy
    # _get_create_client that returns a callable create_client factory.
    monkeypatch.setattr(mod, "_get_create_client", lambda: (lambda url, key: object()))

    # Create client with ephemeral developer id prefix
    lc = mod.LockClient(developer_id="test_dev_ci_123")
    assert getattr(lc, "_is_ephemeral", False) is True

    ok, token = lc.acquire(str(test_file))
    assert ok is True
    assert isinstance(token, str) and token.startswith("ephemeral-")

    ok2, msg = lc.release(str(test_file))
    assert ok2 is True
    assert "ephemeral" in msg


def test_normalize_file_path_handles_exceptions(monkeypatch):
    # Load fresh client
    monkeypatch.setenv("SUPABASE_URL", "https://example.invalid")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon")
    monkeypatch.setattr(mod, "_get_create_client", lambda: (lambda url, key: object()))
    lc = mod.LockClient(developer_id="tester")

    # Force os.path.isabs to raise to exercise the except: branch
    def raising_isabs(p):
        raise RuntimeError("boom")

    monkeypatch.setattr(os.path, "isabs", raising_isabs)
    out = lc._normalize_file_path(r"C:\some\path\file.py")
    # Should replace backslashes with forward slashes even on exception
    assert "\\" not in out
    # restore not strictly necessary due to monkeypatch fixture


def test_non_str_developer_id_sets_ephemeral_false(monkeypatch):
    # If developer_id is not a str, the defensive except branch should run
    monkeypatch.setenv("SUPABASE_URL", "https://example.invalid")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon")
    monkeypatch.setattr(mod, "_get_create_client", lambda: (lambda url, key: object()))

    # Pass an integer as developer_id to trigger AttributeError in startswith
    lc = mod.LockClient(developer_id=12345)  # type: ignore[arg-type]
    # Defensive except should set _is_ephemeral to False
    assert getattr(lc, "_is_ephemeral", None) is False
