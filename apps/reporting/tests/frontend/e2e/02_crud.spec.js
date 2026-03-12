const { test, expect } = require("@playwright/test");

/**
 * Reporting App CRUD Tests (current UI)
 */

const login = async (page) => {
  await page.goto("/login");
  await page.fill('input[name="username"]', "admin");
  await page.fill('input[name="password"]', "admin123");
  await page.click('button[type="submit"]');
  await page.waitForLoadState("networkidle");
};

async function createShiftReport(page) {
  await page.goto("/reporting/");
  await page.waitForLoadState("networkidle");

  await page.click('button[data-target="#generateReportModal"]');
  await expect(page.locator("#generateReportModal")).toBeVisible();

  await page.selectOption("#report_type", "shift_report");
  await page.fill("#shift_date", "2026-01-21");
  await page.selectOption("#shift_name", "Early");

  // Select first available team option that has a value
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
}

test.describe("Reporting App CRUD Tests", () => {
  test("E2E-R01: Create Shift Report and Open Detail", async ({ page }) => {
    await login(page);
    await createShiftReport(page);

    // Advanced table renders links to report detail; open newest one.
    const firstReportLink = page
      .locator('#reportingTable a[href^="/reporting/"]')
      .first();
    await expect(firstReportLink).toBeVisible({ timeout: 15000 });
    await firstReportLink.click();

    await expect(page).toHaveURL(/\/reporting\/\d+$/);
    await expect(page.locator("#report-content")).toBeVisible();
  });
});
