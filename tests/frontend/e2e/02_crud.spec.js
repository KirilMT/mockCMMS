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
        // Wait for potential DB seeding / startup locks to clear
        await page.waitForTimeout(5000);

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

        const dataRows = page.locator('#assetsTable table tbody tr:not(:has(.table-empty))');
        await expect(dataRows.locator(`text=${assetName}`)).toBeVisible();
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

        // Click the Update button - use button[form] selector for submit buttons outside forms
        await page.click('button[form="asset-form"]');

        // Wait for redirect/page reload to complete
        await page.waitForURL(/\/assets/);

        // Verify success toast message appears
        await expect(page.locator('.toast-body:has-text("Asset updated successfully")')).toBeVisible({ timeout: 10000 });


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

        // Click confirm button via JS to ensure it registers despite overlays
        const navigationPromise = page.waitForNavigation({ waitUntil: 'domcontentloaded' });
        await page.evaluate(() => document.getElementById('confirmDeleteBtn').click());
        await navigationPromise;

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
        // AdvancedTable renders a row with "No results found for 'SearchTerm'" which would be matched by the text locator
        // We must exclude the empty message row from our check
        const dataRows = page.locator('#assetsTable table tbody tr:not(:has(.table-empty))');
        const count = await dataRows.count();
        if (count > 0) {
            // If there are data rows, make sure none contain the asset name
            await expect(dataRows.locator(`text=${assetName}`)).toHaveCount(0);
        }
        // Otherwise table is empty which is also correct
    });

    // --- Maintenance Orders ---
    test('E2E-C4: test_create_maintenance_order', async ({ page }) => {
        await page.goto('/maintenance_orders');
        await page.waitForSelector('#mosTable table');
        await page.click('text=Add New MO');

        const moDesc = 'MO ' + Date.now();
        await page.fill('textarea[name="description"]', moDesc);
        await page.selectOption('select[name="order_type"]', 'corrective');
        await page.selectOption('select[name="priority"]', 'Medium');
        await page.fill('input[name="estimated_completion_time"]', '60');
        await page.fill('input[name="labour_count"]', '1');

        const assetSelect = page.locator('select[name="asset_id"]');
        if (await assetSelect.isVisible()) {
            await assetSelect.selectOption({ index: 1 });
        }

        await page.click('button:has-text("Add MO")');

        // Verify creation
        await page.waitForURL(/\/maintenance_orders/);
        await page.waitForSelector('#mosTable table');

        // Search
        await page.fill('#globalSearchInput', moDesc);
        await page.click('#applySearchBtn');

        const dataRows = page.locator('#mosTable table tbody tr:not(:has(.table-empty))');
        await expect(dataRows.locator(`text=${moDesc}`)).toBeVisible();
    });

    test('E2E-C5: test_edit_maintenance_order', async ({ page }) => {
        await page.goto('/maintenance_orders');
        await page.waitForSelector('#mosTable table tbody tr');

        const firstRow = page.locator('#mosTable table tbody tr').first();

        // Click on the first ID link to navigate to detail page
        await firstRow.locator('a').first().click();

        // Now on detail page - can directly edit fields

        const newDesc = 'Updated MO Desc ' + Date.now();
        await page.fill('textarea[name="description"]', newDesc);
        await page.click('button:has-text("Update MO")');

        // Verify update
        // await expect(page.locator('.alert-success')).toBeVisible();
        await page.waitForURL(/\/maintenance_orders/);
        await page.waitForSelector('#mosTable table');

        // Search
        await page.fill('#globalSearchInput', newDesc);
        await page.click('#applySearchBtn');

        const dataRows = page.locator('#mosTable table tbody tr:not(:has(.table-empty))');
        await expect(dataRows.locator(`text=${newDesc}`)).toBeVisible();
    });

    test('E2E-C6: test_delete_mo_from_asset_page', async ({ page }) => {
        // 1. Navigate to Assets and open the first asset's detail page
        await page.goto('/assets');
        await page.waitForSelector('#assetsTable table tbody tr');
        const firstAssetRow = page.locator('#assetsTable table tbody tr').first();
        await firstAssetRow.locator('a').first().click();

        // Wait for Asset Detail page
        await page.waitForSelector('h2:has-text("Maintenance Orders for")');

        // 2. Create an MO from the Asset Detail page using the "Add Maintenance Order" link
        // This link includes return_to=asset&asset_id=X, so it should redirect back here
        await Promise.all([
            page.waitForURL(/\/maintenance_orders\/add/),
            page.click('a:has-text("Add Maintenance Order")')
        ]);

        // Wait for the MO form page to fully load
        await page.waitForSelector('#mo-form');
        await page.waitForSelector('textarea[name="description"]');

        const moDesc = 'Delete Test MO ' + Date.now();
        await page.fill('textarea[name="description"]', moDesc);
        await page.selectOption('select[name="order_type"]', 'corrective');
        await page.selectOption('select[name="priority"]', 'High');
        await page.fill('input[name="estimated_completion_time"]', '60');
        await page.fill('input[name="labour_count"]', '1');
        // asset_id should be pre-selected since we came from asset page

        // Submit and wait for redirect back to asset detail page
        await Promise.all([
            page.waitForURL(/\/assets\/\d+/),
            page.click('button:has-text("Add MO")')
        ]);

        // 3. Verify we're back on Asset Detail page and MO is visible
        await page.waitForSelector('h2:has-text("Maintenance Orders for")');
        const moRow = page.locator('tr', { hasText: moDesc });
        await expect(moRow).toBeVisible();

        // 4. Delete the MO from the Asset Detail page's MO list
        await moRow.locator('button.btn-danger:has-text("Delete")').click();

        // Confirm deletion
        await page.waitForSelector('#confirmDeleteBtn', { state: 'visible' });
        await Promise.all([
            page.waitForNavigation(),
            page.evaluate(() => document.getElementById('confirmDeleteBtn').click())
        ]);

        // 5. Verify redirection back to Asset Detail page
        await page.waitForSelector('h2:has-text("Maintenance Orders for")', { timeout: 10000 });

        // 6. Verify MO is gone - wait a moment for page to update
        await page.waitForTimeout(500);
        await expect(page.locator('tr', { hasText: moDesc })).toHaveCount(0, { timeout: 5000 });

        // 7. Verify flash message (if visible)
        const flashMessage = page.locator('.alert-success');
        if (await flashMessage.isVisible({ timeout: 2000 })) {
            await expect(flashMessage).toContainText('deleted');
        }
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
        const dataRows = page.locator('#sparePartsTable table tbody tr:not(:has(.table-empty))');
        await expect(dataRows.locator(`text=${desc}`)).toBeVisible();
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
        const dataRows = page.locator('#usersTable table tbody tr:not(:has(.table-empty))');
        await expect(dataRows.locator(`text=${username}`)).toBeVisible();
    });

    test('E2E-C9: test_edit_spare_part', async ({ page }) => {
        await page.goto('/spare_parts');
        await page.waitForSelector('#sparePartsTable table tbody tr');

        // Click on first spare part to edit
        const firstRow = page.locator('#sparePartsTable table tbody tr').first();
        await firstRow.locator('a').first().click();

        // Wait for detail page
        await page.waitForSelector('#part-form');

        // Update description
        const newDesc = 'Updated Part ' + Date.now();
        await page.fill('textarea[name="description"]', newDesc);

        // Submit
        await page.click('button:has-text("Update Spare Part")');

        // Verify redirect to list
        await page.waitForURL(/\/spare_parts\/?$/);
        await page.waitForSelector('#sparePartsTable table');

        // Search for updated part
        await page.fill('#globalSearchInput', newDesc);
        await page.click('#applySearchBtn');
        await page.waitForTimeout(500);

        const dataRows = page.locator('#sparePartsTable table tbody tr:not(:has(.table-empty))');
        await expect(dataRows.locator(`text=${newDesc}`)).toBeVisible();
    });

    test('E2E-C10: test_delete_spare_part', async ({ page }) => {
        test.setTimeout(60000);
        // First create a spare part to delete
        await page.goto('/spare_parts/add');
        await page.waitForSelector('#part-form');

        const uniqueSuffix = Date.now();
        const desc = 'Delete Test Part ' + uniqueSuffix;
        await page.fill('textarea[name="description"]', desc);
        await page.fill('input[name="manufacturer"]', 'Delete Test');
        await page.fill('input[name="manufacturer_part_id"]', 'DEL-' + uniqueSuffix);
        await page.fill('input[name="stock_quantity"]', '1');

        // Match working C7 pattern: click then wait
        await page.click('button:has-text("Add Spare Part")');
        await page.waitForSelector('#sparePartsTable table');

        // Search for the created part
        await page.fill('#globalSearchInput', desc);
        await page.click('#applySearchBtn');
        await page.waitForTimeout(1000);

        // Click to go to detail
        const row = page.locator('tr', { hasText: desc });
        await expect(row).toBeVisible({ timeout: 10000 });
        await row.locator('a').first().click();

        // Wait for detail page
        await page.waitForSelector('#part-form');

        // Delete using modal confirmation (matching C6 pattern)
        await page.click('button:has-text("Delete")');
        await page.waitForSelector('#confirmDeleteBtn', { state: 'visible' });
        await Promise.all([
            page.waitForNavigation(),
            page.evaluate(() => document.getElementById('confirmDeleteBtn').click())
        ]);

        // Verify redirection back to list page (C6 pattern)
        await page.waitForSelector('#sparePartsTable table', { timeout: 10000 });

        // Verify part is gone - wait a moment for page to update (C6 pattern)
        await page.waitForTimeout(500);
        await expect(page.locator('tr', { hasText: desc })).toHaveCount(0, { timeout: 5000 });

        // Verify flash message (if visible) - C6 pattern
        const flashMessage = page.locator('.alert-success');
        if (await flashMessage.isVisible({ timeout: 2000 })) {
            await expect(flashMessage).toContainText('deleted');
        }
    });

    test('E2E-C11: test_edit_user', async ({ page }) => {
        test.setTimeout(60000);
        await page.goto('/users');
        await page.waitForSelector('#usersTable table tbody tr');

        // Click on first user to edit
        const firstRow = page.locator('#usersTable table tbody tr').first();
        await firstRow.locator('a').first().click();

        // Wait for detail page
        await page.waitForSelector('#user-form');

        // Update email (username can't usually be changed)
        const newEmail = 'updated' + Date.now() + '@example.com';
        await page.fill('input[name="email"]', newEmail);

        // Submit using form button
        await page.click('button[form="user-form"]');
        await page.waitForSelector('#usersTable table');

        // Search for updated email
        await page.fill('#globalSearchInput', newEmail);
        await page.click('#applySearchBtn');
        await page.waitForTimeout(1000);

        const dataRows = page.locator('#usersTable table tbody tr:not(:has(.table-empty))');
        await expect(dataRows.locator(`text=${newEmail}`)).toBeVisible({ timeout: 10000 });
    });

    test('E2E-C12: test_delete_user', async ({ page }) => {
        test.setTimeout(60000);
        // First create a user to delete
        await page.goto('/register');
        await page.waitForSelector('#user-form');

        const uniqueSuffix = Date.now();
        const username = 'deleteuser' + uniqueSuffix;
        await page.fill('input[name="username"]', username);
        await page.fill('input[name="email"]', `delete${uniqueSuffix}@example.com`);
        await page.fill('input[name="password"]', 'password123');
        await page.selectOption('select[name="roles"]', 'Technician');

        await page.click('button:has-text("Register User")');
        await page.waitForSelector('#usersTable table');

        // Search for the created user
        await page.fill('#globalSearchInput', username);
        await page.click('#applySearchBtn');
        await page.waitForTimeout(1000);

        // Click to go to detail
        const row = page.locator('tr', { hasText: username });
        await expect(row).toBeVisible({ timeout: 10000 });
        await row.locator('a').first().click();

        // Wait for detail page
        await page.waitForSelector('#user-form');

        // Delete using modal confirmation (matching C6 pattern)
        await page.click('button:has-text("Delete")');
        await page.waitForSelector('#confirmDeleteBtn', { state: 'visible' });
        await Promise.all([
            page.waitForNavigation(),
            page.evaluate(() => document.getElementById('confirmDeleteBtn').click())
        ]);

        // Verify redirection back to list page (C6 pattern)
        await page.waitForSelector('#usersTable table', { timeout: 10000 });

        // Verify user is gone - wait a moment for page to update (C6 pattern)
        await page.waitForTimeout(500);
        await expect(page.locator('tr', { hasText: username })).toHaveCount(0, { timeout: 5000 });

        // Verify flash message (if visible) - C6 pattern
        const flashMessage = page.locator('.alert-success');
        if (await flashMessage.isVisible({ timeout: 2000 })) {
            await expect(flashMessage).toContainText('deleted');
        }
    });
});
