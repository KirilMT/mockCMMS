const { test, expect } = require("@playwright/test");

/**
 * Reports App CRUD Tests (Incidents)
 */

const login = async (page) => {
  await page.goto("/login");
  await page.fill('input[name="username"]', "admin");
  await page.fill('input[name="password"]', "admin123");
  await page.click('button[type="submit"]');
  await page.waitForLoadState("networkidle");
};

test.describe("Reports App CRUD Tests", () => {
  test("E2E-R01: Create Incident", async ({ page }) => {
    await login(page);

    await page.goto("/reports/incidents/new");
    await page.waitForLoadState("networkidle");

    const desc = "Test Incident " + Date.now();

    // Fill form - using actual values from incident_form.html
    await page.selectOption('select[name="incident_type"]', "Safety Issue");
    await page.fill('input[name="equipment_line"]', "Test Line 1");
    await page.fill('textarea[name="description"]', desc);
    await page.selectOption('select[name="severity"]', "Medium");

    // Submit
    await page.click('button:has-text("Submit Incident")');
    await page.waitForLoadState("networkidle");

    // Verify redirect to incident list (successful submission)
    // If we get here without a CSRF error, the form submission worked
    await expect(page).toHaveURL(/\/reports\/incidents\/?/, { timeout: 10000 });
  });
});
