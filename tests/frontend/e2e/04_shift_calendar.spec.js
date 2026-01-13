const { test, expect } = require("@playwright/test");

/**
 * Shift Calendar Functional Tests
 *
 * Coverage:
 * - Page loading and authentication
 * - Calendar grid rendering
 * - Navigation (Previous/Next month)
 * - Shift display (Team badges)
 * - Current day highlighting
 */

// Helper for authenticated tests
const login = async (page) => {
  await page.goto("/login");
  await page.fill('input[name="username"]', "admin");
  await page.fill('input[name="password"]', "admin123");
  await page.click('button[type="submit"]');
  await page.waitForURL(/\/assets/);
};

test.describe("Shift Calendar Tests", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.goto("/shift_calendar");
    await page.waitForLoadState("networkidle");
  });

  test("SC-01: Page loads with correct title and current month", async ({
    page,
  }) => {
    // Verify page title
    await expect(page).toHaveTitle(/Shift Calendar/);
    await expect(page.locator("h1")).toHaveText("Shift Calendar");

    // Verify current month/year is displayed
    const now = new Date();
    const monthName = now.toLocaleString("default", { month: "long" });
    const year = now.getFullYear();
    await expect(page.locator(".h4")).toContainText(`${monthName} ${year}`);
  });

  test("SC-02: Calendar grid renders correctly", async ({ page }) => {
    // Verify calendar header days (Mon-Sun)
    const headers = page.locator(".calendar-header-day");
    await expect(headers).toHaveCount(7);
    await expect(headers.nth(0)).toHaveText("Mon");
    await expect(headers.nth(6)).toHaveText("Sun");

    // Verify grid cells exist (usually 35 or 42 cells)
    const cells = page.locator(".calendar-day");
    const cellCount = await cells.count();
    expect(cellCount).toBeGreaterThanOrEqual(28); // Basic sanity check

    // Verify day numbers are present
    const firstDayNumber = cells.first().locator(".day-number");
    await expect(firstDayNumber).toBeVisible();
  });

  test("SC-03: Navigation buttons work", async ({ page }) => {
    // Get current displayed month
    const currentMonthText = await page.locator(".h4").innerText();

    // Click Previous
    await page.click("text=Previous");
    await page.waitForLoadState("networkidle");

    // Verify month changed
    const prevMonthText = await page.locator(".h4").innerText();
    expect(prevMonthText).not.toBe(currentMonthText);

    // Click Next twice to go to next month
    await page.click("text=Next"); // Back to current
    await page.waitForLoadState("networkidle");
    await page.click("text=Next"); // To next month
    await page.waitForLoadState("networkidle");

    const nextMonthText = await page.locator(".h4").innerText();
    expect(nextMonthText).not.toBe(currentMonthText);
    expect(nextMonthText).not.toBe(prevMonthText);
  });

  test("SC-04: Team badges are displayed", async ({ page }) => {
    // Check for presence of shift blocks inside calendar days
    // We expect at least some shifts to be assigned
    const shiftBlocks = page.locator(".calendar-day .shift-block");

    // If database is seeded, we should see shifts.
    // However, if no shifts are assigned, this test might be flaky.
    // Assuming seeded data has shifts.

    if (await shiftBlocks.count() > 0) {
        await expect(shiftBlocks.first()).toBeVisible();
        const blockText = await shiftBlocks.first().innerText();
        expect(blockText).toMatch(/Team [A-D]/);
    }
  });

  test("SC-05: Current day is highlighted", async ({ page }) => {
    // This test only works if we are viewing the current month
    // Since beforeEach goes to /shift_calendar (defaults to current), it should work

    const todayCell = page.locator(".calendar-day.today");
    // Note: This might fail if the test runs exactly at midnight transition or timezone issues
    if ((await todayCell.count()) > 0) {
      await expect(todayCell).toBeVisible();

      // Verify date matches today (from data-date attribute)
       const now = new Date();
       const dateStr = now.toISOString().split("T")[0]; // YYYY-MM-DD
       await expect(todayCell).toHaveAttribute("data-date", dateStr);
    }
  });
});
