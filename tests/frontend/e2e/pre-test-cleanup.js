/* eslint-disable no-console */
const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const TEST_PORT = 5001;

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
const REPORTS_DB_PATH = path.join(
  PROJECT_ROOT,
  "apps",
  "reports",
  "instance",
  "reports_e2e.db",
);

function killPort(port) {
  try {
    const output = execSync(`netstat -ano | findstr :${port}`).toString();
    const lines = output.trim().split("\n");
    if (lines.length > 0) {
      const parts = lines[0].trim().split(/\s+/);
      const pid = parts[parts.length - 1]; // PID is the last column
      if (pid && /^\d+$/.test(pid) && pid !== "0") {
        console.warn(
          `🔪 Killing stale process on port ${port} (PID: ${pid})...`,
        );
        execSync(`taskkill /F /PID ${pid}`);
        return true;
      }
    }
  } catch (e) {
    // Port not in use
  }
  return false;
}

function cleanupDatabases() {
  const dbs = [TEST_DB_PATH, PLANNING_DB_PATH, REPORTS_DB_PATH];
  for (const dbPath of dbs) {
    if (fs.existsSync(dbPath)) {
      try {
        fs.unlinkSync(dbPath);
        console.log(`✅ Deleted stale DB: ${dbPath}`);
      } catch (e) {
        console.warn(`⚠️ Failed to delete ${dbPath}: ${e.message}`);
        // Try one more time after a short delay if we just killed the process
        try {
          // Wait for lock release
          execSync("ping 127.0.0.1 -n 2 > nul");
          fs.unlinkSync(dbPath);
          console.log(`✅ Deleted stale DB (retry): ${dbPath}`);
        } catch (_retryErr) {
          console.error(
            `❌ FATAL: Could not delete ${dbPath}. Setup may fail.`,
          );
        }
      }
    }
  }
}

// Main execution
console.log("🧹 Running pre-test cleanup...");
killPort(TEST_PORT);
cleanupDatabases();
console.log("✨ Cleanup complete.");
