// Collaborative File Locks — VS Code Extension
// Prevents merge conflicts by locking files when you start editing them.
//
// Requires: @supabase/supabase-js (run `npm install` in this directory)
// Reads credentials from workspace .env file.

const vscode = require("vscode");
const path = require("path");
const fs = require("fs");
const { spawn } = require("child_process");

let statusBarItem;
let supabaseClient = null;
let currentSubscription = null;
let watcherProcess = null;
let outputChannel = null;

// =========================================================================
// Activation
// =========================================================================
function activate(context) {
  // Create output channel for watcher logs
  outputChannel = vscode.window.createOutputChannel("Collab Locks");
  context.subscriptions.push(outputChannel);

  // Status bar item — right side
  statusBarItem = vscode.window.createStatusBarItem(
    vscode.StatusBarAlignment.Right,
    100,
  );
  statusBarItem.text = "$(unlock) Locks";
  statusBarItem.tooltip = "Collaborative File Locks — initializing...";
  statusBarItem.command = "collabLocks.showAll";
  statusBarItem.show();
  context.subscriptions.push(statusBarItem);

  // Load credentials from workspace .env
  const config = loadConfig();
  if (!config) {
    statusBarItem.text = "$(warning) Locks: No Config";
    statusBarItem.tooltip = "Missing Supabase credentials in .env";
    vscode.window
      .showInformationMessage(
        "Collab Locks: Supabase credentials not found in .env. " +
          "See .collab/README.md for setup instructions.",
        "Open Setup Guide",
      )
      .then((selection) => {
        if (selection === "Open Setup Guide") {
          const readmePath = path.join(
            vscode.workspace.workspaceFolders?.[0]?.uri?.fsPath || "",
            ".collab",
            "README.md",
          );
          if (fs.existsSync(readmePath)) {
            vscode.workspace
              .openTextDocument(readmePath)
              .then((doc) => vscode.window.showTextDocument(doc));
          }
        }
      });
    return;
  }

  // Initialize Supabase client
  try {
    const { createClient } = require("@supabase/supabase-js");
    supabaseClient = createClient(config.url, config.key);
  } catch (e) {
    statusBarItem.text = "$(warning) Locks: SDK Error";
    statusBarItem.tooltip =
      "Failed to initialize Supabase client. " +
      "Run npm install in .collab/vscode/";
    return;
  }

  // Start auto-watcher (background, output piped to channel)
  startWatcher(context);

  // Subscribe to realtime changes
  subscribeToChanges();

  // Check lock status when switching files
  context.subscriptions.push(
    vscode.window.onDidChangeActiveTextEditor(() => {
      updateStatusBar();
      checkLockOnFileOpen();
    }),
  );

  // Register commands
  context.subscriptions.push(
    vscode.commands.registerCommand("collabLocks.showAll", cmdShowAll),
    vscode.commands.registerCommand("collabLocks.releaseAll", cmdReleaseAll),
    vscode.commands.registerCommand(
      "collabLocks.openDashboard",
      cmdOpenDashboard,
    ),
  );

  // Initial check
  updateStatusBar();
  checkLockOnFileOpen();
}

