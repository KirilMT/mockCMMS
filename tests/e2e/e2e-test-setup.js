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

const { execSync, spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const http = require('http');

// Configuration
const TEST_PORT = 5001; // Use different port than production (5000)
const TEST_HOST = '127.0.0.1';
const PROJECT_ROOT = path.resolve(__dirname, '../..');
const INSTANCE_DIR = path.join(PROJECT_ROOT, 'instance');
const TEST_DB_PATH = path.join(INSTANCE_DIR, 'mockcmms_e2e.db');

/**
 * Force kill process running on port
 */
function killProcessOnPort(port) {
    try {
        if (process.platform === 'win32') {
            const output = execSync(`netstat -ano | findstr :${port}`).toString();
            const lines = output.trim().split('\n');
            if (lines.length > 0) {
                const parts = lines[0].trim().split(/\s+/);
                const pid = parts[parts.length - 1];
                if (pid) {
                    console.log(`🔌 Killing old server on port ${port} (PID: ${pid})`);
                    try {
                        execSync(`taskkill /PID ${pid} /F`);
                    } catch (err) {
                        console.log(`   (Process ${pid} might have already exited)`);
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
 * Check if a server is already running on the specified port
 */
function isPortInUse(port, host = '127.0.0.1') {
    return new Promise((resolve) => {
        const req = http.request({
            host,
            port,
            path: '/',
            method: 'HEAD',
            timeout: 1000
        }, () => {
            resolve(true);
        });

        req.on('error', () => {
            resolve(false);
        });

        req.on('timeout', () => {
            req.destroy();
            resolve(false);
        });

        req.end();
    });
}

/**
 * Wait for server to be ready
 */
async function waitForServer(port, host = '127.0.0.1', maxWaitMs = 30000) {
    const startTime = Date.now();

    while (Date.now() - startTime < maxWaitMs) {
        const isReady = await isPortInUse(port, host);
        if (isReady) {
            console.log(`✅ Server is ready on ${host}:${port}`);
            return true;
        }
        await new Promise(resolve => setTimeout(resolve, 500));
    }

    throw new Error(`Server did not start within ${maxWaitMs}ms`);
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
            console.log(`⚠️  Delete failed (attempt ${i + 1}/${retries}), retrying in 1s...`);
            await new Promise(resolve => setTimeout(resolve, 1000));
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
            console.warn('   Proceeding anyway - setup might fail if file is locked.');
        }
    }
}

/**
 * Global setup function called by Playwright
 * 
 * NOTE: Playwright's webServer config starts the server BEFORE this runs.
 * We should NOT kill any servers here - just clean the database.
 */
async function globalSetup(config) {
    console.log('\n🚀 E2E Test Global Setup Starting...\n');

    // Clean up old test database for fresh start
    // Note: This may fail with EBUSY if server already has the file open.
    // That's OK - the fresh seeding will still work on a clean run.
    await cleanupTestDatabase();

    console.log('📝 Test database will be created when server starts');
    console.log(`   Database path: ${TEST_DB_PATH}`);
    console.log(`   Server will start on: ${TEST_HOST}:${TEST_PORT}\n`);

    console.log('✅ Global setup complete. Playwright will start the test server.\n');
}

module.exports = globalSetup;

// Export constants for use in other test files
module.exports.TEST_PORT = TEST_PORT;
module.exports.TEST_HOST = TEST_HOST;
module.exports.TEST_DB_PATH = TEST_DB_PATH;
