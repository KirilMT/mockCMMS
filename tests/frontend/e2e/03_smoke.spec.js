const { test, expect } = require("@playwright/test");

/**
 * Smoke Tests
 *
 * Quick, essential tests that verify the application's critical paths work.
 * These should run fast and catch major regressions.
 *
 * Coverage:
 * - Authentication (login, logout, access control)
 * - Navigation (all list pages load)
 * - Form loading (create forms accessible)
 * - Detail pages (navigation from list to detail)
 * - Table sidebar (toggle, sections)
 * - Error handling (404)
 */

// Helper for authenticated tests
const login = async (page) => {
  await page.goto("/login");
  await page.fill('input[name="username"]', "admin");
  await page.fill('input[name="password"]', "admin123");
  await page.click('button[type="submit"]');
  await page.waitForURL(/\/assets/);
};

// Helper to wait for table to be fully loaded
async function waitForTable(page, tableId, options = {}) {
  const timeout = options.timeout || 15000;
  await page.waitForSelector(`${tableId} table`, { timeout });
  await page.waitForLoadState("networkidle");
}

// ============================================================================
// AUTHENTICATION
// ============================================================================

test.describe("Authentication Smoke Tests", () => {
  test("SMOKE-01: Successful login and logout", async ({ page }) => {
    await page.goto("/login");
    await page.fill('input[name="username"]', "admin");
    await page.fill('input[name="password"]', "admin123");
    await page.click('button[type="submit"]');

    // Verify login success (redirects to /assets for admin)
    await expect(page).toHaveURL(/\/assets/);
    await expect(page.locator("text=Logout")).toBeVisible();

    // Logout - wait for navigation since it submits a form
    await Promise.all([
      page.waitForURL(/\/login/, { timeout: 10000 }),
      page.click('button:has-text("Logout")'),
    ]);

    // Verify we're on login page
    await expect(page).toHaveURL(/\/login/);
  });

  test("SMOKE-02: Login failure stays on login page", async ({ page }) => {
    await page.goto("/login");
    await page.fill('input[name="username"]', "admin");
    await page.fill('input[name="password"]', "wrongpassword");
    await page.click('button[type="submit"]');

    // Should stay on login page (not redirect to assets)
    await expect(page).toHaveURL(/\/login/);
    await expect(page.locator('input[name="username"]')).toBeVisible();
  });

  test("SMOKE-03: Unauthenticated user redirected to login", async ({
    page,
  }) => {
    await page.goto("/assets");
    await expect(page).toHaveURL(/\/login/);
  });
});

// ============================================================================
// LIST PAGE NAVIGATION
// ============================================================================

test.describe("Navigation Smoke Tests", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("SMOKE-04: Assets page loads with table", async ({ page }) => {
    await page.goto("/assets");
    await expect(page.locator("#assetsTable table")).toBeVisible({
      timeout: 15000,
    });
  });

  test("SMOKE-05: Maintenance Orders page loads with table", async ({
    page,
  }) => {
    await page.goto("/maintenance_orders");
    await expect(page.locator("#mosTable table")).toBeVisible({
      timeout: 15000,
    });
  });

  test("SMOKE-06: Spare Parts page loads with table", async ({ page }) => {
    await page.goto("/spare_parts");
    await expect(page.locator("#sparePartsTable table")).toBeVisible({
      timeout: 15000,
    });
  });

  test("SMOKE-07: Users page loads with table", async ({ page }) => {
    await page.goto("/users");
    await expect(page.locator("#usersTable table")).toBeVisible({
      timeout: 15000,
    });
  });

  test("SMOKE-08: Shift Calendar page loads", async ({ page }) => {
    await page.goto("/shift_calendar");
    await page.waitForLoadState("networkidle");
    // Verify page loaded (calendar or content present)
    await expect(page.locator("body")).toContainText(/calendar|shift/i);
  });
});

// ============================================================================
// DETAIL PAGE NAVIGATION
// ============================================================================

test.describe("Detail Page Navigation Tests", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("SMOKE-09: Navigate from Assets list to Asset detail", async ({
    page,
  }) => {
    await page.goto("/assets");
    await waitForTable(page, "#assetsTable");

    // Click on the link in the first row (not the row itself)
    const firstRow = page.locator("#assetsTable tbody tr").first();
    await firstRow.locator("a").first().click();

    // Verify we're on detail page
    await expect(page).toHaveURL(/\/assets\/\d+/);
    await expect(page.locator("#asset-form")).toBeVisible();
  });

  test("SMOKE-10: Navigate from MO list to MO detail", async ({ page }) => {
    await page.goto("/maintenance_orders");
    await waitForTable(page, "#mosTable");

    const firstRow = page.locator("#mosTable tbody tr").first();
    await firstRow.locator("a").first().click();

    await expect(page).toHaveURL(/\/maintenance_orders\/\d+/);
    await expect(page.locator("#mo-form")).toBeVisible();
  });

  test("SMOKE-11: Navigate from Spare Parts list to detail", async ({
    page,
  }) => {
    await page.goto("/spare_parts");
    await waitForTable(page, "#sparePartsTable");

    const firstRow = page.locator("#sparePartsTable tbody tr").first();
    await firstRow.locator("a").first().click();

    await expect(page).toHaveURL(/\/spare_parts\/\d+/);
  });

  test("SMOKE-12: Navigate from Users list to User detail", async ({
    page,
  }) => {
    await page.goto("/users");
    await waitForTable(page, "#usersTable");

    const firstRow = page.locator("#usersTable tbody tr").first();
    await firstRow.locator("a").first().click();

    await expect(page).toHaveURL(/\/users\/\d+/);
  });
});

