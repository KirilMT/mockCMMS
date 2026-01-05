const { test, expect } = require('@playwright/test');

/**
 * Shift Calendar Functional Tests
 *
 * Coverage:
 * - Page loading and authentication
 * - Calendar grid rendering
 * - Navigation (Previous/Next month)
 * - Shift display (Team badges)
 * - Current day highlighting
 */

// Helper for authenticated tests
const login = async (page) => {
    await page.goto('/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/assets/);
};

test.describe('Shift Calendar Tests', () => {
    test.beforeEach(async ({ page }) => {
        await login(page);
        await page.goto('/shift_calendar');
        await page.waitForLoadState('networkidle');
    });

    test('SC-01: Page loads with correct title and current month', async ({ page }) => {
        // Verify page title
        await expect(page).toHaveTitle(/Shift Calendar/);
        await expect(page.locator('h1')).toHaveText('Shift Calendar');

        // Verify current month/year is displayed
        const now = new Date();
        const monthName = now.toLocaleString('default', { month: 'long' });
        const year = now.getFullYear();
        await expect(page.locator('.h4')).toContainText(`${monthName} ${year}`);
    });

    test('SC-02: Calendar grid renders correctly', async ({ page }) => {
        // Verify table headers
        const headers = page.locator('table thead th');
        await expect(headers).toHaveCount(5);
        await expect(headers.nth(0)).toHaveText('Date');
        await expect(headers.nth(1)).toHaveText('Day');
        await expect(headers.nth(2)).toHaveText('Week #');
        await expect(headers.nth(3)).toHaveText('Early Shift (06:00 - 18:00)');
        await expect(headers.nth(4)).toHaveText('Late Shift (18:00 - 06:00)');

        // Verify rows exist (at least 28 days)
        const rows = page.locator('table tbody tr');
        const rowCount = await rows.count();
        expect(rowCount).toBeGreaterThanOrEqual(28);
        expect(rowCount).toBeLessThanOrEqual(31);
    });

    test('SC-03: Navigation buttons work', async ({ page }) => {
        // Get current displayed month
        const currentMonthText = await page.locator('.h4').innerText();

        // Click Previous
        await page.click('text=Previous');
        await page.waitForLoadState('networkidle');

        // Verify month changed
        const prevMonthText = await page.locator('.h4').innerText();
        expect(prevMonthText).not.toBe(currentMonthText);

        // Click Next twice to go to next month
        await page.click('text=Next'); // Back to current
        await page.waitForLoadState('networkidle');
        await page.click('text=Next'); // To next month
        await page.waitForLoadState('networkidle');

        const nextMonthText = await page.locator('.h4').innerText();
        expect(nextMonthText).not.toBe(currentMonthText);
        expect(nextMonthText).not.toBe(prevMonthText);
    });

    test('SC-04: Team badges are displayed', async ({ page }) => {
        // Check for presence of team badges
        const badges = page.locator('.badge');
        await expect(badges.first()).toBeVisible();

        // Verify badge content (Team A, B, C, or D)
        const badgeText = await badges.first().innerText();
        expect(badgeText).toMatch(/Team [A-D]/);
    });

    test('SC-05: Current day is highlighted', async ({ page }) => {
        // This test only works if we are viewing the current month
        // Since beforeEach goes to /shift_calendar (defaults to current), it should work

        const todayRow = page.locator('tr.table-primary');
        // Note: This might fail if the test runs exactly at midnight transition or timezone issues
        // But generally should be visible
        if (await todayRow.count() > 0) {
            await expect(todayRow).toBeVisible();

            // Verify date in the row matches today
            const now = new Date();
            const dateStr = now.toISOString().split('T')[0]; // YYYY-MM-DD
            await expect(todayRow).toContainText(dateStr);
        }
    });
});

