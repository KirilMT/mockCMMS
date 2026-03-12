/**
 * Shared test utilities for E2E tests.
 *
 * Follows the same pattern as backend tests (conftest.py) for module toggling.
 */

const fs = require("fs");
const path = require("path");

/**
 * Load environment variables from .env file.
 */
function loadEnvFile() {
  const envPath = path.resolve(__dirname, "../../..", ".env");
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
 *
 * @param {string} moduleName - The module name (e.g., 'PLANNING', 'REPORTING')
 * @returns {boolean} - Whether the module is enabled
 */
function isModuleEnabled(moduleName) {
  const envVars = loadEnvFile();
  const envVar = `${moduleName.toUpperCase()}_ENABLED`;
  const value = (envVars[envVar] || "true").toLowerCase();
  return ["true", "1", "t", "yes"].includes(value);
}

/**
 * Skip all tests in a describe block if the module is disabled.
 * Use this at the top of modular app test files.
 *
 * @param {import('@playwright/test').test} test - The Playwright test object
 * @param {string} moduleName - The module name (e.g., 'PLANNING', 'REPORTING')
 * @returns {boolean} - Whether tests should run
 */
function skipIfModuleDisabled(test, moduleName) {
  const enabled = isModuleEnabled(moduleName);
  if (!enabled) {
    // eslint-disable-next-line no-console
    console.log(`Skipping ${moduleName} tests - module disabled in .env`);
    test.skip(true, `${moduleName} module is disabled in .env`);
  }
  return enabled;
}

module.exports = {
  isModuleEnabled,
  skipIfModuleDisabled,
  loadEnvFile,
};
