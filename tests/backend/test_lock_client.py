import pytest
import responses

from src.services.lock_client import LockClient


class TestLockClient:
    @pytest.fixture
    def client(self):
        """Create a client with fixed developer_id for testing."""
        return LockClient(server_url="http://localhost:5001", developer_id="test_user")

    def test_init_default_developer(self, monkeypatch):
        """Test default developer_id initialization from git user."""

        def mock_git_user(*args):
            return "alice_git"

        monkeypatch.setattr(
            "src.services.lock_client.LockClient._get_git_user", mock_git_user
        )
        # Pass developer_id=None so it calls _get_git_user
        c = LockClient(server_url="http://localhost:5001", developer_id=None)
        assert c.developer_id == "alice_git"

    def test_get_git_user_fallback(self, monkeypatch):
        """Test fallback when git command fails."""

        def mock_error(*args, **kwargs):
            raise Exception("Subprocess Error")

        monkeypatch.setattr("subprocess.check_output", mock_error)
        c = LockClient()
        assert c.developer_id == "unknown_user"

    @responses.activate
    def test_health_success(self, client):
        """Test health check success."""
        responses.add(
            responses.GET,
            "http://localhost:5001/api/locks/health",
            json={"status": "ok"},
            status=200,
        )
        assert client.health() is True

    @responses.activate
    def test_health_failure(self, client):
        """Test health check failure."""
        # Non-200 response
        responses.add(
            responses.GET,
            "http://localhost:5001/api/locks/health",
            status=500,
        )
        assert client.health() is False

        # Exception (connection refusal)
        responses.add(
            responses.GET,
            "http://localhost:5001/api/locks/health",
            body=Exception("Conn Refused"),
        )
        assert client.health() is False

    @responses.activate
    def test_acquire_success(self, client):
        """Test acquiring a lock via client."""
        responses.add(
            responses.POST,
            "http://localhost:5001/api/locks/acquire",
            json={"lock_token": "token123", "status": "acquired"},
            status=200,
        )
        success, res = client.acquire("test.py", branch_name="feat", reason="editing")
        assert success is True
        assert res == "token123"

    @responses.activate
    def test_acquire_failure(self, client):
        """Test acquisition failure handling."""
        responses.add(
            responses.POST,
            "http://localhost:5001/api/locks/acquire",
            json={"message": "Conflict", "status": "conflict"},
            status=409,
        )
        success, res = client.acquire("test.py")
        assert success is False
        assert res == "Conflict"

    @responses.activate
    def test_acquire_exception(self, client):
        """Test acquisition exception handling."""
        responses.add(
            responses.POST,
            "http://localhost:5001/api/locks/acquire",
            body=Exception("Error acquisition"),
        )
        success, res = client.acquire("test.py")
        assert success is False
        assert "Error acquisition" in res

    @responses.activate
    def test_release_success(self, client):
        """Test releasing a lock via client."""
        responses.add(
            responses.POST,
            "http://localhost:5001/api/locks/release",
            json={"status": "released"},
            status=200,
        )
        success, res = client.release("token123")
        assert success is True
        assert res == "released"

    @responses.activate
    def test_release_failure(self, client):
        """Test release failure handling."""
        responses.add(
            responses.POST,
            "http://localhost:5001/api/locks/release",
            json={"message": "Not found", "status": "not_found"},
            status=404,
        )
        success, res = client.release("token123")
        assert success is False
        assert res == "Not found"

    @responses.activate
    def test_release_exception(self, client):
        """Test release exception handling."""
        responses.add(
            responses.POST,
            "http://localhost:5001/api/locks/release",
            body=Exception("Error release"),
        )
        success, res = client.release("token123")
        assert success is False
        assert "Error release" in res

    @responses.activate
    def test_status_locked(self, client):
        """Test getting lock status via client."""
        responses.add(
            responses.GET,
            "http://localhost:5001/api/locks/status",
            json={"is_locked": True, "locked_by": "alice"},
            status=200,
        )
        res = client.status("test.py")
        assert res["is_locked"] is True
        assert res["locked_by"] == "alice"

    @responses.activate
    def test_status_server_error(self, client):
        """Test lock status server error handling."""
        responses.add(
            responses.GET,
            "http://localhost:5001/api/locks/status",
            status=500,
        )
        res = client.status("test.py")
        assert res["is_locked"] is False
        assert "Server returned 500" in res["error"]

    @responses.activate
    def test_status_exception(self, client):
        """Test lock status server exception handling."""
        responses.add(
            responses.GET,
            "http://localhost:5001/api/locks/status",
            body=Exception("Status Error"),
        )
        res = client.status("test.py")
        assert res["is_locked"] is False
        assert "Status Error" in res["error"]

    @responses.activate
    def test_active_locks_success(self, client):
        """Test listing all active locks via client."""
        responses.add(
            responses.GET,
            "http://localhost:5001/api/locks/active",
            json=[{"file_path": "a.py"}],
            status=200,
        )
        res = client.active_locks()
        assert len(res) == 1
        assert res[0]["file_path"] == "a.py"

    @responses.activate
    def test_active_locks_failure(self, client):
        """Test list active locks failure handling."""
        responses.add(
            responses.GET,
            "http://localhost:5001/api/locks/active",
            status=500,
        )
        res = client.active_locks()
        assert res == []

        # Exception case
        responses.add(
            responses.GET,
            "http://localhost:5001/api/locks/active",
            body=Exception("Active Lock failure"),
        )
        res = client.active_locks()
        assert res == []

    @responses.activate
    def test_my_locks_success(self, client):
        """Test listing developer's active locks via client."""
        responses.add(
            responses.GET,
            "http://localhost:5001/api/locks/developer/test_user",
            json=[{"file_path": "b.py", "lock_token": "t1"}],
            status=200,
        )
        res = client.my_locks()
        assert len(res) == 1
        assert res[0]["file_path"] == "b.py"

    @responses.activate
    def test_my_locks_failure(self, client):
        """Test my_locks failure and exception handling."""
        responses.add(
            responses.GET,
            "http://localhost:5001/api/locks/developer/test_user",
            status=500,
        )
        res = client.my_locks()
        assert res == []

        responses.add(
            responses.GET,
            "http://localhost:5001/api/locks/developer/test_user",
            body=Exception("My locks error"),
        )
        res = client.my_locks()
        assert res == []

    @responses.activate
    def test_release_all_my_locks_logic(self, client):
        """Test multi-release convenience function."""
        responses.add(
            responses.GET,
            "http://localhost:5001/api/locks/developer/test_user",
            json=[{"lock_token": "t1"}, {"lock_token": "t2"}],
            status=200,
        )
        responses.add(
            responses.POST,
            "http://localhost:5001/api/locks/release",
            json={"status": "released"},
            status=200,
        )

        count = client.release_all_my_locks()
        assert count == 2

    def test_cli_main_argparse(self, monkeypatch, capsys):
        """Test the CLI entry point (main) for basic commands."""
        import sys

        from src.services.lock_client import main as cli_main

        # Use the context manager form of the mock
        with responses.RequestsMock() as rsps:
            # Test health via CLI
            rsps.add(
                responses.GET,
                "http://localhost:5001/api/locks/health",
                json={"status": "ok"},
                status=200,
            )
            monkeypatch.setattr(sys, "argv", ["lock_client.py", "health"])
            cli_main()
            captured = capsys.readouterr()
            assert "Server alive: True" in captured.out

        with responses.RequestsMock() as rsps:
            # Test acquire via CLI
            rsps.add(
                responses.POST,
                "http://localhost:5001/api/locks/acquire",
                json={"lock_token": "cli_token", "status": "acquired"},
                status=200,
            )
            monkeypatch.setattr(sys, "argv", ["lock_client.py", "acquire", "test.py"])
            cli_main()
            captured = capsys.readouterr()
            assert "Success: True, Result: cli_token" in captured.out

        with responses.RequestsMock() as rsps:
            # Test release via CLI
            rsps.add(
                responses.POST,
                "http://localhost:5001/api/locks/release",
                json={"status": "released"},
                status=200,
            )
            monkeypatch.setattr(sys, "argv", ["lock_client.py", "release", "cli_token"])
            cli_main()
            captured = capsys.readouterr()
            assert "Success: True, Result: released" in captured.out

        with responses.RequestsMock() as rsps:
            # Test status via CLI
            rsps.add(
                responses.GET,
                "http://localhost:5001/api/locks/status",
                json={"is_locked": True, "locked_by": "alice"},
                status=200,
            )
            monkeypatch.setattr(sys, "argv", ["lock_client.py", "status", "test.py"])
            cli_main()
            captured = capsys.readouterr()
            assert '"is_locked": true' in captured.out

        with responses.RequestsMock() as rsps:
            # Test active via CLI
            rsps.add(
                responses.GET,
                "http://localhost:5001/api/locks/active",
                json=[{"file_path": "a.py"}],
                status=200,
            )
            monkeypatch.setattr(sys, "argv", ["lock_client.py", "active"])
            cli_main()
            captured = capsys.readouterr()
            assert "a.py" in captured.out

        with responses.RequestsMock() as rsps:
            # Test mine via CLI
            rsps.add(
                responses.GET,
                "http://localhost:5001/api/locks/developer/test_user",
                json=[{"file_path": "mine.py"}],
                status=200,
            )
            monkeypatch.setattr(
                sys, "argv", ["lock_client.py", "--user", "test_user", "mine"]
            )
            cli_main()
            captured = capsys.readouterr()
            assert "mine.py" in captured.out

        with responses.RequestsMock() as rsps:
            # Test release-all via CLI
            rsps.add(
                responses.GET,
                "http://localhost:5001/api/locks/developer/test_user",
                json=[{"lock_token": "tk1"}],
                status=200,
            )
            rsps.add(
                responses.POST,
                "http://localhost:5001/api/locks/release",
                json={"status": "released"},
                status=200,
            )
            monkeypatch.setattr(
                sys, "argv", ["lock_client.py", "--user", "test_user", "release-all"]
            )
            cli_main()
            captured = capsys.readouterr()
            assert "Released 1 locks" in captured.out

    def test_cli_help(self, monkeypatch, capsys):
        """Test default CLI help output."""
        import sys

        from src.services.lock_client import main as cli_main

        monkeypatch.setattr(sys, "argv", ["lock_client.py"])
        try:
            cli_main()
        except SystemExit:
            pass
        captured = capsys.readouterr()
        # Help text check
        assert "acquire" in captured.out or "acquire" in captured.err
