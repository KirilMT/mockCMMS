"""
lock_manager.py

File lock manager for collaborative development.
Prevents simultaneous edits to the same file by multiple developers.
"""

import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    create_engine,
    desc,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class FileLock(Base):
    __tablename__ = "file_locks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_path = Column(String(512), unique=True, nullable=False, index=True)
    developer_id = Column(String(100), nullable=False, index=True)
    developer_email = Column(String(255), nullable=True)
    lock_token = Column(String(255), unique=True, nullable=False)
    acquired_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, index=True)
    released_at = Column(DateTime, nullable=True, index=True)
    branch_name = Column(String(255), nullable=True)
    reason = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "file_path": self.file_path,
            "developer_id": self.developer_id,
            "developer_email": self.developer_email,
            "lock_token": self.lock_token,
            "acquired_at": self.acquired_at.isoformat() if self.acquired_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "released_at": self.released_at.isoformat() if self.released_at else None,
            "branch_name": self.branch_name,
            "reason": self.reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class LockManager:
    def __init__(self, db_path: Optional[str] = None):
        if not db_path:
            db_path = os.environ.get("LOCK_DB_PATH", "instance/locks.db")

        if db_path == ":memory:":
            self.engine = create_engine("sqlite:///:memory:")
        else:
            # Ensure directory exists
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
        session = self.Session()
        try:
            now = datetime.utcnow()
            expires_at = now + timedelta(minutes=expires_minutes)

            # Check if there's an active lock
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
                    # Refresh lock
                    existing_lock.expires_at = expires_at
                    existing_lock.branch_name = branch_name or existing_lock.branch_name
                    existing_lock.reason = reason or existing_lock.reason
                    session.commit()
                    self.logger.info(
                        f"Lock refreshed for {file_path} by {developer_id}"
                    )
                    return True, {
                        "status": "refreshed",
                        "lock_token": existing_lock.lock_token,
                        "expires_at": existing_lock.expires_at.isoformat(),
                    }
                else:
                    return False, {
                        "status": "conflict",
                        "message": f"File is already locked by {existing_lock.developer_id}",
                        "locked_by": existing_lock.developer_id,
                        "expires_at": existing_lock.expires_at.isoformat(),
                    }

            # No active lock, or previous lock expired/released
            # Handle the case where an expired/released lock exists (clean up for unique constraint if using file_path as unique)
            # In our schema, file_path is UNIQUE. So we must reuse or delete the old one if it's not active.
            old_lock = (
                session.query(FileLock).filter(FileLock.file_path == file_path).first()
            )

            lock_token = str(uuid.uuid4())
            if old_lock:
                # Update existing record (since file_path is unique)
                old_lock.developer_id = developer_id
                old_lock.developer_email = developer_email
                old_lock.lock_token = lock_token
                old_lock.acquired_at = now
                old_lock.expires_at = expires_at
                old_lock.released_at = None
                old_lock.branch_name = branch_name
                old_lock.reason = reason
                session.commit()
            else:
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

            self.logger.info(f"Lock acquired for {file_path} by {developer_id}")
            return True, {
                "status": "acquired",
                "lock_token": lock_token,
                "expires_at": expires_at.isoformat(),
            }
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error acquiring lock: {str(e)}")
            return False, {"status": "error", "message": str(e)}
        finally:
            session.close()

    def release_lock(self, lock_token: str) -> Tuple[bool, Dict]:
        session = self.Session()
        try:
            lock = (
                session.query(FileLock)
                .filter(
                    FileLock.lock_token == lock_token, FileLock.released_at.is_(None)
                )
                .first()
            )

            if not lock:
                return False, {
                    "status": "not_found",
                    "message": "Active lock with given token not found",
                }

            lock.released_at = datetime.utcnow()
            session.commit()
            self.logger.info(f"Lock released for {lock.file_path}")
            return True, {"status": "released", "file_path": lock.file_path}
        except Exception as e:
            session.rollback()
            return False, {"status": "error", "message": str(e)}
        finally:
            session.close()

    def get_lock_status(self, file_path: str) -> Dict:
        session = self.Session()
        try:
            now = datetime.utcnow()
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
                    "locked_at": lock.acquired_at.isoformat(),
                    "expires_at": lock.expires_at.isoformat(),
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
        session = self.Session()
        try:
            now = datetime.utcnow()
            locks = (
                session.query(FileLock)
                .filter(FileLock.released_at.is_(None), FileLock.expires_at > now)
                .all()
            )
            return [lock.to_dict() for lock in locks]
        finally:
            session.close()

    def get_locks_by_developer(self, developer_id: str) -> List[Dict]:
        session = self.Session()
        try:
            now = datetime.utcnow()
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
        session = self.Session()
        try:
            now = datetime.utcnow()
            expired_locks = (
                session.query(FileLock)
                .filter(FileLock.released_at.is_(None), FileLock.expires_at <= now)
                .all()
            )
            count = len(expired_locks)
            for lock in expired_locks:
                lock.released_at = now
            session.commit()
            if count > 0:
                self.logger.info(f"Cleaned up {count} expired locks")
            return count
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error during cleanup: {str(e)}")
            return 0
        finally:
            session.close()

    def force_release_lock(self, file_path: str, admin_id: str) -> Tuple[bool, Dict]:
        session = self.Session()
        try:
            lock = (
                session.query(FileLock)
                .filter(FileLock.file_path == file_path, FileLock.released_at.is_(None))
                .first()
            )

            if not lock:
                return False, {
                    "status": "not_found",
                    "message": "Active lock not found",
                }

            lock.released_at = datetime.utcnow()
            lock.reason = (lock.reason or "") + f" [Force released by {admin_id}]"
            session.commit()
            self.logger.info(f"Lock force-released for {file_path} by {admin_id}")
            return True, {"status": "released", "file_path": file_path}
        except Exception as e:
            session.rollback()
            return False, {"status": "error", "message": str(e)}
        finally:
            session.close()

    def get_lock_history(
        self, file_path: Optional[str] = None, limit: int = 50
    ) -> List[Dict]:
        session = self.Session()
        try:
            query = session.query(FileLock)
            if file_path:
                query = query.filter(FileLock.file_path == file_path)
            locks = query.order_by(desc(FileLock.acquired_at)).limit(limit).all()
            return [lock.to_dict() for lock in locks]
        finally:
            session.close()
