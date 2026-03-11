const { test, expect } = require("@playwright/test");

test.describe("Planning Dashboard", () => {
  // Increase timeout for this suite as planning logic can be heavy
  test.setTimeout(60000);

  test.beforeEach(async ({ page }) => {
    // Authenticate as admin
    await page.goto("/login");
    await page.fill('input[name="username"]', "admin");
    await page.fill('input[name="password"]', "admin123");
    await page.click('button[type="submit"]');
    await page.waitForLoadState("networkidle");
  });

  test("should load the planning dashboard", async ({ page }) => {
    await page.goto("/planning/");

    // Wait for potential heavy specific elements instead of just title
    // "Planning Module" is an h1 tag (with class h2), so strict role check needs level 1
    await expect(
      page.getByRole("heading", { level: 1, name: "Planning Module" }),
    ).toBeVisible({ timeout: 30000 });

    // Check for Create New Schedule form instead of legacy "New Plan" link
    await expect(
      page.getByRole("heading", { name: "Create New Schedule" }),
    ).toBeVisible();
    await expect(page.locator("#createScheduleForm")).toBeVisible();
  });

  // Navigation link to manage mappings is not currently on the dashboard
  // SMOKE-P02 covers the direct access to that page.
});
