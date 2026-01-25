/**
 * E2E Test Global Teardown for Planning App
 */

const path = require("path");
const fs = require("fs");
const { execSync } = require("child_process");

// Configuration - must match e2e-test-setup.js
const TEST_PORT = 5002;
const PROJECT_ROOT = path.resolve(__dirname, "../../../../..");
const INSTANCE_DIR = path.join(PROJECT_ROOT, "instance");
const TEST_DB_PATH = path.join(INSTANCE_DIR, "mockcmms_planning_e2e.db");

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
  console.log("\n🧹 Planning App E2E Test Global Teardown Starting...\n");

  killProcessOnPort(TEST_PORT);
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
    }
  } else {
    console.log("   No test database to clean up.");
  }

  console.log("\n✅ Global teardown complete.\n");
}

module.exports = globalTeardown;
