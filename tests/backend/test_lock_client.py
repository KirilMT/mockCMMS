import pytest
import responses
from src.services.lock_client import LockClient

class TestLockClient:
    @pytest.fixture
    def client(self):
        return LockClient(server_url="http://localhost:5001", developer_id="test_user")

    @responses.activate
    def test_health(self, client):
        responses.add(responses.GET, "http://localhost:5001/api/locks/health",
                      json={"status": "ok"}, status=200)
        assert client.health() is True

    @responses.activate
    def test_acquire_success(self, client):
        responses.add(responses.POST, "http://localhost:5001/api/locks/acquire",
                      json={"lock_token": "token123", "status": "acquired"}, status=200)
        success, res = client.acquire("test.py")
        assert success is True
        assert res == "token123"

    @responses.activate
    def test_acquire_conflict(self, client):
        responses.add(responses.POST, "http://localhost:5001/api/locks/acquire",
                      json={"message": "Conflict", "status": "conflict"}, status=409)
        success, res = client.acquire("test.py")
        assert success is False
        assert res == "Conflict"

    @responses.activate
    def test_release_success(self, client):
        responses.add(responses.POST, "http://localhost:5001/api/locks/release",
                      json={"status": "released"}, status=200)
        success, res = client.release("token123")
        assert success is True
        assert res == "released"

    @responses.activate
    def test_status_locked(self, client):
        responses.add(responses.GET, "http://localhost:5001/api/locks/status",
                      json={"is_locked": True, "locked_by": "alice"}, status=200)
        res = client.status("test.py")
        assert res["is_locked"] is True
        assert res["locked_by"] == "alice"

    @responses.activate
    def test_active_locks(self, client):
        responses.add(responses.GET, "http://localhost:5001/api/locks/active",
                      json=[{"file_path": "a.py"}], status=200)
        res = client.active_locks()
        assert len(res) == 1
        assert res[0]["file_path"] == "a.py"

    @responses.activate
    def test_my_locks(self, client):
        responses.add(responses.GET, "http://localhost:5001/api/locks/developer/test_user",
                      json=[{"file_path": "b.py", "lock_token": "t1"}], status=200)
        res = client.my_locks()
        assert len(res) == 1
        assert res[0]["file_path"] == "b.py"

    @responses.activate
    def test_release_all_my_locks(self, client):
        responses.add(responses.GET, "http://localhost:5001/api/locks/developer/test_user",
                      json=[{"lock_token": "t1"}, {"lock_token": "t2"}], status=200)
        responses.add(responses.POST, "http://localhost:5001/api/locks/release",
                      json={"status": "released"}, status=200)

        count = client.release_all_my_locks()
        assert count == 2
