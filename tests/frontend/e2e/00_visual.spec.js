const { test, expect } = require('@playwright/test');

/**
 * Visual Regression Tests
 * 
 * These tests capture screenshots of pages and compare them against baseline images.
 * - First run with --update-snapshots generates baselines
 * - Subsequent runs compare against baselines
 * - Any pixel difference = test failure
 * 
 * Coverage:
 * - Public pages (login, 404)
 * - List pages (assets, MOs, spare parts, users)
 * - Detail pages
 * - Add/Edit forms
 * - Sidebar states (open/closed)
 * - Collapsible sections
 */

// Helper function to login
async function login(page) {
    await page.goto('/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/assets/);
}

// Helper to wait for table to be fully loaded
async function waitForTable(page, tableId, options = {}) {
    const timeout = options.timeout || 15000;
    await page.waitForSelector(`${tableId} table`, { timeout });
    await page.waitForLoadState('networkidle');
    // Wait for any loading overlays to disappear
    const loadingOverlay = page.locator('.table-loading-overlay');
    if (await loadingOverlay.count() > 0) {
        await loadingOverlay.waitFor({ state: 'hidden', timeout: 10000 }).catch(() => { });
    }
}

// ============================================================================
// GLOBAL SETUP
// ============================================================================

test.beforeEach(async ({ page }) => {
    // Force a consistent minimum height on body to avoid "Expected image size X, received Y" errors
    // across platforms (Windows often renders taller than Linux).
    // Using addInitScript with DOMContentLoaded ensures the CSS is injected after DOM is ready,
    // on EVERY page load (including after navigation).
    await page.addInitScript(() => {
        // Wait for DOM to be ready before injecting CSS
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', injectStyle);
        } else {
            injectStyle();
        }

        function injectStyle() {
            const style = document.createElement('style');
            style.id = 'playwright-visual-test-height';
            style.textContent = 'body { min-height: 3000px !important; }';
            document.head.appendChild(style);
        }
    });
});

// ============================================================================
// PUBLIC PAGES (No Authentication Required)
// ============================================================================

test.describe('Visual Regression - Public Pages', () => {
    test('VR-01: Login page', async ({ page }) => {
        await page.goto('/login');
        await page.waitForLoadState('networkidle');
        await expect(page).toHaveScreenshot('login-page.png', { fullPage: true });
    });

    test('VR-02: 404 error page', async ({ page }) => {
        await page.goto('/nonexistent-page-12345');
        await page.waitForLoadState('networkidle');
        await expect(page).toHaveScreenshot('404-page.png', { fullPage: true });
    });
});

// ============================================================================
// LIST PAGES
// ============================================================================

test.describe('Visual Regression - List Pages', () => {
    test.beforeEach(async ({ page }) => {
        await login(page);
        // Ensure clean state for every test in this block
        await page.evaluate(() => {
            localStorage.setItem('tableSidebarCollapsed', 'true');
            localStorage.removeItem('tableSidebarSections');
        });
    });

    test('VR-03: Assets list - default view', async ({ page }) => {
        await page.goto('/assets');
        await waitForTable(page, '#assetsTable');
        await expect(page).toHaveScreenshot('assets-list-default.png', {
            fullPage: true,
            mask: [page.locator('input[name="csrf_token"]')]
        });
    });

    test('VR-04: Assets list - sidebar open', async ({ page }) => {
        await page.goto('/assets');
        await waitForTable(page, '#assetsTable');

        // Toggle sidebar open (starts collapsed due to beforeEach)
        const toggleBtn = page.locator('.btn-toggle-sidebar');
        await expect(toggleBtn).toBeVisible();
        await toggleBtn.click();

        // Wait for sidebar to be fully expanded (not collapsed class)
        const sidebar = page.locator('.table-sidebar');
        await expect(sidebar).not.toHaveClass(/collapsed/);
        await page.waitForTimeout(500); // Allow animation to settle

        await expect(page).toHaveScreenshot('assets-list-sidebar-open.png', {
            fullPage: true,
            mask: [page.locator('input[name="csrf_token"]')]
        });
    });

    test('VR-05: Maintenance Orders list - default view', async ({ page }) => {
        await page.goto('/maintenance_orders');
        await waitForTable(page, '#mosTable');
        await expect(page).toHaveScreenshot('mo-list-default.png', { fullPage: true });
    });

    test('VR-06: Spare Parts list - default view', async ({ page }) => {
        await page.goto('/spare_parts');
        await waitForTable(page, '#sparePartsTable');
        await expect(page).toHaveScreenshot('spare-parts-list-default.png', { fullPage: true });
    });

    test('VR-07: Users list - default view', async ({ page }) => {
        await page.goto('/users');
        await waitForTable(page, '#usersTable');
        await expect(page).toHaveScreenshot('users-list-default.png', { fullPage: true });
    });
});