// ============================================================================
// ADD/CREATE FORMS
// ============================================================================

test.describe("Form Loading Tests", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("SMOKE-13: Add New Asset form loads correctly", async ({ page }) => {
    await page.goto("/assets/add");
    await page.waitForLoadState("networkidle");

    // Asset form uses #asset-form, submit button linked via form attribute
    await expect(page.locator("#asset-form")).toBeVisible();
    await expect(page.locator('input[name="name"]')).toBeVisible();
    await expect(page.locator('button[form="asset-form"]')).toBeVisible();
  });

  test("SMOKE-14: Add New MO form loads correctly", async ({ page }) => {
    await page.goto("/maintenance_orders/add");
    await page.waitForLoadState("networkidle");

    await expect(page.locator("#mo-form")).toBeVisible();
    await expect(page.locator('textarea[name="description"]')).toBeVisible();
    await expect(page.locator('button[form="mo-form"]')).toBeVisible();
  });

  test("SMOKE-15: Add New Spare Part form loads correctly", async ({
    page,
  }) => {
    await page.goto("/spare_parts/add");
    await page.waitForLoadState("networkidle");

    // Spare part form uses description textarea, not name. Form ID is #part-form
    await expect(page.locator("#part-form")).toBeVisible();
    await expect(page.locator('textarea[name="description"]')).toBeVisible();
    await expect(page.locator('button[form="part-form"]')).toBeVisible();
  });

  test("SMOKE-16: User registration form loads correctly", async ({ page }) => {
    await page.goto("/register");
    await page.waitForLoadState("networkidle");

    // Register form uses #user-form, submit button is outside form with form="user-form"
    await expect(page.locator("#user-form")).toBeVisible();
    await expect(page.locator('input[name="username"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('button[form="user-form"]')).toBeVisible();
  });
});

// ============================================================================
// TABLE SIDEBAR
// ============================================================================

test.describe("Table Sidebar Tests", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("SMOKE-17: Table sidebar toggle works", async ({ page }) => {
    await page.goto("/assets");
    await waitForTable(page, "#assetsTable");

    // Ensure sidebar starts COLLAPSED
    await page.evaluate(() => {
      localStorage.setItem("tableSidebarCollapsed", "true");
      localStorage.removeItem("tableSidebarSections");
    });
    // Use navigation instead of reload to avoid timeout issues on Firefox
    await page.goto("/assets", { waitUntil: "domcontentloaded" });
    await waitForTable(page, "#assetsTable");

    const toggleBtn = page.locator(".btn-toggle-sidebar");
    await expect(toggleBtn).toBeVisible();

    // Click to open sidebar (starts collapsed)
    await toggleBtn.click();

    // Verify sidebar is visible and not collapsed
    const sidebar = page.locator(".table-sidebar");
    await expect(sidebar).toBeVisible();
    await expect(sidebar).not.toHaveClass(/collapsed/);
  });

  test("SMOKE-18: Sidebar filter section expands", async ({ page }) => {
    await page.goto("/assets");
    await waitForTable(page, "#assetsTable");

    // Ensure sidebar starts COLLAPSED so we can open it cleanly
    await page.evaluate(() => {
      localStorage.setItem("tableSidebarCollapsed", "true");
      localStorage.removeItem("tableSidebarSections");
    });
    await page.goto("/assets", { waitUntil: "domcontentloaded" });
    await waitForTable(page, "#assetsTable");

    // Open sidebar first
    await page.locator(".btn-toggle-sidebar").click();

    // Click filters section header to expand
    // Wait for the section to improve stability
    const filtersSection = page.locator(
      '.sidebar-section[data-section="filters"]',
    );
    await expect(filtersSection).toBeVisible();

    // Wait for section header to be stable and click
    const header = filtersSection.locator(".section-header");
    await header.waitFor({ state: "visible" });
    await header.click();

    // Verify section expanded (content no longer has 'collapsed' class)
    const filtersContent = filtersSection.locator(".section-content");
    await expect(filtersContent).toBeVisible();
    await expect(filtersContent).not.toHaveClass(/collapsed/);
  });

  test("SMOKE-19: Sidebar columns section expands", async ({ page }) => {
    await page.goto("/assets");
    await waitForTable(page, "#assetsTable");

    // Ensure sidebar starts COLLAPSED
    await page.evaluate(() => {
      localStorage.setItem("tableSidebarCollapsed", "true");
      localStorage.removeItem("tableSidebarSections");
    });
    await page.goto("/assets", { waitUntil: "domcontentloaded" });
    await waitForTable(page, "#assetsTable");

    // Open sidebar first
    await page.locator(".btn-toggle-sidebar").click();

    // Click columns section header to expand
    const columnsSection = page.locator(
      '.sidebar-section[data-section="columns"]',
    );
    await expect(columnsSection).toBeVisible();

    const header = columnsSection.locator(".section-header");
    await header.waitFor({ state: "visible" });
    await header.click();

    // Verify section expanded (content no longer has 'collapsed' class)
    const columnsContent = columnsSection.locator(".section-content");
    // Also verify column list is visible
    await expect(columnsContent).toBeVisible();
    await expect(columnsContent).not.toHaveClass(/collapsed/);
    await expect(columnsSection.locator("#columnList")).toBeVisible();
  });
});

