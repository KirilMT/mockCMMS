// Collaborative File Locks — VS Code Extension
// Prevents merge conflicts by locking files when you start editing them.
//
// Requires: @supabase/supabase-js (run `npm install` in this directory)
// Reads credentials from workspace .env file.

const vscode = require("vscode");
const path = require("path");
const fs = require("fs");
const { spawn, execSync } = require("child_process");
const os = require("os");
const crypto = require("crypto");

/**
 * Per-workspace state directory (outside the repo) for transient files.
 * Defaults to $TMP/mockcmms_collab_<hash> unless COLLAB_STATE_DIR is set.
 */
function getStateDir(workspaceRoot) {
  const env = process.env.COLLAB_STATE_DIR;
  if (env) return env;
  try {
    const h = crypto
      .createHash("sha1")
      .update(workspaceRoot)
      .digest("hex")
      .slice(0, 8);
    const dir = path.join(os.tmpdir(), `mockcmms_collab_${h}`);
    if (!fs.existsSync(dir)) {
      try {
        fs.mkdirSync(dir, { recursive: true });
      } catch (e) {
        // Best effort: directory creation can race.
      }
    }
    return dir;
  } catch (e) {
    return os.tmpdir();
  }
}

let statusBarItem;
let supabaseClient = null;
let currentSubscription = null;
let watcherProcess = null;
let watcherHeartbeatInterval = null;
let watcherHeartbeatFile = null;
let outputChannel = null;
// Prevent duplicate startup notifications (file vs. log paths)
let startupNotificationShown = false;
let lastStartupNotificationKey = null;
let watcherHeartbeatTicks = 0;

/**
 * Show a startup notification once within a short window.
 * Both the file-polling and log-parsing paths should call this helper
 * to avoid duplicate VS Code popups for the same startup summary.
 */
