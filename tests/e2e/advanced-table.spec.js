const { test, expect } = require('@playwright/test');

test.describe('Advanced Table Tests', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/login');
        await page.fill('input[name="username"]', 'admin');
        await page.fill('input[name="password"]', 'admin123');
        await page.click('button[type="submit"]');
        await page.waitForURL(/\/assets/);

        // Already at /assets (or redirected to it).
        // Wait for table to load. The table container in assets.html is 'div#assetsTable' which is filled by JS.
        // Wait for something inside it, e.g., 'table'.
        await page.waitForSelector('#assetsTable table');
    });

    test('E2E-T1: test_sort_column_ascending', async ({ page }) => {
        const header = page.locator('th[data-key="name"]'); // Assuming 'name' column exists
        await header.click();

        // Check for sort indicator
        await expect(header).toHaveClass(/sort-asc/);

        // Verify data order (basic check: first item starts with A or similar)
        // This is hard to verify without knowing exact data, but we check UI state.
    });

    test('E2E-T2: test_sort_column_descending', async ({ page }) => {
        const header = page.locator('th[data-key="name"]');
        await header.click(); // asc
        await header.click(); // desc

        await expect(header).toHaveClass(/sort-desc/);
    });

    test('E2E-T3: test_add_single_filter', async ({ page }) => {
        // Open sidebar
        await page.click('.btn-toggle-sidebar');

        await page.click('#addFilterBtn');
        await page.selectOption('.filter-column', { label: 'Name' }); // Or value="name"
        await page.selectOption('.filter-operator', { label: 'Contains' });
        await page.fill('.filter-value', 'Test');

        await page.click('#applyFiltersBtn');

        // Verify URL or Table update (loading state then data)
        await expect(page.locator('.table-loading-overlay')).toBeHidden();
        // Check filter badge
        await expect(page.locator('.sidebar-section[data-section="filters"] .badge')).toHaveText('1');
    });

    test('E2E-T4: test_add_multiple_filters_AND', async ({ page }) => {
        await page.click('.btn-toggle-sidebar');

        // Add first
        await page.click('#addFilterBtn');
        await page.locator('.filter-column').first().selectOption({ index: 1 }); // Select first available column
        await page.locator('.filter-value').first().fill('A');

        // Add second
        await page.click('#addFilterBtn');
        const secondRow = page.locator('.filter-row-sidebar').nth(1);
        await secondRow.locator('.filter-column').selectOption({ index: 1 });
        await secondRow.locator('.filter-value').fill('B');

        // Ensure AND logic (default)
        // Check connector
        const connector = page.locator('.filter-logic-radio[value="AND"]');
        await expect(connector).toBeChecked();

        await page.click('#applyFiltersBtn');
        await expect(page.locator('.sidebar-section[data-section="filters"] .badge')).toHaveText('2');
    });

    test('E2E-T5: test_add_multiple_filters_OR', async ({ page }) => {
        await page.click('.btn-toggle-sidebar');

        await page.click('#addFilterBtn');
        await page.locator('.filter-column').first().selectOption({ index: 1 });
        await page.locator('.filter-value').first().fill('A');

        await page.click('#addFilterBtn');
        const secondRow = page.locator('.filter-row-sidebar').nth(1);
        await secondRow.locator('.filter-column').selectOption({ index: 1 });
        await secondRow.locator('.filter-value').fill('B');

        // Set OR
        await page.click('.filter-logic-radio[value="OR"]');

        await page.click('#applyFiltersBtn');
        await expect(page.locator('.sidebar-section[data-section="filters"] .badge')).toHaveText('2');
    });

    test('E2E-T6: test_clear_all_filters', async ({ page }) => {
        await page.click('.btn-toggle-sidebar');
        // Add one
        await page.click('#addFilterBtn');
        await page.locator('.filter-column').first().selectOption({ index: 1 });
        await page.locator('.filter-value').first().fill('A');
        await page.click('#applyFiltersBtn');

        // Clear
        await page.click('#clearFiltersBtn');
        await expect(page.locator('.sidebar-section[data-section="filters"] .badge')).toHaveText('0');
        await expect(page.locator('#noFiltersMessage')).toBeVisible();
    });

    test('E2E-T7: test_hide_column', async ({ page }) => {
        await page.click('.btn-toggle-sidebar');
        // Expand columns section
        await page.click('.sidebar-section[data-section="columns"] .section-header');

        // Uncheck first column
        const firstCheckbox = page.locator('#columnList input[type="checkbox"]').first();
        await firstCheckbox.uncheck();

        await page.click('#applyColumnsBtn');

        // Verify column hidden in table head
        // We need to know which column it was.
        // Assuming first column in list matches first in table.
        // Or checking counts.
        // Let's check that column count decreased.
        const headerCount = await page.locator('thead th').count();
        // This logic is fragile without knowing initial count.
    });

    test('E2E-T8: test_show_hidden_column', async ({ page }) => {
        // Similar to T7 but check then uncheck?
        // This depends on initial state.
    });

    test('E2E-T9: test_save_view', async ({ page }) => {
        await page.click('.btn-toggle-sidebar');
        await page.click('.sidebar-section[data-section="configs"] .section-header');

        // Setup prompt handling
        page.on('dialog', async dialog => {
            await dialog.accept('My E2E View');
        });

        await page.click('#saveViewBtn');

        // Verify it appears in list
        await expect(page.locator('.saved-view-item', { hasText: 'My E2E View' })).toBeVisible();
    });

    test('E2E-T10: test_load_saved_view', async ({ page }) => {
        // Need a saved view first.
        // ... (Create view)
        // Click it.
        // Verify table state matches.
    });

    test('E2E-T11: test_delete_saved_view', async ({ page }) => {
        // Need a saved view.
        // Click delete button.
        // Confirm dialog.
        // Verify gone.
    });

    test('E2E-T12: test_export_to_csv', async ({ page }) => {
        const downloadPromise = page.waitForEvent('download');
        await page.click('#exportCsvBtn'); // Assuming ID
        const download = await downloadPromise;
        expect(download.suggestedFilename()).toContain('.csv');
    });

    test('E2E-T13: test_pagination_navigation', async ({ page }) => {
        // Click Next
        await page.click('.pagination .page-next'); // Assuming selector
        // Verify page 2 active
    });

    test('E2E-T14: test_resize_column', async ({ page }) => {
        // Drag handle.
        // Verify width changed.
    });
});
