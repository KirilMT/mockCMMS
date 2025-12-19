const { defineConfig, devices } = require('@playwright/test');

/**
 * Playwright E2E Test Configuration
 * 
 * Key Features:
 * - Uses port 5001 to avoid conflicts with production server (5000)
 * - Sets E2E_TEST=true for test database isolation
 * - Global setup ensures clean test environment
 * - Retries for flaky test resilience
 */

module.exports = defineConfig({
  testDir: './tests/frontend/e2e',

  // Global setup runs before all tests
  globalSetup: require.resolve('./tests/frontend/e2e/e2e-test-setup.js'),

  // Global teardown runs after all tests (cleanup like pytest)
  globalTeardown: require.resolve('./tests/frontend/e2e/e2e-test-teardown.js'),

  // Test execution settings
  timeout: 30000,
  expect: {
    timeout: 10000, // Timeout for expect() assertions
  },

  // Retry failed tests for resilience
  retries: process.env.CI ? 2 : 1,

  // Run tests sequentially to avoid race conditions
  fullyParallel: false,
  workers: 1,

  // Reporter configuration
  reporter: [
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['list']
  ],

  use: {
    // Use dedicated test port
    baseURL: 'http://127.0.0.1:5001',

    // Capture evidence on failure
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',

    // Navigation timeout
    navigationTimeout: 15000,
    actionTimeout: 10000,
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] }
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] }
    },
  ],

  // Web server configuration - starts Flask with test database
  webServer: {
    // Windows command to set environment variables and start server
    command: 'python run.py',
    env: {
      E2E_TEST: 'true',
      FLASK_RUN_PORT: '5001',
    },
    url: 'http://127.0.0.1:5001',

    // Don't reuse existing server - always start fresh for isolation
    reuseExistingServer: !process.env.CI,

    // Give server time to start
    timeout: 60000,

    // Show server output in console for debugging
    stdout: 'pipe',
    stderr: 'pipe',
  },
});
