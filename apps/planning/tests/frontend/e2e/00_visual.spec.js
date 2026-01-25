const { test, expect } = require("@playwright/test");

/**
 * Planning App - Visual Regression Tests
 */

async function login(page) {
  await page.goto("/login");
  await page.fill('input[name="username"]', "admin");
  await page.fill('input[name="password"]', "admin123");
  await page.click('button[type="submit"]');
  // Wait for redirect to assets page after login
  await page.waitForURL(/\/(assets|planning)/, { timeout: 15000 });
  await page.waitForLoadState("networkidle");
  // Verify login success by checking for nav or sidebar
  await expect(page.locator("nav").first()).toBeVisible({ timeout: 10000 });
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

test.describe("Visual Regression - Planning App", () => {
  test("VR-P01: Planning Dashboard", async ({ page }) => {
    await page.goto("/planning");
    // Wait for potential schedule cards or empty state
    await expect(
      page.locator("h1").filter({ hasText: "Planning Module" }),
    ).toBeVisible();
    await page.waitForLoadState("networkidle");

    await page.waitForTimeout(500); // Wait for fonts and rendering

    await expect(page).toHaveScreenshot("planning-dashboard.png", {
      fullPage: true,
      maxDiffPixelRatio: 0.02, // Allow 2% tolerance for font rendering
      mask: [
        page.locator('input[name="csrf_token"]'),
        page.locator('input[type="date"]'), // Mask date pickers
        page.locator("td:nth-child(5)"), // Mask CREATED column timestamps
      ],
    });
  });

  test("VR-P02: Schedule Detail Page (Gantt View)", async ({ page }) => {
    await page.goto("/planning/schedules/1");

    await expect(page).toHaveURL(/\/planning\/schedules\/\d+/);

    // Click "Run Planning" button to generate the schedule
    const runPlanningBtn = page
      .locator("button.btn-success")
      .filter({ hasText: /Run Planning/i });
    if (await runPlanningBtn.isVisible({ timeout: 5000 })) {
      await runPlanningBtn.click();
      // Wait for planning to complete
      await page.waitForTimeout(3000);
    }

    // Ensure gantt chart container and planning tasks table are visible
    // The actual selectors in schedule_view.html are:
    // - #gantt-container for the Gantt chart
    // - #planningTasksTable for the tasks table
    await expect(page.locator("#gantt-container")).toBeVisible({
      timeout: 15000,
    });
    await expect(page.locator("#planningTasksTable")).toBeVisible();

    // Wait for data to fully render
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);

    await expect(page).toHaveScreenshot("planning-schedule-detail.png", {
      fullPage: true,
      maxDiffPixelRatio: 0.02, // Allow 2% tolerance for font rendering (Masks handle dynamic content)
      mask: [
        page.locator('input[name="csrf_token"]'),
        page.locator(".alert-success"), // Mask success toast with dynamic task count
      ],
    });
  });
});
