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
      // Use pipe correctly to filter for port
      const output = execSync(`netstat -ano | findstr :${port}`).toString();
      const lines = output.trim().split("\n");
      let killed = false;

      for (const line of lines) {
        // Only target LISTENING processes to avoid killing clients or TIME_WAIT
        if (line.includes(`:${port}`) && line.includes("LISTENING")) {
          const parts = line.trim().split(/\s+/);
          // PID is the last column
          const pid = parts[parts.length - 1];

          if (pid && /^\d+$/.test(pid) && pid !== "0") {
            console.warn(`🛑 Killing server on port ${port} (PID: ${pid})`);
            try {
              execSync(`taskkill /PID ${pid} /F`);
              killed = true;
            } catch (_err) {
              // Process might have already exited
            }
          }
        }
      }
      return killed;
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
  const REPORTING_DB_PATH = path.join(
    PROJECT_ROOT,
    "apps",
    "reporting",
    "instance",
    "reporting_e2e.db",
  );

  // Step 1: Remove test databases if they exist
  const dbs = [TEST_DB_PATH, PLANNING_DB_PATH, REPORTING_DB_PATH];

  for (const dbPath of dbs) {
    if (fs.existsSync(dbPath)) {
      console.log(`   Found database to delete: ${dbPath}`);
      await tryDeleteFile(dbPath);
    } else {
      console.log(`   No test database to clean up: ${path.basename(dbPath)}`);
    }
  }

  // Step 2: Remove instance directories ONLY if they are empty
  const instanceDirs = [
    INSTANCE_DIR,
    path.dirname(PLANNING_DB_PATH),
    path.dirname(REPORTING_DB_PATH),
  ];

  for (const dir of instanceDirs) {
    if (fs.existsSync(dir)) {
      try {
        const files = fs.readdirSync(dir);
        if (files.length === 0) {
          fs.rmdirSync(dir);
          console.log(`✅ Removed empty instance directory: ${dir}`);
        } else {
          // Check if valid production DBs exist to avoid confusing logs
          const prodFiles = files.filter(
            (f) =>
              f.endsWith(".db") && !f.includes("_test") && !f.includes("_e2e"),
          );
          if (prodFiles.length > 0) {
            console.log(
              `   Keeping instance directory (Production DBs present): ${path.basename(dir)}`,
            );
          } else {
            console.log(
              `   Instance directory not empty, keeping: ${path.basename(dir)} (${files.length} files)`,
            );
          }
        }
      } catch (error) {
        console.warn(
          `⚠️  Could not check/remove instance directory: ${error.message}`,
        );
      }
    }
  }

  console.log("\n✅ Global teardown complete.\n");
}

module.exports = globalTeardown;