// =========================================================================
// Deactivation
// =========================================================================
function deactivate() {
  if (watcherProcess) {
    try {
      watcherProcess.kill();
    } catch (e) {
      /* best effort */
    }
    watcherProcess = null;
  }

  if (currentSubscription) {
    try {
      currentSubscription.unsubscribe();
    } catch (e) {
      /* best effort */
    }
    currentSubscription = null;
  }

  if (supabaseClient) {
    const config = loadConfig();
    if (config && config.user) {
      supabaseClient
        .from("file_locks")
        .delete()
        .eq("developer_id", config.user)
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

  const envPath = path.join(workspaceRoot, ".env");
  if (!fs.existsSync(envPath)) return null;

  const envContent = fs.readFileSync(envPath, "utf-8");
  const vars = {};
  for (const line of envContent.split("\n")) {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith("#")) {
      const eqIdx = trimmed.indexOf("=");
      if (eqIdx > 0) {
        const key = trimmed.substring(0, eqIdx).trim();
        const val = trimmed.substring(eqIdx + 1).trim();
        vars[key] = val;
      }
    }
  }

  const url = vars["SUPABASE_URL"];
  const key = vars["SUPABASE_SERVICE_ROLE_KEY"] || vars["SUPABASE_ANON_KEY"];
  const user =
    vars["USERNAME"] || require("os").userInfo().username || "unknown";

  if (!url || !key) return null;
  return { url, key, user };
}

// =========================================================================
// Watcher Management
// =========================================================================
function startWatcher(context) {
  const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri?.fsPath;
  if (!workspaceRoot) return;

  const venvPython = path.join(workspaceRoot, ".venv", "Scripts", "python.exe");
  const pythonCmd = fs.existsSync(venvPython) ? venvPython : "python";

  try {
    watcherProcess = spawn(
      pythonCmd,
      [
        path.join(workspaceRoot, ".collab", "core", "lock_client.py"),
        "watch",
        "--interval",
        "5",
        "--timeout",
        "480",
      ],
      {
        cwd: workspaceRoot,
        stdio: ["ignore", "pipe", "pipe"],
        detached: false,
      },
    );

    // Pipe stdout/stderr to Output Channel
    if (watcherProcess.stdout) {
      watcherProcess.stdout.on("data", (data) => {
        const msg = data.toString().trim();
        if (msg) {
          outputChannel.appendLine(msg);
          // Detect conflict lines
          if (msg.includes("CONFLICT")) {
            handleConflictFromWatcher(msg);
          }
        }
      });
    }
    if (watcherProcess.stderr) {
      watcherProcess.stderr.on("data", (data) => {
        const msg = data.toString().trim();
        if (msg) outputChannel.appendLine(`[ERR] ${msg}`);
      });
    }

    watcherProcess.on("error", () => {
      watcherProcess = null;
    });
    watcherProcess.on("exit", () => {
      watcherProcess = null;
    });
  } catch (e) {
    watcherProcess = null;
  }
}

/**
 * Parse a conflict line from the watcher and show a VS Code popup.
 */
function handleConflictFromWatcher(msg) {
  const match = msg.match(/CONFLICT:\s+(.+?)\s+is locked by\s+@(\S+)/);
  if (!match) return;

  const filePath = match[1];
  const owner = match[2];

  vscode.window
    .showWarningMessage(
      `🔒 ${filePath} is locked by @${owner}. ` +
        "Your changes may cause a merge conflict.",
      "Open Dashboard",
      "Show Details",
    )
    .then((selection) => {
      if (selection === "Open Dashboard") {
        cmdOpenDashboard();
      } else if (selection === "Show Details") {
        outputChannel.show(true);
      }
    });
}

// =========================================================================
// Lock Check on File Open
// =========================================================================
async function checkLockOnFileOpen() {
  if (!supabaseClient) return;

  const activeFile = getRelativeActivePath();
  if (!activeFile) return;

  try {
    const { data, error } = await supabaseClient
      .from("file_locks")
      .select("*")
      .eq("file_path", activeFile)
      .limit(1);

    if (error || !data || data.length === 0) return;

    const lock = data[0];
    const config = loadConfig();
    const isMine = config && lock.developer_id === config.user;

    if (!isMine) {
      const lockTime = new Date(lock.acquired_at).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      });
      vscode.window
        .showWarningMessage(
          `🔒 ${activeFile} is locked by @${lock.developer_id} ` +
            `since ${lockTime}. Editing may cause conflicts.`,
          "Open Dashboard",
          "Show Locks",
        )
        .then((selection) => {
          if (selection === "Open Dashboard") {
            cmdOpenDashboard();
          } else if (selection === "Show Locks") {
            cmdShowAll();
          }
        });
    }
  } catch (e) {
    // Non-fatal
  }
}

