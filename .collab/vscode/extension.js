// Collaborative File Locks — VS Code Extension
// Prevents merge conflicts by locking files when you start editing them.
//
// Requires: @supabase/supabase-js (run `npm install` in this directory)
// Reads credentials from workspace .env file.

const vscode = require('vscode');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

let statusBarItem;
let supabaseClient = null;
let currentSubscription = null;
let watcherProcess = null;

// =========================================================================
// Activation
// =========================================================================
function activate(context) {
    // Status bar item — right side
    statusBarItem = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Right,
        100
    );
    statusBarItem.text = '$(unlock) Locks';
    statusBarItem.tooltip = 'Collaborative File Locks — initializing...';
    statusBarItem.show();
    context.subscriptions.push(statusBarItem);

    // Load credentials from workspace .env
    const config = loadConfig();
    if (!config) {
        statusBarItem.text = '$(warning) Locks: No Config';
        statusBarItem.tooltip = 'Missing Supabase credentials in .env';
        vscode.window.showInformationMessage(
            'Collab Locks: Supabase credentials not found in .env. ' +
            'See .collab/README.md for setup instructions.',
            'Open Setup Guide'
        ).then(selection => {
            if (selection === 'Open Setup Guide') {
                const readmePath = path.join(
                    vscode.workspace.workspaceFolders?.[0]?.uri?.fsPath || '',
                    '.collab', 'README.md'
                );
                if (fs.existsSync(readmePath)) {
                    vscode.workspace.openTextDocument(readmePath)
                        .then(doc => vscode.window.showTextDocument(doc));
                }
            }
        });
        return;
    }

    // Initialize Supabase client
    try {
        const { createClient } = require('@supabase/supabase-js');
        supabaseClient = createClient(config.url, config.key);
    } catch (e) {
        statusBarItem.text = '$(warning) Locks: SDK Error';
        statusBarItem.tooltip = 'Failed to initialize Supabase client. Run npm install in .collab/vscode/';
        return;
    }

    // Start auto-watcher
    startWatcher(context);

    // Subscribe to realtime changes
    subscribeToChanges();

    // Update status bar when active editor changes
    context.subscriptions.push(
        vscode.window.onDidChangeActiveTextEditor(() => updateStatusBar())
    );

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('collabLocks.showAll', cmdShowAll),
        vscode.commands.registerCommand('collabLocks.releaseAll', cmdReleaseAll),
        vscode.commands.registerCommand('collabLocks.openDashboard', cmdOpenDashboard)
    );

    // Initial status bar update
    updateStatusBar();
}

// =========================================================================
// Deactivation
// =========================================================================
function deactivate() {
    // Stop watcher process
    if (watcherProcess) {
        try { watcherProcess.kill(); } catch (e) { /* best effort */ }
        watcherProcess = null;
    }

    // Unsubscribe from realtime
    if (currentSubscription) {
        try { currentSubscription.unsubscribe(); } catch (e) { /* best effort */ }
        currentSubscription = null;
    }

    // Release all locks held by this session
    if (supabaseClient) {
        const config = loadConfig();
        if (config && config.user) {
            supabaseClient.from('file_locks')
                .delete()
                .eq('developer_id', config.user)
                .then(() => {})
                .catch(() => {});
        }
    }
}

// =========================================================================
// Configuration
// =========================================================================
function loadConfig() {
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri?.fsPath;
    if (!workspaceRoot) return null;

    const envPath = path.join(workspaceRoot, '.env');
    if (!fs.existsSync(envPath)) return null;

    const envContent = fs.readFileSync(envPath, 'utf-8');
    const vars = {};
    for (const line of envContent.split('\n')) {
        const trimmed = line.trim();
        if (trimmed && !trimmed.startsWith('#')) {
            const eqIdx = trimmed.indexOf('=');
            if (eqIdx > 0) {
                const key = trimmed.substring(0, eqIdx).trim();
                const val = trimmed.substring(eqIdx + 1).trim();
                vars[key] = val;
            }
        }
    }

    const url = vars['SUPABASE_URL'];
    const key = vars['SUPABASE_SERVICE_ROLE_KEY'] || vars['SUPABASE_ANON_KEY'];
    const user = vars['USERNAME'] || require('os').userInfo().username || 'unknown';

    if (!url || !key) return null;
    return { url, key, user };
}

// =========================================================================
// Watcher Management
// =========================================================================
function startWatcher(context) {
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri?.fsPath;
    if (!workspaceRoot) return;

    // Find python executable
    const venvPython = path.join(workspaceRoot, '.venv', 'Scripts', 'python.exe');
    const pythonCmd = fs.existsSync(venvPython) ? venvPython : 'python';

    try {
        watcherProcess = spawn(pythonCmd, [
            '.collab/core/lock_client.py', 'watch',
            '--interval', '5', '--timeout', '480'
        ], {
            cwd: workspaceRoot,
            stdio: 'ignore',
            detached: true
        });

        watcherProcess.unref();
        watcherProcess.on('error', () => {
            // Watcher failed to start — non-fatal
            watcherProcess = null;
        });
    } catch (e) {
        // Non-fatal: watcher is a convenience, not a requirement
        watcherProcess = null;
    }
}

