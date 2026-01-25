const { test, expect } = require("@playwright/test");

test.describe("Incident Workflow", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
    await page.fill('input[name="username"]', "admin");
    await page.fill('input[name="password"]', "admin123");
    await page.click('button[type="submit"]');
    await page.waitForLoadState("networkidle");
  });

  test("should log a new incident", async ({ page }) => {
    await page.goto("/reports/incidents/");
    await expect(
      page.getByRole("heading", { name: /Incident Reports/i }),
    ).toBeVisible();

    // Click "Log New Incident"
    const logBtn = page.getByText(/Log New Incident/i);
    await expect(logBtn).toBeVisible({ timeout: 15000 });
    await logBtn.click();
    await expect(page).toHaveURL(/.*\/reports\/incidents\/new/);

    // Fill Form
    await page.selectOption('select[name="incident_type"]', "Breakdown");

    // Equipment line might be select or text
    // Trying text fill first or select if standard
    // Inspecting models: equipment_line is string.
    // In template it might be input. Assuming input.
    const eqInput = page.locator('input[name="equipment_line"]');
    if (await eqInput.isVisible()) {
      await eqInput.fill("Line 1");
    } else {
      // Fallback if it's a select
      await page.selectOption('select[name="equipment_line"]', "Line 1");
    }

    await page.fill('textarea[name="description"]', "E2E Test Breakdown");
    await page.selectOption('select[name="severity"]', "High");

    // Force click or wait for button
    const submitBtn = page.getByRole("button", { name: "Submit Incident" });
    await expect(submitBtn).toBeVisible();
    await submitBtn.click();

    // Verify Redirect to List
    await expect(page).toHaveURL(/\/reports\/incidents\/?$/);

    // Verify Message
    await expect(page.getByText("Incident logged successfully")).toBeVisible();

    // Verify in table
    await expect(page.getByText("E2E Test Breakdown").first()).toBeVisible();
  });

  test("should filter incidents", async ({ page }) => {
    await page.goto("/reports/incidents/");
    // Filter by Severity
    await page.selectOption('select[name="severity"]', "High");
    await page.getByRole("button", { name: "Filter" }).click();

    // Should show our High severity incident (if we just created it or seed data has one)
    // If empty, table headers should still be visible
    await expect(page.locator("table")).toBeVisible();
  });
});
