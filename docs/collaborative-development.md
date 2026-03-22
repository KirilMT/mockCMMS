# Collaborative Development Guide

This system provides a file locking mechanism to prevent merge conflicts and give developers visibility into who is working on what files. It is now a **pure serverless** system powered by GitHub Gists.

---

## 🛠️ Quick Setup (Windows)

The simplest way to set up your environment is to run the development setup script:

```powershell
.\scripts\setup-dev.ps1
```

This script will:

1. **Configure Credentials**: Prompt you for your GitHub Personal Access Token (PAT) and Gist ID.
2. **Install Hooks**: Automatically install the `pre-commit` and `post-commit` hooks into your local `.git` directory.
3. **Validate Environment**: Ensure your `.env` file is correctly populated with `GITHUB_TOKEN` and `LOCK_GIST_ID`.

---

## 💻 CLI Client Usage

The `lock_client.py` tool is used for manual lock management and is called automatically by Git hooks.

### Check File Status

```bash
python -m src.services.lock_client status path/to/file.py
```

### Acquire a Lock (Manual)

```bash
python -m src.services.lock_client acquire path/to/file.py --reason "Refactoring core logic"
```

### Acquire Multiple Locks (Batch)

```bash
python -m src.services.lock_client acquire-batch path/to/file1.py path/to/file2.py
```

### Release a Lock (Manual)

```bash
python -m src.services.lock_client release path/to/file.py
```

### Release All My Locks

```bash
python -m src.services.lock_client release-all
```

### Workflow & Automation

### 1. The Watcher (Automatic)

The system is now fully automated. The **Gist Lock Watcher** starts automatically in the background whenever you perform git operations (checkout, pull, merge). It monitors your local git status and locks files as soon as you edit them.

- **Zero Configuration**: No need to manually start the watcher. It launches on `git checkout` or `git pull`.
- **Auto-Lock**: Locks are acquired when `git status` detects modifications.
- **Conflict Alert**: If you edit a file locked by someone else, the watcher will print a **⚠️ WARNING** (or you can see the conflict on the dashboard).
- **Auto-Release**: Locks are released if you discard changes (rollback) or if you commit/push your work.
- **Self-Cleaning**: The background process automatically stops after 60 minutes of inactivity to save resources.

#### Manual Control (if needed)

While automation is recommended, you can manage the background process manually:

- **Status**: `python -m src.services.lock_client daemon-status`
- **Stop**: `python -m src.services.lock_client daemon-stop`
- **Start**: `python -m src.services.lock_client daemon-start`

### 2. Git Hooks (Safety Net)

- **`pre-commit`**: Automatically attempts to acquire locks for all files you are committing (safety check).
- **`post-commit`**: Automatically releases locks for the committed files.
- **`pre-push`**: Automatically releases all your remaining locks after a successful push.

---

## Lock Dashboard

Monitor all team activity via the standalone **Collaborative Explorer**.

1.  **Open the Dashboard**:
    - **Recommended**: Run `python -m src.services.lock_client dashboard`
      > [!TIP]
      > This command is the best way to open the explorer. It dynamically resolves your local path and forces your **default browser** to open the page.
    - **Editor Link**: [Collaborative Explorer](../src/services/collaborative_explorer.html)
      > [!NOTE]
      > Clicking this link in your editor (like VS Code) will open the **HTML source code**. To view the actual dashboard, use the command above or right-click the file and select "Open in Browser".
2.  **First-time usage**: The dashboard will prompt for your Token and Gist ID (check your `.env` file).
3.  **Real-time Monitoring**: Keep this tab open on a second monitor to see who is working on what across the entire team.

---

## Manual CLI Usage

If you prefer manual control, use the `lock_client` directly:

- **Check Status**: `python -m src.services.lock_client status <file>`
- **Acquire**: `python -m src.services.lock_client acquire <file> --reason "Feature X"`
- **Release**: `python -m src.services.lock_client release <file>`
- **List All**: `python -m src.services.lock_client active`
- **Release All**: `python -m src.services.lock_client release-all`

---

## ⚠️ Handling Stuck Locks

If a developer is away and you need to edit a locked file:

1. **Via Dashboard**: Open the dashboard, find the lock, and use the **Force Release** button.
2. **Via CLI**: Manually release the lock if you have the developer's permission, or manually edit the `locks.json` file in the GitHub Gist.

---

## ⚙️ Configuration Reference (.env)

| Variable                      | Description                                |
| :---------------------------- | :----------------------------------------- |
| `GITHUB_TOKEN`                | GitHub PAT with `gist` scope               |
| `LOCK_GIST_ID`                | Secret Gist ID for storage                 |
| `LOCK_DEFAULT_EXPIRY_MINUTES` | Auto-expiry (default 480 / 8 hours)        |
| `LOCK_STRICT`                 | If `1`, hooks fail-closed (block on error) |