function showStartupNotificationOnce(message, key) {
  try {
    // If we've recently shown a startup notification, skip duplicates
    if (startupNotificationShown) return;
    if (key && lastStartupNotificationKey === key) return;

    startupNotificationShown = true;
    lastStartupNotificationKey = key || null;

    vscode.window.showInformationMessage(message);

    // Clear the flag after a short debounce window so future separate
    // startups can still surface notifications.
    setTimeout(() => {
      startupNotificationShown = false;
      lastStartupNotificationKey = null;
    }, 5000);
  } catch (e) {
    // Best-effort: if showing fails, ignore and continue.
  }
}

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
  // Log deactivation start for debugging
  if (outputChannel) {
    outputChannel.appendLine(`[collab] VSCode deactivating - cleaning up...`);
  }

  const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri?.fsPath;
  // Use per-workspace state dir in OS temp for transient files
  const stateDir = workspaceRoot ? getStateDir(workspaceRoot) : os.tmpdir();
  const pidFile = workspaceRoot
    ? path.join(workspaceRoot, ".collab", ".daemon.pid")
    : null;

  // Read the actual PID from file (more reliable than watcherProcess.pid which may be a wrapper)
  let actualWatcherPid = null;
  if (pidFile && fs.existsSync(pidFile)) {
    try {
      const pidData = fs.readFileSync(pidFile, "utf-8").trim();
      if (pidData.startsWith("{")) {
        const meta = JSON.parse(pidData);
        actualWatcherPid = meta.pid;
      } else {
        actualWatcherPid = parseInt(pidData);
      }
      if (outputChannel) {
        outputChannel.appendLine(
          `[collab] Found watcher PID in file: ${actualWatcherPid}`,
        );
      }
    } catch (e) {
      if (outputChannel) {
        outputChannel.appendLine(
          `[collab] Failed to read PID file: ${e.message}`,
        );
      }
    }
  }

  // Gracefully terminate the watcher process using a stop-request file
  if (watcherProcess || actualWatcherPid) {
    const pidToKill = actualWatcherPid || watcherProcess?.pid;
    if (outputChannel) {
      outputChannel.appendLine(
        `[collab] Gracefully terminating watcher (PID: ${pidToKill})...`,
      );
    }

    const { execSync } = require("child_process");
    const path = require("path");
    const fsLocal = require("fs");

    // Helper to check if process is still alive
    const isProcessAlive = (pid) => {
      try {
        if (process.platform === "win32") {
          execSync(`tasklist /FI "PID eq ${pid}"`, { stdio: "pipe" });
          return true;
        } else {
          process.kill(pid, 0);
          return true;
        }
      } catch (e) {
        return false;
      }
    };

    // Prepare stop-request and shutdown file paths
    const stopFile = path.join(stateDir, ".stop_request");
    const shutdownFile = path.join(stateDir, ".shutdown_complete");

    try {
      try {
        // Write stop request (pid) and fsync to ensure watcher sees it quickly
        const fd = fsLocal.openSync(stopFile, "w");
        try {
          fsLocal.writeSync(fd, String(pidToKill));
          try {
            fsLocal.fsyncSync(fd);
          } catch (e) {
            /* ignore */
          }
        } finally {
          try {
            fsLocal.closeSync(fd);
          } catch (e) {
            /* ignore */
          }
        }
      } catch (e) {
        if (outputChannel)
          outputChannel.appendLine(
            `[collab] Failed to write stop_request: ${e.message}`,
          );
      }

      // Wait up to 10 seconds for graceful shutdown (give Python extra time)
      let waited = 0;
      let shutdownDetected = false;
      while (waited < 10000 && isProcessAlive(pidToKill)) {
        // Check if shutdown file was created (indicates clean shutdown)
        if (!shutdownDetected && fsLocal.existsSync(shutdownFile)) {
          shutdownDetected = true;
          if (outputChannel) {
            const kept = fsLocal.readFileSync(shutdownFile, "utf8").trim();
            outputChannel.appendLine(
              `[collab] Watcher shutdown detected: ${kept} locks kept`,
            );
          }
        }

        // Small delay (blocking)
        const startWait = Date.now();
        try {
          if (process.platform === "win32") {
            execSync("ping 127.0.0.1 -n 1 > nul", { stdio: "ignore" });
          } else {
            execSync("sleep 0.1", { stdio: "ignore" });
          }
        } catch (e) {
          // Ignore
        }
        waited += Date.now() - startWait;
      }

      // Cleanup stop file if still present
      try {
        if (fsLocal.existsSync(stopFile)) fsLocal.unlinkSync(stopFile);
      } catch (e) {
        /* ignore */
      }

      // Force kill if still alive
      if (isProcessAlive(pidToKill)) {
        if (outputChannel) {
          outputChannel.appendLine(
            `[collab] Watcher still alive after ${waited}ms, force killing...`,
          );
        }
        if (process.platform === "win32") {
          try {
            execSync(`taskkill /F /T /PID ${pidToKill}`, { stdio: "ignore" });
          } catch (e) {
            // Already dead
          }
        } else {
          try {
            process.kill(-pidToKill, "SIGKILL");
          } catch (e) {
            try {
              watcherProcess?.kill("SIGKILL");
            } catch (e2) {
              // Best effort fallback if process group kill fails.
            }
          }
        }
      } else {
        if (outputChannel) {
          outputChannel.appendLine(`[collab] Watcher shut down gracefully`);
        }
      }

      // Cleanup shutdown file (in the per-workspace state dir)
      if (fsLocal.existsSync(shutdownFile)) {
        try {
          fsLocal.unlinkSync(shutdownFile);
        } catch (e) {
          // Ignore
        }
      }

      // Cleanup PID file if it still exists (watcher should have removed it)
      const pidFilePath = path.join(
        path.join(workspaceRoot, ".collab"),
        ".daemon.pid",
      );
      if (fsLocal.existsSync(pidFilePath)) {
        try {
          fsLocal.unlinkSync(pidFilePath);
          if (outputChannel) {
            outputChannel.appendLine(`[collab] Cleaned up PID file`);
          }
        } catch (e) {
          // Ignore
        }
      }
    } catch (e) {
      if (outputChannel) {
        outputChannel.appendLine(
          `[collab] Error during shutdown: ${e.message}`,
        );
      }
    }

    // Stop heartbeat after shutdown attempt so watcher can observe it if needed
    if (watcherHeartbeatInterval) {
      try {
        clearInterval(watcherHeartbeatInterval);
      } catch (e) {
        // Ignore heartbeat timer cleanup failures.
      }
      watcherHeartbeatInterval = null;
    }
    if (watcherHeartbeatFile) {
      try {
        if (fs.existsSync(watcherHeartbeatFile))
          fs.unlinkSync(watcherHeartbeatFile);
      } catch (e) {
        // Ignore heartbeat marker cleanup failures.
      }
      watcherHeartbeatFile = null;
    }

    watcherProcess = null;
  } else {
    if (outputChannel) {
      outputChannel.appendLine(
        `[collab] No active watcher process to terminate`,
      );
    }

    // Even if no watcher process, clean up PID file if it exists
    try {
      const collabRoot = path.join(
        vscode.workspace.workspaceFolders[0].uri.fsPath,
        ".collab",
      );
      const pidFile = path.join(collabRoot, ".daemon.pid");
      if (fs.existsSync(pidFile)) {
        fs.unlinkSync(pidFile);
        if (outputChannel) {
          outputChannel.appendLine(`[collab] Cleaned up stale PID file`);
        }
      }
    } catch (e) {
      // Ignore
    }
  }

  // CRITICAL: Explicitly remove PID file even if process termination failed
  // This prevents stale PID detection when switching to PyCharm
  if (pidFile && fs.existsSync(pidFile)) {
    try {
      fs.unlinkSync(pidFile);
      if (outputChannel) {
        outputChannel.appendLine(`[collab] PID file removed: ${pidFile}`);
      }
    } catch (e) {
      if (outputChannel) {
        outputChannel.appendLine(
          `[collab] Failed to remove PID file: ${e.message}`,
        );
      }
    }
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
      // Smart shutdown: only release locks for files that are clean
      // in git status. Keep locks alive for files still being edited.
      let dirtyFiles = new Set();
      let gitFailed = false;
      try {
        const workspaceRoot =
          vscode.workspace.workspaceFolders?.[0]?.uri?.fsPath;
        if (workspaceRoot) {
          const gitOut = execSync("git status --porcelain", {
            cwd: workspaceRoot,
            timeout: 3000,
            encoding: "utf8",
          }).trim();
          if (gitOut) {
            for (const line of gitOut.split("\n")) {
              if (line.length > 3) {
                let fp = line.substring(3).trim();
                // Handle renames: take the destination path
                if (fp.includes(" -> ")) {
                  fp = fp.split(" -> ").pop().trim();
                }
                // Strip surrounding quotes
                if (fp.startsWith('"') && fp.endsWith('"')) {
                  fp = fp.slice(1, -1);
                }
                dirtyFiles.add(fp);
              }
            }
          }
        }
      } catch (e) {
        gitFailed = true;
        if (outputChannel) {
          outputChannel.appendLine(
            `[collab] WARNING: git status failed during shutdown: ${e.message}`,
          );
          outputChannel.appendLine(
            "[collab] Keeping all locks alive (safe default).",
          );
        }
      }

      if (gitFailed) {
        // Safe default: keep all locks, don't delete anything
        if (outputChannel) {
          outputChannel.appendLine(
            "[collab] All locks preserved (git status unavailable).",
          );
        }
      } else {
        // Query existing locks and release only clean-file ones
        supabaseClient
          .from("file_locks")
          .select("file_path")
          .eq("developer_id", config.user)
          .then((res) => {
            const locks = res?.data || [];
            let nKept = 0;
            let nReleased = 0;
            const releasePromises = [];
            for (const lock of locks) {
              const fp = lock.file_path;
              if (fp && !dirtyFiles.has(fp)) {
                nReleased++;
                releasePromises.push(
                  supabaseClient
                    .from("file_locks")
                    .delete()
                    .eq("file_path", fp)
                    .eq("developer_id", config.user)
                    .then(() => {})
                    .catch(() => {}),
                );
              } else if (fp) {
                nKept++;
              }
            }
            if (outputChannel) {
              outputChannel.appendLine(
                `[collab] Shutdown: kept ${nKept} lock(s), ` +
                  `released ${nReleased} lock(s).`,
              );
            }
            return Promise.all(releasePromises);
          })
          .catch(() => {});
      }
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

  let user = vars["DEVELOPER_ID"] || vars["USERNAME"];
  if (!user) {
    try {
      const { execSync } = require("child_process");
      const gitName = execSync("git config user.name", { cwd: workspaceRoot })
        .toString()
        .trim();
      if (gitName) user = gitName;
    } catch (e) {
      /* ignore git failure */
    }
  }
  if (!user) {
    user = require("os").userInfo().username || "unknown";
  }

  if (!url || !key) return null;
  return { url, key, user };
}

