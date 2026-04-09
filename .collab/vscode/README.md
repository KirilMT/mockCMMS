# VS Code Extension — Collaborative File Locks

## Automatic Setup (Recommended)

Run the development setup script — it auto-detects VS Code and installs the
extension dependencies for you:

```powershell
.\scripts\setup-dev.ps1
```

Then install the extension in VS Code:

1. Press `F1` → Run `Developer: Install Extension from Location...`
2. Select the `.collab/vscode/` directory
3. Reload VS Code — the extension activates automatically on startup

## Features

### Lock-on-Open Warning

When you open or switch to a file that is locked by another developer,
a popup immediately warns you with actionable buttons:

- **Open Dashboard** — opens the real-time lock dashboard
- **Show Locks** — lists all active locks in a quick pick

### Status Bar

The extension shows a status bar item on the right side:

- `$(unlock) Unlocked` — current file is unlocked
- `$(lock) You` — you hold the lock
- `$(warning) Locked: @devname` — someone else holds the lock

Click it to see all active locks.

### Output Channel

Watcher logs are piped to the **Collab Locks** output channel.
Open via: **View > Output > Collab Locks** (dropdown).

Conflict events appear in the output channel with timestamps and
details. When a conflict is detected from the watcher, a popup
automatically appears with options to open the dashboard or view logs.
Physical logs are persisted in `.collab/logs/application.log` and `.collab/logs/errors.log`.

### Commands

| Command                     | Title                 |
| --------------------------- | --------------------- |
| `collabLocks.showAll`       | Show All Locked Files |
| `collabLocks.releaseAll`    | Release My Locks      |
| `collabLocks.openDashboard` | Open Dashboard        |

## Configuration

The extension reads credentials from the workspace `.env` file:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
```

### Developer Identity

By default, the extension derives your identity from `git config user.name`. If not found, it falls back to the system username. You can override this by setting `DEVELOPER_ID` in your `.env` file.

If credentials are missing, the extension shows a one-time setup message.
