const { test, expect } = require('@playwright/test');

test.describe('CRUD Functional Tests', () => {
    test.beforeEach(async ({ page }) => {
        // Login before each test
        await page.goto('/login');
        await page.fill('input[name="username"]', 'admin');
        await page.fill('input[name="password"]', 'admin123');
        await page.click('button[type="submit"]');
        await page.waitForURL(/\/assets/);
    });

    // --- Assets ---
    test('E2E-C1: test_create_asset', async ({ page }) => {
        await page.goto('/assets');
        await page.click('text=New Asset');

        const assetName = 'Test Asset ' + Date.now();
        await page.fill('input[name="asset_code"]', 'AC-' + Date.now());
        await page.fill('input[name="name"]', assetName);
        await page.fill('textarea[name="description"]', 'Description for ' + assetName);
        await page.selectOption('select[name="asset_type"]', 'robot');
        await page.selectOption('select[name="cost_center"]', 'assembly');
        await page.selectOption('select[name="status"]', 'Operational');

        await page.click('button[type="submit"]');

        // Verify creation
        await expect(page.locator(`text=${assetName}`)).toBeVisible();
    });

    test('E2E-C2: test_edit_asset', async ({ page }) => {
        await page.goto('/assets');
        // Click first edit button. Assuming row has an edit link/button.
        // We might need to target a specific asset to avoid editing data that affects other tests,
        // but for now let's try to edit the one we created or just the first one.
        // Better: create one, then edit it.

        // Let's reuse creation logic or just pick the first one.
        const firstRow = page.locator('table tbody tr').first();
        const assetName = await firstRow.locator('td').nth(1).textContent(); // Assuming 2nd col is Name

        await firstRow.locator('a:has-text("Edit")').click();

        const newDesc = 'Updated Description ' + Date.now();
        await page.fill('textarea[name="description"]', newDesc);
        await page.click('button[type="submit"]');

        // Verify update
        await expect(page.locator('text=Asset updated successfully')).toBeVisible(); // Flash message?
    });

    test('E2E-C3: test_delete_asset', async ({ page }) => {
        await page.goto('/assets');
        // Ensure we have something to delete.
        // Careful not to delete critical data.
        // Ideally we create a disposable asset.

        await page.click('text=New Asset');
        const assetName = 'Delete Me ' + Date.now();
        await page.fill('input[name="name"]', assetName);
        await page.click('button[type="submit"]');

        // Now delete it
        const row = page.locator('tr', { hasText: assetName });

        // Handle confirmation dialog
        page.on('dialog', dialog => dialog.accept());

        await row.locator('button:has-text("Delete")').click(); // or form button

        await expect(page.locator(`text=${assetName}`)).not.toBeVisible();
    });

    // --- Maintenance Orders ---
    test('E2E-C4: test_create_maintenance_order', async ({ page }) => {
        await page.goto('/maintenance_orders');
        await page.click('text=Add New MO');

        await page.fill('textarea[name="description"]', 'MO ' + Date.now());
        // Select Order Type: 'corrective' based on HTML value
        await page.selectOption('select[name="order_type"]', 'corrective');
        await page.selectOption('select[name="priority"]', 'Medium');

        // Required fields
        await page.fill('input[name="estimated_completion_time"]', '60');
        await page.fill('input[name="labour_count"]', '1');

        // Select Asset (assuming dropdown)
        const assetSelect = page.locator('select[name="asset_id"]');
        if (await assetSelect.isVisible()) {
             await assetSelect.selectOption({ index: 1 }); // Select first available
        }

        await page.click('button[type="submit"]');
        await expect(page.locator('.alert-success')).toBeVisible();
    });

    test('E2E-C5: test_edit_maintenance_order', async ({ page }) => {
        await page.goto('/maintenance_orders');
        // Need to ensure there is an order.

        const firstRow = page.locator('#maintenanceOrdersTable table tbody tr').first();
        // Wait for table to load
        await page.waitForSelector('#maintenanceOrdersTable table tbody tr');

        // Check if rows exist
        if (await firstRow.count() === 0) {
             // Create one if none
             await page.click('text=Add New MO');
             await page.fill('textarea[name="description"]', 'Temp MO');
             await page.selectOption('select[name="order_type"]', 'CM');
             await page.selectOption('select[name="priority"]', 'Low');
             await page.selectOption('select[name="asset_id"]', { index: 1 });
             await page.click('button[type="submit"]');
             await page.goto('/maintenance_orders');
        }

        await firstRow.locator('a:has-text("Edit")').click();

        await page.fill('textarea[name="description"]', 'Updated MO Desc ' + Date.now());
        await page.click('button[type="submit"]');

        await expect(page.locator('.alert-success')).toBeVisible();
    });

    test('E2E-C6: test_delete_maintenance_order', async ({ page }) => {
        await page.goto('/maintenance_orders');
        // Create one to delete
        await page.click('text=Add New MO');
        const desc = 'Delete MO ' + Date.now();
        await page.fill('textarea[name="description"]', desc);
        await page.selectOption('select[name="order_type"]', 'CM');
        await page.selectOption('select[name="priority"]', 'Low');
        await page.locator('select[name="asset_id"]').selectOption({ index: 1 });
        await page.click('button[type="submit"]');

        // Go back to list (if not redirected) - add_mo redirects to maintenance_orders

        // Find row
        // Advanced Table uses complex structure?
        // Assuming desc is visible.
        await expect(page.locator(`text=${desc}`)).toBeVisible();
        const row = page.locator('tr', { hasText: desc });

        // Handle confirmation dialog
        page.on('dialog', dialog => dialog.accept());

        // Delete button might be in a menu or direct
        // Assuming "Delete" button/form
        // Usually inside a form with method POST
        await row.locator('button.btn-danger').click(); // Adjust selector

        await expect(page.locator(`text=${desc}`)).not.toBeVisible();
    });

    // --- Spare Parts ---
    test('E2E-C7: test_create_spare_part', async ({ page }) => {
        await page.goto('/spare_parts');
        await page.click('text=Add New Spare Part');

        const desc = 'Part ' + Date.now();
        // Note: SparePart uses description as main text, not name.
        await page.fill('textarea[name="description"]', desc); // Check if textarea or input
        await page.fill('input[name="manufacturer"]', 'Acme Corp');
        await page.fill('input[name="manufacturer_part_id"]', 'PN-' + Date.now());
        await page.fill('input[name="stock_quantity"]', '10');
        await page.fill('input[name="location"]', 'Warehouse A');
        await page.fill('input[name="min_quantity"]', '5');

        await page.click('button[type="submit"]');
        await expect(page.locator(`text=${desc}`)).toBeVisible();
    });

    // --- Users ---
    test('E2E-C8: test_create_user', async ({ page }) => {
        await page.goto('/users');
        await page.click('text=Add New User');

        const username = 'user' + Date.now();
        await page.fill('input[name="username"]', username);
        await page.fill('input[name="email"]', `${username}@example.com`);
        await page.fill('input[name="password"]', 'password123');
        // 'roles' is a multi-select. Value is likely 'Technician'.
        await page.selectOption('select[name="roles"]', 'Technician');

        await page.click('button[type="submit"]');
        await expect(page.locator(`text=${username}`)).toBeVisible();
    });
});
