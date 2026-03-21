"""Tests for the LockManager class."""

from datetime import datetime, timedelta, timezone

import pytest

from src.services.lock_manager import FileLock, LockManager


def _utcnow():
    """Return current UTC time as naive datetime."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TestLockManager:
    """Tests for the LockManager class."""

    @pytest.fixture
    def manager(self):
        """Create an in-memory LockManager for testing."""
        return LockManager(db_path=":memory:")

    def test_init_with_env_path(self, monkeypatch, tmp_path):
        """Test initialization using environment variable for DB path."""
        db_file = tmp_path / "env_locks.db"
        monkeypatch.setenv("LOCK_DB_PATH", str(db_file))
        # Pass None so it picks up from env
        m = LockManager(db_path=None)
        assert m.engine.url.database == str(db_file)
        # Ensure directory was created
        assert db_file.parent.exists()

    def test_acquire_new_lock_succeeds(self, manager):
        """Test acquiring a new lock succeeds."""
        success, result = manager.acquire_lock("test.py", "alice")
        assert success is True
        assert result["status"] == "acquired"
        assert "lock_token" in result

    def test_acquire_returns_lock_token(self, manager):
        """Test that acquiring a lock returns a token."""
        _, result = manager.acquire_lock("test.py", "alice")
        assert len(result["lock_token"]) > 0

    def test_acquire_sets_correct_expiry(self, manager):
        """Test that lock expiry is set correctly."""
        _, result = manager.acquire_lock("test.py", "alice", expires_minutes=10)
        expires_at = datetime.fromisoformat(result["expires_at"])
        now = _utcnow()
        assert expires_at > now
        assert expires_at <= now + timedelta(minutes=11)

    def test_acquire_with_custom_expiry(self, manager):
        """Test acquiring a lock with custom expiry."""
        _, result = manager.acquire_lock("test.py", "alice", expires_minutes=60)
        expires_at = datetime.fromisoformat(result["expires_at"])
        assert expires_at > _utcnow() + timedelta(minutes=59)

    def test_acquire_same_file_same_developer_refreshes(self, manager):
        """Test re-acquiring refreshes the lock."""
        _, res1 = manager.acquire_lock("test.py", "alice", expires_minutes=10)
        token1 = res1["lock_token"]

        success, res2 = manager.acquire_lock("test.py", "alice", expires_minutes=20)
        assert success is True
        assert res2["status"] == "refreshed"
        assert res2["lock_token"] == token1
        assert datetime.fromisoformat(res2["expires_at"]) > datetime.fromisoformat(
            res1["expires_at"]
        )

    def test_acquire_same_file_different_developer_conflicts(self, manager):
        """Test that a different developer gets a conflict."""
        manager.acquire_lock("test.py", "alice")
        success, result = manager.acquire_lock("test.py", "bob")
        assert success is False
        assert result["status"] == "conflict"
        assert result["locked_by"] == "alice"

    def test_acquire_after_release_succeeds(self, manager):
        """Test acquiring after release works."""
        _, res = manager.acquire_lock("test.py", "alice")
        manager.release_lock(res["lock_token"])
        success, result = manager.acquire_lock("test.py", "bob")
        assert success is True
        assert result["status"] == "acquired"

    def test_acquire_after_expiry_succeeds(self, manager):
        """Test acquiring after expiry works."""
        session = manager.Session()
        expired_lock = FileLock(
            file_path="expired.py",
            developer_id="oldie",
            lock_token="old_token",
            expires_at=_utcnow() - timedelta(minutes=1),
        )
        session.add(expired_lock)
        session.commit()
        session.close()

        success, result = manager.acquire_lock("expired.py", "newbie")
        assert success is True
        assert result["status"] == "acquired"
        assert result["lock_token"] != "old_token"

    def test_acquire_exception_handing(self, manager, monkeypatch):
        """Test exception handling during lock acquisition."""

        def mock_query(*args, **kwargs):
            raise Exception("DB Error")

        # Patch the session query to raise an exception
        monkeypatch.setattr("sqlalchemy.orm.Session.query", mock_query)

        success, result = manager.acquire_lock("error.py", "alice")
        assert success is False
        assert result["status"] == "error"
        assert "DB Error" in result["message"]

    def test_release_by_valid_token(self, manager):
        """Test releasing a lock by valid token."""
        _, res = manager.acquire_lock("test.py", "alice")
        success, result = manager.release_lock(res["lock_token"])
        assert success is True
        assert result["status"] == "released"

    def test_release_invalid_token_returns_not_found(self, manager):
        """Test releasing with invalid token fails."""
        success, result = manager.release_lock("invalid_token")
        assert success is False
        assert result["status"] == "not_found"

    def test_release_exception_handling(self, manager, monkeypatch):
        """Test exception handling during lock release."""

        def mock_query(*args, **kwargs):
            raise Exception("DB Error Release")

        monkeypatch.setattr("sqlalchemy.orm.Session.query", mock_query)

        success, result = manager.release_lock("some_token")
        assert success is False
        assert result["status"] == "error"
        assert "DB Error Release" in result["message"]

    def test_release_already_released_returns_not_found(self, manager):
        """Test double-release returns not_found."""
        _, res = manager.acquire_lock("test.py", "alice")
        manager.release_lock(res["lock_token"])
        success, result = manager.release_lock(res["lock_token"])
        assert success is False
        assert result["status"] == "not_found"

    def test_status_locked_file(self, manager):
        """Test status for a locked file."""
        manager.acquire_lock("test.py", "alice")
        status = manager.get_lock_status("test.py")
        assert status["is_locked"] is True
        assert status["locked_by"] == "alice"
        assert status["can_edit"] is False

    def test_status_unlocked_file(self, manager):
        """Test status for an unlocked file."""
        status = manager.get_lock_status("free.py")
        assert status["is_locked"] is False
        assert status["can_edit"] is True

    def test_get_all_active_locks_empty(self, manager):
        """Test empty active locks list."""
        assert len(manager.get_all_active_locks()) == 0

    def test_get_all_active_locks_returns_only_active(self, manager):
        """Test active locks excludes released locks."""
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
        """Test filtering locks by developer."""
        manager.acquire_lock("a.py", "alice")
        manager.acquire_lock("b.py", "alice")
        manager.acquire_lock("c.py", "bob")

        alice_locks = manager.get_locks_by_developer("alice")
        assert len(alice_locks) == 2

    def test_cleanup_expired_locks(self, manager):
        """Test cleanup of expired locks."""
        session = manager.Session()
        expired_lock = FileLock(
            file_path="expired.py",
            developer_id="oldie",
            lock_token="old_token",
            expires_at=_utcnow() - timedelta(minutes=1),
        )
        session.add(expired_lock)
        session.commit()

        count = manager.cleanup_expired_locks()
        assert count == 1

        status = manager.get_lock_status("expired.py")
        assert status["is_locked"] is False

    def test_cleanup_exception_handling(self, manager, monkeypatch):
        """Test exception handling during cleanup."""

        def mock_query(*args, **kwargs):
            raise Exception("Cleanup Error")

        monkeypatch.setattr("sqlalchemy.orm.Session.query", mock_query)

        count = manager.cleanup_expired_locks()
        assert count == 0

    def test_force_release_active_lock(self, manager):
        """Test force-releasing an active lock."""
        manager.acquire_lock("test.py", "alice")
        success, result = manager.force_release_lock("test.py", "admin")
        assert success is True
        status = manager.get_lock_status("test.py")
        assert status["is_locked"] is False

    def test_force_release_not_found(self, manager):
        """Test force-releasing a non-existent lock."""
        success, result = manager.force_release_lock("nonexistent.py", "admin")
        assert success is False
        assert result["status"] == "not_found"

    def test_force_release_exception_handling(self, manager, monkeypatch):
        """Test exception handling during force release."""

        def mock_query(*args, **kwargs):
            raise Exception("Force Release Error")

        monkeypatch.setattr("sqlalchemy.orm.Session.query", mock_query)

        success, result = manager.force_release_lock("test.py", "admin")
        assert success is False
        assert result["status"] == "error"

    def test_get_lock_history_all(self, manager):
        """Test getting all lock history."""
        manager.acquire_lock("a.py", "alice")
        _, res = manager.acquire_lock("b.py", "bob")
        manager.release_lock(res["lock_token"])

        history = manager.get_lock_history()
        assert len(history) == 2

    def test_get_lock_history_filtered_by_file(self, manager):
        """Test filtering lock history by file."""
        manager.acquire_lock("a.py", "alice")
        manager.acquire_lock("b.py", "bob")

        history = manager.get_lock_history(file_path="a.py")
        assert len(history) == 1
        assert history[0]["file_path"] == "a.py"

    def test_to_dict_coverage(self, manager):
        """Test FileLock.to_dict for coverage."""
        success, _ = manager.acquire_lock("test.py", "alice")
        session = manager.Session()
        lock = session.query(FileLock).filter(FileLock.file_path == "test.py").first()
        d = lock.to_dict()
        assert d["file_path"] == "test.py"
        assert d["developer_id"] == "alice"
        assert d["released_at"] is None
        session.close()