// =========================================================================
// Watcher Management
// =========================================================================
function getVSCodeWindowPid() {
  /**
   * Get the actual VSCode window process PID for reliable parent tracking.
   * The extension host process.pid is not the window process and may not
   * terminate when VSCode closes, leaving orphaned watchers.
   */
  try {
    // First choice: VSCODE_PID environment variable (most reliable)
    if (process.env.VSCODE_PID) {
      const pid = parseInt(process.env.VSCODE_PID, 10);
      if (pid > 0) {
        return pid;
      }
    }

    // Fallback: walk up process tree to find Code.exe
    if (process.platform === "win32") {
      try {
        const wmicOut = execSync(
          `wmic process where "ProcessId=${process.pid}" get ParentProcessId /value`,
          { encoding: "utf8", timeout: 5000 },
        );
        const match = wmicOut.match(/ParentProcessId=(\d+)/);
        if (match) {
          const parentPid = parseInt(match[1], 10);
          // Verify this is Code.exe
          const nameOut = execSync(
            `wmic process where "ProcessId=${parentPid}" get Name /value`,
            { encoding: "utf8", timeout: 5000 },
          );
          if (nameOut.toLowerCase().includes("code")) {
            return parentPid;
          }
        }
      } catch (e) {
        // WMIC failed, continue to next fallback
      }
    }

    // Last resort: use extension host PID (less reliable but better than nothing)
    return process.pid;
  } catch (e) {
    return process.pid;
  }
}

