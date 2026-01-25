const { test, expect } = require("@playwright/test");

/**
 * Reports App - Visual Regression Tests
 */

async function login(page) {
  await page.goto("/login");
  await page.fill('input[name="username"]', "admin");
  await page.fill('input[name="password"]', "admin123");
  await page.click('button[type="submit"]');
  await page.waitForLoadState("networkidle");
  // Verify login success by checking for nav or sidebar
  await expect(page.locator("nav").first()).toBeVisible({ timeout: 15000 });
}

test.beforeEach(async ({ page }) => {
  await login(page);
  // Inject consistent height style matching core standard
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

test.describe("Visual Regression - Reports App", () => {
  test("VR-R01: Reports Dashboard / Generate", async ({ page }) => {
    await page.goto("/reports/generate");
    await expect(
      page.locator("h2").filter({ hasText: "Generate Report" }),
    ).toBeVisible();
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveScreenshot("reports-generate.png", {
      fullPage: true,
      mask: [page.locator('input[name="csrf_token"]')],
    });
  });

  test("VR-R02: Incident Reporting", async ({ page }) => {
    await page.goto("/reports/incidents/");
    // Wait for table to be populated
    await expect(page.locator("table tbody tr")).toHaveCount(10, {
      timeout: 15000,
    });
    await expect(
      page.locator("h2").filter({ hasText: "Incident Reports" }),
    ).toBeVisible();
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveScreenshot("reports-incidents.png", {
      fullPage: true,
      mask: [page.locator('input[name="csrf_token"]')],
    });
  });

  test("VR-R03: Shift Report", async ({ page }) => {
    // Data is seeded with FIXED_DATE_SEEDING="2026-01-21" for E2E tests
    const today = "2026-01-21";

    // Go to shift report page with today's date
    await page.goto(`/reports/shift/?date=${today}&shift=Morning`);

    // Ensure report generated
    await expect(
      page.locator("h2").filter({ hasText: "Shift Production Report" }),
    ).toBeVisible();
    await page.waitForLoadState("networkidle");

    // Click "View Report" if needed to refresh data
    const generateBtn = page.locator('button:has-text("View Report")');
    if (await generateBtn.isVisible()) {
      await generateBtn.click();
      await page.waitForLoadState("networkidle");
    }

    // Wait for data to load and ASSERT data exists (non-zero)
    // The stats count is displayed in a h2 with class mb-0 inside a card
    await expect(page.locator(".card h2.mb-0").first()).not.toHaveText("0", {
      timeout: 10000,
    });

    // Wait for data to load
    await page.waitForTimeout(1000);

    await expect(page).toHaveScreenshot("reports-shift.png", {
      fullPage: true,
      mask: [page.locator('input[name="csrf_token"]')],
    });
  });

  test("VR-R04: Weekend Report", async ({ page }) => {
    // Seed data "Weekend Maintenance" tasks have due_days_from_weekend relative to the base date
    // Base date is Wed 2026-01-21. Next Saturday is 2026-01-24.
    const startDate = "2026-01-24";
    const endDate = "2026-01-25";

    await page.goto(
      `/reports/weekend/?start_date=${startDate}&end_date=${endDate}`,
    );
    await expect(
      page.locator("h2").filter({ hasText: "Weekend Task Report" }),
    ).toBeVisible();
    await page.waitForLoadState("networkidle");

    // Click "Generate Report" if needed
    const generateBtn = page.locator('button:has-text("Generate Report")');
    if (await generateBtn.isVisible()) {
      await generateBtn.click();
      await page.waitForLoadState("networkidle");
    }

    // Wait for data to load and ASSERT data exists (non-zero)
    await expect(page.locator(".card-text.display-4").first()).not.toHaveText(
      "0",
      { timeout: 10000 },
    );

    // Wait for data to load
    await page.waitForTimeout(1000);

    await expect(page).toHaveScreenshot("reports-weekend.png", {
      fullPage: true,
      mask: [page.locator('input[name="csrf_token"]')],
    });
  });
});
