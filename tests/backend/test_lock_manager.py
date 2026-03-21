import pytest
from datetime import datetime, timedelta

from src.services.lock_manager import LockManager


class TestLockManager:
    @pytest.fixture
    def manager(self):
        return LockManager(db_path=":memory:")

    def test_acquire_new_lock_succeeds(self, manager):
        success, result = manager.acquire_lock("test.py", "alice")
        assert success is True
        assert result["status"] == "acquired"
        assert "lock_token" in result

    def test_acquire_returns_lock_token(self, manager):
        _, result = manager.acquire_lock("test.py", "alice")
        assert len(result["lock_token"]) > 0

    def test_acquire_sets_correct_expiry(self, manager):
        _, result = manager.acquire_lock("test.py", "alice", expires_minutes=10)
        expires_at = datetime.fromisoformat(result["expires_at"])
        now = datetime.utcnow()
        assert expires_at > now
        assert expires_at <= now + timedelta(minutes=11)

    def test_acquire_with_custom_expiry(self, manager):
        _, result = manager.acquire_lock("test.py", "alice", expires_minutes=60)
        expires_at = datetime.fromisoformat(result["expires_at"])
        assert expires_at > datetime.utcnow() + timedelta(minutes=59)

    def test_acquire_same_file_same_developer_refreshes(self, manager):
        _, res1 = manager.acquire_lock("test.py", "alice", expires_minutes=10)
        token1 = res1["lock_token"]

        success, res2 = manager.acquire_lock("test.py", "alice", expires_minutes=20)
        assert success is True
        assert res2["status"] == "refreshed"
        assert res2["lock_token"] == token1
        assert datetime.fromisoformat(res2["expires_at"]) > datetime.fromisoformat(res1["expires_at"])

    def test_acquire_same_file_different_developer_conflicts(self, manager):
        manager.acquire_lock("test.py", "alice")
        success, result = manager.acquire_lock("test.py", "bob")
        assert success is False
        assert result["status"] == "conflict"
        assert result["locked_by"] == "alice"

    def test_acquire_after_release_succeeds(self, manager):
        _, res = manager.acquire_lock("test.py", "alice")
        manager.release_lock(res["lock_token"])
        success, result = manager.acquire_lock("test.py", "bob")
        assert success is True
        assert result["status"] == "acquired"

    def test_acquire_after_expiry_succeeds(self, manager):
        from src.services.lock_manager import FileLock
        session = manager.Session()
        expired_lock = FileLock(
            file_path="expired.py",
            developer_id="oldie",
            lock_token="old_token",
            expires_at=datetime.utcnow() - timedelta(minutes=1)
        )
        session.add(expired_lock)
        session.commit()
        session.close()

        success, result = manager.acquire_lock("expired.py", "newbie")
        assert success is True
        assert result["status"] == "acquired"
        assert result["lock_token"] != "old_token"

    def test_release_by_valid_token(self, manager):
        _, res = manager.acquire_lock("test.py", "alice")
        success, result = manager.release_lock(res["lock_token"])
        assert success is True
        assert result["status"] == "released"

    def test_release_invalid_token_returns_not_found(self, manager):
        success, result = manager.release_lock("invalid_token")
        assert success is False
        assert result["status"] == "not_found"

    def test_release_already_released_returns_not_found(self, manager):
        _, res = manager.acquire_lock("test.py", "alice")
        manager.release_lock(res["lock_token"])
        success, result = manager.release_lock(res["lock_token"])
        assert success is False
        assert result["status"] == "not_found"

    def test_status_locked_file(self, manager):
        manager.acquire_lock("test.py", "alice")
        status = manager.get_lock_status("test.py")
        assert status["is_locked"] is True
        assert status["locked_by"] == "alice"
        assert status["can_edit"] is False

    def test_status_unlocked_file(self, manager):
        status = manager.get_lock_status("free.py")
        assert status["is_locked"] is False
        assert status["can_edit"] is True

    def test_get_all_active_locks_empty(self, manager):
        assert len(manager.get_all_active_locks()) == 0

    def test_get_all_active_locks_returns_only_active(self, manager):
        manager.acquire_lock("a.py", "alice")
        manager.acquire_lock("b.py", "bob")
        _, res = manager.acquire_lock("c.py", "charlie")
        manager.release_lock(res["lock_token"])

        active = manager.get_all_active_locks()
        assert len(active) == 2
        paths = [lock["file_path"] for lock in active]
        assert "a.py" in paths
        assert "b.py" in paths
        assert "c.py" not in paths

    def test_get_locks_by_developer(self, manager):
        manager.acquire_lock("a.py", "alice")
        manager.acquire_lock("b.py", "alice")
        manager.acquire_lock("c.py", "bob")

        alice_locks = manager.get_locks_by_developer("alice")
        assert len(alice_locks) == 2

    def test_cleanup_expired_locks(self, manager):
        # Manually insert an expired lock since we can't easily mock datetime.utcnow in SQLAlchemy default
        from src.services.lock_manager import FileLock
        session = manager.Session()
        expired_lock = FileLock(
            file_path="expired.py",
            developer_id="oldie",
            lock_token="old_token",
            expires_at=datetime.utcnow() - timedelta(minutes=1)
        )
        session.add(expired_lock)
        session.commit()

        count = manager.cleanup_expired_locks()
        assert count == 1

        status = manager.get_lock_status("expired.py")
        assert status["is_locked"] is False

    def test_force_release_active_lock(self, manager):
        manager.acquire_lock("test.py", "alice")
        success, result = manager.force_release_lock("test.py", "admin")
        assert success is True
        status = manager.get_lock_status("test.py")
        assert status["is_locked"] is False

    def test_get_lock_history_all(self, manager):
        manager.acquire_lock("a.py", "alice")
        _, res = manager.acquire_lock("b.py", "bob")
        manager.release_lock(res["lock_token"])

        history = manager.get_lock_history()
        assert len(history) == 2

    def test_get_lock_history_filtered_by_file(self, manager):
        manager.acquire_lock("a.py", "alice")
        manager.acquire_lock("b.py", "bob")

        history = manager.get_lock_history(file_path="a.py")
        assert len(history) == 1
        assert history[0]["file_path"] == "a.py"
