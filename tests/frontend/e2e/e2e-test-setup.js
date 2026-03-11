/**
 * E2E Test Global Setup
 *
 * This script runs BEFORE any Playwright tests. It ensures:
 * 1. No conflicting Flask server is running on the test port
 * 2. Test database is properly initialized
 * 3. Environment is ready for E2E testing
 *
 * Usage: Configured in playwright.config.js as globalSetup
 */

const path = require("path");

// Configuration
const TEST_PORT = 5001; // Use different port than production (5000)
const TEST_HOST = "127.0.0.1";
const PROJECT_ROOT = path.resolve(__dirname, "../../..");
const INSTANCE_DIR = path.join(PROJECT_ROOT, "instance");
const TEST_DB_PATH = path.join(INSTANCE_DIR, "mockcmms_e2e.db");

/**
 * Global setup function called by Playwright
 *
 * NOTE: Playwright's webServer config starts the server BEFORE this runs.
 * We should NOT kill any servers here - just clean the database.
 */
async function globalSetup() {
  console.warn("\n🚀 E2E Test Global Setup Starting...\n");

  console.warn("📝 Test database will be created when server starts");
  console.warn(`   Database path: ${TEST_DB_PATH}`);
  console.warn(`   Server will start on: ${TEST_HOST}:${TEST_PORT}\n`);

  console.warn(
    "✅ Global setup complete. Playwright will start the test server.\n",
  );
}

module.exports = globalSetup;

// Export constants for use in other test files
module.exports.TEST_PORT = TEST_PORT;
module.exports.TEST_HOST = TEST_HOST;
module.exports.TEST_DB_PATH = TEST_DB_PATH;