// ============================================================================
// ERROR HANDLING
// ============================================================================

test.describe("Error Handling Tests", () => {
  test("SMOKE-20: 404 page displays correctly", async ({ page }) => {
    await page.goto("/nonexistent-page-xyz");
    const content = await page.content();
    expect(content).toMatch(/404|not found|error/i);
  });
});

// ============================================================================
// CRUD LIFECYCLE TESTS
// ============================================================================

test.describe("CRUD Lifecycle Tests", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("SMOKE-21: Create New Asset and Verify in List", async ({ page }) => {
    const assetName = `Test Asset ${Date.now()}`;
    const assetCode = `TA-${Date.now()}`;

    // 1. Go to Add Asset Page
    await page.goto("/assets/add");
    await page.waitForLoadState("networkidle");

    // 2. Fill Form
    await page.fill('input[name="name"]', assetName);
    await page.fill('input[name="asset_code"]', assetCode);
    await page.selectOption('select[name="asset_type"]', "robot");
    await page.selectOption('select[name="cost_center"]', "assembly");
    await page.selectOption('select[name="status"]', "Operational");
    await page.fill(
      'textarea[name="description"]',
      "E2E Test Asset Description",
    );

    // 3. Submit Form
    await page.click('button[form="asset-form"]');

    // 4. Verify Redirect to List
    await expect(page).toHaveURL(/\/assets\/?$/);
    await waitForTable(page, "#assetsTable");

    // Filter to ensure visibility
    await page.getByPlaceholder("Search all columns...").fill(assetName);
    await page.keyboard.press("Enter");

    // 5. Verify presence in table
    await expect(page.locator(`text=${assetName}`)).toBeVisible();
  });

  test("SMOKE-22: Delete Asset and Verify Absence", async ({ page }) => {
    // Create a temporary asset to delete
    const assetName = `Delete Me ${Date.now()}`;
    const assetCode = `DEL-${Date.now()}`;

    // Quick creation
    await page.goto("/assets/add");
    await page.fill('input[name="name"]', assetName);
    await page.fill('input[name="asset_code"]', assetCode);
    await page.selectOption('select[name="asset_type"]', "tooling");
    await page.selectOption('select[name="cost_center"]', "paint");
    await page.selectOption('select[name="status"]', "Down");

    await page.click('button[form="asset-form"]');
    await expect(page).toHaveURL(/\/assets\/?$/);

    // Filter to ensure visibility
    await page.getByPlaceholder("Search all columns...").fill(assetName);
    await page.keyboard.press("Enter");

    // Find row with this asset
    const row = page.locator("tr", { has: page.locator(`text=${assetName}`) });
    await expect(row).toBeVisible();

    // Click link to go to detail
    await row.locator("a").first().click();
    await page.waitForLoadState("networkidle");

    // Click Delete button on detail page (opens modal confirmation)
    await page.click('button:has-text("Delete")');

    // Wait for modal and confirm
    await expect(page.locator("#confirmDeleteBtn")).toBeVisible();
    await Promise.all([
      page.waitForNavigation(),
      page.locator("#confirmDeleteBtn").click(),
    ]);

    // Validate removal
    await expect(page).toHaveURL(/\/assets\/?$/);

    // Search again to verify absence
    await page.getByPlaceholder("Search all columns...").fill(assetName);
    await page.keyboard.press("Enter");

    // Confirm "No results found" message appears
    await expect(
      page.locator(`text=No results found for "${assetName}"`),
    ).toBeVisible();
  });
});
