import json
import os
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import mock_open, patch

import pytest
import responses

from src.services.lock_client import LockClient
from src.services.lock_client import main as cli_main


class TestLockClientExtra:
    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch):
        """Mock environment variables for all tests."""
        monkeypatch.setenv("USE_SUPABASE", "0")

    @pytest.fixture
    def client(self):
        """Create a client with fixed developer_id for testing."""
        return LockClient(developer_id="test_user")

    def test_get_pid_exists(self, client):
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="1234")):
                assert client._get_pid() == 1234

    def test_get_pid_not_exists(self, client):
        with patch("os.path.exists", return_value=False):
            assert client._get_pid() is None

    def test_get_pid_exception(self, client):
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", side_effect=Exception("error")):
                assert client._get_pid() is None

    def test_is_running_win32(self, client, monkeypatch):
        monkeypatch.setattr(sys, "platform", "win32")
        with patch("subprocess.check_output", return_value="1234"):
            assert client._is_running(1234) is True

        with patch("subprocess.check_output", side_effect=Exception("error")):
            assert client._is_running(1234) is False

    def test_is_running_unix(self, client, monkeypatch):
        monkeypatch.setattr(sys, "platform", "linux")
        with patch("os.kill", return_value=None):
            assert client._is_running(1234) is True

        with patch("os.kill", side_effect=OSError()):
            assert client._is_running(1234) is False

    def test_daemon_status_running(self, client):
        with patch.object(client, "_get_pid", return_value=1234):
            with patch.object(client, "_is_running", return_value=True):
                assert client.daemon_status() is True

    def test_daemon_status_not_running(self, client):
        with patch.object(client, "_get_pid", return_value=1234):
            with patch.object(client, "_is_running", return_value=False):
                with patch("os.path.exists", return_value=True):
                    with patch("os.remove") as mock_remove:
                        assert client.daemon_status() is False
                        mock_remove.assert_called_once_with(client.pid_file)

    def test_daemon_stop_running_win32(self, client, monkeypatch):
        monkeypatch.setattr(sys, "platform", "win32")
        with patch.object(client, "_get_pid", return_value=1234):
            with patch.object(client, "_is_running", return_value=True):
                with patch("subprocess.run") as mock_run:
                    with patch("os.path.exists", return_value=True):
                        with patch("os.remove") as mock_remove:
                            client.daemon_stop()
                            mock_run.assert_called_once()
                            mock_remove.assert_called_once_with(client.pid_file)

    def test_daemon_stop_running_unix(self, client, monkeypatch):
        monkeypatch.setattr(sys, "platform", "linux")
        with patch.object(client, "_get_pid", return_value=1234):
            with patch.object(client, "_is_running", return_value=True):
                with patch("os.kill") as mock_kill:
                    with patch("os.path.exists", return_value=True):
                        with patch("os.remove") as mock_remove:
                            client.daemon_stop()
                            mock_kill.assert_called_once_with(1234, 9)
                            mock_remove.assert_called_once_with(client.pid_file)

    def test_daemon_stop_not_running(self, client, capsys):
        with patch.object(client, "_get_pid", return_value=None):
            client.daemon_stop()
            assert "No running watcher found" in capsys.readouterr().out

    def test_daemon_start_already_running(self, client, capsys):
        with patch.object(client, "_get_pid", return_value=1234):
            with patch.object(client, "_is_running", return_value=True):
                client.daemon_start()
                assert "Watcher already running" in capsys.readouterr().out

    def test_daemon_start_win32(self, client, monkeypatch):
        monkeypatch.setattr(sys, "platform", "win32")
        with patch.object(client, "_get_pid", return_value=None):
            with patch("os.path.exists", return_value=True):
                with patch("subprocess.Popen") as mock_popen:
                    mock_popen.return_value.pid = 5678
                    with patch("builtins.open", mock_open()) as mock_file:
                        client.daemon_start()
                        mock_popen.assert_called_once()
                        mock_file().write.assert_called_with("5678")

    def test_daemon_start_unix(self, client, monkeypatch):
        monkeypatch.setattr(sys, "platform", "linux")
        with patch.object(client, "_get_pid", return_value=None):
            with patch("subprocess.Popen") as mock_popen:
                mock_popen.return_value.pid = 5678
                with patch("builtins.open", mock_open()) as mock_file:
                    client.daemon_start()
                    mock_popen.assert_called_once()
                    mock_file().write.assert_called_with("5678")

    def test_get_git_username_email_fallback(self, client):
        def mock_output(cmd, **kwargs):
            if cmd == ["git", "config", "user.name"]:
                return b"\n"
            if cmd == ["git", "config", "user.email"]:
                return b"alice@example.com\n"
            return b""

        with patch("subprocess.check_output", side_effect=mock_output):
            assert client._get_git_username() == "alice"

    def test_get_git_username_env_fallback(self, client, monkeypatch):
        monkeypatch.setenv("USERNAME", "env_user")
        with patch("subprocess.check_output", side_effect=Exception("error")):
            assert client._get_git_username() == "env_user"

    @responses.activate
    def test_get_full_gist_data(self, client):
        url = "https://api.github.com/gists/fake_gist_id"
        locks = {"a.py": {"file_path": "a.py"}}
        history = [{"file_path": "b.py", "outcome": "released"}]
        responses.add(
            responses.GET,
            url,
            json={
                "files": {
                    "locks.json": {"content": json.dumps(locks)},
                    "history.json": {"content": json.dumps(history)},
                }
            },
            status=200,
            headers={"ETag": "etag1"},
        )
        locks_res, history_res, etag_res = client._get_full_gist_data()
        assert locks_res == locks
        assert history_res == history
        assert etag_res == "etag1"

    @responses.activate
    def test_update_full_gist_data_success(self, client):
        url = "https://api.github.com/gists/fake_gist_id"
        responses.add(responses.PATCH, url, status=200)
        assert client._update_full_gist_data({}, [], "etag1") is True

    @responses.activate
    def test_update_full_gist_data_412(self, client):
        url = "https://api.github.com/gists/fake_gist_id"
        responses.add(responses.PATCH, url, status=412)
        assert client._update_full_gist_data({}, [], "etag1") is False

    @responses.activate
    def test_acquire_multiple_retry_on_412(self, client):
        url = "https://api.github.com/gists/fake_gist_id"
        responses.add(responses.GET, url, json={"files": {}}, status=200)
        responses.add(responses.PATCH, url, status=412)
        responses.add(responses.PATCH, url, status=200)

        with patch("time.sleep"):
            success, affected, msg = client.acquire_multiple(["a.py"])
        assert success is True

    @responses.activate
    def test_acquire_multiple_no_locks_needed(self, client):
        url = "https://api.github.com/gists/fake_gist_id"
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        locks = {"a.py": {"developer_id": "test_user", "expires_at": future}}
        responses.add(
            responses.GET,
            url,
            json={"files": {"locks.json": {"content": json.dumps(locks)}}},
            status=200,
        )

        success, affected, msg = client.acquire_multiple(["a.py"])
        assert success is True
        assert affected == []
        assert "No new locks needed" in msg

    @responses.activate
    def test_release_multiple_retry_on_412(self, client):
        url = "https://api.github.com/gists/fake_gist_id"
        locks = {"a.py": {"developer_id": "test_user"}}
        responses.add(
            responses.GET,
            url,
            json={"files": {"locks.json": {"content": json.dumps(locks)}}},
            status=200,
        )
        responses.add(responses.PATCH, url, status=412)
        responses.add(responses.PATCH, url, status=200)

        with patch("time.sleep"):
            success, count, msg = client.release_multiple(["a.py"])
        assert success is True
        assert count == 1

    @responses.activate
    def test_release_multiple_api_error(self, client):
        url = "https://api.github.com/gists/fake_gist_id"
        responses.add(responses.GET, url, status=500)
        with patch("time.sleep"):
            success, count, msg = client.release_multiple(["a.py"])
        assert success is False
        assert "API Error" in msg

    def test_status_file_not_found(self, client):
        with patch("os.path.exists", return_value=False):
            res = client.status("missing.py")
            assert res["is_locked"] is False
            assert "File not found locally" in res["error"]

    @responses.activate
    def test_status_not_locked(self, client):
        url = "https://api.github.com/gists/fake_gist_id"
        responses.add(responses.GET, url, json={"files": {}}, status=200)
        with patch("os.path.exists", return_value=True):
            res = client.status("clean.py")
            assert res["is_locked"] is False
            assert res["can_edit"] is True

    def test_open_dashboard_exists(self, client):
        with patch("os.path.exists", return_value=True):
            with patch("webbrowser.open") as mock_open_browser:
                client.open_dashboard()
                mock_open_browser.assert_called_once()

    def test_open_dashboard_not_exists(self, client, capsys):
        with patch("os.path.exists", return_value=False):
            client.open_dashboard()
            assert "Error: Dashboard file not found" in capsys.readouterr().out

    @responses.activate
    def test_reconcile_success(self, client):
        with patch.object(client, "_run_git_status", return_value="M  a.py\nM  b.py"):
            active_locks = [
                {"file_path": "a.py", "developer_id": "test_user"},
                {"file_path": "c.py", "developer_id": "test_user"},
            ]
            with patch.object(client, "active_locks", return_value=active_locks):
                with patch.object(client, "release_multiple") as mock_release:
                    with patch.object(client, "acquire_multiple") as mock_acquire:
                        client.reconcile()
                        # b.py is missing from gist but in git
                        mock_acquire.assert_called_once()
                        # c.py is in gist but missing from git
                        mock_release.assert_called_once_with(["c.py"])

    def test_reconcile_git_error(self, client):
        with patch.object(
            client, "_run_git_status", side_effect=Exception("git error")
        ):
            assert client.reconcile() == set()

    def test_reconcile_gist_error(self, client):
        with patch.object(client, "_run_git_status", return_value="M  a.py"):
            with patch.object(
                client, "active_locks", side_effect=Exception("gist error")
            ):
                assert client.reconcile() == {"a.py"}

    def test_run_git_status_win32(self, client, monkeypatch):
        monkeypatch.setattr(sys, "platform", "win32")
        with patch("subprocess.check_output", return_value=b"M  file.py\n"):
            assert client._run_git_status() == "M  file.py"

    def test_run_git_status_unix(self, client, monkeypatch):
        monkeypatch.setattr(sys, "platform", "linux")
        with patch("subprocess.check_output", return_value=b"M  file.py\n"):
            assert client._run_git_status() == "M  file.py"

    @responses.activate
    def test_cli_acquire_batch_error(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "platform", "linux")
        url = "https://api.github.com/gists/fake_gist_id"
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        locks = {"a.py": {"developer_id": "bob", "expires_at": future}}
        responses.add(
            responses.GET,
            url,
            json={"files": {"locks.json": {"content": json.dumps(locks)}}},
            status=200,
        )

        monkeypatch.setattr(sys, "argv", ["lock_client.py", "acquire-batch", "a.py"])
        with pytest.raises(SystemExit) as e:
            cli_main()
        assert e.value.code == 1
        assert "ERROR:" in capsys.readouterr().out

    def test_cli_daemon_commands(self, monkeypatch):
        with patch("src.services.lock_client.LockClient.daemon_start") as m_start:
            monkeypatch.setattr(sys, "argv", ["lock_client.py", "daemon-start"])
            cli_main()
            m_start.assert_called_once()

        with patch("src.services.lock_client.LockClient.daemon_stop") as m_stop:
            monkeypatch.setattr(sys, "argv", ["lock_client.py", "daemon-stop"])
            cli_main()
            m_stop.assert_called_once()

        with patch("src.services.lock_client.LockClient.daemon_status") as m_status:
            monkeypatch.setattr(sys, "argv", ["lock_client.py", "daemon-status"])
            cli_main()
            m_status.assert_called_once()

    def test_cli_dashboard_reconcile(self, monkeypatch):
        with patch("src.services.lock_client.LockClient.open_dashboard") as m_dash:
            monkeypatch.setattr(sys, "argv", ["lock_client.py", "dashboard"])
            cli_main()
            m_dash.assert_called_once()

        with patch("src.services.lock_client.LockClient.reconcile") as m_rec:
            monkeypatch.setattr(sys, "argv", ["lock_client.py", "reconcile"])
            cli_main()
            m_rec.assert_called_once()

    def test_watch_logic(self, client):
        # Mocking the loop to run once and then stop via KeyboardInterrupt
        with patch.object(client, "_run_git_status") as mock_git:
            mock_git.side_effect = ["M  new.py", KeyboardInterrupt()]
            with patch.object(client, "reconcile", return_value=set()):
                with patch.object(
                    client,
                    "acquire_multiple",
                    return_value=(True, ["new.py"], "Success"),
                ):
                    with patch.object(
                        client, "release_multiple", return_value=(True, 0, "Success")
                    ):
                        with patch("time.sleep"):
                            with patch("builtins.open", mock_open()):
                                with patch("os.path.exists", return_value=True):
                                    with patch.object(
                                        client, "_get_pid", return_value=os.getpid()
                                    ):
                                        with patch("os.remove"):
                                            client.watch(interval=0, timeout_mins=0)
                                            # It should have attempted to acquire new.py
                                            client.acquire_multiple.assert_called()

    def test_watch_timeout(self, client, capsys):
        with patch.object(client, "_run_git_status", return_value=""):
            with patch.object(client, "reconcile", return_value=set()):
                # Simulate timeout
                with patch("src.services.lock_client.datetime") as mock_dt:
                    start = datetime(2026, 3, 22, 10, 0, 0, tzinfo=timezone.utc)
                    # Use a function to return times and avoid StopIteration
                    times = [
                        start,  # last_change_time
                        start,  # last_reconcile_time
                        start,  # active_locks in reconcile
                        start,  # sync_delta
                        start + timedelta(hours=2),  # idle_delta -> trigger timeout
                    ]

                    def side_effect(*args, **kwargs):
                        if times:
                            return times.pop(0)
                        return start + timedelta(hours=2)

                    mock_dt.now.side_effect = side_effect
                    mock_dt.fromisoformat = datetime.fromisoformat
                    mock_dt.timedelta = timedelta

                    with patch("time.sleep", side_effect=[None, KeyboardInterrupt()]):
                        with patch("builtins.open", mock_open()):
                            client.watch(interval=0, timeout_mins=1)
                            out = capsys.readouterr().out
                            assert "Watcher timed out" in out

    def test_daemon_start_win32_fallback(self, client, monkeypatch):
        monkeypatch.setattr(sys, "platform", "win32")
        with patch.object(client, "_get_pid", return_value=None):

            def mock_exists(path):
                if "pythonw.exe" in path:
                    return False
                return True

            with patch("os.path.exists", side_effect=mock_exists):
                with patch("subprocess.Popen") as mock_popen:
                    mock_popen.return_value.pid = 5678
                    with patch("builtins.open", mock_open()):
                        client.daemon_start()
                        assert mock_popen.call_args[0][0][0] == "pythonw"

    @responses.activate
    def test_acquire_multiple_api_error_retries(self, client):
        url = "https://api.github.com/gists/fake_gist_id"
        responses.add(responses.GET, url, status=500)
        with patch("time.sleep"):
            success, affected, msg = client.acquire_multiple(["a.py"])
            assert success is False
            assert "API Error" in msg

    @responses.activate
    def test_acquire_multiple_conflict_final(self, client):
        url = "https://api.github.com/gists/fake_gist_id"
        responses.add(responses.GET, url, json={"files": {}}, status=200)
        responses.add(responses.PATCH, url, status=412)
        responses.add(responses.PATCH, url, status=412)
        responses.add(responses.PATCH, url, status=412)
        with patch("time.sleep"):
            success, affected, msg = client.acquire_multiple(["a.py"])
            assert success is False
            assert "Concurrent update conflict" in msg

    @responses.activate
    def test_release_multiple_conflict_final(self, client):
        url = "https://api.github.com/gists/fake_gist_id"
        locks = {"a.py": {"developer_id": "test_user"}}
        responses.add(
            responses.GET,
            url,
            json={"files": {"locks.json": {"content": json.dumps(locks)}}},
            status=200,
        )
        responses.add(responses.PATCH, url, status=412)
        responses.add(responses.PATCH, url, status=412)
        responses.add(responses.PATCH, url, status=412)
        with patch("time.sleep"):
            success, count, msg = client.release_multiple(["a.py"])
            assert success is False
            assert "Concurrent update conflict" in msg

    def test_watch_released_and_conflict(self, client, capsys):
        with patch.object(client, "_run_git_status") as mock_git:
            mock_git.side_effect = ["M  a.py", "", "M  b.py", KeyboardInterrupt()]
            with patch.object(client, "reconcile", return_value=set()):
                with patch.object(client, "acquire_multiple") as mock_acq:
                    mock_acq.side_effect = [
                        (True, ["a.py"], "Success"),
                        (False, ["b.py"], "Conflict!"),
                    ]
                    with patch.object(
                        client, "release_multiple", return_value=(True, 1, "Success")
                    ):
                        with patch("time.sleep"):
                            with patch("builtins.open", mock_open()):
                                client.watch(interval=0, timeout_mins=0)
                                out = capsys.readouterr().out
                                assert "Locked: ['a.py']" in out
                                assert "Released: 1 file(s)" in out
                                assert "CONFLICT ALERT: Conflict!" in out

    def test_watch_exception_loop(self, client, capsys):
        with patch.object(client, "_run_git_status") as mock_git:
            mock_git.side_effect = [Exception("loop error"), KeyboardInterrupt()]
            with patch.object(client, "reconcile", return_value=set()):
                with patch("time.sleep"):
                    with patch("builtins.open", mock_open()):
                        client.watch(interval=0, timeout_mins=0)
                        assert "Error in watcher: loop error" in capsys.readouterr().out

    def test_cli_watch(self, monkeypatch):
        with patch("src.services.lock_client.LockClient.watch") as m_watch:
            monkeypatch.setattr(
                sys,
                "argv",
                ["lock_client.py", "watch", "--interval", "1", "--timeout", "10"],
            )
            cli_main()
            m_watch.assert_called_once_with(interval=1, timeout_mins=10)
