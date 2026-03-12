/* eslint-disable no-console */
const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const TEST_PORT = 5001;
const MAX_RETRY_ATTEMPTS = 5;
const RETRY_DELAY_MS = 500;

// Define DB paths relative to this script
// Script location: tests/frontend/e2e/pre-test-cleanup.js
// Root is ../../..
const PROJECT_ROOT = path.resolve(__dirname, "../../..");
const INSTANCE_DIR = path.join(PROJECT_ROOT, "instance");
const TEST_DB_PATH = path.join(INSTANCE_DIR, "mockcmms_e2e.db");

const PLANNING_DB_PATH = path.join(
  PROJECT_ROOT,
  "apps",
  "planning",
  "instance",
  "planning_e2e.db",
);
const REPORTING_DB_PATH = path.join(
  PROJECT_ROOT,
  "apps",
  "reporting",
  "instance",
  "reporting_e2e.db",
);

/**
 * Sleep for specified milliseconds
 */
function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Kill all Python processes that might be holding database locks
 */
function killPythonProcesses() {
  console.log("🔪 Killing Python processes...");
  try {
    // Kill any python process running run.py
    execSync(
      "wmic process where \"CommandLine like '%run.py%'\" call terminate",
      {
        stdio: "ignore",
      },
    );
  } catch (_e) {
    // Command fails if no process found, which is fine
  }

  try {
    // Also try the window title method just in case
    execSync('taskkill /F /IM python.exe /FI "WINDOWTITLE eq Flask*" 2>nul', {
      stdio: "ignore",
    });
  } catch (_e) {
    // Ignore errors
  }

  try {
    // Force kill any python process started from this project location
    // This catches stray worker processes
    execSync(
      `wmic process where "CommandLine like '%mockCMMS%' and Name='python.exe'" call terminate`,
      {
        stdio: "ignore",
      },
    );
  } catch (_e) {
    // Ignore
  }
}

function killPort(port) {
  try {
    const output = execSync(`netstat -ano | findstr :${port}`).toString();
    const lines = output.trim().split("\n");
    const killedPids = new Set();

    for (const line of lines) {
      const parts = line.trim().split(/\s+/);
      const pid = parts[parts.length - 1]; // PID is the last column

      if (pid && /^\d+$/.test(pid) && pid !== "0" && !killedPids.has(pid)) {
        try {
          console.warn(
            `🔪 Killing stale process on port ${port} (PID: ${pid})...`,
          );
          execSync(`taskkill /F /PID ${pid}`, { stdio: "ignore" });
          killedPids.add(pid);
        } catch (killErr) {
          console.warn(`⚠️ Could not kill PID ${pid}: ${killErr.message}`);
        }
      }
    }

    return killedPids.size > 0;
  } catch (_e) {
    // Port not in use - this is fine
  }
  return false;
}

/**
 * Attempt to delete a database file with retries
 * This handles cases where the file is locked by a process that just got killed
 */
async function deleteDbWithRetry(dbPath) {
  if (!fs.existsSync(dbPath)) {
    return true;
  }

  for (let attempt = 1; attempt <= MAX_RETRY_ATTEMPTS; attempt++) {
    try {
      // Try to rename first (atomic check if locked) then delete
      if (fs.existsSync(dbPath)) {
        fs.unlinkSync(dbPath);
      }
      console.log(`✅ Deleted stale DB: ${dbPath}`);
      return true;
    } catch (e) {
      if (attempt < MAX_RETRY_ATTEMPTS) {
        console.warn(
          `⚠️ Attempt ${attempt}/${MAX_RETRY_ATTEMPTS} failed to delete ${path.basename(dbPath)}: ${e.code || e.message}`,
        );
        // Force GC garbage collection if available (requires node --expose-gc)
        if (global.gc) {
          global.gc();
        }
        // Wait before retrying - locks may take time to release
        await sleep(RETRY_DELAY_MS * attempt);
      } else {
        console.error(
          `❌ Failed to delete ${dbPath} after ${MAX_RETRY_ATTEMPTS} attempts. Test may fail.`,
        );
        // Try one last desperate measure: overwrite with empty
        try {
          fs.writeFileSync(dbPath, "");
          console.log("⚠️ Overwrote locked DB with empty content as fallback.");
        } catch (writeErr) {
          console.error("❌ Even overwrite failed:", writeErr.message);
        }
        return false;
      }
    }
  }
  return false;
}

/**
 * Also delete SQLite journal files (-wal, -shm) that may cause lock issues
 */
async function deleteDbJournalFiles(dbPath) {
  const journalFiles = [`${dbPath}-wal`, `${dbPath}-shm`, `${dbPath}-journal`];

  for (const journalFile of journalFiles) {
    if (fs.existsSync(journalFile)) {
      try {
        fs.unlinkSync(journalFile);
        console.log(`✅ Deleted journal file: ${path.basename(journalFile)}`);
      } catch (e) {
        console.warn(
          `⚠️ Could not delete ${path.basename(journalFile)}: ${e.message}`,
        );
      }
    }
  }
}

async function cleanupDatabases() {
  const dbs = [TEST_DB_PATH, PLANNING_DB_PATH, REPORTING_DB_PATH];

  for (const dbPath of dbs) {
    // First, try to delete any journal files
    await deleteDbJournalFiles(dbPath);
    // Then delete the main database file
    await deleteDbWithRetry(dbPath);
  }
}

// Main execution
async function main() {
  console.log("🧹 Running pre-test cleanup...");

  // Step 1: Kill any processes on the test port
  const killedPort = killPort(TEST_PORT);

  // Step 2: Kill any Python processes that might be holding DB locks
  killPythonProcesses();

  // Step 3: Wait a bit if we killed processes to let locks release
  if (killedPort) {
    console.log("⏳ Waiting for process termination...");
    await sleep(1000);
  }

  // Step 4: Clean up database files
  await cleanupDatabases();

  console.log("✨ Cleanup complete.");
}

main().catch((err) => {
  console.error("❌ Cleanup failed:", err);
  process.exit(1);
});
