import os

import pytest

from src.services.lock_manager_app import app


@pytest.fixture
def client():
    """Create a test client with in-memory DB."""
    app.config["TESTING"] = True
    os.environ["LOCK_DB_PATH"] = ":memory:"
    from src.services.lock_manager import Base
    from src.services.lock_manager_app import lock_manager

    # Clear the database for each test to avoid state leakage
    Base.metadata.drop_all(lock_manager.engine)
    Base.metadata.create_all(lock_manager.engine)

    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    """Test health check API."""
    res = client.get("/api/locks/health")
    assert res.status_code == 200
    assert res.json["status"] == "ok"
    assert "timestamp" in res.json


def test_acquire_lock_params_validation(client):
    """Test API field validation for acquisition."""
    # Missing file_path
    res = client.post("/api/locks/acquire", json={"developer_id": "alice"})
    assert res.status_code == 400
    assert "Missing required fields" in res.json["error"]

    # Missing developer_id
    res = client.post("/api/locks/acquire", json={"file_path": "a.py"})
    assert res.status_code == 400


def test_acquire_lock_full_flow(client):
    """Test full acquisition API flow."""
    res = client.post(
        "/api/locks/acquire",
        json={
            "file_path": "src/app.py",
            "developer_id": "alice",
            "developer_email": "alice@example.com",
            "branch_name": "feat1",
            "reason": "bugfix",
            "expires_minutes": 10,
        },
    )
    assert res.status_code == 200
    assert "lock_token" in res.json
    assert res.json["status"] in ["acquired", "refreshed"]


def test_acquire_conflict_api(client):
    """Test acquisition conflict API handling."""
    client.post(
        "/api/locks/acquire", json={"file_path": "a.py", "developer_id": "alice"}
    )
    res = client.post(
        "/api/locks/acquire", json={"file_path": "a.py", "developer_id": "bob"}
    )
    assert res.status_code == 409
    assert res.json["status"] == "conflict"


def test_release_lock_validation(client):
    """Test field validation for release API."""
    res = client.post("/api/locks/release", json={})
    assert res.status_code == 400
    assert "Missing lock_token" in res.json["error"]


def test_release_lock_api_success(client):
    """Test successful release API."""
    res_acq = client.post(
        "/api/locks/acquire", json={"file_path": "b.py", "developer_id": "alice"}
    )
    token = res_acq.json["lock_token"]
    res_rel = client.post("/api/locks/release", json={"lock_token": token})
    assert res_rel.status_code == 200
    assert res_rel.json["status"] == "released"


def test_release_lock_api_not_found(client):
    """Test release API for missing lock."""
    res = client.post("/api/locks/release", json={"lock_token": "token-not-exist"})
    assert res.status_code == 404
    assert res.json["status"] == "not_found"


def test_status_api(client):
    """Test status API for locked and unlocked files."""
    # Check locked
    client.post(
        "/api/locks/acquire", json={"file_path": "locked.py", "developer_id": "alice"}
    )
    res = client.get("/api/locks/status?file_path=locked.py")
    assert res.status_code == 200
    assert res.json["is_locked"] is True
    assert res.json["locked_by"] == "alice"

    # Check missing file_path param
    res = client.get("/api/locks/status")
    assert res.status_code == 400

    # Check unlocked
    res = client.get("/api/locks/status?file_path=unlocked.py")
    assert res.json["is_locked"] is False


def test_active_locks_api(client):
    """Test list active locks API."""
    client.post(
        "/api/locks/acquire", json={"file_path": "x.py", "developer_id": "alice"}
    )
    res = client.get("/api/locks/active")
    assert res.status_code == 200
    assert len(res.json) == 1
    assert res.json[0]["file_path"] == "x.py"


def test_history_api(client):
    """Test history API with filtering."""
    client.post(
        "/api/locks/acquire", json={"file_path": "hist1.py", "developer_id": "alice"}
    )
    res = client.get("/api/locks/history?limit=10")
    assert res.status_code == 200
    # Active locks are not in history
    assert len(res.json) == 0

    # Release it to make it appear in history
    client.post(
        "/api/locks/release-by-path",
        json={"file_path": "hist1.py", "developer_id": "alice"},
    )

    res = client.get("/api/locks/history?file_path=hist1.py")
    assert len(res.json) == 1
    assert res.json[0]["file_path"] == "hist1.py"


def test_developer_locks_api(client):
    """Test filtering locks by developer via API."""
    client.post(
        "/api/locks/acquire", json={"file_path": "d1.py", "developer_id": "dev1"}
    )
    res = client.get("/api/locks/developer/dev1")
    assert res.status_code == 200
    assert len(res.json) == 1


def test_force_release_api_validation(client):
    """Test validation for force-release API."""
    res = client.post("/api/locks/force-release", json={"admin_id": "admin"})
    assert res.status_code == 400


def test_force_release_api_success(client):
    """Test successful force-release API."""
    client.post(
        "/api/locks/acquire", json={"file_path": "force.py", "developer_id": "alice"}
    )
    res = client.post(
        "/api/locks/force-release",
        json={"file_path": "force.py", "admin_id": "admin"},
    )
    assert res.status_code == 200
    assert res.json["status"] == "released"


def test_force_release_api_not_found(client):
    """Test force-release API for missing file."""
    res = client.post(
        "/api/locks/force-release",
        json={"file_path": "ghost.py", "admin_id": "admin"},
    )
    assert res.status_code == 404


def test_cleanup_api(client):
    """Test manual cleanup trigger API."""
    res = client.post("/api/locks/cleanup")
    assert res.status_code == 200
    assert res.json["status"] == "success"
    assert "cleaned_count" in res.json


def test_dashboard_api(client, monkeypatch):
    """Test dashboard serving API."""
    # Ensure template exists
    res = client.get("/admin/lock-dashboard")
    assert res.status_code == 200
    # Template has <h1>🔒 Lock Manager Dashboard</h1>
    assert "Lock Manager Dashboard" in res.get_data(as_text=True)


def test_server_error_responses(client, monkeypatch):
    """Test mock server error responses (500) for robustness."""
    from src.services.lock_manager_app import lock_manager

    def mock_error(*args, **kwargs):
        return False, {"status": "error", "message": "Simulated error"}

    # Mock acquire failure with 500
    monkeypatch.setattr(lock_manager, "acquire_lock", mock_error)
    res = client.post(
        "/api/locks/acquire", json={"file_path": "err.py", "developer_id": "alice"}
    )
    assert res.status_code == 500

    # Mock release failure with 500
    monkeypatch.setattr(lock_manager, "release_lock", mock_error)
    res = client.post("/api/locks/release", json={"lock_token": "tk"})
    assert res.status_code == 500

    # Mock force-release failure with 500
    monkeypatch.setattr(lock_manager, "force_release_lock", mock_error)
    res = client.post(
        "/api/locks/force-release", json={"file_path": "err.py", "admin_id": "admin"}
    )
    assert res.status_code == 500