function startWatcher(context) {
  const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri?.fsPath;
  if (!workspaceRoot) return;

  // Log startup for debugging
  if (outputChannel) {
    outputChannel.appendLine(`[collab] VSCode extension starting...`);
    outputChannel.appendLine(`[collab] Workspace: ${workspaceRoot}`);
  }

  // Use per-workspace state dir for transient files (stop/shutdown)
  const stateDir = getStateDir(workspaceRoot);

  // Kill any orphaned watcher from previous session.
  // Prefer a graceful stop via the stop-request file so the watcher can
  // perform a clean shutdown and write logs. Only fall back to forceful
  // termination if the watcher does not respond within the grace period.
  const pidFile = path.join(workspaceRoot, ".collab", ".daemon.pid");
  if (fs.existsSync(pidFile)) {
    try {
      const pidData = fs.readFileSync(pidFile, "utf-8").trim();
      let pid = null;
      let parentPid = null;
      if (pidData.startsWith("{")) {
        const meta = JSON.parse(pidData);
        pid = meta.pid;
        parentPid = meta.parent_pid;
      } else {
        pid = parseInt(pidData);
      }

      if (pid) {
        if (outputChannel) {
          outputChannel.appendLine(
            `[collab] Cleaning up existing watcher (PID: ${pid}, parent: ${parentPid || "unknown"})`,
          );
        }

        const stopFile = path.join(stateDir, ".stop_request");
        const shutdownFile = path.join(stateDir, ".shutdown_complete");

        // Helper to check if a PID is alive
        const isProcessAlive = (p) => {
          try {
            if (process.platform === "win32") {
              execSync(`tasklist /FI "PID eq ${p}"`, { stdio: "pipe" });
              return true;
            } else {
              process.kill(p, 0);
              return true;
            }
          } catch (e) {
            return false;
          }
        };

        // Try graceful stop via stop-request file
        try {
          try {
            const fd = fs.openSync(stopFile, "w");
            try {
              fs.writeSync(fd, String(pid));
              try {
                fs.fsyncSync(fd);
              } catch (e) {
                /* ignore */
              }
            } finally {
              try {
                fs.closeSync(fd);
              } catch (e) {
                /* ignore */
              }
            }
          } catch (e) {
            if (outputChannel)
              outputChannel.appendLine(
                `[collab] Failed to write stop_request: ${e.message}`,
              );
          }

          // Wait up to 8s for graceful shutdown (poll)
          let waited = 0;
          let graceful = false;
          while (waited < 8000) {
            if (!isProcessAlive(pid)) {
              graceful = true;
              break;
            }
            if (fs.existsSync(shutdownFile)) {
              graceful = true;
              break;
            }
            try {
              if (process.platform === "win32") {
                execSync("ping 127.0.0.1 -n 1 > nul", { stdio: "ignore" });
                waited += 200;
              } else {
                execSync("sleep 0.2", { stdio: "ignore" });
                waited += 200;
              }
            } catch (e) {
              waited += 200;
            }
          }

          if (graceful) {
            if (fs.existsSync(shutdownFile)) {
              try {
                const kept = fs.readFileSync(shutdownFile, "utf8").trim();
                if (outputChannel)
                  outputChannel.appendLine(
                    `[collab] Watcher shutdown detected: ${kept} locks kept`,
                  );
              } catch (e) {
                /* ignore */
              }
              try {
                fs.unlinkSync(shutdownFile);
              } catch (e) {
                /* ignore */
              }
            } else {
              if (outputChannel)
                outputChannel.appendLine(
                  `[collab] Watcher process ${pid} exited (no shutdown marker)`,
                );
            }
            try {
              if (fs.existsSync(stopFile)) fs.unlinkSync(stopFile);
            } catch (e) {
              /* ignore */
            }
            try {
              if (fs.existsSync(pidFile)) fs.unlinkSync(pidFile);
            } catch (e) {
              /* ignore */
            }
            // graceful cleanup done
            // continue to starting new watcher
          } else {
            // Fallback to original behavior: attempt signal then force kill
            try {
              if (process.platform === "win32") {
                try {
                  process.kill(pid, "SIGINT");
                  if (outputChannel)
                    outputChannel.appendLine(
                      `[collab] Sent SIGINT to existing watcher PID ${pid}`,
                    );
                } catch (e) {
                  /* best effort */
                }
                try {
                  execSync("ping 127.0.0.1 -n 2 > nul", { stdio: "ignore" });
                } catch (e) {
                  /* ignore */
                }
                if (fs.existsSync(pidFile)) {
                  try {
                    execSync(`taskkill /F /T /PID ${pid}`, { stdio: "ignore" });
                  } catch (e) {
                    /* ignore */
                  }
                }
              } else {
                try {
                  process.kill(pid, "SIGTERM");
                } catch (e) {
                  /* best effort */
                }
              }
            } catch (e) {
              /* best effort cleanup */
            }
          }
        } catch (e) {
          /* best effort cleanup */
        }
      }
    } catch (e) {
      /* best effort cleanup */
    }
  }

  const venvPython = path.join(workspaceRoot, ".venv", "Scripts", "python.exe");
  const pythonCmd = fs.existsSync(venvPython) ? venvPython : "python";

  // Prefer the actual VS Code window PID for parent tracking so the watcher
  // shuts down when the window closes. Fallback to the extension host PID
  // if the window PID cannot be resolved.
  const resolvedWindowPid = getVSCodeWindowPid();
  const parentPid = resolvedWindowPid || process.pid;
  if (outputChannel) {
    outputChannel.appendLine(
      `[collab] Starting watcher with parent PID: ${parentPid} (VSCODE_PID: ${process.env.VSCODE_PID || "not set"}, ext_host=${process.pid})`,
    );
  }

  try {
    // Use a per-workspace state dir for transient files (heartbeat/summary)
    const stateDir = getStateDir(workspaceRoot);
    watcherProcess = spawn(
      pythonCmd,
      [
        path.join(workspaceRoot, ".collab", "core", "lock_client.py"),
        "watch",
        "--interval",
        "5",
        "--timeout",
        "0",
        "--parent-pid",
        parentPid.toString(),
        "--heartbeat-file",
        path.join(stateDir, ".vscode_heartbeat"),
        "--heartbeat-grace-seconds",
        "20",
      ],
      {
        cwd: workspaceRoot,
        stdio: ["ignore", "pipe", "pipe"],
        detached: false,
      },
    );

    // Heartbeat: touch a file periodically so the watcher can detect VSCode window close
    try {
      watcherHeartbeatFile = path.join(stateDir, ".vscode_heartbeat");
      // Ensure the state dir exists and create the heartbeat file immediately
      try {
        fs.mkdirSync(stateDir, { recursive: true });
      } catch (e) {
        // Ignore optional watcher startup edge-case failures.
      }
      fs.writeFileSync(watcherHeartbeatFile, `${Date.now()}\n`, {
        encoding: "utf8",
      });
      if (watcherHeartbeatInterval) {
        clearInterval(watcherHeartbeatInterval);
      }
      watcherHeartbeatInterval = setInterval(() => {
        try {
          if (watcherHeartbeatFile) {
            fs.writeFileSync(watcherHeartbeatFile, `${Date.now()}\n`, {
              encoding: "utf8",
            });
            // Throttled debug message to verify heartbeat updates without flooding
            try {
              watcherHeartbeatTicks = (watcherHeartbeatTicks || 0) + 1;
              if (outputChannel && watcherHeartbeatTicks % 5 === 0) {
                outputChannel.appendLine(
                  `[collab] Heartbeat updated (${watcherHeartbeatTicks})`,
                );
              }
            } catch (e) {
              /* ignore logging errors */
            }
          }
        } catch (e) {
          // Ignore
        }
      }, 2000);
    } catch (e) {
      // Ignore
    }

    if (outputChannel) {
      outputChannel.appendLine(
        `[collab] Watcher spawned (PID: ${watcherProcess.pid})`,
      );
    }

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
          // Detect startup reconciliation complete
          if (msg.includes("Startup reconciliation complete")) {
            handleStartupSummaryFromWatcher(msg);
          }
          // Collect startup summary stat lines (only active after trigger)
          processStartupSummaryLine(msg);
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

    // Poll for startup summary file (more reliable than log parsing).
    // For backward compatibility we check both the per-workspace state
    // directory (preferred) and the legacy in-repo `.collab/` location.
    const pollForStartupSummary = () => {
      const fs = require("fs");
      const path = require("path");
      const stateSummary = path.join(stateDir, ".startup_summary.json");
      const repoSummary = path.join(
        workspaceRoot,
        ".collab",
        ".startup_summary.json",
      );
      let summaryFile = null;

      if (fs.existsSync(stateSummary)) {
        summaryFile = stateSummary;
      } else if (fs.existsSync(repoSummary)) {
        // Legacy fallback for older extension instances that haven't been
        // reloaded yet. We prefer state dir but tolerate the repo file.
        summaryFile = repoSummary;
      }

      if (!summaryFile) return;

      try {
        const data = JSON.parse(fs.readFileSync(summaryFile, "utf8"));
        const msg =
          `Collab Locks — Startup Summary: [` +
          ` Re-adopted: ${data.readopted || 0} lock(s) |` +
          ` Stale released: ${data.stale_released || 0} lock(s) |` +
          ` Newly locked: ${data.newly_locked || 0} file(s) |` +
          ` Conflicts: ${data.conflicts || 0} file(s)` +
          ` ]`;

        try {
          showStartupNotificationOnce(msg, JSON.stringify(data));
        } catch (e) {
          try {
            vscode.window.showInformationMessage(msg);
          } catch (e2) {
            /* ignore */
          }
        }

        // Delete whichever summary we read so we don't show it again
        try {
          fs.unlinkSync(summaryFile);
        } catch (e) {
          // Ignore
        }
      } catch (e) {
        // Ignore parse errors
      }
    };

    // Poll every 500ms for up to 30 seconds after startup
    let pollCount = 0;
    const startupPollInterval = setInterval(() => {
      pollCount++;
      pollForStartupSummary();
      if (pollCount > 60) {
        // 30 seconds
        clearInterval(startupPollInterval);
      }
    }, 500);

    // Stop polling if process exits
    watcherProcess.on("exit", () => {
      clearInterval(startupPollInterval);
      watcherProcess = null;
    });
  } catch (e) {
    watcherProcess = null;
  }
}

