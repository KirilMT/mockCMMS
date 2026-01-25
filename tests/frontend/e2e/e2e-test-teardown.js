/**
 * E2E Test Global Teardown
 *
 * This script runs AFTER all Playwright tests complete. It ensures:
 * 1. Test database is cleaned up
 * 2. Instance directory is removed if empty
 *
 * Follows same cleanup pattern as pytest's cleanup_test_artifacts fixture.
 */

const path = require("path");
const fs = require("fs");

const { execSync } = require("child_process");

// Configuration - must match e2e-test-setup.js
const TEST_PORT = 5001;
const PROJECT_ROOT = path.resolve(__dirname, "../../..");
const INSTANCE_DIR = path.join(PROJECT_ROOT, "instance");
const TEST_DB_PATH = path.join(INSTANCE_DIR, "mockcmms_e2e.db");

/**
 * Force kill process running on port
 */
function killProcessOnPort(port) {
  try {
    if (process.platform === "win32") {
      const output = execSync(`netstat -ano | findstr :${port}`).toString();
      const lines = output.trim().split("\n");
      if (lines.length > 0) {
        const parts = lines[0].trim().split(/\s+/);
        const pid = parts[parts.length - 1];
        if (pid) {
          console.warn(`🔌 Killing server on port ${port} (PID: ${pid})`);
          try {
            execSync(`taskkill /PID ${pid} /F`);
          } catch (_err) {
            // Process might have already exited
          }
          return true;
        }
      }
    } else {
      // Linux/Mac fallback (lsof)
      const pid = execSync(`lsof -t -i:${port}`).toString().trim();
      if (pid) {
        process.kill(pid);
        return true;
      }
    }
  } catch (_e) {
    // Ignore errors (no process found)
  }
  return false;
}

async function tryDeleteFile(filePath, retries = 5) {
  for (let i = 0; i < retries; i++) {
    try {
      if (fs.existsSync(filePath)) {
        fs.unlinkSync(filePath);
        console.warn(`✅ Removed test database: ${filePath}`);
      }
      return true;
    } catch (error) {
      if (i === retries - 1) {
        console.warn(
          `⚠️  Could not remove test database (likely locked): ${error.message}`,
        );
      } else {
        console.warn(
          `   Delete failed (attempt ${i + 1}/${retries}), retrying in 1s...`,
        );
        await new Promise((resolve) => setTimeout(resolve, 1000));
      }
    }
  }
}

/**
 * Global teardown function called by Playwright after all tests complete
 */
async function globalTeardown() {
  console.log("\n🧹 E2E Test Global Teardown Starting...\n");

  // Kill the server to release DB file lock.
  // This is safe now because:
  // 1. Tests are complete
  // 2. Reloader is disabled (single process via E2E_TEST env var)
  killProcessOnPort(TEST_PORT);
  // Wait for process to fully release file handles
  await new Promise((resolve) => setTimeout(resolve, 1500));

  // Modular App DB Paths
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

  // Step 1: Remove test databases if they exist
  const dbs = [TEST_DB_PATH, PLANNING_DB_PATH, REPORTS_DB_PATH];

  for (const dbPath of dbs) {
    if (fs.existsSync(dbPath)) {
      await tryDeleteFile(dbPath);
    } else {
      console.log(`   No test database to clean up: ${path.basename(dbPath)}`);
    }
  }

  // Step 2: Remove instance directory ONLY if it's empty
  // This ensures we never delete the directory if mockcmms.db exists
  if (fs.existsSync(INSTANCE_DIR)) {
    try {
      const files = fs.readdirSync(INSTANCE_DIR);
      if (files.length === 0) {
        fs.rmdirSync(INSTANCE_DIR);
        console.log(`✅ Removed empty instance directory: ${INSTANCE_DIR}`);
      } else {
        console.log(
          `   Instance directory not empty, keeping: ${files.join(", ")}`,
        );
      }
    } catch (error) {
      console.log(
        `⚠️  Could not check/remove instance directory: ${error.message}`,
      );
    }
  }

  console.log("\n✅ Global teardown complete.\n");
}

module.exports = globalTeardown;
