# Collaborative Development Guide

This system provides a file locking mechanism to prevent merge conflicts and give developers visibility into who is working on what files.

## Overview

The system consists of:
1. **Lock Service**: A Flask microservice that manages locks in a database.
2. **Lock Dashboard**: A web interface to view active locks and history.
3. **Git Hooks**:
   - `pre-commit`: Automatically acquires/checks locks before you commit.
   - `pre-push`: Warns if your branch is significantly behind `main`.
4. **Python Client/CLI**: Tools for manual lock management.

## Getting Started

1. **Install Hooks**:
   ```bash
   bash scripts/setup_collab_dev.sh
   ```

2. **Start the Lock Service** (usually run by a lead or in a central location):
   ```bash
   python -m src.services.lock_manager_app
   ```
   By default, it runs on `http://localhost:5001`.

3. **Verify Connection**:
   ```bash
   python -m src.services.lock_client health
   ```

## Daily Workflow

1. **Working on files**:
   As you edit files and prepare to commit, the `pre-commit` hook will automatically try to acquire locks for you.
   - If a file is **free**, the lock is acquired and the commit proceeds.
   - If a file is **already locked by you**, the lock is refreshed and the commit proceeds.
   - If a file is **locked by someone else**, the commit is **blocked** to prevent conflicts.

2. **Checking Status**:
   Visit the dashboard at `http://localhost:5001/admin/lock-dashboard` to see who is working on what.

3. **Manual Locking** (Optional):
   If you want to lock a file before you even start editing:
   ```bash
   python -m src.services.lock_client acquire path/to/file.py
   ```

4. **Releasing Locks**:
   Locks expire automatically after 8 hours (default). They are also "released" in the system when someone else acquires them after they've expired.
   To release all your locks manually:
   ```bash
   python -m src.services.lock_client release-all
   ```

## Handling Stuck Locks

If a developer is away and you need to edit a file they have locked:
1. Contact the developer to see if they can release it.
2. Use the **Force Release** button on the Dashboard.
3. Use the CLI:
   ```bash
   # Note: This requires an admin_id for auditing
   # Currently implemented in API but not directly in CLI client for safety
   curl -X POST http://localhost:5001/api/locks/force-release -H "Content-Type: application/json" -d '{"file_path": "path/to/file.py", "admin_id": "your_name"}'
   ```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOCK_SERVER_URL` | URL of the lock service | `http://localhost:5001` |
| `LOCK_DB_PATH` | Path to the SQLite DB | `instance/locks.db` |
| `LOCK_SERVICE_PORT` | Port for the Flask app | `5001` |
| `LOCK_DEFAULT_EXPIRY_MINUTES` | Default lock duration | `480` (8 hours) |
| `LOCK_STRICT` | If 1, fail commit if server unreachable | `0` (fail-open) |