// State for collecting startup summary
let collectingSummary = false;
let summaryBuffer = [];
let summaryTimeout = null;

/**
 * Handle startup summary from watcher and show VS Code popup.
 * Called when 'Startup reconciliation complete' is detected.
 */
function handleStartupSummaryFromWatcher(msg) {
  // Start collecting subsequent lines (stats come after this message)
  collectingSummary = true;
  summaryBuffer = [msg];

  // Clear any existing timeout
  if (summaryTimeout) {
    clearTimeout(summaryTimeout);
  }

  // Wait for stats lines to arrive, then show notification
  summaryTimeout = setTimeout(() => {
    showStartupNotification();
  }, 300); // Wait 300ms for stats lines
}

/**
 * Process a log line that might be a startup summary stat.
 * Called for every log line when collectingSummary is true.
 */
function processStartupSummaryLine(msg) {
  if (!collectingSummary) return;

  // Check if this is a stat line
  if (
    msg.match(/Re-adopted:\s+\d+/) ||
    msg.match(/Stale released:\s+\d+/) ||
    msg.match(/Newly locked:\s+\d+/) ||
    msg.match(/Conflicts:\s+\d+/)
  ) {
    summaryBuffer.push(msg);
  } else {
    // Non-stat line received - stop collecting and show notification
    collectingSummary = false;
    if (summaryTimeout) {
      clearTimeout(summaryTimeout);
      summaryTimeout = null;
    }
    showStartupNotification();
  }
}

