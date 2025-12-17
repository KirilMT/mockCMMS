const { test, expect } = require('@playwright/test');

test.describe('Visual Regression Tests', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/login');
        await page.fill('input[name="username"]', 'admin');
        await page.fill('input[name="password"]', 'admin123');
        await page.click('button[type="submit"]');
        await page.waitForURL(/\/assets/);
    });

    test('VR-1: test_visual_assets_page_default', async ({ page }) => {
        await page.goto('/assets');
        await page.waitForSelector('#assetsTable table');
        await expect(page).toHaveScreenshot('assets-default.png');
    });

    test('VR-2: test_visual_assets_page_sidebar_open', async ({ page }) => {
        await page.goto('/assets');
        await page.waitForSelector('#assetsTable table');
        await page.click('.btn-toggle-sidebar');
        // Wait for animation or sidebar to be visible
        await page.waitForSelector('.table-sidebar:not(.collapsed)');
        await expect(page).toHaveScreenshot('assets-sidebar-open.png');
    });

    test('VR-3: test_visual_mo_page_default', async ({ page }) => {
        await page.goto('/maintenance_orders');
        await page.waitForSelector('#maintenanceOrdersTable table');
        await expect(page).toHaveScreenshot('mo-default.png');
    });

    test('VR-4: test_visual_mo_page_filtered', async ({ page }) => {
        await page.goto('/maintenance_orders');
        await page.waitForSelector('#maintenanceOrdersTable table');
        await page.click('.btn-toggle-sidebar');
        await page.click('#addFilterBtn');
        // Add a filter (assuming simple one available)
        // ...
        await page.click('#applyFiltersBtn');
        await expect(page).toHaveScreenshot('mo-filtered.png');
    });

    test('VR-5: test_visual_login_page', async ({ page }) => {
        await page.goto('/logout'); // Ensure logged out
        await page.goto('/login');
        await expect(page).toHaveScreenshot('login-page.png');
    });

    test('VR-6: test_visual_dark_mode', async ({ page }) => {
        // Toggle dark mode if available
        // ...
        // await expect(page).toHaveScreenshot('dark-mode.png');
    });
});
