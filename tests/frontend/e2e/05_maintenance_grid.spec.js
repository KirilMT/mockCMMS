const { test, expect } = require('@playwright/test');

/**
 * Maintenance Grid Functional Tests
 *
 * Coverage:
 * - Page loading
 * - ID display
 */

test.describe('Maintenance Grid Tests', () => {
    test('MG-01: Page loads with correct IDs', async ({ page }) => {
        const ids = '101,102,103';
        await page.goto(`/maintenance_grid/${ids}`);

        // Verify title
        await expect(page).toHaveTitle(/Maintenance Grid/);
        await expect(page.locator('h1')).toHaveText('Mock CMMS Maintenance Grid');

        // Verify IDs are displayed
        await expect(page.locator('.grid-info')).toContainText(ids);

        // Verify back link
        await expect(page.locator('a[href="/"]')).toBeVisible();
    });
});