// =========================================================================
// Realtime Subscription
// =========================================================================
function subscribeToChanges() {
    if (!supabaseClient) return;
    try {
        currentSubscription = supabaseClient
            .channel('vscode-locks')
            .on('postgres_changes', {
                event: '*',
                schema: 'public',
                table: 'file_locks'
            }, (payload) => {
                updateStatusBar();

                // Show conflict warning if someone else locked the current file
                if (payload.eventType === 'INSERT' || payload.eventType === 'UPDATE') {
                    const newLock = payload.new;
                    const config = loadConfig();
                    if (newLock && config && newLock.developer_id !== config.user) {
                        const activeFile = getRelativeActivePath();
                        if (activeFile && newLock.file_path === activeFile) {
                            const lockTime = new Date(newLock.acquired_at)
                                .toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                            vscode.window.showWarningMessage(
                                `⚠ ${newLock.file_path} is locked by @${newLock.developer_id} ` +
                                `since ${lockTime}. Editing is not recommended.`
                            );
                        }
                    }
                }
            })
            .subscribe();
    } catch (e) {
        // Non-fatal
    }
}

// =========================================================================
// Status Bar
// =========================================================================
async function updateStatusBar() {
    if (!supabaseClient) return;

    const activeFile = getRelativeActivePath();
    if (!activeFile) {
        statusBarItem.text = '$(unlock) Locks';
        statusBarItem.tooltip = 'No file open';
        return;
    }

    try {
        const { data, error } = await supabaseClient
            .from('file_locks')
            .select('*')
            .eq('file_path', activeFile)
            .limit(1);

        if (error || !data || data.length === 0) {
            statusBarItem.text = '$(unlock) Unlocked';
            statusBarItem.tooltip = `${activeFile} is not locked`;
            return;
        }

        const lock = data[0];
        const config = loadConfig();
        const isMine = config && lock.developer_id === config.user;

        if (isMine) {
            statusBarItem.text = '$(lock) You';
            statusBarItem.tooltip = `You hold the lock on ${activeFile}`;
        } else {
            statusBarItem.text = `$(warning) Locked: @${lock.developer_id}`;
            statusBarItem.tooltip = `${activeFile} is locked by @${lock.developer_id} since ${lock.acquired_at}`;
        }
    } catch (e) {
        statusBarItem.text = '$(unlock) Locks';
    }
}

function getRelativeActivePath() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return null;

    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri?.fsPath;
    if (!workspaceRoot) return null;

    const absPath = editor.document.uri.fsPath;
    return path.relative(workspaceRoot, absPath).replace(/\\/g, '/');
}

// =========================================================================
// Commands
// =========================================================================
async function cmdShowAll() {
    if (!supabaseClient) {
        vscode.window.showErrorMessage('Collab Locks: Not connected to Supabase.');
        return;
    }

    const { data, error } = await supabaseClient
        .from('file_locks')
        .select('*')
        .order('acquired_at', { ascending: false });

    if (error) {
        vscode.window.showErrorMessage(`Collab Locks: ${error.message}`);
        return;
    }

    if (!data || data.length === 0) {
        vscode.window.showInformationMessage('No active file locks.');
        return;
    }

    const items = data.map(lock => ({
        label: `$(lock) ${lock.file_path}`,
        description: `@${lock.developer_id}`,
        detail: `Branch: ${lock.branch_name || 'N/A'} | Reason: ${lock.reason || 'N/A'}`
    }));

    vscode.window.showQuickPick(items, {
        placeHolder: `${data.length} active lock(s)`,
        canPickMany: false
    });
}

async function cmdReleaseAll() {
    if (!supabaseClient) {
        vscode.window.showErrorMessage('Collab Locks: Not connected to Supabase.');
        return;
    }

    const config = loadConfig();
    if (!config) return;

    const { data, error } = await supabaseClient
        .from('file_locks')
        .delete()
        .eq('developer_id', config.user)
        .select();

    if (error) {
        vscode.window.showErrorMessage(`Release failed: ${error.message}`);
        return;
    }

    const count = data ? data.length : 0;
    vscode.window.showInformationMessage(`Released ${count} lock(s).`);
    updateStatusBar();
}

function cmdOpenDashboard() {
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri?.fsPath;
    if (!workspaceRoot) return;

    // Find python and run the dashboard command
    const venvPython = path.join(workspaceRoot, '.venv', 'Scripts', 'python.exe');
    const pythonCmd = fs.existsSync(venvPython) ? venvPython : 'python';

    const terminal = vscode.window.createTerminal('Collab Dashboard');
    terminal.sendText(`${pythonCmd} .collab/core/lock_client.py dashboard`);
    terminal.show();
}

// =========================================================================
// Exports
// =========================================================================
module.exports = { activate, deactivate };