// =========================================================================
// Realtime Subscription
// =========================================================================
function subscribeToChanges() {
  if (!supabaseClient) return;
  try {
    currentSubscription = supabaseClient
      .channel("vscode-locks")
      .on(
        "postgres_changes",
        {
          event: "*",
          schema: "public",
          table: "file_locks",
        },
        (payload) => {
          updateStatusBar();

          if (
            payload.eventType === "INSERT" ||
            payload.eventType === "UPDATE"
          ) {
            const newLock = payload.new;
            const config = loadConfig();
            if (newLock && config && newLock.developer_id !== config.user) {
              const activeFile = getRelativeActivePath();
              if (activeFile && newLock.file_path === activeFile) {
                const lockTime = new Date(
                  newLock.acquired_at,
                ).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                });
                vscode.window
                  .showWarningMessage(
                    `🔒 ${newLock.file_path} is locked by ` +
                      `@${newLock.developer_id} since ` +
                      `${lockTime}. Editing may cause ` +
                      "conflicts.",
                    "Open Dashboard",
                    "Show Locks",
                  )
                  .then((selection) => {
                    if (selection === "Open Dashboard") {
                      cmdOpenDashboard();
                    } else if (selection === "Show Locks") {
                      cmdShowAll();
                    }
                  });
              }
            }
          }
        },
      )
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
    statusBarItem.text = "$(unlock) Locks";
    statusBarItem.tooltip = "No file open";
    return;
  }

  try {
    const { data, error } = await supabaseClient
      .from("file_locks")
      .select("*")
      .eq("file_path", activeFile)
      .limit(1);

    if (error || !data || data.length === 0) {
      statusBarItem.text = "$(unlock) Unlocked";
      statusBarItem.tooltip = `${activeFile} is not locked`;
      return;
    }

    const lock = data[0];
    const config = loadConfig();
    const isMine = config && lock.developer_id === config.user;

    if (isMine) {
      statusBarItem.text = "$(lock) You";
      statusBarItem.tooltip = `You hold the lock on ${activeFile}`;
    } else {
      statusBarItem.text = `$(warning) Locked: @${lock.developer_id}`;
      statusBarItem.tooltip =
        `${activeFile} is locked by ` +
        `@${lock.developer_id} since ${lock.acquired_at}`;
    }
  } catch (e) {
    statusBarItem.text = "$(unlock) Locks";
  }
}

function getRelativeActivePath() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) return null;

  const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri?.fsPath;
  if (!workspaceRoot) return null;

  const absPath = editor.document.uri.fsPath;
  return path.relative(workspaceRoot, absPath).replace(/\\/g, "/");
}

// =========================================================================
// Commands
// =========================================================================
async function cmdShowAll() {
  if (!supabaseClient) {
    vscode.window.showErrorMessage("Collab Locks: Not connected to Supabase.");
    return;
  }

  const { data, error } = await supabaseClient
    .from("file_locks")
    .select("*")
    .order("acquired_at", { ascending: false });

  if (error) {
    vscode.window.showErrorMessage(`Collab Locks: ${error.message}`);
    return;
  }

  if (!data || data.length === 0) {
    vscode.window.showInformationMessage("No active file locks.");
    return;
  }

  const items = data.map((lock) => ({
    label: `$(lock) ${lock.file_path}`,
    description: `@${lock.developer_id}`,
    detail:
      `Branch: ${lock.branch_name || "N/A"} | ` +
      `Reason: ${lock.reason || "N/A"}`,
  }));

  vscode.window.showQuickPick(items, {
    placeHolder: `${data.length} active lock(s)`,
    canPickMany: false,
  });
}

async function cmdReleaseAll() {
  if (!supabaseClient) {
    vscode.window.showErrorMessage("Collab Locks: Not connected to Supabase.");
    return;
  }

  const config = loadConfig();
  if (!config) return;

  const { data, error } = await supabaseClient
    .from("file_locks")
    .delete()
    .eq("developer_id", config.user)
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

  const collabPy = path.join(workspaceRoot, "collab.py");
  const venvPython = path.join(workspaceRoot, ".venv", "Scripts", "python.exe");
  const pythonCmd = fs.existsSync(venvPython) ? venvPython : "python";

  const terminal = vscode.window.createTerminal("Collab Dashboard");
  terminal.sendText(`${pythonCmd} "${collabPy}" dashboard`);
  terminal.show();
}

// =========================================================================
// Exports
// =========================================================================
module.exports = { activate, deactivate };