/**
 * Show the startup summary notification from collected buffer.
 */
function showStartupNotification() {
  if (summaryBuffer.length === 0) return;

  // Parse stats from buffered messages
  const stats = {
    readopted: 0,
    staleReleased: 0,
    newlyLocked: 0,
    conflicts: 0,
  };

  for (const line of summaryBuffer) {
    const readoptedMatch = line.match(/Re-adopted:\s+(\d+)\s+lock/);
    const staleMatch = line.match(/Stale released:\s+(\d+)\s+lock/);
    const newMatch = line.match(/Newly locked:\s+(\d+)\s+file/);
    const conflictMatch = line.match(/Conflicts:\s+(\d+)\s+file/);

    if (readoptedMatch) stats.readopted = parseInt(readoptedMatch[1], 10);
    if (staleMatch) stats.staleReleased = parseInt(staleMatch[1], 10);
    if (newMatch) stats.newlyLocked = parseInt(newMatch[1], 10);
    if (conflictMatch) stats.conflicts = parseInt(conflictMatch[1], 10);
  }

  // Build notification message matching PyCharm format
  const notificationMsg = [
    `Re-adopted: ${stats.readopted} lock(s)`,
    `Stale released: ${stats.staleReleased} lock(s)`,
    `Newly locked: ${stats.newlyLocked} file(s)`,
    `Conflicts: ${stats.conflicts} file(s)`,
  ].join("\n");

  // Show VSCode notification (matches PyCharm popup)
  // Format: Title with newline then details
  const fullMessage = `Collab Locks — Startup Summary\n\n${notificationMsg}`;

  // Use single-shot helper so file-poll and log-collector don't both show the popup
  try {
    showStartupNotificationOnce(fullMessage, JSON.stringify(stats));
  } catch (e) {
    try {
      vscode.window.showInformationMessage(fullMessage);
    } catch (e2) {
      /* ignore */
    }
  }

  // Reset state
  collectingSummary = false;
  summaryBuffer = [];
  summaryTimeout = null;
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
