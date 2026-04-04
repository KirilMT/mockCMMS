from __future__ import annotations

import importlib.util
from pathlib import Path

# Load module from .collab/pycharm/live_locks_watcher.py
proj_root = Path(__file__).resolve().parents[3]
module_path = proj_root / ".collab" / "pycharm" / "live_locks_watcher.py"
spec = importlib.util.spec_from_file_location(
    "collab.live_locks_watcher", str(module_path)
)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)  # type: ignore[arg-type]


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


def test_color_without_colorama():
    # Ensure colorama-disabled branch returns plain text
    mod._HAS_COLORAMA = False
    out = mod._color("hello", "X")
    assert out == "hello"


def test_scan_remote_locks_client_exception(monkeypatch):
    # If the client's table.select.execute raises, the function should return
    fake = FakeClient(explode=True)
    # Clear state
    mod._warned_remote_locks.clear()
    mod._known_remote_locks.clear()
    # Should not raise
    mod._scan_remote_locks(fake)


def test_scan_remote_locks_warns_for_other_owner(monkeypatch):
    # Fake a remote lock owned by another developer
    fake_data = [
        {
            "developer_id": "other_user",
            "file_path": "src/locked.txt",
            "branch_name": None,
            "reason": None,
        }
    ]
    fake = FakeClient(data=fake_data)
    # Set our developer id to something else
    mod.DEVELOPER_ID = "me"
    mod._warned_remote_locks.clear()
    mod._known_remote_locks.clear()

    mod._scan_remote_locks(fake)
    assert "src/locked.txt" in mod._warned_remote_locks


def test_is_process_alive_fallback_without_psutil(monkeypatch):
    # Simulate ImportError for psutil and make tasklist command fail
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *a, **k):
        if name == "psutil":
            raise ImportError("no psutil")
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    def fake_check_output(*a, **k):
        raise Exception("tasklist failed")

    monkeypatch.setattr("subprocess.check_output", fake_check_output)

    # Should return False when both psutil unavailable and tasklist fails
    assert mod._is_process_alive(999999) is False


def test_scan_remote_locks_same_owner_updates_known(monkeypatch):
    # Fake a remote lock owned by the same developer
    fake_data = [
        {
            "developer_id": "me",
            "file_path": "src/mine.txt",
            "branch_name": None,
            "reason": None,
        }
    ]
    fake = FakeClient(data=fake_data)
    mod.DEVELOPER_ID = "me"
    mod._known_remote_locks.clear()
    mod._warned_remote_locks.clear()

    mod._scan_remote_locks(fake)
    # After scan, known_remote_locks should include the file
    assert "src/mine.txt" in mod._known_remote_locks


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

    monkeypatch.setattr(mod, "create_client", lambda url, key: ExplodeClient())
    monkeypatch.setattr(mod, "_start_dashboard_server", lambda: None)

    # Make git status report one modified file so the watcher will attempt acquire
    monkeypatch.setattr("subprocess.check_output", lambda *a, **k: b" M src/app.py")

    # Make sleep raise KeyboardInterrupt to exit after first iteration
    def raise_kb(_):
        raise KeyboardInterrupt()

    monkeypatch.setattr(mod.time, "sleep", raise_kb)

    # Ensure developer id is deterministic
    monkeypatch.setattr(mod, "_get_developer_id", lambda: "me")

    # Avoid argparse picking up pytest args
    import sys as _sys

    monkeypatch.setattr(_sys, "argv", ["collab"])  # safe minimal argv

    # Should not raise (main handles KeyboardInterrupt and exits cleanly)
    mod.main()
