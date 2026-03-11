/**
 * E2E Test Global Setup for Reports App
 */

const { execSync } = require("child_process");
const path = require("path");
const fs = require("fs");
const http = require("http");

// Configuration
const TEST_PORT = 5003; // Distinct port for Reports App (5000=prod, 5001=core, 5002=planning)
const TEST_HOST = "127.0.0.1";
// Adjust path to root: apps/reports/tests/frontend/e2e -> ../../../../..
const PROJECT_ROOT = path.resolve(__dirname, "../../../../..");
const INSTANCE_DIR = path.join(PROJECT_ROOT, "instance");
const TEST_DB_PATH = path.join(INSTANCE_DIR, "mockcmms_reports_e2e.db");

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
      await new Promise((resolve) => setTimeout(resolve, 1000));
    }
  }
}

async function cleanupTestDatabase() {
  if (fs.existsSync(TEST_DB_PATH)) {
    try {
      await tryDeleteFile(TEST_DB_PATH);
    } catch (e) {
      // Ignore
    }
  }
}

async function globalSetup(config) {
  console.log("\n🚀 Reports App E2E Test Global Setup Starting...\n");
  await cleanupTestDatabase();
  console.log(`   Server will start on: ${TEST_HOST}:${TEST_PORT}\n`);
}

module.exports = globalSetup;
module.exports.TEST_PORT = TEST_PORT;
module.exports.TEST_HOST = TEST_HOST;
module.exports.TEST_DB_PATH = TEST_DB_PATH;
