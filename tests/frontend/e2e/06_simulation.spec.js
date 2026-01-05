const { test, expect } = require('@playwright/test');

/**
 * Simulation Dashboard Tests
 *
 * Coverage:
 * - Page loading
 * - Stats cards visibility
 * - Action forms visibility
 */

// Helper for authenticated tests
const login = async (page) => {
    await page.goto('/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/assets/);
};

test.describe('Simulation Dashboard Tests', () => {
    test.beforeEach(async ({ page }) => {
        await login(page);
        await page.goto('/simulation/');
        await page.waitForLoadState('networkidle');
    });

    test('SIM-01: Page loads with correct title', async ({ page }) => {
        await expect(page).toHaveTitle(/Simulation Tools/);
        await expect(page.locator('h1')).toContainText('Simulation & Testing Tools');
    });

    test('SIM-02: Stats cards are visible', async ({ page }) => {
        await expect(page.locator('.card-title').first()).toBeVisible();
        // Check for specific cards using more specific locators to avoid strict mode violations
        await expect(page.locator('.card-header', { hasText: 'Total Assets' })).toBeVisible();
        await expect(page.locator('.card-header', { hasText: 'Maintenance Orders' })).toBeVisible();
        await expect(page.locator('.card-header', { hasText: 'Total Users' })).toBeVisible();
        await expect(page.locator('.card-header', { hasText: 'Spare Parts' })).toBeVisible();
    });

    test('SIM-03: Breakdown simulation section is visible', async ({ page }) => {
        await expect(page.locator('text=Breakdown Simulation')).toBeVisible();
        await expect(page.locator('button:has-text("TRIGGER BREAKDOWN")')).toBeVisible();
    });

    test('SIM-04: Bulk Data Generator section is visible', async ({ page }) => {
        await expect(page.locator('text=Bulk Data Generator')).toBeVisible();
        // Use button text instead of form action which might vary
        await expect(page.locator('button:has-text("GENERATE DATA")')).toBeVisible();
    });
});
