const { defineConfig, devices } = require("@playwright/test");
const fs = require("fs");
const path = require("path");

/**
 * Load environment variables from .env file.
 * This follows the same pattern as backend tests (conftest.py).
 */
function loadEnvFile() {
  const envPath = path.resolve(__dirname, ".env");
  const env = {};
  if (fs.existsSync(envPath)) {
    const content = fs.readFileSync(envPath, "utf8");
    for (const line of content.split("\n")) {
      const trimmed = line.trim();
      if (trimmed && !trimmed.startsWith("#")) {
        const [key, ...valueParts] = trimmed.split("=");
        if (key && valueParts.length > 0) {
          env[key.trim()] = valueParts.join("=").trim();
        }
      }
    }
  }
  return env;
}

/**
 * Check if a module is enabled based on .env configuration.
 * Follows same logic as backend tests: default to true unless explicitly disabled.
 */
function isModuleEnabled(envVars, moduleName) {
  const envVar = `${moduleName.toUpperCase()}_ENABLED`;
  const value = (envVars[envVar] || "true").toLowerCase();
  return ["true", "1", "t", "yes"].includes(value);
}

// Load .env settings
const envVars = loadEnvFile();
const planningEnabled = isModuleEnabled(envVars, "PLANNING");
const reportsEnabled = isModuleEnabled(envVars, "REPORTS");

// Dynamically build testMatch based on enabled modules
const testMatch = ["tests/frontend/e2e/**/*.spec.js"];
const testIgnore = [];

if (planningEnabled) {
  testMatch.push("apps/planning/tests/frontend/e2e/**/*.spec.js");
} else {
  testIgnore.push("**/apps/planning/**");
}

if (reportsEnabled) {
  testMatch.push("apps/reports/tests/frontend/e2e/**/*.spec.js");
} else {
  testIgnore.push("**/apps/reports/**");
}

/**
 * Playwright E2E Test Configuration
 *
 * Key Features:
 * - Uses port 5001 to avoid conflicts with production server (5000)
 * - Sets E2E_TEST=true for test database isolation
 * - Global setup ensures clean test environment
 * - Retries for flaky test resilience
 * - Respects .env settings for PLANNING_ENABLED and REPORTS_ENABLED (like backend tests)
 *   NOTE: Test files in apps/ should use test.skip() based on process.env to skip when disabled
 */

module.exports = defineConfig({
  testDir: ".",
  testMatch: testMatch,
  testIgnore: testIgnore,

  // Global setup runs before all tests
  globalSetup: require.resolve("./tests/frontend/e2e/e2e-test-setup.js"),

  // Global teardown runs after all tests (cleanup like pytest)
  globalTeardown: require.resolve("./tests/frontend/e2e/e2e-test-teardown.js"),

  // Test execution settings
  timeout: 30000,
  expect: {
    timeout: 10000, // Timeout for expect() assertions
    toHaveScreenshot: {
      maxDiffPixelRatio: 0.05, // Allow 5% diff for cross-platform (Win/Linux) rendering differences
      threshold: 0.2, // Color difference threshold
      animations: "disabled",
    },
  },

  // Unify snapshots across platforms (Windows/Linux) to avoid "missing snapshot" errors on CI
  // coupled with maxDiffPixelRatio above, this allows single-source-of-truth visual testing
  snapshotPathTemplate:
    "{testDir}/{testFileDir}/{testFileName}-snapshots/{arg}-{projectName}{ext}",

  // Retry failed tests for resilience
  retries: process.env.CI ? 2 : 1,

  // Run tests sequentially to avoid race conditions
  fullyParallel: false,
  workers: 1,

  // Reporter configuration
  reporter: [
    ["html", { outputFolder: "playwright-report", open: "never" }],
    ["list"],
  ],

  use: {
    // Use dedicated test port
    baseURL: "http://127.0.0.1:5001",
    timezoneId: "UTC", // Force UTC for absolute visual regression parity across OSs

    // Capture evidence on failure
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    trace: "retain-on-failure",

    // Navigation timeout
    navigationTimeout: 15000,
    actionTimeout: 10000,
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "firefox",
      use: { ...devices["Desktop Firefox"] },
    },
  ],

  // Web server configuration - starts Flask with test database
  webServer: {
    // Windows command to set environment variables and start server
    command: "node tests/frontend/e2e/pre-test-cleanup.js && python run.py",
    env: {
      E2E_TEST: "true",
      FLASK_RUN_PORT: "5001",
      // Pass through module settings from .env (follows backend test pattern)
      PLANNING_ENABLED: planningEnabled ? "true" : "false",
      REPORTS_ENABLED: reportsEnabled ? "true" : "false",
      FIXED_DATE_SEEDING: "2026-01-21", // Seed DB with this fixed date for consistent visual tests
    },
    url: "http://127.0.0.1:5001",

    // Don't reuse existing server - always start fresh for isolation
    reuseExistingServer: !process.env.CI,

    // Give server time to start
    timeout: 60000,

    // Show server output in console for debugging
    stdout: "pipe",
    stderr: "pipe",
  },
});
