# VS Code Extension — Development Installation

## Prerequisites

- VS Code ^1.85.0
- Node.js (for `npm install`)

## Installation Steps

1. **Install dependencies**:

   ```bash
   cd .collab/vscode
   npm install
   ```

2. **Open in Development Mode**:

   - Open VS Code
   - Press `F1` → Run `Developer: Install Extension from Location...`
   - Select the `.collab/vscode/` directory
   - Alternatively, create a symlink:

     ```bash
     # Windows (PowerShell as Admin)
     New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.vscode\extensions\collab-file-locks" -Target ".collab\vscode"

     # Unix/macOS
     ln -s "$(pwd)/.collab/vscode" "$HOME/.vscode/extensions/collab-file-locks"
     ```

3. **Reload VS Code** — the extension activates automatically on startup.

## Commands

| Command | Title |
|---------|-------|
| `collabLocks.showAll` | Show All Locked Files |
| `collabLocks.releaseAll` | Release My Locks |
| `collabLocks.openDashboard` | Open Dashboard |

## Status Bar

The extension shows a status bar item on the right side:

- `$(unlock)` — current file is unlocked
- `$(lock) You` — you hold the lock
- `$(warning) Locked: @devname` — someone else holds the lock

## Configuration

The extension reads credentials from the workspace `.env` file:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
```

If credentials are missing, the extension shows a one-time setup message.
