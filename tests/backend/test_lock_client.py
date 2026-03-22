import json
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
import responses

from src.services.lock_client import LockClient


class TestLockClient:
    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch):
        """Mock environment variables for all tests."""
        monkeypatch.setenv("GITHUB_TOKEN", "fake_token")
        monkeypatch.setenv("LOCK_GIST_ID", "fake_gist_id")

    @pytest.fixture
    def client(self):
        """Create a client with fixed developer_id for testing."""
        return LockClient(developer_id="test_user")

    def test_init_missing_token(self, monkeypatch):
        """Test initialization fails without token."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        with pytest.raises(ValueError, match="Missing GITHUB_TOKEN"):
            LockClient()

    def test_init_missing_gist(self, monkeypatch):
        """Test initialization fails without gist id."""
        monkeypatch.setenv("LOCK_GIST_ID", "your_gist_id_here")
        with pytest.raises(ValueError, match="Missing LOCK_GIST_ID"):
            LockClient()

    def test_init_default_developer(self, monkeypatch):
        """Test default developer_id initialization from git user."""

        def mock_git_user(*args):
            return "alice_git"

        monkeypatch.setattr(
            "src.services.lock_client.LockClient._get_git_username", mock_git_user
        )
        c = LockClient(developer_id=None)
        assert c.developer_id == "alice_git"

    def test_get_git_user_fallback(self, monkeypatch):
        """Test fallback when git command fails."""

        def mock_error(*args, **kwargs):
            raise Exception("Subprocess Error")

        monkeypatch.setattr("subprocess.check_output", mock_error)
        monkeypatch.setenv("USERNAME", "unknown_user")
        c = LockClient(developer_id=None)
        assert c.developer_id == "unknown_user"

    def test_get_current_branch(self, monkeypatch):
        """Test branch detection."""

        def mock_branch(cmd, **kwargs):
            if cmd == ["git", "branch", "--show-current"]:
                return b"main\n"
            return b""

        monkeypatch.setattr("subprocess.check_output", mock_branch)
        c = LockClient()
        assert c._get_current_branch() == "main"

    def test_get_current_branch_error(self, monkeypatch):
        """Test branch detection error fallback."""

        def mock_error(*args, **kwargs):
            raise Exception("Git Error")

        monkeypatch.setattr("subprocess.check_output", mock_error)
        c = LockClient()
        assert c._get_current_branch() is None

    def test_utcnow_iso_coverage(self, client):
        """Cover the helper method explicitly."""
        iso = client._utcnow_iso()
        assert isinstance(iso, str)
        assert "T" in iso

    @responses.activate
    def test_get_gist_data_no_file(self, client):
        """Test fetching gist data when file is missing."""
        responses.add(
            responses.GET,
            "https://api.github.com/gists/fake_gist_id",
            json={"files": {}},
            status=200,
        )
        locks, _ = client._get_gist_data()
        assert locks == {}

    @responses.activate
    def test_get_gist_data_empty_content(self, client):
        """Test fetching gist data when file content is empty string."""
        responses.add(
            responses.GET,
            "https://api.github.com/gists/fake_gist_id",
            json={"files": {"locks.json": {"content": ""}}},
            status=200,
        )
        locks, _ = client._get_gist_data()
        assert locks == {}

    @responses.activate
    def test_update_gist_data_412(self, client):
        """Test optimistic locking failure (412)."""
        responses.add(
            responses.PATCH, "https://api.github.com/gists/fake_gist_id", status=412
        )
        assert client._update_gist_data({}, "old_etag") is False

    @responses.activate
    def test_acquire_success(self, client):
        """Test acquiring a lock via Gist."""
        # Mock GET Gist (empty locks)
        responses.add(
            responses.GET,
            "https://api.github.com/gists/fake_gist_id",
            json={"files": {"locks.json": {"content": "{}"}}},
            status=200,
            headers={"ETag": "etag1"},
        )
        # Mock PATCH Gist
        responses.add(
            responses.PATCH,
            "https://api.github.com/gists/fake_gist_id",
            json={"status": "success"},
            status=200,
        )

        success, res = client.acquire("test.py", reason="editing")
        assert success is True
        assert len(res) > 20  # UUID token

    @responses.activate
    def test_acquire_conflict_already_locked(self, client):
        """Test acquisition failure when already locked by another."""
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        locks = {
            "test.py": {
                "file_path": "test.py",
                "developer_id": "bob",
                "expires_at": future,
            }
        }
        responses.add(
            responses.GET,
            "https://api.github.com/gists/fake_gist_id",
            json={"files": {"locks.json": {"content": json.dumps(locks)}}},
            status=200,
        )

        success, res = client.acquire("test.py")
        assert success is False
        assert "locked by bob" in res

    @responses.activate
    def test_acquire_already_locked_by_me(self, client):
        """Test failure when already locked by self."""
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        locks = {
            "test.py": {
                "file_path": "test.py",
                "developer_id": "test_user",
                "expires_at": future,
            }
        }
        responses.add(
            responses.GET,
            "https://api.github.com/gists/fake_gist_id",
            json={"files": {"locks.json": {"content": json.dumps(locks)}}},
            status=200,
        )
        success, res = client.acquire("test.py")
        assert success is False
        assert "You hold active lock" in res

    @responses.activate
    def test_acquire_retry_on_patch_fail(self, client):
        """Test retry logic if PATCH fails (e.g. concurrent update)."""
        responses.add(
            responses.GET,
            "https://api.github.com/gists/fake_gist_id",
            json={"files": {"locks.json": {"content": "{}"}}},
            status=200,
        )
        # First patch fails with 412
        responses.add(
            responses.PATCH, "https://api.github.com/gists/fake_gist_id", status=412
        )
        # Second patch succeeds
        responses.add(
            responses.PATCH, "https://api.github.com/gists/fake_gist_id", status=200
        )

        with patch("time.sleep"):  # Skip actual sleeping
            success, _ = client.acquire("test.py")
        assert success is True

    @responses.activate
    def test_acquire_conflict_retry_exhausted(self, client):
        """Test that acquisition fails after max retries due to conflict."""
        url = "https://api.github.com/gists/fake_gist_id"
        responses.add(
            responses.GET,
            url,
            json={"files": {"locks.json": {"content": "{}"}}},
            status=200,
        )
        # Three failed patches
        responses.add(responses.PATCH, url, status=412)
        responses.add(responses.PATCH, url, status=412)
        responses.add(responses.PATCH, url, status=412)

        with patch("time.sleep"):
            success, res = client.acquire("test.py")
        assert success is False
        assert "concurrent updates" in res

    @responses.activate
    def test_acquire_api_error_limit(self, client):
        """Test that acquisition fails after max retries."""
        url = "https://api.github.com/gists/fake_gist_id"
        responses.add(responses.GET, url, status=500)
        with patch("time.sleep"):
            success, res = client.acquire("test.py")
        assert success is False
        assert "API Error" in res

    @responses.activate
    def test_release_success(self, client):
        """Test releasing a lock."""
        locks = {"test.py": {"file_path": "test.py", "developer_id": "test_user"}}
        responses.add(
            responses.GET,
            "https://api.github.com/gists/fake_gist_id",
            json={"files": {"locks.json": {"content": json.dumps(locks)}}},
            status=200,
        )
        responses.add(
            responses.PATCH, "https://api.github.com/gists/fake_gist_id", status=200
        )

        success, res = client.release_by_path("test.py")
        assert success is True
        assert res == "released"

    @responses.activate
    def test_release_not_found(self, client):
        """Test release error path when lock doesn't exist."""
        responses.add(
            responses.GET,
            "https://api.github.com/gists/fake_gist_id",
            json={"files": {"locks.json": {"content": "{}"}}},
            status=200,
        )
        success, res = client.release_by_path("ghost.py")
        assert success is False
        assert "No active lock found" in res

    @responses.activate
    def test_release_unauthorised(self, client):
        """Test release failure when not owner."""
        locks = {"test.py": {"file_path": "test.py", "developer_id": "bob"}}
        responses.add(
            responses.GET,
            "https://api.github.com/gists/fake_gist_id",
            json={"files": {"locks.json": {"content": json.dumps(locks)}}},
            status=200,
        )
        success, res = client.release_by_path("test.py")
        assert success is False
        assert "Unauthorised" in res

    @responses.activate
    def test_release_api_exception(self, client):
        """Test release handle API exception."""
        url = "https://api.github.com/gists/fake_gist_id"
        responses.add(responses.GET, url, status=500)
        with patch("time.sleep"):
            success, res = client.release_by_path("test.py")
        assert success is False
        assert "API Error" in res

    @responses.activate
    def test_release_concurrent_failure(self, client):
        """Test release final conflict failure."""
        url = "https://api.github.com/gists/fake_gist_id"
        locks = {"a.py": {"developer_id": "test_user"}}
        responses.add(
            responses.GET,
            url,
            json={"files": {"locks.json": {"content": json.dumps(locks)}}},
            status=200,
        )
        responses.add(responses.PATCH, url, status=412)
        with patch("time.sleep"):
            success, res = client.release_by_path("a.py")
        assert success is False
        assert "conflict" in res

    @responses.activate
    def test_status_locked(self, client):
        """Test status check."""
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        locks = {
            "test.py": {
                "file_path": "test.py",
                "developer_id": "alice",
                "expires_at": future,
                "acquired_at": "2026-01-01T00:00:00Z",
                "reason": "testing",
            }
        }
        responses.add(
            responses.GET,
            "https://api.github.com/gists/fake_gist_id",
            json={"files": {"locks.json": {"content": json.dumps(locks)}}},
            status=200,
        )

        with patch("os.path.exists", return_value=True):
            res = client.status("test.py")
        assert res["is_locked"] is True
        assert res["locked_by"] == "alice"
        assert res["can_edit"] is False
        assert res["reason"] == "testing"

    @responses.activate
    def test_status_expired(self, client):
        """Test visibility of expired locks via status."""
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        locks = {
            "test.py": {
                "file_path": "test.py",
                "developer_id": "alice",
                "expires_at": past,
            }
        }
        responses.add(
            responses.GET,
            "https://api.github.com/gists/fake_gist_id",
            json={"files": {"locks.json": {"content": json.dumps(locks)}}},
            status=200,
        )
        with patch("os.path.exists", return_value=True):
            res = client.status("test.py")
        assert res["is_locked"] is False
        assert res.get("expired") is True

    @responses.activate
    def test_status_api_error(self, client):
        """Test status with API error."""
        url = "https://api.github.com/gists/fake_gist_id"
        responses.add(responses.GET, url, status=500)
        with patch("os.path.exists", return_value=True):
            res = client.status("test.py")
        assert res["is_locked"] is False
        assert "error" in res

    @responses.activate
    def test_active_locks_filters_expired(self, client):
        """Test that active_locks list only includes non-expired items."""
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        locks = {
            "old.py": {"file_path": "old.py", "expires_at": past, "developer_id": "a"},
            "new.py": {
                "file_path": "new.py",
                "expires_at": future,
                "developer_id": "b",
            },
        }
        responses.add(
            responses.GET,
            "https://api.github.com/gists/fake_gist_id",
            json={"files": {"locks.json": {"content": json.dumps(locks)}}},
            status=200,
        )

        res = client.active_locks()
        assert len(res) == 1
        assert res[0]["file_path"] == "new.py"

    @responses.activate
    def test_active_locks_exception(self, client):
        """Test active_locks handling exception."""
        url = "https://api.github.com/gists/fake_gist_id"
        responses.add(responses.GET, url, status=500)
        assert client.active_locks() == []

    @responses.activate
    def test_release_all_my_locks(self, client):
        """Test multi-release script."""
        locks = {
            "mine.py": {"developer_id": "test_user"},
            "others.py": {"developer_id": "bob"},
        }
        responses.add(
            responses.GET,
            "https://api.github.com/gists/fake_gist_id",
            json={"files": {"locks.json": {"content": json.dumps(locks)}}},
            status=200,
        )
        responses.add(
            responses.PATCH, "https://api.github.com/gists/fake_gist_id", status=200
        )

        count = client.release_all_my_locks()
        assert count == 1

    @responses.activate
    def test_release_all_failed_patch(self, client):
        """Test release-all failure if patch fails."""
        locks = {"mine.py": {"developer_id": "test_user"}}
        responses.add(
            responses.GET,
            "https://api.github.com/gists/fake_gist_id",
            json={"files": {"locks.json": {"content": json.dumps(locks)}}},
            status=200,
        )
        responses.add(
            responses.PATCH, "https://api.github.com/gists/fake_gist_id", status=412
        )
        assert client.release_all_my_locks() == 0

    @responses.activate
    def test_release_all_none(self, client):
        """Test release-all when nothing to release."""
        responses.add(
            responses.GET,
            "https://api.github.com/gists/fake_gist_id",
            json={"files": {"locks.json": {"content": "{}"}}},
            status=200,
        )
        assert client.release_all_my_locks() == 0

    @responses.activate
    def test_release_all_exception(self, client):
        """Test release-all handling exception."""
        url = "https://api.github.com/gists/fake_gist_id"
        responses.add(responses.GET, url, status=500)
        assert client.release_all_my_locks() == 0

    @responses.activate
    def test_acquire_multiple_success(self, client):
        """Test acquiring multiple locks in one batch."""
        responses.add(
            responses.GET,
            "https://api.github.com/gists/fake_gist_id",
            json={"files": {"locks.json": {"content": "{}"}}},
            status=200,
            headers={"ETag": "etag1"},
        )
        responses.add(
            responses.PATCH,
            "https://api.github.com/gists/fake_gist_id",
            json={"status": "success"},
            status=200,
        )

        success, locked, msg = client.acquire_multiple(["a.py", "b.py"])
        assert success is True
        assert len(locked) == 2
        assert "a.py" in locked
        assert "b.py" in locked

    @responses.activate
    def test_acquire_multiple_conflict(self, client):
        """Test batch acquisition failure if one file is already locked."""
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        locks = {
            "a.py": {
                "file_path": "a.py",
                "developer_id": "bob",
                "expires_at": future,
            }
        }
        responses.add(
            responses.GET,
            "https://api.github.com/gists/fake_gist_id",
            json={"files": {"locks.json": {"content": json.dumps(locks)}}},
            status=200,
        )

        success, locked, msg = client.acquire_multiple(["a.py", "c.py"])
        assert success is False
        assert "locked by bob" in msg
        assert len(locked) == 1
        assert "a.py" in locked

    @responses.activate
    def test_release_multiple_success(self, client):
        """Test releasing multiple locks in one batch."""
        locks = {
            "a.py": {"file_path": "a.py", "developer_id": "test_user"},
            "b.py": {"file_path": "b.py", "developer_id": "test_user"},
        }
        responses.add(
            responses.GET,
            "https://api.github.com/gists/fake_gist_id",
            json={"files": {"locks.json": {"content": json.dumps(locks)}}},
            status=200,
        )
        responses.add(
            responses.PATCH, "https://api.github.com/gists/fake_gist_id", status=200
        )

        success, count, msg = client.release_multiple(["a.py", "b.py"])
        assert success is True
        assert count == 2

    @responses.activate
    def test_cli_main_argparse(self, monkeypatch, capsys):
        """Minimal CLI check for the new command structure."""
        from src.services.lock_client import main as cli_main

        responses.add(
            responses.GET,
            "https://api.github.com/gists/fake_gist_id",
            json={"files": {"locks.json": {"content": "{}"}}},
            status=200,
        )
        monkeypatch.setattr(sys, "argv", ["lock_client.py", "active"])
        cli_main()
        captured = capsys.readouterr()
        assert "[]" in captured.out

    @responses.activate
    def test_cli_main_mine(self, monkeypatch, capsys):
        """CLI check for 'mine' command."""
        from src.services.lock_client import main as cli_main

        def mock_git_user(*args):
            return "test_user"

        monkeypatch.setattr(
            "src.services.lock_client.LockClient._get_git_username", mock_git_user
        )

        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        locks = {
            "a.py": {
                "developer_id": "test_user",
                "expires_at": future,
                "file_path": "a.py",
            }
        }
        responses.add(
            responses.GET,
            "https://api.github.com/gists/fake_gist_id",
            json={"files": {"locks.json": {"content": json.dumps(locks)}}},
            status=200,
        )
        monkeypatch.setattr(sys, "argv", ["lock_client.py", "mine"])
        cli_main()
        captured = capsys.readouterr()
        assert "a.py" in captured.out

    def test_cli_main_init_error(self, monkeypatch, capsys):
        """CLI handles init errors."""
        from src.services.lock_client import main as cli_main

        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.setattr(sys, "argv", ["lock_client.py", "status", "a.py"])
        with patch("os.path.exists", return_value=True):
            cli_main()
        captured = capsys.readouterr()
        assert "Error:" in captured.out

    def test_cli_help(self, monkeypatch, capsys):
        """Test help output."""
        from src.services.lock_client import main as cli_main

        monkeypatch.setattr(sys, "argv", ["lock_client.py", "--help"])
        with pytest.raises(SystemExit):
            cli_main()
        captured = capsys.readouterr()
        assert "acquire" in captured.out

    def test_cli_main_no_cmd(self, monkeypatch, capsys):
        """CLI prints help if no command."""
        from src.services.lock_client import main as cli_main

        monkeypatch.setattr(sys, "argv", ["lock_client.py"])
        cli_main()
        captured = capsys.readouterr()
        assert "acquire" in captured.out

    @responses.activate
    def test_cli_commands_coverage(self, monkeypatch, capsys):
        """Run CLI commands for coverage only."""
        from src.services.lock_client import main as cli_main

        url = "https://api.github.com/gists/fake_gist_id"

        gist_json = {"files": {"locks.json": {"content": "{}"}}}
        responses.add(responses.GET, url, json=gist_json, status=200)
        responses.add(responses.PATCH, url, status=200)

        # acquire
        monkeypatch.setattr(sys, "argv", ["lock_client.py", "acquire", "cli.py"])
        cli_main()
        # release
        monkeypatch.setattr(sys, "argv", ["lock_client.py", "release", "cli.py"])
        cli_main()
        # release-all
        monkeypatch.setattr(sys, "argv", ["lock_client.py", "release-all"])
        cli_main()
        # status
        monkeypatch.setattr(sys, "argv", ["lock_client.py", "status", "cli.py"])
        with patch("os.path.exists", return_value=True):
            cli_main()
        # acquire-batch
        args = ["lock_client.py", "acquire-batch", "a.py", "b.py"]
        monkeypatch.setattr(sys, "argv", args)
        cli_main()
        # release-batch
        args = ["lock_client.py", "release-batch", "a.py", "b.py"]
        monkeypatch.setattr(sys, "argv", args)
        cli_main()

    def test_cli_main_no_args_script(self, monkeypatch, capsys):
        """CLI direct launch coverage."""
        from src.services.lock_client import main as cli_main

        monkeypatch.setattr(sys, "argv", ["lock_client.py"])
        cli_main()
        captured = capsys.readouterr()
        assert "acquire" in captured.out
