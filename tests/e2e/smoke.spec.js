const { test, expect } = require('@playwright/test');

test.describe('Smoke Tests', () => {
    test('E2E-S1: test_login_and_logout', async ({ page }) => {
        await page.goto('/login');
        await page.fill('input[name="username"]', 'admin');
        await page.fill('input[name="password"]', 'admin123');
        await page.click('button[type="submit"]');

        // Verify login success (redirect to dashboard or check for logout button)
        // Note: App redirects / to /assets for admin
        await expect(page).toHaveURL(/\/assets/);
        await expect(page.locator('text=Logout')).toBeVisible();

        // Logout
        await page.click('text=Logout');
        await expect(page).toHaveURL(/\/login/);
    });

    // Helper for subsequent tests to login
    const login = async (page) => {
        await page.goto('/login');
        await page.fill('input[name="username"]', 'admin');
        await page.fill('input[name="password"]', 'admin123');
        await page.click('button[type="submit"]');
        await page.waitForURL(/\/assets/);
    };

    test('E2E-S2: test_navigate_to_assets_page', async ({ page }) => {
        await login(page);
        await page.goto('/assets');
        await expect(page).toHaveTitle(/Assets/i);
        await expect(page.locator('h1')).toContainText('Assets');
    });

    test('E2E-S3: test_navigate_to_maintenance_orders_page', async ({ page }) => {
        await login(page);
        await page.goto('/maintenance_orders');
        await expect(page).toHaveTitle(/Maintenance Orders/i);
        await expect(page.locator('h1')).toContainText('Maintenance Orders');
    });

    test('E2E-S4: test_navigate_to_spare_parts_page', async ({ page }) => {
        await login(page);
        await page.goto('/spare_parts');
        await expect(page).toHaveTitle(/Spare Parts/i);
        await expect(page.locator('h1')).toContainText('Spare Parts');
    });

    test('E2E-S5: test_navigate_to_users_page', async ({ page }) => {
        await login(page);
        await page.goto('/users');
        await expect(page).toHaveTitle(/Users/i);
        await expect(page.locator('h1')).toContainText('Users');
    });
});
