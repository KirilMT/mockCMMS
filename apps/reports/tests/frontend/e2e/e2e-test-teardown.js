/**
 * E2E Test Global Teardown for Reports App
 */

const path = require("path");
const fs = require("fs");
const { execSync } = require("child_process");

const TEST_PORT = 5003;
const PROJECT_ROOT = path.resolve(__dirname, "../../../../..");
const INSTANCE_DIR = path.join(PROJECT_ROOT, "instance");
const TEST_DB_PATH = path.join(INSTANCE_DIR, "mockcmms_reports_e2e.db");

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

  if (fs.existsSync(TEST_DB_PATH)) {
    try {
      fs.unlinkSync(TEST_DB_PATH);
    } catch (error) {
      // Ignore cleanup errors
    }
  }
  console.log("\n✅ Global teardown complete.\n");
}

module.exports = globalTeardown;
