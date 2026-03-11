const { test, expect } = require("@playwright/test");

test.describe("Weekend Report", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
    await page.fill('input[name="username"]', "admin");
    await page.fill('input[name="password"]', "admin123");
    await page.click('button[type="submit"]');
    await page.waitForLoadState("networkidle");
  });

  test("should generate weekend report from reports modal", async ({
    page,
  }) => {
    await page.goto("/reports/");
    await expect(
      page.getByRole("heading", { name: /^Reports$/ }),
    ).toBeVisible();

    await page.click('button[data-target="#generateReportModal"]');
    await expect(page.locator("#generateReportModal")).toBeVisible();

    await page.selectOption("#report_type", "weekend_report");
    await page.fill("#weekend_date", "2026-01-24");
    await page.selectOption("#weekend_shift", "Night");

    await page.click('#generateReportModal button[type="submit"]');
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveURL(/\/reports\/?$/);

    // Open the newest report.
    const firstReportLink = page
      .locator('#reportsTable a[href^="/reports/"]')
      .first();
    await expect(firstReportLink).toBeVisible({ timeout: 15000 });
    await firstReportLink.click();

    await expect(page).toHaveURL(/\/reports\/\d+$/);
    await expect(page.locator("#report-content")).toBeVisible();
  });

  test("should display markdown copy and export controls in detail", async ({
    page,
  }) => {
    await page.goto("/reports/");
    const firstReportLink = page
      .locator('#reportsTable a[href^="/reports/"]')
      .first();
    await expect(firstReportLink).toBeVisible({ timeout: 15000 });
    await firstReportLink.click();

    await expect(page.locator("#copyMdBtn")).toBeVisible();
    await expect(page.locator('button:has-text("Export")')).toBeVisible();
  });
});
