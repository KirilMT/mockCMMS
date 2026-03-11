const { test, expect } = require("@playwright/test");

/**
 * Reports App Smoke Tests
 */

const login = async (page) => {
  await page.goto("/login");
  await page.fill('input[name="username"]', "admin");
  await page.fill('input[name="password"]', "admin123");
  await page.click('button[type="submit"]');
  await page.waitForLoadState("networkidle");
};

test.describe("Reports App Smoke Tests", () => {
  test("SMOKE-R01: Navigate to Reports Dashboard", async ({ page }) => {
    await login(page);
    await page.goto("/reports/");
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveURL(/reports/);
    await expect(page.locator("h1, h2, .navbar-brand").first()).toBeVisible();
  });

  test("SMOKE-R02: Generate Report Page Loads", async ({ page }) => {
    await login(page);
    await page.goto("/reports/generate");
    await page.waitForLoadState("networkidle");
    await expect(page.locator(".card-body form")).toBeVisible();
  });
});