// ============================================================================
// DETAIL PAGES
// ============================================================================

test.describe('Visual Regression - Detail Pages', () => {
    test.beforeEach(async ({ page }) => {
        await login(page);
    });

    test('VR-08: Asset detail page', async ({ page }) => {
        // First get an asset ID from the list
        await page.goto('/assets');
        await waitForTable(page, '#assetsTable');

        // Click first row link to navigate to detail
        const firstRow = page.locator('#assetsTable tbody tr').first();
        await firstRow.locator('a').first().click();
        await page.waitForLoadState('networkidle');

        await expect(page).toHaveScreenshot('asset-detail.png', {
            fullPage: true,
            mask: [page.locator('input[name="csrf_token"]')]
        });
    });

    test('VR-09: Maintenance Order detail page', async ({ page }) => {
        await page.goto('/maintenance_orders');
        await waitForTable(page, '#mosTable');

        const firstRow = page.locator('#mosTable tbody tr').first();
        await firstRow.locator('a').first().click();
        await page.waitForLoadState('networkidle');

        await expect(page).toHaveScreenshot('mo-detail.png', { fullPage: true });
    });

    test('VR-10: Spare Part detail page', async ({ page }) => {
        await page.goto('/spare_parts');
        await waitForTable(page, '#sparePartsTable');

        const firstRow = page.locator('#sparePartsTable tbody tr').first();
        await firstRow.locator('a').first().click();
        await page.waitForLoadState('networkidle');

        await expect(page).toHaveScreenshot('spare-part-detail.png', { fullPage: true });
    });

    test('VR-11: User detail page', async ({ page }) => {
        await page.goto('/users');
        await waitForTable(page, '#usersTable');

        const firstRow = page.locator('#usersTable tbody tr').first();
        await firstRow.locator('a').first().click();
        await page.waitForLoadState('networkidle');

        await expect(page).toHaveScreenshot('user-detail.png', { fullPage: true });
    });
});

// ============================================================================
// ADD/CREATE FORMS
// ============================================================================

test.describe('Visual Regression - Add Forms', () => {
    test.beforeEach(async ({ page }) => {
        await login(page);
    });

    test('VR-12: Add New Asset form', async ({ page }) => {
        await page.goto('/assets/add');
        await page.waitForLoadState('networkidle');
        await expect(page).toHaveScreenshot('asset-add-form.png', { fullPage: true });
    });

    test('VR-13: Add New Maintenance Order form', async ({ page }) => {
        await page.goto('/maintenance_orders/add');
        await page.waitForLoadState('networkidle');
        await expect(page).toHaveScreenshot('mo-add-form.png', { fullPage: true });
    });

    test('VR-14: Add New Spare Part form', async ({ page }) => {
        await page.goto('/spare_parts/add');
        await page.waitForLoadState('networkidle');
        await expect(page).toHaveScreenshot('spare-part-add-form.png', { fullPage: true });
    });

    test('VR-15: Add New User form (Register)', async ({ page }) => {
        await page.goto('/register');
        await page.waitForLoadState('networkidle');
        await expect(page).toHaveScreenshot('user-add-form.png', { fullPage: true });
    });
});

