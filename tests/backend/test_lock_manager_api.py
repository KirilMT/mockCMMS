import os

import pytest

from src.services.lock_manager_app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    # Ensure it uses in-memory DB for tests
    os.environ["LOCK_DB_PATH"] = ":memory:"
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    res = client.get("/api/locks/health")
    assert res.status_code == 200
    assert res.json["status"] == "ok"


def test_acquire_lock_api(client):
    res = client.post(
        "/api/locks/acquire", json={"file_path": "src/app.py", "developer_id": "alice"}
    )
    assert res.status_code == 200
    assert "lock_token" in res.json


def test_acquire_conflict_api(client):
    client.post(
        "/api/locks/acquire", json={"file_path": "src/app.py", "developer_id": "alice"}
    )
    res = client.post(
        "/api/locks/acquire", json={"file_path": "src/app.py", "developer_id": "bob"}
    )
    assert res.status_code == 409
    assert res.json["status"] == "conflict"


def test_release_lock_api(client):
    res_acq = client.post(
        "/api/locks/acquire", json={"file_path": "src/app.py", "developer_id": "alice"}
    )
    token = res_acq.json["lock_token"]
    res_rel = client.post("/api/locks/release", json={"lock_token": token})
    assert res_rel.status_code == 200
    assert res_rel.json["status"] == "released"


def test_status_api(client):
    client.post(
        "/api/locks/acquire", json={"file_path": "src/app.py", "developer_id": "alice"}
    )
    res = client.get("/api/locks/status?file_path=src/app.py")
    assert res.status_code == 200
    assert res.json["is_locked"] is True
    assert res.json["locked_by"] == "alice"


def test_active_locks_api(client):
    client.post(
        "/api/locks/acquire", json={"file_path": "src/app.py", "developer_id": "alice"}
    )
    res = client.get("/api/locks/active")
    assert res.status_code == 200
    assert len(res.json) == 1


def test_force_release_api(client):
    client.post(
        "/api/locks/acquire", json={"file_path": "src/app.py", "developer_id": "alice"}
    )
    res = client.post(
        "/api/locks/force-release",
        json={"file_path": "src/app.py", "admin_id": "admin"},
    )
    assert res.status_code == 200
    status = client.get("/api/locks/status?file_path=src/app.py")
    assert status.json["is_locked"] is False
