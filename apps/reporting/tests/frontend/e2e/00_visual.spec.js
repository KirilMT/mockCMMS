const { test, expect } = require("@playwright/test");

/**
 * Reporting App - Visual Regression Tests
 */

async function login(page) {
  await page.goto("/login");
  await page.fill('input[name="username"]', "admin");
  await page.fill('input[name="password"]', "admin123");
  await page.click('button[type="submit"]');
  await page.waitForLoadState("networkidle");
  await expect(page.locator("nav").first()).toBeVisible({ timeout: 15000 });
}

async function openGenerateModal(page) {
  await page.click('button[data-target="#generateReportModal"]');
  await expect(page.locator("#generateReportModal")).toBeVisible();
}

async function createShiftReport(page) {
  await openGenerateModal(page);
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
}

async function createWeekendReport(page) {
  await openGenerateModal(page);
  await page.selectOption("#report_type", "weekend_report");
  await page.fill("#weekend_date", "2026-01-24");
  await page.selectOption("#weekend_shift", "Night");
  await page.click('#generateReportModal button[type="submit"]');
  await page.waitForLoadState("networkidle");
}

test.beforeEach(async ({ page }) => {
  await login(page);
  await page.addInitScript(() => {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", injectStyle);
    } else {
      injectStyle();
    }
    function injectStyle() {
      const style = document.createElement("style");
      style.id = "playwright-visual-test-height";
      style.textContent = "body { min-height: 3000px !important; }";
      document.head.appendChild(style);
    }
  });
});

test.describe("Visual Regression - Reporting App", () => {
  test("VR-R01: Reporting Dashboard / Generate", async ({ page }) => {
    await page.goto("/reporting/generate");
    await expect(
      page.locator("h2").filter({ hasText: "Generate Report" }),
    ).toBeVisible();
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveScreenshot("reporting-generate.png", {
      fullPage: true,
      mask: [page.locator('input[name="csrf_token"]')],
    });
  });

  test("VR-R02: Reporting List", async ({ page }) => {
    await page.goto("/reporting/");
    await expect(
      page.getByRole("heading", { name: /^Reporting$/ }),
    ).toBeVisible();

    // Wait for reporting table and at least one report to load
    const reportLinks = page.locator('#reportingTable a[href^="/reporting/"]');
    await expect(reportLinks.first()).toBeVisible({
      timeout: 15000,
    });

    await page.waitForLoadState("networkidle");
    await expect(page).toHaveScreenshot("reporting-list.png", {
      fullPage: true,
      mask: [page.locator('input[name="csrf_token"]')],
    });
  });

  test("VR-R03: Shift Report - Visual Check", async ({ page }) => {
    await page.goto("/reporting/");
    await createShiftReport(page);

    const firstReportLink = page
      .locator('#reportingTable a[href^="/reporting/"]')
      .first();
    await expect(firstReportLink).toBeVisible({ timeout: 15000 });
    await firstReportLink.click();

    await expect(page.locator("#report-content")).toBeVisible();
    await expect(page.locator(".report-header")).toBeVisible();
    await page.waitForTimeout(500);

    await expect(page).toHaveScreenshot("reporting-shift-generated.png", {
      fullPage: true,
      mask: [page.locator('input[name="csrf_token"]')],
    });
  });

  test("VR-R03b: Weekend Report - Visual Check", async ({ page }) => {
    await page.goto("/reporting/");
    await createWeekendReport(page);

    const firstReportLink = page
      .locator('#reportingTable a[href^="/reporting/"]')
      .first();
    await expect(firstReportLink).toBeVisible({ timeout: 15000 });
    await firstReportLink.click();

    await expect(page.locator("#report-content")).toBeVisible();
    await expect(page.locator(".report-header")).toBeVisible();
    await page.waitForTimeout(500);

    await expect(page).toHaveScreenshot("reporting-weekend-generated.png", {
      fullPage: true,
      mask: [page.locator('input[name="csrf_token"]')],
    });
  });
});