// ============================================================================
// SIDEBAR COLLAPSIBLE SECTIONS
// ============================================================================

test.describe('Visual Regression - Sidebar Sections', () => {
    test.beforeEach(async ({ page }) => {
        await login(page);
    });

    test('VR-16: Sidebar filters section expanded', async ({ page }) => {
        await page.goto('/assets');
        await waitForTable(page, '#assetsTable');

        // Ensure sidebar starts COLLAPSED
        await page.evaluate(() => {
            localStorage.setItem('tableSidebarCollapsed', 'true');
            localStorage.removeItem('tableSidebarSections');
        });
        await page.reload();
        await waitForTable(page, '#assetsTable');

        // Open sidebar first
        const toggleBtn = page.locator('.btn-toggle-sidebar');
        await toggleBtn.click();
        await page.waitForTimeout(500);

        // Expand filters section
        const filtersHeader = page.locator('.sidebar-section[data-section="filters"] .section-header');
        if (await filtersHeader.isVisible()) {
            await filtersHeader.click();
            await page.waitForTimeout(300);
        }

        await expect(page).toHaveScreenshot('sidebar-filters-expanded.png', {
            fullPage: true,
            mask: [page.locator('input[name="csrf_token"]')]
        });
    });

    test('VR-17: Sidebar columns section expanded', async ({ page }) => {
        await page.goto('/assets');
        await waitForTable(page, '#assetsTable');

        // Ensure sidebar starts COLLAPSED
        await page.evaluate(() => {
            localStorage.setItem('tableSidebarCollapsed', 'true');
            localStorage.removeItem('tableSidebarSections');
        });
        await page.reload();
        await waitForTable(page, '#assetsTable');

        // Open sidebar
        const toggleBtn = page.locator('.btn-toggle-sidebar');
        await toggleBtn.click();
        await page.waitForTimeout(500);

        // Expand columns section
        const columnsHeader = page.locator('.sidebar-section[data-section="columns"] .section-header');
        if (await columnsHeader.isVisible()) {
            await columnsHeader.click();
            await page.waitForTimeout(300);
        }

        await expect(page).toHaveScreenshot('sidebar-columns-expanded.png', {
            fullPage: true,
            mask: [page.locator('input[name="csrf_token"]')]
        });
    });

    test('VR-18: Sidebar saved views section expanded', async ({ page }) => {
        await page.goto('/assets');
        await waitForTable(page, '#assetsTable');

        // Ensure sidebar starts COLLAPSED
        await page.evaluate(() => {
            localStorage.setItem('tableSidebarCollapsed', 'true');
            localStorage.removeItem('tableSidebarSections');
        });
        await page.reload();
        await waitForTable(page, '#assetsTable');

        // Open sidebar
        const toggleBtn = page.locator('.btn-toggle-sidebar');
        await toggleBtn.click();
        await page.waitForTimeout(500);

        // Expand configs/saved views section
        const configsHeader = page.locator('.sidebar-section[data-section="configs"] .section-header');
        if (await configsHeader.isVisible()) {
            await configsHeader.click();
            await page.waitForTimeout(300);
        }

        await expect(page).toHaveScreenshot('sidebar-configs-expanded.png', {
            fullPage: true,
            mask: [page.locator('input[name="csrf_token"]')]
        });
    });
});

// ============================================================================
// SPECIAL PAGES
// ============================================================================

test.describe('Visual Regression - Special Pages', () => {
    test.beforeEach(async ({ page }) => {
        await login(page);
    });

    test('VR-19: Shift Calendar page', async ({ page }) => {
        await page.goto('/shift_calendar');
        await page.waitForLoadState('networkidle');
        await expect(page).toHaveScreenshot('shift-calendar.png', {
            fullPage: true,
            maxDiffPixelRatio: 0.1, // Increase threshold for complex calendar grid
        });
    });
});
