const { test, expect } = require("@playwright/test");

test.describe("Report Workflow", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
    await page.fill('input[name="username"]', "admin");
    await page.fill('input[name="password"]', "admin123");
    await page.click('button[type="submit"]');
    await page.waitForLoadState("networkidle");
  });

  test("should generate a new weekend report from modal", async ({ page }) => {
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

    // Validate list has at least one report entry link.
    await expect(
      page.locator('#reportsTable a[href^="/reports/"]').first(),
    ).toBeVisible({ timeout: 15000 });
  });

  test("should open report details from report list", async ({ page }) => {
    await page.goto("/reports/");

    const firstReportLink = page
      .locator('#reportsTable a[href^="/reports/"]')
      .first();
    await expect(firstReportLink).toBeVisible({ timeout: 15000 });
    await firstReportLink.click();

    await expect(page).toHaveURL(/\/reports\/\d+$/);
    await expect(page.locator("#report-content")).toBeVisible();
    await expect(page.locator("#copyMdBtn")).toBeVisible();
  });
});
