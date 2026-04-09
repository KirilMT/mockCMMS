"""Additional LockClient tests (migrated from test_lock_client_more.py).

This module consolidates smaller 'more' tests into a clearer named file.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def _always_alive(_p):
    return True


def _none_cmd(_p):
    return None


def _locked_by_bob(_fp):
    return {"is_locked": True, "locked_by": "bob"}


def _load_lock_client_module():
    proj_root = Path(__file__).resolve().parents[3]
    module_path = proj_root / ".collab" / "core" / "lock_client.py"
    spec = importlib.util.spec_from_file_location(
        "collab.core.lock_client", str(module_path)
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


def _load_watcher_module():
    proj_root = Path(__file__).resolve().parents[3]
    module_path = proj_root / ".collab" / "pycharm" / "live_locks_watcher.py"
    spec = importlib.util.spec_from_file_location(
        "collab.pycharm.live_locks_watcher", str(module_path)
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


def test_retry_on_network_error_succeeds_after_retries():
    mod = _load_lock_client_module()

    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise Exception("Connection timeout")
        return "ok"

    got = mod._retry_on_network_error(flaky)
    assert got == "ok"


def test__parse_response_various_shapes():
    mod = _load_lock_client_module()

    class ResObj:
        def __init__(self):
            self.status_code = 200
            self.data = [{"status": "ok"}]
            self.error = None

    status, data, error = mod.LockClient._parse_response(ResObj())
    assert status == 200 and isinstance(data, list)

    d = {"status": 201, "data": [1, 2], "error": None}
    status2, data2, error2 = mod.LockClient._parse_response(d)
    assert status2 == 201 and data2 == [1, 2]


def test_acquire_and_release_ephemeral(tmp_path, monkeypatch):
    mod = _load_lock_client_module()

    # Create a temp file to acquire
    f = tmp_path / "file.txt"
    f.write_text("x")

    client = object.__new__(mod.LockClient)
    # Simulate ephemeral developer
    client.developer_id = "test_dev_123"
    client._is_ephemeral = True

    ok, token = mod.LockClient.acquire(client, str(f))
    assert ok and token.startswith("ephemeral-")

    ok_rel, msg = mod.LockClient.release(client, str(f))
    assert ok_rel and "ephemeral" in msg


def test_force_release_permission_denied(monkeypatch):
    mod = _load_lock_client_module()
    client = object.__new__(mod.LockClient)
    client._is_admin = False
    client.developer_id = "alice"

    # Simulate lock owned by bob
    monkeypatch.setattr(mod.LockClient, "get_lock_status", staticmethod(_locked_by_bob))
    ok, msg = mod.LockClient.force_release(client, "some/file")
    assert not ok and "Permission denied" in msg


def test_daemon_start_uses_pid_metadata(monkeypatch, tmp_path, capsys):
    mod = _load_lock_client_module()
    pid_file = tmp_path / ".daemon.pid"
    pid_file.write_text(json.dumps({"pid": 9999, "entrypoint": "watcher"}))
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))

    # Simulate read_pid and process alive
    monkeypatch.setattr(mod.LockClient, "_read_pid", staticmethod(lambda: 9999))
    monkeypatch.setattr(
        mod.LockClient, "_is_process_alive", staticmethod(_always_alive)
    )

    client = object.__new__(mod.LockClient)
    mod.LockClient.daemon_start(client)
    captured = capsys.readouterr()
    assert "Watcher already running" in captured.out


def test_daemon_start_legacy_plain_pid_matches_current(monkeypatch, tmp_path, capsys):
    mod = _load_lock_client_module()
    pid_file = tmp_path / ".daemon.pid"
    pid_file.write_text(str(os.getpid()))
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))

    monkeypatch.setattr(mod.LockClient, "_read_pid", staticmethod(lambda: os.getpid()))
    monkeypatch.setattr(
        mod.LockClient, "_is_process_alive", staticmethod(_always_alive)
    )

    client = object.__new__(mod.LockClient)
    mod.LockClient.daemon_start(client)
    captured = capsys.readouterr()
    assert "Watcher already running" in captured.out


def test_prepare_dashboard_server_success_additional(tmp_path, monkeypatch):
    mod = _load_lock_client_module()
    # Create a fake dashboard index.html under a temp _COLLAB_ROOT
    tmp_root = tmp_path / "collab_root"
    (tmp_root / "dashboard").mkdir(parents=True)
    html = tmp_root / "dashboard" / "index.html"
    html.write_text("<html>ok</html>")

    monkeypatch.setattr(mod, "_COLLAB_ROOT", str(tmp_root))
    client = object.__new__(mod.LockClient)
    client.developer_id = "u"
    url, tmpname = mod.LockClient._prepare_dashboard_server(client)
    assert url is not None and tmpname and os.path.exists(tmpname)
    # cleanup tmp file
    try:
        os.unlink(tmpname)
    except Exception:
        pass


def test_read_int_pid_file(monkeypatch, tmp_path):
    mod = _load_lock_client_module()
    pid_file = tmp_path / ".daemon.pid"
    pid_file.write_text("12345")
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))
    pid = mod.LockClient._read_pid()
    assert pid == 12345


def test_read_json_pid_file(monkeypatch, tmp_path):
    mod = _load_lock_client_module()
    pid_file = tmp_path / ".daemon.pid"
    pid_file.write_text(
        json.dumps({"pid": 4242, "cmd": "python live_locks_watcher.py"})
    )
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))
    pid = mod.LockClient._read_pid()
    assert pid == 4242


def test_read_malformed_pid_file(monkeypatch, tmp_path):
    mod = _load_lock_client_module()
    pid_file = tmp_path / ".daemon.pid"
    pid_file.write_text("not-a-pid")
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))
    pid = mod.LockClient._read_pid()
    assert pid is None


def test_write_pid_metadata(monkeypatch, tmp_path):
    mod = _load_watcher_module()
    pid_file = tmp_path / ".daemon.pid"
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))
    # Call the helper to write metadata
    mod._write_pid_file(5555)
    raw = pid_file.read_text(encoding="utf-8")
    obj = json.loads(raw)
    assert obj["pid"] == 5555
    assert "started_at" in obj
    assert "cmdline" in obj


def test_daemon_status_prefers_entrypoint(tmp_path, monkeypatch):
    # Start a dummy background python process to ensure the PID is alive.
    p = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        pid_file = tmp_path / ".daemon.pid"

        # reuse a minimal writer to create the PID file used by the CLI
        def _write_meta(pid: int, entrypoint: str, cmdline: str) -> None:
            meta = {
                "pid": pid,
                "started_at": (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
                "entrypoint": entrypoint,
                "cmdline": cmdline,
                "cwd": os.getcwd(),
            }
            pid_file.write_text(json.dumps(meta), encoding="utf-8")

        _write_meta(p.pid, "python lock_client.py", f"{sys.executable} -c dummy_sleep")

        # Run the CLI status command with dummy SUPABASE env to avoid credential checks
        env = dict(os.environ)
        env["SUPABASE_URL"] = env.get("SUPABASE_URL", "http://example.invalid")
        env["SUPABASE_ANON_KEY"] = env.get("SUPABASE_ANON_KEY", "anon")
        env["PYTHONPATH"] = str(Path(__file__).resolve().parents[3])
        env["COLLAB_TEST_MODE"] = "1"
        env["COLLAB_PID_FILE"] = str(pid_file)

        res = subprocess.run(
            [sys.executable, "collab.py", "daemon-status"],
            capture_output=True,
            text=True,
            env=env,
        )
        out = res.stdout + res.stderr
        assert f"Lock watcher is RUNNING (PID: {p.pid})" in out
        assert "python lock_client.py" in out
    finally:
        try:
            p.terminate()
        except Exception:
            pass
        try:
            if pid_file.exists():
                pid_file.unlink()
        except Exception:
            pass


def test_daemon_status_removes_stale_pid(monkeypatch, tmp_path):
    mod = _load_lock_client_module()
    pid_file = tmp_path / ".daemon.pid"
    pid_file.write_text("99999")
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))
    monkeypatch.setenv("COLLAB_TEST_MODE", "0")

    # Simulate that the PID exists but belongs to another process
    monkeypatch.setattr(mod.LockClient, "_read_pid", staticmethod(lambda: 99999))
    monkeypatch.setattr(
        mod.LockClient, "_is_process_alive", staticmethod(lambda p: True)
    )
    monkeypatch.setattr(
        mod.LockClient,
        "_get_cmdline_for_pid",
        staticmethod(lambda p: "C:\\Windows\\System32\\not_the_watcher.exe"),
    )

    # Create instance without running __init__
    client = object.__new__(mod.LockClient)
    # Call daemon_status(), expect False and PID file removed
    ok = mod.LockClient.daemon_status(client)
    assert ok is False
    assert not os.path.exists(str(pid_file))


def test_cmdline_matching():
    mod = _load_lock_client_module()
    assert mod.LockClient._cmdline_matches_watcher(
        "/usr/bin/python .collab/pycharm/live_locks_watcher.py"
    )
    assert mod.LockClient._cmdline_matches_watcher(
        "python lock_client.py watch --daemon"
    )
    assert not mod.LockClient._cmdline_matches_watcher(
        "C:\\Windows\\System32\\not_the_watcher.exe"
    )


def test_safe_now_normal():
    mod = _load_lock_client_module()
    now = mod._safe_now()
    from datetime import datetime as _real_dt

    assert isinstance(now, _real_dt)


def test_safe_now_classlevel_now_called_when_instance_now_raises(monkeypatch):
    mod = _load_lock_client_module()
    from datetime import datetime as _real_dt

    # Create a class with a class-level now that returns a known datetime
    class WithClassNow:
        @staticmethod
        def now():
            return _real_dt(2000, 1, 2, 3, 4, 5)

    # Create an instance whose instance-level now will raise TypeError
    inst = object.__new__(WithClassNow)
    inst.now = lambda: (_ for _ in ()).throw(TypeError("bound error"))

    monkeypatch.setattr(mod, "datetime", inst)
    got = mod._safe_now()
    assert isinstance(got, _real_dt)
    assert got.year == 2000 and got.month == 1 and got.day == 2


def test_safe_now_falls_back_to_stdlib_when_nothing_usable(monkeypatch):
    mod = _load_lock_client_module()
    from datetime import datetime as _real_dt

    class NoNow:
        pass

    inst = object.__new__(NoNow)
    inst.now = lambda: (_ for _ in ()).throw(TypeError("boom"))

    monkeypatch.setattr(mod, "datetime", inst)
    got = mod._safe_now()
    # Should be a datetime from stdlib (close to now) — just verify type
    assert isinstance(got, _real_dt)


# -------------------------- Restored: PID & cmdline helpers ------------------


def test_read_pid_empty_file(monkeypatch, tmp_path):
    mod = _load_lock_client_module()
    pid_file = tmp_path / ".daemon.pid"
    pid_file.write_text("")
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))
    assert mod.LockClient._read_pid() is None


def test_read_pid_invalid_json(monkeypatch, tmp_path):
    mod = _load_lock_client_module()
    pid_file = tmp_path / ".daemon.pid"
    pid_file.write_text("{not: json}")
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))
    assert mod.LockClient._read_pid() is None


def test_read_pid_raises_oserror(monkeypatch, tmp_path):
    mod = _load_lock_client_module()
    pid_file = tmp_path / ".daemon.pid"
    pid_file.write_text("4242")
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))

    def _bad_open(*a, **k):
        raise OSError("boom")

    monkeypatch.setattr("builtins.open", _bad_open)
    assert mod.LockClient._read_pid() is None


def test_get_cmdline_with_and_without_psutil(monkeypatch):
    mod = _load_lock_client_module()

    class DummyProc:
        def __init__(self, pid):
            pass

        def cmdline(self):
            return ["python", "live_locks_watcher.py"]

    sys.modules["psutil"] = type(
        "m", (), {"Process": DummyProc, "pid_exists": lambda p: True}
    )
    try:
        got = mod.LockClient._get_cmdline_for_pid(1234)
        assert "live_locks_watcher.py" in got
    finally:
        del sys.modules["psutil"]

    class BadProc:
        def __init__(self, pid):
            raise Exception("no access")

    sys.modules["psutil"] = type("m", (), {"Process": BadProc})
    try:
        assert mod.LockClient._get_cmdline_for_pid(1234) is None
    finally:
        del sys.modules["psutil"]


def test_cmdline_string_and_empty():
    mod = _load_lock_client_module()

    class StrProc:
        def __init__(self, pid):
            pass

        def cmdline(self):
            return "python lock_client.py watch"

    sys.modules["psutil"] = type("m", (), {"Process": StrProc})
    try:
        got = mod.LockClient._get_cmdline_for_pid(1)
        assert "lock_client.py watch" in got
    finally:
        del sys.modules["psutil"]

    assert not mod.LockClient._cmdline_matches_watcher("")


# -------------------------- Restored: ephemeral & helpers -------------------


def test_ephemeral_developer_short_circuits_acquire_and_release(tmp_path, monkeypatch):
    mod = _load_lock_client_module()
    test_file = tmp_path / "src" / "file.txt"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("hello")

    monkeypatch.setenv("SUPABASE_URL", "https://example.invalid")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon")
    monkeypatch.setattr(mod, "_get_create_client", lambda: (lambda url, key: object()))

    lc = mod.LockClient(developer_id="test_dev_ci_123")
    assert getattr(lc, "_is_ephemeral", False) is True

    ok, token = lc.acquire(str(test_file))
    assert ok is True
    assert isinstance(token, str) and token.startswith("ephemeral-")

    ok2, msg = lc.release(str(test_file))
    assert ok2 is True
    assert "ephemeral" in msg


def test_normalize_file_path_handles_exceptions(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.invalid")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon")
    mod = _load_lock_client_module()
    monkeypatch.setattr(mod, "_get_create_client", lambda: (lambda url, key: object()))
    lc = mod.LockClient(developer_id="tester")

    def raising_isabs(p):
        raise RuntimeError("boom")

    import os as _os

    monkeypatch.setattr(_os.path, "isabs", raising_isabs)
    out = lc._normalize_file_path(r"C:\some\path\file.py")
    assert "\\" not in out


def test_non_str_developer_id_sets_ephemeral_false(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.invalid")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon")
    mod = _load_lock_client_module()
    monkeypatch.setattr(mod, "_get_create_client", lambda: (lambda url, key: object()))
    lc = mod.LockClient(developer_id=12345)  # type: ignore[arg-type]
    assert getattr(lc, "_is_ephemeral", None) is False


# Restored archived-only test: test_daemon_status_running_preserves_pid
def test_daemon_status_running_preserves_pid(monkeypatch, tmp_path):
    """Ensure daemon_status returns True and preserves PID when watcher is running."""
    mod = _load_lock_client_module()
    pid_file = tmp_path / ".daemon.pid"
    pid_file.write_text("4242")
    monkeypatch.setattr(mod, "PID_FILE", str(pid_file))

    # Simulate watchers
    monkeypatch.setattr(mod.LockClient, "_read_pid", staticmethod(lambda: 4242))

    def _alive(p):
        return True

    monkeypatch.setattr(mod.LockClient, "_is_process_alive", staticmethod(_alive))
    monkeypatch.setattr(
        mod.LockClient,
        "_get_cmdline_for_pid",
        staticmethod(lambda p: "python live_locks_watcher.py"),
    )

    client = object.__new__(mod.LockClient)
    ok = mod.LockClient.daemon_status(client)
    assert ok is True
    assert pid_file.exists()


# New targeted tests to cover platform-specific and fallback branches in lock_client
def test_get_current_branch_win32(monkeypatch):
    """Ensure _get_current_branch uses the Windows code path when platform is win32."""
    mod = _load_lock_client_module()
    monkeypatch.setattr(sys, "platform", "win32")

    def fake_check_output(cmd, *a, **k):
        return b"feature/win-branch\n"

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)
    got = mod.LockClient._get_current_branch()
    assert got == "feature/win-branch"


def test_daemon_start_cmdline_unavailable_assumes_running(
    monkeypatch, tmp_path, capsys
):
    """When cmdline cannot be determined for a live PID, daemon_start should assume the
    watcher is running and return without starting a new process."""
    mod = _load_lock_client_module()
    client = object.__new__(mod.LockClient)

    # Simulate a PID that exists but is not this process
    # and whose cmdline is unavailable
    monkeypatch.setattr(mod.LockClient, "_read_pid", staticmethod(lambda: 42424))
    monkeypatch.setattr(
        mod.LockClient, "_is_process_alive", staticmethod(lambda p: True)
    )
    monkeypatch.setattr(
        mod.LockClient, "_get_cmdline_for_pid", staticmethod(lambda p: None)
    )

    # Ensure PID_FILE does not exist to trigger had_metadata=False path
    try:
        if os.path.exists(mod.PID_FILE):
            os.unlink(mod.PID_FILE)
    except Exception:
        pass

    # Call daemon_start and capture stdout
    client.daemon_start()
    captured = capsys.readouterr()
    assert "Watcher already running (PID" in captured.out


def test_get_current_branch_non_win_error(monkeypatch):
    """When git command fails, _get_current_branch should return None on LockClient."""
    mod = _load_lock_client_module()
    monkeypatch.setattr(sys, "platform", "linux")

    def fail_check_output(cmd, *a, **k):
        raise subprocess.CalledProcessError(2, cmd)

    monkeypatch.setattr(subprocess, "check_output", fail_check_output)
    got = mod.LockClient._get_current_branch()
    assert got is None


def test_run_git_status_unix(monkeypatch):
    mod = _load_lock_client_module()
    monkeypatch.setattr(sys, "platform", "linux")

    def fake_check_output(args, *a, **k):
        return b" M src/foo.py\n"

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)
    out = mod.LockClient._run_git_status()
    assert "src/foo.py" in out
