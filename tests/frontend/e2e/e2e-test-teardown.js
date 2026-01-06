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
const PROJECT_ROOT = path.resolve(__dirname, "../..");
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
          console.log(`🔌 Killing server on port ${port} (PID: ${pid})`);
          try {
            execSync(`taskkill /PID ${pid} /F`);
          } catch (err) {
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
  } catch (e) {
    // Ignore errors (no process found)
  }
  return false;
}

/**
 * Global teardown function called by Playwright after all tests complete
 */
async function globalTeardown(config) {
  console.log("\n🧹 E2E Test Global Teardown Starting...\n");

  // Kill the server to release DB file lock.
  // This is safe now because:
  // 1. Tests are complete
  // 2. Reloader is disabled (single process via E2E_TEST env var)
  killProcessOnPort(TEST_PORT);
  // Wait for process to fully release file handles
  await new Promise((resolve) => setTimeout(resolve, 1500));

  // Step 1: Remove test database if it exists
  if (fs.existsSync(TEST_DB_PATH)) {
    try {
      fs.unlinkSync(TEST_DB_PATH);
      console.log(`✅ Removed test database: ${TEST_DB_PATH}`);
    } catch (error) {
      console.log(
        `⚠️  Could not remove test database (likely locked): ${error.message}`,
      );
      // Do not throw here - allow graceful exit. Setup will clean it next time.
    }
  } else {
    console.log("   No test database to clean up.");
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
