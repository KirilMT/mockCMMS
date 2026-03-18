const { test, expect } = require("@playwright/test");

test.describe("Shift Report", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
    await page.fill('input[name="username"]', "admin");
    await page.fill('input[name="password"]', "admin123");
    await page.click('button[type="submit"]');
    await page.waitForLoadState("networkidle");
  });

  test("should generate shift report from reporting modal", async ({
    page,
  }) => {
    await page.goto("/reporting/");

    await page.click('button[data-target="#generateReportModal"]');
    await expect(page.locator("#generateReportModal")).toBeVisible();

    await page.selectOption("#report_type", "shift_report");
    await page.fill("#shift_date", "2026-01-21");
    await page.selectOption("#shift_name", "Early");

    const teamOptions = page.locator("#team_id option[value]");
    const count = await teamOptions.count();
    if (count > 0) {
      const value = await teamOptions.nth(0).getAttribute("value");
      if (value) {
        await page.selectOption("#team_id", value);
      }
    }

    await page.click('#generateReportModal button[type="submit"]');
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveURL(/\/reporting\/?$/);

    const firstReportLink = page
      .locator('#reportingTable a[href^="/reporting/"]')
      .first();
    await expect(firstReportLink).toBeVisible({ timeout: 15000 });
    await firstReportLink.click();

    await expect(page).toHaveURL(/\/reporting\/\d+$/);
    await expect(page.locator(".report-header")).toBeVisible();
    await expect(page.locator("#report-content")).toBeVisible();
  });

  test("should show export controls in shift report detail", async ({
    page,
  }) => {
    await page.goto("/reporting/");
    const firstReportLink = page
      .locator('#reportingTable a[href^="/reporting/"]')
      .first();
    await expect(firstReportLink).toBeVisible({ timeout: 15000 });
    await firstReportLink.click();

    await expect(page.locator('button:has-text("Export")')).toBeVisible();
    await page.click('button:has-text("Export")');
    await expect(page.locator(".dropdown-menu")).toBeVisible();
  });
});
