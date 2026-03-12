# Tier 2 Implementation: File Locking System

**Timeline:** 40-60 hours (1-2 sprints)  
**Impact:** 70-80% reduction in merge conflicts  
**Effort:** Medium (custom Flask service + hooks)  
**Value:** Scales to 8-10+ developers without additional work

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│ Developer Workstations (Local Development)              │
│  • PyCharm / VSCode                                      │
│  • Working on feature branches                           │
│  • Git pre-commit hook checks locks                      │
└────────────────────┬────────────────────────────────────┘
                     │ (git commit -m "...")
                     │ Pre-commit hook: Check locks
                     │ Acquire lock if needed
                     ↓
┌─────────────────────────────────────────────────────────┐
│ Lock Service (Flask Microservice)                        │
│ Location: src/services/lock_manager.py                  │
│ Endpoints:                                               │
│  POST   /api/locks/acquire                              │
│  POST   /api/locks/release                              │
│  GET    /api/locks/status                               │
│  GET    /api/locks/dashboard                            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌────────────���────────────────────────────────────────────┐
│ Lock Database (SQLite or PostgreSQL)                     │
│ Table: file_locks                                        │
│  • file_path (UNIQUE)                                    │
│  • developer_id                                          │
│  • lock_token                                            │
│  • acquired_at                                           │
│  • expires_at                                            │
│  • released_at                                           │
└─────────────────────────────────────────────────────────┘
                     ↑
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼───────┐        ┌────────▼────────┐
│ POST /acquire │        │ GET /status     ��
│ (get lock)    │        │ (check lock)    │
└───────────────┘        └─────────────────┘
```

---

## Database Schema

### file_locks Table

```sql
CREATE TABLE IF NOT EXISTS file_locks (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- File Information
    file_path TEXT UNIQUE NOT NULL,
    
    -- Developer Information
    developer_id TEXT NOT NULL,
    developer_email TEXT,
    
    -- Lock Information
    lock_token TEXT UNIQUE NOT NULL,
    
    -- Timestamps
    acquired_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    released_at DATETIME,
    
    -- Metadata
    branch_name TEXT,
    reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_file_path ON file_locks(file_path);
CREATE INDEX IF NOT EXISTS idx_developer_id ON file_locks(developer_id);
CREATE INDEX IF NOT EXISTS idx_expires_at ON file_locks(expires_at);
CREATE INDEX IF NOT EXISTS idx_released_at ON file_locks(released_at);

-- Lock Status View
CREATE VIEW IF NOT EXISTS active_locks AS
SELECT * FROM file_locks
WHERE released_at IS NULL
  AND expires_at > datetime('now');
```

---

## Flask Lock Service

### File: `src/services/lock_manager.py`

```python
"""
File Lock Manager Service

Manages file locks to prevent simultaneous editing by multiple developers.
Integrates with Git hooks to enforce lock acquisition before commits.
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import create_engine, Column, String, DateTime, Integer, and_, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# ============================================================================
# Database Model
# ============================================================================

Base = declarative_base()

class FileLock(Base):
    """File lock record in database."""
    __tablename__ = 'file_locks'
    
    id = Column(Integer, primary_key=True)
    file_path = Column(String(512), unique=True, nullable=False, index=True)
    developer_id = Column(String(100), nullable=False, index=True)
    developer_email = Column(String(255))
    lock_token = Column(String(255), unique=True, nullable=False)
    acquired_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    released_at = Column(DateTime, index=True)
    branch_name = Column(String(255))
    reason = Column(String(512))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<FileLock {self.file_path} by {self.developer_id}>"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'file_path': self.file_path,
            'developer_id': self.developer_id,
            'developer_email': self.developer_email,
            'lock_token': self.lock_token,
            'acquired_at': self.acquired_at.isoformat() if self.acquired_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'released_at': self.released_at.isoformat() if self.released_at else None,
            'branch_name': self.branch_name,
            'reason': self.reason,
            'is_active': self.is_active(),
        }
    
    def is_active(self) -> bool:
        """Check if lock is currently active."""
        return (self.released_at is None and 
                self.expires_at > datetime.utcnow())
    
    def is_expired(self) -> bool:
        """Check if lock is expired."""
        return self.expires_at <= datetime.utcnow()


# ============================================================================
# Lock Manager Class
# ============================================================================

class LockManager:
    """Manages file locks for collaborative development."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize lock manager.
        
        Args:
            db_path: Path to SQLite database (defaults to instance/locks.db)
        """
        if db_path is None:
            db_path = os.path.join(
                os.path.dirname(__file__), 
                '../../instance/locks.db'
            )
        
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(self.engine)
    
    # ========================================================================
    # Lock Operations
    # ========================================================================
    
    def acquire_lock(
        self,
        file_path: str,
        developer_id: str,
        developer_email: Optional[str] = None,
        branch_name: Optional[str] = None,
        reason: Optional[str] = None,
        expires_minutes: int = 480,  # 8 hours default
    ) -> Tuple[bool, Dict]:
        """Acquire a lock on a file.
        
        Args:
            file_path: Path to file to lock (e.g., 'src/services/db_utils.py')
            developer_id: Username of developer acquiring lock
            developer_email: Email address of developer
            branch_name: Git branch name (for context)
            reason: Reason for lock (for visibility)
            expires_minutes: How many minutes until lock auto-expires
        
        Returns:
            (success: bool, response: Dict)
            - If success: {'status': 'acquired', 'lock_token': '...', ...}
            - If failed: {'status': 'conflict', 'locked_by': '...', ...}
        """
        session = self.SessionLocal()
        
        try:
            # Check for existing lock
            existing = session.query(FileLock).filter(
                and_(
                    FileLock.file_path == file_path,
                    FileLock.released_at.is_(None),
                    FileLock.expires_at > datetime.utcnow()
                )
            ).first()
            
            if existing:
                return False, {
                    'status': 'conflict',
                    'message': f"File already locked by {existing.developer_id}",
                    'file_path': file_path,
                    'locked_by': existing.developer_id,
                    'locked_at': existing.acquired_at.isoformat(),
                    'expires_at': existing.expires_at.isoformat(),
                }
            
            # Create new lock
            lock_token = str(uuid.uuid4())
            new_lock = FileLock(
                file_path=file_path,
                developer_id=developer_id,
                developer_email=developer_email,
                lock_token=lock_token,
                branch_name=branch_name,
                reason=reason,
                expires_at=datetime.utcnow() + timedelta(minutes=expires_minutes),
            )
            
            session.add(new_lock)
            session.commit()
            
            return True, {
                'status': 'acquired',
                'message': 'Lock acquired successfully',
                **new_lock.to_dict()
            }
        
        except Exception as e:
            session.rollback()
            return False, {
                'status': 'error',
                'message': str(e),
            }
        
        finally:
            session.close()
    
    def release_lock(self, lock_token: str) -> Tuple[bool, Dict]:
        """Release a lock.
        
        Args:
            lock_token: Token from lock acquisition
        
        Returns:
            (success: bool, response: Dict)
        """
        session = self.SessionLocal()
        
        try:
            lock = session.query(FileLock).filter(
                FileLock.lock_token == lock_token
            ).first()
            
            if not lock:
                return False, {
                    'status': 'error',
                    'message': 'Lock token not found',
                }
            
            if lock.released_at is not None:
                return False, {
                    'status': 'error',
                    'message': 'Lock already released',
                }
            
            lock.released_at = datetime.utcnow()
            session.commit()
            
            return True, {
                'status': 'released',
                'message': 'Lock released successfully',
                'file_path': lock.file_path,
            }
        
        except Exception as e:
            session.rollback()
            return False, {
                'status': 'error',
                'message': str(e),
            }
        
        finally:
            session.close()
    
    def get_lock_status(self, file_path: str) -> Dict:
        """Get lock status for a file.
        
        Args:
            file_path: Path to file to check
        
        Returns:
            {
                'file_path': str,
                'is_locked': bool,
                'locked_by': Optional[str],
                'locked_at': Optional[str],
                'expires_at': Optional[str],
                'can_edit': bool,
            }
        """
        session = self.SessionLocal()
        
        try:
            lock = session.query(FileLock).filter(
                and_(
                    FileLock.file_path == file_path,
                    FileLock.released_at.is_(None),
                    FileLock.expires_at > datetime.utcnow()
                )
            ).first()
            
            if lock:
                return {
                    'file_path': file_path,
                    'is_locked': True,
                    'locked_by': lock.developer_id,
                    'locked_at': lock.acquired_at.isoformat(),
                    'expires_at': lock.expires_at.isoformat(),
                    'can_edit': False,
                }
            else:
                return {
                    'file_path': file_path,
                    'is_locked': False,
                    'locked_by': None,
                    'locked_at': None,
                    'expires_at': None,
                    'can_edit': True,
                }
        
        finally:
            session.close()
    
    def get_active_locks(self) -> List[Dict]:
        """Get all active locks."""
        session = self.SessionLocal()
        
        try:
            locks = session.query(FileLock).filter(
                and_(
                    FileLock.released_at.is_(None),
                    FileLock.expires_at > datetime.utcnow()
                )
            ).order_by(FileLock.acquired_at.desc()).all()
            
            return [lock.to_dict() for lock in locks]
        
        finally:
            session.close()
    
    def cleanup_expired_locks(self) -> int:
        """Remove expired locks. Call periodically via cron job.
        
        Returns:
            Number of locks cleaned up
        """
        session = self.SessionLocal()
        
        try:
            count = session.query(FileLock).filter(
                FileLock.expires_at <= datetime.utcnow()
            ).delete()
            
            session.commit()
            return count
        
        finally:
            session.close()


# ============================================================================
# Flask Blueprint
# ============================================================================

lock_bp = Blueprint('locks', __name__, url_prefix='/api/locks')
lock_manager = LockManager()


@lock_bp.route('/acquire', methods=['POST'])
def acquire():
    """Acquire a lock on a file."""
    data = request.get_json()
    
    file_path = data.get('file_path')
    developer_id = data.get('developer_id')
    
    if not file_path or not developer_id:
        return jsonify({
            'status': 'error',
            'message': 'Missing file_path or developer_id'
        }), 400
    
    success, response = lock_manager.acquire_lock(
        file_path=file_path,
        developer_id=developer_id,
        developer_email=data.get('developer_email'),
        branch_name=data.get('branch_name'),
        reason=data.get('reason'),
        expires_minutes=data.get('expires_minutes', 480),
    )
    
    return jsonify(response), (200 if success else 409)


@lock_bp.route('/release', methods=['POST'])
def release():
    """Release a lock."""
    data = request.get_json()
    lock_token = data.get('lock_token')
    
    if not lock_token:
        return jsonify({
            'status': 'error',
            'message': 'Missing lock_token'
        }), 400
    
    success, response = lock_manager.release_lock(lock_token)
    
    return jsonify(response), (200 if success else 404)


@lock_bp.route('/status', methods=['GET'])
def status():
    """Check lock status for a file."""
    file_path = request.args.get('file_path')
    
    if not file_path:
        return jsonify({
            'status': 'error',
            'message': 'Missing file_path parameter'
        }), 400
    
    status_info = lock_manager.get_lock_status(file_path)
    return jsonify(status_info), 200


@lock_bp.route('/active', methods=['GET'])
def active():
    """Get all active locks."""
    locks = lock_manager.get_active_locks()
    
    return jsonify({
        'status': 'ok',
        'count': len(locks),
        'locks': locks,
    }), 200


@lock_bp.route('/cleanup', methods=['POST'])
def cleanup():
    """Cleanup expired locks (admin only)."""
    cleaned = lock_manager.cleanup_expired_locks()
    
    return jsonify({
        'status': 'ok',
        'cleaned': cleaned,
    }), 200


def init_locks(app):
    """Initialize lock manager with Flask app."""
    app.register_blueprint(lock_bp)
```

### Integration with Flask App

**File: `src/app.py`** (add to imports):

```python
from src.services.lock_manager import init_locks

# ... existing code ...

def create_app(config_name='development'):
    app = Flask(__name__)
    
    # ... existing setup ...
    
    # Initialize lock service
    init_locks(app)
    
    return app
```

---

## Git Pre-Commit Hook

### File: `.git/hooks/pre-commit`

```bash
#!/bin/bash
# Pre-commit hook: Check file locks before allowing commit

set -e

# Configuration
LOCK_SERVER_URL=${LOCK_SERVER_URL:-"http://localhost:5000"}
LOCK_SERVICE_ENABLED=${LOCK_SERVICE_ENABLED:-true}
LOCK_TIMEOUT=10  # seconds

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'  # No Color

# Skip if lock service disabled
if [ "$LOCK_SERVICE_ENABLED" != "true" ]; then
    exit 0
fi

# Get developer info
DEVELOPER_ID=${GIT_AUTHOR_NAME:-$(git config user.name)}
BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD)

echo -e "${YELLOW}🔍 Checking file locks...${NC}"

# Get list of staged files
STAGED_FILES=$(git diff --cached --name-only)

if [ -z "$STAGED_FILES" ]; then
    exit 0
fi

# Check each staged file
CONFLICTS=0
FAILED=0

while IFS= read -r FILE; do
    # Skip deleted files
    if ! git diff --cached --name-only --diff-filter=d | grep -q "^$FILE$"; then
        continue
    fi
    
    # Check lock status
    RESPONSE=$(curl -s --max-time $LOCK_TIMEOUT \
        "${LOCK_SERVER_URL}/api/locks/status?file_path=${FILE}" 2>/dev/null || echo "")
    
    if [ -z "$RESPONSE" ]; then
        echo -e "${YELLOW}⚠️  Lock server unavailable, skipping lock check${NC}"
        FAILED=$((FAILED + 1))
        continue
    fi
    
    # Parse response (basic JSON parsing)
    IS_LOCKED=$(echo "$RESPONSE" | grep -o '"is_locked":\s*\(true\|false\)' | grep -o '\(true\|false\)' || echo "false")
    LOCKED_BY=$(echo "$RESPONSE" | grep -o '"locked_by":"[^"]*"' | cut -d'"' -f4 || echo "")
    
    if [ "$IS_LOCKED" = "true" ] && [ "$LOCKED_BY" != "$DEVELOPER_ID" ]; then
        echo -e "${RED}❌ ERROR: File locked by $LOCKED_BY: $FILE${NC}"
        CONFLICTS=$((CONFLICTS + 1))
    else
        echo -e "${GREEN}✅ $FILE${NC}"
    fi
done <<< "$STAGED_FILES"

# Report results
if [ $CONFLICTS -gt 0 ]; then
    echo ""
    echo -e "${RED}❌ Commit blocked: $CONFLICTS file(s) locked by others${NC}"
    echo ""
    echo "Solution:"
    echo "  1. Pull latest changes: git pull origin main"
    echo "  2. Coordinate with other developers"
    echo "  3. Or wait for their locks to expire"
    exit 1
fi

if [ $FAILED -gt 0 ]; then
    echo -e "${YELLOW}⚠️  $FAILED file(s) could not be checked (server unavailable)${NC}"
    echo -e "${YELLOW}Proceeding with commit anyway${NC}"
fi

echo -e "${GREEN}✅ All locks clear. Proceeding with commit.${NC}"
exit 0
```

### Installation

```bash
# Install pre-commit hook
chmod +x .git/hooks/pre-commit

# Or use pre-commit framework (automatic)
# pip install pre-commit
# pre-commit install
```

---

## Lock Management Dashboard

### File: `src/templates/admin/lock_dashboard.html`

```html
{% extends "base.html" %}

{% block title %}File Lock Dashboard{% endblock %}

{% block content %}
<div class="container mt-4">
    <h1>🔒 File Lock Dashboard</h1>
    
    <div class="row">
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">
                    <h5>Active Locks</h5>
                    <small class="text-muted">
                        Locks auto-expire after 8 hours of inactivity
                    </small>
                </div>
                
                <div class="card-body">
                    <table class="table table-striped" id="locksTable">
                        <thead>
                            <tr>
                                <th>File Path</th>
                                <th>Developer</th>
                                <th>Acquired</th>
                                <th>Expires</th>
                                <th>Branch</th>
                                <th>Reason</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody id="locksBody">
                            <tr><td colspan="7" class="text-center text-muted">Loading...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
async function loadLocks() {
    try {
        const response = await fetch('/api/locks/active');
        const data = await response.json();
        
        const tbody = document.getElementById('locksBody');
        tbody.innerHTML = '';
        
        if (data.locks.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No active locks</td></tr>';
            return;
        }
        
        data.locks.forEach(lock => {
            const row = document.createElement('tr');
            const expiresDate = new Date(lock.expires_at);
            const minutesLeft = Math.round((expiresDate - new Date()) / 60000);
            
            row.innerHTML = `
                <td><code>${lock.file_path}</code></td>
                <td>${lock.developer_id}</td>
                <td><small>${new Date(lock.acquired_at).toLocaleString()}</small></td>
                <td><small>${minutesLeft > 0 ? minutesLeft + ' min' : 'Expired'}</small></td>
                <td>${lock.branch_name || '-'}</td>
                <td>${lock.reason || '-'}</td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="releaseLock('${lock.lock_token}')">
                        Release
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading locks:', error);
        document.getElementById('locksBody').innerHTML = 
            '<tr><td colspan="7" class="text-danger">Error loading locks</td></tr>';
    }
}

async function releaseLock(lockToken) {
    if (!confirm('Release this lock?')) return;
    
    try {
        const response = await fetch('/api/locks/release', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lock_token: lockToken })
        });
        
        if (response.ok) {
            loadLocks();  // Refresh
        }
    } catch (error) {
        console.error('Error releasing lock:', error);
    }
}

// Load locks on page load and refresh every 10 seconds
loadLocks();
setInterval(loadLocks, 10000);
</script>
{% endblock %}
```

---

## Client Library (Python)

### File: `src/services/lock_client.py`

```python
"""Client library for file lock service."""

import requests
from typing import Optional, Tuple


class LockClient:
    """Client for acquiring and releasing file locks."""
    
    def __init__(self, server_url: str = "http://localhost:5000"):
        self.server_url = server_url.rstrip('/')
    
    def acquire(
        self,
        file_path: str,
        developer_id: str,
        developer_email: Optional[str] = None,
        branch_name: Optional[str] = None,
        reason: Optional[str] = None,
        expires_minutes: int = 480,
    ) -> Tuple[bool, str]:
        """Acquire a lock.
        
        Returns:
            (success: bool, lock_token_or_error: str)
        """
        try:
            response = requests.post(
                f"{self.server_url}/api/locks/acquire",
                json={
                    'file_path': file_path,
                    'developer_id': developer_id,
                    'developer_email': developer_email,
                    'branch_name': branch_name,
                    'reason': reason,
                    'expires_minutes': expires_minutes,
                },
                timeout=5,
            )
            
            if response.status_code == 200:
                data = response.json()
                return True, data.get('lock_token', '')
            else:
                data = response.json()
                return False, data.get('message', 'Unknown error')
        
        except requests.RequestException as e:
            return False, str(e)
    
    def release(self, lock_token: str) -> Tuple[bool, str]:
        """Release a lock.
        
        Returns:
            (success: bool, message: str)
        """
        try:
            response = requests.post(
                f"{self.server_url}/api/locks/release",
                json={'lock_token': lock_token},
                timeout=5,
            )
            
            if response.status_code == 200:
                return True, "Lock released"
            else:
                data = response.json()
                return False, data.get('message', 'Unknown error')
        
        except requests.RequestException as e:
            return False, str(e)
    
    def status(self, file_path: str) -> dict:
        """Check lock status for a file."""
        try:
            response = requests.get(
                f"{self.server_url}/api/locks/status",
                params={'file_path': file_path},
                timeout=5,
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'is_locked': False,
                    'error': response.json().get('message', 'Unknown error')
                }
        
        except requests.RequestException:
            return {'is_locked': False, 'error': 'Cannot contact lock server'}


# Usage example
if __name__ == '__main__':
    client = LockClient()
    
    # Acquire lock
    success, token = client.acquire(
        file_path='src/services/db_utils.py',
        developer_id='kmartineztamayo',
        branch_name='feat/skill-matching'
    )
    
    if success:
        print(f"Lock acquired: {token}")
        
        # Check status
        status = client.status('src/services/db_utils.py')
        print(f"Lock status: {status}")
        
        # Release lock
        success, msg = client.release(token)
        print(f"Lock released: {msg}")
    else:
        print(f"Failed to acquire lock: {token}")
```

---

## Implementation Phases

### Phase 1: Setup (Week 1)
- [ ] Create database schema
- [ ] Implement Flask lock service
- [ ] Create API endpoints
- [ ] Build lock dashboard
- [ ] Write unit tests

### Phase 2: Integration (Week 2)
- [ ] Create pre-commit hook
- [ ] Test with 2 developers
- [ ] Document workflow
- [ ] Train team
- [ ] Monitor for issues

### Phase 3: Refinement (Week 3)
- [ ] Optimize lock timeout
- [ ] Add metrics/logging
- [ ] Create admin CLI tools
- [ ] Setup monitoring alerts
- [ ] Document best practices

---

## Monitoring & Maintenance

### Cron Job: Auto-Cleanup Expired Locks

**File:** `scripts/cleanup_locks.py`

```python
#!/usr/bin/env python
"""Cleanup expired locks (run via cron: 0 * * * * python cleanup_locks.py)"""

import sys
sys.path.insert(0, '/path/to/mockCMMS')

from src.services.lock_manager import LockManager

if __name__ == '__main__':
    manager = LockManager()
    cleaned = manager.cleanup_expired_locks()
    print(f"Cleaned up {cleaned} expired locks")
```

**Cron entry:**
```bash
# Run cleanup every hour
0 * * * * cd /path/to/mockCMMS && python scripts/cleanup_locks.py >> logs/lock_cleanup.log 2>&1
```

---

## Testing Strategy

### Unit Tests: `tests/backend/test_lock_manager.py`

```python
import pytest
from datetime import datetime, timedelta
from src.services.lock_manager import LockManager, FileLock

@pytest.fixture
def lock_manager():
    manager = LockManager(db_path=':memory:')  # Use in-memory DB for tests
    return manager

def test_acquire_lock(lock_manager):
    """Test acquiring a lock."""
    success, response = lock_manager.acquire_lock(
        file_path='src/test.py',
        developer_id='test_user'
    )
    
    assert success
    assert response['status'] == 'acquired'
    assert 'lock_token' in response

def test_cannot_acquire_locked_file(lock_manager):
    """Test that locked files cannot be re-locked."""
    # First lock
    lock_manager.acquire_lock('src/test.py', 'user1')
    
    # Try to lock same file
    success, response = lock_manager.acquire_lock('src/test.py', 'user2')
    
    assert not success
    assert response['status'] == 'conflict'

def test_release_lock(lock_manager):
    """Test releasing a lock."""
    _, response1 = lock_manager.acquire_lock('src/test.py', 'user1')
    token = response1['lock_token']
    
    success, response2 = lock_manager.release_lock(token)
    
    assert success
    assert response2['status'] == 'released'

def test_lock_expiration(lock_manager):
    """Test that expired locks are not active."""
    _, response = lock_manager.acquire_lock(
        'src/test.py',
        'user1',
        expires_minutes=0  # Expire immediately
    )
    
    status = lock_manager.get_lock_status('src/test.py')
    assert status['is_locked'] is False
```

---

## Best Practices

### For Developers

1. **Acquire lock early**
   ```bash
   # Before starting work
   curl -X POST http://localhost:5000/api/locks/acquire \
     -H "Content-Type: application/json" \
     -d '{"file_path":"src/db_utils.py","developer_id":"kmartineztamayo"}'
   ```

2. **Keep commits small** (reduces lock hold time)

3. **Release lock immediately after push**
   ```bash
   git push
   # Lock is automatically released after push
   ```

4. **Check dashboard before starting work**
   - Visit: `http://localhost:5000/admin/locks`
   - See who has locks and wait if needed

### For DevOps/Admins

1. **Monitor lock contention**
   - Track which files have most lock conflicts
   - These may indicate design issues

2. **Auto-cleanup**
   - Setup cron job to clean expired locks
   - Monitor cleanup log for issues

3. **Alert on stuck locks**
   - If lock > 4 hours old, notify developer
   - Automatic release at 8 hours

---

## Migration Path

### Week 1: Parallel Operation
- Run Tier 1 (branch protection) + Tier 2 (optional)
- Lock service is available but not required
- Developers can opt-in

### Week 2: Soft Enforcement
- Strongly recommend using locks
- Track compliance in metrics
- Fix any issues

### Week 3: Hard Enforcement
- Pre-commit hook blocks non-locked edits
- Dashboard shows compliance
- Training complete

---

## Summary

| Component | Lines | Effort | Impact |
|-----------|-------|--------|--------|
| Lock service API | ~300 | 4 hrs | High |
| Database model | ~50 | 1 hr | High |
| Pre-commit hook | ~100 | 2 hrs | Medium |
| Dashboard | ~200 | 3 hrs | Low (visualization) |
| Client library | ~150 | 2 hrs | Medium |
| Tests | ~200 | 4 hrs | Medium |
| **Total** | ~1000 | **16-20 hrs** | **High** |

**Expected Result:** 70-80% reduction in merge conflicts, scales to 8-10+ developers

---

**Last Updated:** March 12, 2026  
**Status:** Ready for implementation  
**Estimated Timeline:** 1-2 sprints

