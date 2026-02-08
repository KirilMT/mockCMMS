/**
 * E2E Test Global Teardown for Reports App
 */

const path = require("path");
const fs = require("fs");
const { execSync } = require("child_process");

const TEST_PORT = 5003;
const PROJECT_ROOT = path.resolve(__dirname, "../../../../..");
const INSTANCE_DIR = path.join(PROJECT_ROOT, "instance");
// Main app E2E database
const MAIN_TEST_DB_PATH = path.join(INSTANCE_DIR, "mockcmms_e2e.db");
// Reports module E2E database (correct path)
const REPORTS_E2E_DB_PATH = path.join(
  PROJECT_ROOT,
  "apps",
  "reports",
  "instance",
  "reports_e2e.db",
);
// Planning module E2E database (for completeness)
const PLANNING_E2E_DB_PATH = path.join(
  PROJECT_ROOT,
  "apps",
  "planning",
  "instance",
  "planning_e2e.db",
);

function killProcessOnPort(port) {
  try {
    if (process.platform === "win32") {
      const output = execSync(`netstat -ano | findstr :${port}`).toString();
      const lines = output.trim().split("\n");
      if (lines.length > 0) {
        const parts = lines[0].trim().split(/\s+/);
        const pid = parts[parts.length - 1];
        if (pid) {
          try {
            execSync(`taskkill /PID ${pid} /F`);
          } catch (e) {
            // Ignore cleanup errors
          }
          return true;
        }
      }
    } else {
      const pid = execSync(`lsof -t -i:${port}`).toString().trim();
      if (pid) {
        process.kill(pid);
        return true;
      }
    }
  } catch (e) {
    // Ignore cleanup errors
  }
  return false;
}

async function globalTeardown(config) {
  console.log("\n🧹 Reports App E2E Test Global Teardown Starting...\n");
  killProcessOnPort(TEST_PORT);
  await new Promise((resolve) => setTimeout(resolve, 1500));

  // Clean up all E2E databases
  const dbsToClean = [
    MAIN_TEST_DB_PATH,
    REPORTS_E2E_DB_PATH,
    PLANNING_E2E_DB_PATH,
  ];

  for (const dbPath of dbsToClean) {
    if (fs.existsSync(dbPath)) {
      try {
        fs.unlinkSync(dbPath);
        console.log(`✅ Removed E2E database: ${dbPath}`);
      } catch (error) {
        console.warn(`⚠️  Could not remove ${dbPath}: ${error.message}`);
      }
    }
  }

  // Clean up empty instance directories
  const instanceDirs = [
    path.dirname(REPORTS_E2E_DB_PATH),
    path.dirname(PLANNING_E2E_DB_PATH),
  ];

  for (const dir of instanceDirs) {
    if (fs.existsSync(dir)) {
      try {
        const files = fs.readdirSync(dir);
        if (files.length === 0) {
          fs.rmdirSync(dir);
          console.log(`✅ Removed empty directory: ${dir}`);
        }
      } catch (error) {
        // Ignore errors
      }
    }
  }

  console.log("\n✅ Global teardown complete.\n");
}

module.exports = globalTeardown;
