/**
 * E2E Test Global Setup for Planning App
 */

const { execSync } = require("child_process");
const path = require("path");
const fs = require("fs");
const http = require("http");

// Configuration
const TEST_PORT = 5002; // Use distinct port for Planning App E2E (5000=prod, 5001=core_e2e)
const TEST_HOST = "127.0.0.1";
// Adjust path to root: apps/planning/tests/frontend/e2e -> ../../../../..
const PROJECT_ROOT = path.resolve(__dirname, "../../../../..");
const INSTANCE_DIR = path.join(PROJECT_ROOT, "instance");
const TEST_DB_PATH = path.join(INSTANCE_DIR, "mockcmms_planning_e2e.db");

/**
 * Check if a server is already running on the specified port
 */
function isPortInUse(port, host = "127.0.0.1") {
  return new Promise((resolve) => {
    const req = http.request(
      {
        host,
        port,
        path: "/",
        method: "HEAD",
        timeout: 1000,
      },
      () => {
        resolve(true);
      },
    );

    req.on("error", () => {
      resolve(false);
    });

    req.on("timeout", () => {
      req.destroy();
      resolve(false);
    });

    req.end();
  });
}

async function tryDeleteFile(filePath, retries = 5) {
  for (let i = 0; i < retries; i++) {
    try {
      if (fs.existsSync(filePath)) {
        fs.unlinkSync(filePath);
        console.log(`✅ Removed file: ${filePath}`);
      }
      return true;
    } catch (e) {
      if (i === retries - 1) throw e;
      console.log(`   Detailed error: ${e.message}`);
      console.log(
        `⚠️  Delete failed (attempt ${i + 1}/${retries}), retrying in 1s...`,
      );
      await new Promise((resolve) => setTimeout(resolve, 1000));
    }
  }
}

/**
 * Clean up old test database
 */
async function cleanupTestDatabase() {
  if (fs.existsSync(TEST_DB_PATH)) {
    console.log(`🗑️  Removing old test database: ${TEST_DB_PATH}`);
    try {
      await tryDeleteFile(TEST_DB_PATH);
    } catch (e) {
      console.warn(`   WARNING: Failed to delete DB: ${e.message}`);
      console.warn(
        "   Proceeding anyway - setup might fail if file is locked.",
      );
    }
  }
}

/**
 * Global setup function called by Playwright
 */
async function globalSetup(config) {
  console.log("\n🚀 Planning App E2E Test Global Setup Starting...\n");

  await cleanupTestDatabase();

  console.log("📝 Test database will be created when server starts");
  console.log(`   Database path: ${TEST_DB_PATH}`);
  console.log(`   Server will start on: ${TEST_HOST}:${TEST_PORT}\n`);

  console.log(
    "✅ Global setup complete. Playwright will start the test server.\n",
  );
}

module.exports = globalSetup;

// Export constants for use in other test files
module.exports.TEST_PORT = TEST_PORT;
module.exports.TEST_HOST = TEST_HOST;
module.exports.TEST_DB_PATH = TEST_DB_PATH;
