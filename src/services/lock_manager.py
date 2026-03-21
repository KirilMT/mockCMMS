"""lock_manager.py.

File lock manager for collaborative development. Prevents simultaneous edits to the same
file by multiple developers.
"""

import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy import String, create_engine, desc
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


def _utcnow() -> datetime:
    """Return current UTC time as naive datetime (SQLite compat)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""


class FileLock(Base):
    """Represents a file lock record in the database."""

    __tablename__ = "file_locks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    file_path: Mapped[str] = mapped_column(String(512), index=True)
    developer_id: Mapped[str] = mapped_column(String(100), index=True)
    developer_email: Mapped[Optional[str]] = mapped_column(String(255), default=None)
    lock_token: Mapped[str] = mapped_column(String(255), unique=True)
    acquired_at: Mapped[Optional[datetime]] = mapped_column(default=_utcnow)
    expires_at: Mapped[datetime] = mapped_column(index=True)
    released_at: Mapped[Optional[datetime]] = mapped_column(default=None, index=True)
    released_by: Mapped[Optional[str]] = mapped_column(String(100), default=None)
    branch_name: Mapped[Optional[str]] = mapped_column(String(255), default=None)
    reason: Mapped[Optional[str]] = mapped_column(String(512), default=None)
    created_at: Mapped[Optional[datetime]] = mapped_column(default=_utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        default=_utcnow, onupdate=_utcnow
    )

    def to_dict(self) -> Dict:
        """Convert lock to a dictionary representation."""
        return {
            "id": self.id,
            "file_path": self.file_path,
            "developer_id": self.developer_id,
            "developer_email": self.developer_email,
            "lock_token": self.lock_token,
            "acquired_at": (self.acquired_at.isoformat() if self.acquired_at else None),
            "expires_at": (self.expires_at.isoformat() if self.expires_at else None),
            "released_at": (self.released_at.isoformat() if self.released_at else None),
            "released_by": self.released_by,
            "branch_name": self.branch_name,
            "reason": self.reason,
            "created_at": (self.created_at.isoformat() if self.created_at else None),
            "updated_at": (self.updated_at.isoformat() if self.updated_at else None),
        }


class LockManager:
    """Manages file locks for collaborative development."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize the lock manager with a database path."""
        if not db_path:
            db_path = os.environ.get("LOCK_DB_PATH", "instance/locks.db")

        if db_path == ":memory:":
            self.engine = create_engine("sqlite:///:memory:")
        else:
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            self.engine = create_engine(f"sqlite:///{db_path}")

        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.logger = logging.getLogger(__name__)

    def acquire_lock(
        self,
        file_path: str,
        developer_id: str,
        developer_email: Optional[str] = None,
        branch_name: Optional[str] = None,
        reason: Optional[str] = None,
        expires_minutes: int = 480,
    ) -> Tuple[bool, Dict]:
        """Acquire a lock on a file for a developer."""
        session = self.Session()
        try:
            now = _utcnow()
            # 0 means "Eternal" (set to 525600 minutes = 1 year)
            effective_minutes = expires_minutes if expires_minutes > 0 else 525600
            expires_at = now + timedelta(minutes=effective_minutes)

            existing_lock = (
                session.query(FileLock)
                .filter(
                    FileLock.file_path == file_path,
                    FileLock.released_at.is_(None),
                    FileLock.expires_at > now,
                )
                .first()
            )

            if existing_lock:
                if existing_lock.developer_id == developer_id:
                    return False, {
                        "status": "conflict",
                        "message": "You already hold an active lock on this file",
                        "expires_at": (existing_lock.expires_at.isoformat()),
                    }
                else:
                    dev = existing_lock.developer_id
                    return False, {
                        "status": "conflict",
                        "message": (f"File is locked by {dev}"),
                        "locked_by": dev,
                        "expires_at": (existing_lock.expires_at.isoformat()),
                    }

            # Create a clean new record for the history
            lock_token = str(uuid.uuid4())
            new_lock = FileLock(
                file_path=file_path,
                developer_id=developer_id,
                developer_email=developer_email,
                lock_token=lock_token,
                acquired_at=now,
                expires_at=expires_at,
                branch_name=branch_name,
                reason=reason,
            )
            session.add(new_lock)
            session.commit()

            self.logger.info(
                "Lock acquired for %s by %s",
                file_path,
                developer_id,
            )
            return True, {
                "status": "acquired",
                "lock_token": lock_token,
                "expires_at": expires_at.isoformat(),
            }
        except Exception as e:
            session.rollback()
            self.logger.error("Error acquiring lock: %s", str(e))
            return False, {
                "status": "error",
                "message": str(e),
            }
        finally:
            session.close()

    def release_lock(self, lock_token: str) -> Tuple[bool, Dict]:
        """Release a lock by its token."""
        session = self.Session()
        try:
            lock = (
                session.query(FileLock)
                .filter(
                    FileLock.lock_token == lock_token,
                    FileLock.released_at.is_(None),
                )
                .first()
            )

            if not lock:
                return False, {
                    "status": "not_found",
                    "message": ("Active lock with given token not found"),
                }

            lock.released_at = _utcnow()
            lock.released_by = lock.developer_id  # Owner released it
            session.commit()
            self.logger.info("Lock released for %s", lock.file_path)
            return True, {
                "status": "released",
                "file_path": lock.file_path,
            }
        except Exception as e:
            session.rollback()
            return False, {
                "status": "error",
                "message": str(e),
            }
        finally:
            session.close()

    def release_lock_by_path(
        self, file_path: str, developer_id: str
    ) -> Tuple[bool, Dict]:
        """Release a lock by file path and developer ID."""
        session = self.Session()
        try:
            now = _utcnow()
            lock = (
                session.query(FileLock)
                .filter(
                    FileLock.file_path == file_path,
                    FileLock.developer_id == developer_id,
                    FileLock.released_at.is_(None),
                    FileLock.expires_at > now,
                )
                .first()
            )

            if not lock:
                return False, {
                    "status": "not_found",
                    "message": "No active lock found for this file/developer",
                }

            lock.released_at = now
            lock.released_by = developer_id  # Track who released it
            session.commit()
            return True, {"status": "released", "file_path": file_path}
        except Exception as e:
            session.rollback()
            return False, {"status": "error", "message": str(e)}
        finally:
            session.close()

    def get_lock_status(self, file_path: str) -> Dict:
        """Get the lock status of a file."""
        session = self.Session()
        try:
            now = _utcnow()
            lock = (
                session.query(FileLock)
                .filter(
                    FileLock.file_path == file_path,
                    FileLock.released_at.is_(None),
                    FileLock.expires_at > now,
                )
                .first()
            )

            if lock:
                return {
                    "file_path": file_path,
                    "is_locked": True,
                    "locked_by": lock.developer_id,
                    "locked_at": (
                        lock.acquired_at.isoformat() if lock.acquired_at else None
                    ),
                    "expires_at": (lock.expires_at.isoformat()),
                    "branch_name": lock.branch_name,
                    "can_edit": False,
                }
            else:
                return {
                    "file_path": file_path,
                    "is_locked": False,
                    "locked_by": None,
                    "locked_at": None,
                    "expires_at": None,
                    "branch_name": None,
                    "can_edit": True,
                }
        finally:
            session.close()

    def get_all_active_locks(self) -> List[Dict]:
        """Get all active (non-expired, non-released) locks."""
        session = self.Session()
        try:
            now = _utcnow()
            locks = (
                session.query(FileLock)
                .filter(
                    FileLock.released_at.is_(None),
                    FileLock.expires_at > now,
                )
                .all()
            )
            return [lock.to_dict() for lock in locks]
        finally:
            session.close()

    def get_locks_by_developer(self, developer_id: str) -> List[Dict]:
        """Get all active locks held by a developer."""
        session = self.Session()
        try:
            now = _utcnow()
            locks = (
                session.query(FileLock)
                .filter(
                    FileLock.developer_id == developer_id,
                    FileLock.released_at.is_(None),
                    FileLock.expires_at > now,
                )
                .all()
            )
            return [lock.to_dict() for lock in locks]
        finally:
            session.close()

    def cleanup_expired_locks(self) -> int:
        """Mark all expired locks as released."""
        session = self.Session()
        try:
            now = _utcnow()
            expired_locks = (
                session.query(FileLock)
                .filter(
                    FileLock.released_at.is_(None),
                    FileLock.expires_at <= now,
                )
                .all()
            )
            count = len(expired_locks)
            for lock in expired_locks:
                lock.released_at = now
            session.commit()
            if count > 0:
                self.logger.info("Cleaned up %d expired locks", count)
            return count
        except Exception as e:
            session.rollback()
            self.logger.error("Error during cleanup: %s", str(e))
            return 0
        finally:
            session.close()

    def force_release_lock(self, file_path: str, admin_id: str) -> Tuple[bool, Dict]:
        """Force-release a lock (admin operation)."""
        session = self.Session()
        try:
            lock = (
                session.query(FileLock)
                .filter(
                    FileLock.file_path == file_path,
                    FileLock.released_at.is_(None),
                )
                .first()
            )

            if not lock:
                return False, {
                    "status": "not_found",
                    "message": "Active lock not found",
                }

            lock.released_at = _utcnow()
            lock.released_by = admin_id  # Who triggered the force release
            reason_suffix = f" [Force released by {admin_id}]"
            lock.reason = (lock.reason or "") + reason_suffix
            session.commit()
            self.logger.info(
                "Lock force-released for %s by %s",
                file_path,
                admin_id,
            )
            return True, {
                "status": "released",
                "file_path": file_path,
            }
        except Exception as e:
            session.rollback()
            return False, {
                "status": "error",
                "message": str(e),
            }
        finally:
            session.close()

    def get_lock_history(
        self,
        file_path: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """Get lock history, optionally filtered by file."""
        session = self.Session()
        try:
            query = session.query(FileLock).filter(FileLock.released_at.is_not(None))
            if file_path:
                query = query.filter(FileLock.file_path == file_path)
            locks = query.order_by(desc(FileLock.acquired_at)).limit(limit).all()
            return [lock.to_dict() for lock in locks]
        finally:
            session.close()
