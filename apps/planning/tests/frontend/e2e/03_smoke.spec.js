const { test, expect } = require("@playwright/test");

/**
 * Planning App Smoke Tests
 */

// Helper: Login
const login = async (page) => {
  await page.goto("/login");
  await page.fill('input[name="username"]', "admin");
  await page.fill('input[name="password"]', "admin123");
  await page.click('button[type="submit"]');
  // Wait for redirect to default page (assets) or planning root if configured
  await page.waitForLoadState("networkidle");
};

test.describe("Planning App Smoke Tests", () => {
  test("SMOKE-P01: Login and Navigate to Planning Dashboard", async ({
    page,
  }) => {
    await login(page);

    // Navigate specifically to Planning app
    await page.goto("/planning/");
    await page.waitForLoadState("networkidle");

    // Verify title or key element
    await expect(page).toHaveURL(/planning/);
    await expect(
      page.getByRole("heading", { name: "Planning Module" }),
    ).toBeVisible();
  });

  test("SMOKE-P02: Navigate to Manage Mappings UI", async ({ page }) => {
    await login(page);
    await page.goto("/planning/manage_mappings_ui");
    // Use domcontentloaded instead of networkidle which can timeout on slow pages
    await page.waitForLoadState("domcontentloaded");

    // Verify unique element on this page
    await expect(
      page.getByRole("heading", { name: "Skill-Based Mappings Management" }),
    ).toBeVisible({ timeout: 15000 });
    await expect(page.locator("#manageSatelliteLinesSection")).toBeVisible({
      timeout: 10000,
    });
  });

  test("SMOKE-P03: API Health Check - Get Technicians", async ({ page }) => {
    // We need auth cookie for API call if it's protected, usually via browser context
    // But for simplicity, we can try accessing via Page to ensure session is active
    await login(page);

    const response = await page.request.get("/planning/api/technicians");
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data).toBeDefined();
  });
});
