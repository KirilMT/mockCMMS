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

    def delete(self, *a, **k):
        return self

    def eq(self, *a, **k):
        return self

    def execute(self):
        if self._explode:
            raise RuntimeError("backend down")
        return FakeResp(self._data)


def test_is_ephemeral_dev_empty():
    # Cover the branch where dev_id is falsy and returns False
    assert mod._is_ephemeral_dev("") is False


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
    fake = FakeClient(data=fake_data)
    mod.DEVELOPER_ID = "me"
    mod._local_owned_locks.clear()
    mod._local_owned_locks.add("src/owned.txt")
    mod._warned_remote_locks.clear()
    mod._known_remote_locks.clear()

    # Should not raise and should not add to _warned_remote_locks
    mod._scan_remote_locks(fake)
    assert "src/owned.txt" not in mod._warned_remote_locks


def test_scan_remote_locks_removed_discards_local_owned(monkeypatch):
    # Simulate a previously-known remote lock that was released; if we had it
    # recorded locally, the code path should discard it from _local_owned_locks.
    mod._known_remote_locks.clear()
    mod._known_remote_locks.add("src/released.txt")
    mod._local_owned_locks.clear()
    mod._local_owned_locks.add("src/released.txt")
    # Fake client returns no locks (empty list)
    fake = FakeClient(data=[])

    mod._scan_remote_locks(fake)
    # After scanning, released lock should be removed from local-owned set
    assert "src/released.txt" not in mod._local_owned_locks


def test_process_new_files_handles_local_add_exception(monkeypatch):
    # Replace _local_owned_locks with an object whose add() raises to hit the
    # exception-handling branch inside the helper.
    class BadSet:
        def add(self, *a, **k):
            raise RuntimeError("boom add")

    old = mod._local_owned_locks
    mod._local_owned_locks = BadSet()

    # Fake client returns success (no conflict)
    class RpcClient:
        def rpc(self, *a, **k):
            return self

        def execute(self):
            return FakeResp([])

    client = RpcClient()
    mod.DEVELOPER_ID = "tester"

    # Should not raise even though add() raises inside
    mod._process_new_files(client, "main", {"src/a.py"})

    # restore
    mod._local_owned_locks = old


def test_process_releases_handles_discard_exception(monkeypatch):
    # Replace _local_owned_locks with object whose discard raises
    class BadSet:
        def discard(self, *a, **k):
            raise RuntimeError("boom discard")

    old = mod._local_owned_locks
    mod._local_owned_locks = BadSet()

    # Fake client for delete.execute()
    fake = FakeClient(data=[])
    mod.DEVELOPER_ID = "tester"

    # Should not raise even though discard() raises inside
    mod._process_releases(fake, {"src/b.py"})

    mod._local_owned_locks = old


def test_main_exits_when_create_client_none(monkeypatch):
    # Ensure main() will exit early with SystemExit when create_client is None
    monkeypatch.setenv("SUPABASE_URL", "https://example.invalid")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon:fake")

    monkeypatch.setattr(mod, "create_client", None)
    monkeypatch.setattr(mod, "_start_dashboard_server", lambda: None)

    # Avoid argparse picking up pytest args
    import sys as _sys

    monkeypatch.setattr(_sys, "argv", ["collab"])  # safe minimal argv

    import pytest

    with pytest.raises(SystemExit):
        mod.main()
