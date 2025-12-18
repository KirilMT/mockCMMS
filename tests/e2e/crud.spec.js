const { test, expect } = require('@playwright/test');

test.describe('CRUD Functional Tests', () => {
    test.beforeEach(async ({ page }) => {
        // Login before each test
        await page.goto('/login');
        await page.fill('input[name="username"]', 'admin');
        await page.fill('input[name="password"]', 'admin123');
        await page.click('button:has-text("Login")');
        await page.waitForURL(/\/assets/);
    });

    // --- Assets ---
    test('E2E-C1: test_create_asset', async ({ page }) => {
        // Already on /assets from beforeEach
        await page.waitForSelector('#assetsTable table');
        await page.click('text=New Asset');

        const assetName = 'Test Asset ' + Date.now();
        await page.fill('input[name="asset_code"]', 'AC-' + Date.now());
        await page.fill('input[name="name"]', assetName);
        await page.fill('textarea[name="description"]', 'Description ' + Date.now());
        await page.selectOption('select[name="asset_type"]', 'robot');
        await page.selectOption('select[name="cost_center"]', 'assembly');
        await page.selectOption('select[name="status"]', 'Operational');

        await page.click('button:has-text("Add Asset")');

        // Verify creation - Search to handle pagination
        await page.waitForURL(/\/assets/);
        await page.waitForSelector('#assetsTable table');
        await page.fill('#globalSearchInput', assetName);
        await page.click('#applySearchBtn');
        await expect(page.locator(`text=${assetName}`)).toBeVisible();
    });

    test('E2E-C2: test_edit_asset', async ({ page }) => {
        // Already on /assets
        await page.waitForSelector('#assetsTable table');

        // Click on the first ID link to navigate to detail page
        const firstIdLink = page.locator('#assetsTable table tbody tr').first().locator('a').first();
        await firstIdLink.click();

        // Now on detail page - can directly edit fields

        const newDesc = 'Updated Description ' + Date.now();
        await page.fill('textarea[name="description"]', newDesc);
        await page.click('button:has-text("Update Asset")');

        // Verify update
        await expect(page.locator('text=Asset updated successfully')).toBeVisible();
    });

    test('E2E-C3: test_delete_asset', async ({ page }) => {
        // Already on /assets
        await page.waitForSelector('#assetsTable table');

        // Create an asset first
        await page.click('text=New Asset');
        const assetName = 'Delete Me ' + Date.now();
        await page.fill('input[name="asset_code"]', 'DEL-' + Date.now());
        await page.fill('input[name="name"]', assetName);
        await page.selectOption('select[name="asset_type"]', 'robot');
        await page.selectOption('select[name="cost_center"]', 'assembly');
        await page.selectOption('select[name="status"]', 'Operational');
        await page.click('button:has-text("Add Asset")');
        await page.waitForURL(/\/assets/);

        // Search for the asset
        await page.fill('#globalSearchInput', assetName);
        await page.click('#applySearchBtn');
        await expect(page.locator(`text=${assetName}`)).toBeVisible();

        // Click on the ID link to go to detail page
        const row = page.locator('tr', { hasText: assetName });
        await row.locator('a').first().click();

        // Click Delete button (opens modal)
        await page.click('button.btn-danger:has-text("Delete")');

        // Wait for modal confirm button to be visible
        await page.waitForSelector('#confirmDeleteBtn', { state: 'visible', timeout: 5000 });

        // Click confirm button in modal
        await Promise.all([
            page.waitForNavigation(),
            page.click('#confirmDeleteBtn')
        ]);

        // Verify deletion - should be back on list page
        await page.waitForSelector('#assetsTable table');

        // Clear search first to refresh table
        const clearBtn = page.locator('#clearSearchBtn');
        if (await clearBtn.isVisible()) {
            await clearBtn.click();
        }

        // Now search for the deleted asset
        await page.fill('#globalSearchInput', assetName);
        await page.click('#applySearchBtn');

        // Wait a moment for search to complete
        await page.waitForTimeout(500);

        // Check that the asset is not in the table
        const rows = await page.locator('#assetsTable table tbody tr').count();
        if (rows > 0) {
            // If there are rows, make sure none contain the asset name
            await expect(page.locator(`#assetsTable table tbody tr:has-text("${assetName}")`)).toHaveCount(0);
        }
        // Otherwise table is empty which is also correct
    });

    // --- Maintenance Orders ---
    test('E2E-C4: test_create_maintenance_order', async ({ page }) => {
        await page.goto('/maintenance_orders');
        await page.waitForSelector('#mosTable table');
        await page.click('text=Add New MO');

        await page.fill('textarea[name="description"]', 'MO ' + Date.now());
        await page.selectOption('select[name="order_type"]', 'corrective');
        await page.selectOption('select[name="priority"]', 'Medium');
        await page.fill('input[name="estimated_completion_time"]', '60');
        await page.fill('input[name="labour_count"]', '1');

        const assetSelect = page.locator('select[name="asset_id"]');
        if (await assetSelect.isVisible()) {
            await assetSelect.selectOption({ index: 1 });
        }

        await page.click('button:has-text("Add MO")');
        await expect(page.locator('.alert-success')).toBeVisible();
    });

    test('E2E-C5: test_edit_maintenance_order', async ({ page }) => {
        await page.goto('/maintenance_orders');
        await page.waitForSelector('#mosTable table tbody tr');

        const firstRow = page.locator('#mosTable table tbody tr').first();

        // Click on the first ID link to navigate to detail page
        await firstRow.locator('a').first().click();

        // Now on detail page - can directly edit fields

        await page.fill('textarea[name="description"]', 'Updated MO Desc ' + Date.now());
        await page.click('button:has-text("Update MO")');

        await expect(page.locator('.alert-success')).toBeVisible();
    });

    test('E2E-C6: test_delete_maintenance_order', async ({ page }) => {
        await page.goto('/maintenance_orders');
        await page.waitForSelector('#mosTable table');

        // Create one to delete
        await page.click('text=Add New MO');
        const desc = 'Delete MO ' + Date.now();
        await page.fill('textarea[name="description"]', desc);
        await page.selectOption('select[name="order_type"]', 'CM');
        await page.selectOption('select[name="priority"]', 'Low');
        await page.locator('select[name="asset_id"]').selectOption({ index: 1 });
        await page.click('button:has-text("Add MO")');
        await page.goto('/maintenance_orders');

        // Click on ID link to go to detail page
        await page.fill('#globalSearchInput', desc);
        await page.click('#applySearchBtn');
        const row = page.locator('tr', { hasText: desc });
        await row.locator('a').first().click();

        // Click Delete button (opens modal)
        await page.click('button.btn-danger:has-text("Delete")');

        // Wait for modal confirm button to be visible
        await page.waitForSelector('#confirmDeleteBtn', { state: 'visible', timeout: 5000 });

        // Click confirm button and wait for navigation
        await Promise.all([
            page.waitForNavigation({ waitUntil: 'networkidle' }),
            page.click('#confirmDeleteBtn')
        ]);

        // Verify deletion
        await page.waitForSelector('#mosTable table');

        // Clear search first to refresh table
        const clearBtn = page.locator('#clearSearchBtn');
        if (await clearBtn.isVisible()) {
            await clearBtn.click();
        }

        // Now search for the deleted MO
        await page.fill('#globalSearchInput', desc);
        await page.click('#applySearchBtn');

        // Wait a moment for search to complete
        await page.waitForTimeout(500);

        // Check that the MO is not in the table
        const rows = await page.locator('#mosTable table tbody tr').count();
        if (rows > 0) {
            // If there are rows, make sure none contain the description
            await expect(page.locator(`#mosTable table tbody tr:has-text("${desc}")`)).toHaveCount(0);
        }
        // Otherwise table is empty which is also correct
    });

    // --- Spare Parts ---
    test('E2E-C7: test_create_spare_part', async ({ page }) => {
        test.setTimeout(60000);
        await page.goto('/spare_parts');
        await page.waitForSelector('#sparePartsTable table');
        await page.click('text=Add New Spare Part');

        const uniqueSuffix = Date.now() + '-' + Math.floor(Math.random() * 1000);
        const desc = 'Part ' + uniqueSuffix;
        await page.fill('textarea[name="description"]', desc);
        await page.fill('input[name="manufacturer"]', 'Acme Corp');
        await page.fill('input[name="manufacturer_part_id"]', 'PN-' + uniqueSuffix);
        await page.fill('input[name="stock_quantity"]', '10');
        await page.fill('input[name="location"]', 'Warehouse A');
        await page.fill('input[name="min_quantity"]', '5');

        await page.click('button:has-text("Add Spare Part")');

        await page.waitForSelector('#sparePartsTable table');

        // Search
        await page.fill('#globalSearchInput', desc);
        await page.click('#applySearchBtn');
        await expect(page.locator(`text=${desc}`)).toBeVisible();
    });

    // --- Users ---
    test('E2E-C8: test_create_user', async ({ page }) => {
        test.setTimeout(60000);
        await page.goto('/users');
        await page.waitForSelector('#usersTable table');
        await page.click('text=Add New User');
        await page.waitForURL(/\/register/);
        await page.waitForSelector('input[name="username"]');

        const uniqueSuffix = Date.now() + '-' + Math.floor(Math.random() * 1000);
        const username = 'user' + uniqueSuffix;
        await page.fill('input[name="username"]', username);
        await page.fill('input[name="email"]', `email${uniqueSuffix}@example.com`);
        await page.fill('input[name="password"]', 'password123');
        await page.selectOption('select[name="roles"]', 'Technician');

        await page.click('button:has-text("Register User")');

        await page.waitForSelector('#usersTable table');

        // Search
        await page.fill('#globalSearchInput', username);
        await page.click('#applySearchBtn');
        await expect(page.locator(`text=${username}`)).toBeVisible();
    });
});
