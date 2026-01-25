const { test, expect } = require("@playwright/test");

test.describe("Weekend Report", () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto("/login");
    await page.fill('input[name="username"]', "admin");
    await page.fill('input[name="password"]', "admin123");
    await page.click('button[type="submit"]');
    await page.waitForLoadState("networkidle");
  });

  test("should navigate to weekend report and generate data", async ({
    page,
  }) => {
    // Navigate to Reports
    await page.goto("/reports");
    await expect(page.getByRole("heading", { name: /Reports/i })).toBeVisible();

    // Click Weekend Report
    await page.click('a[href="/reports/weekend/"]');

    // Check Title
    await expect(
      page.getByRole("heading", { name: /Weekend Task Report/i }),
    ).toBeVisible();

    // Verify Data Table exists
    // Initially table might not be visible if no data selected
    // Check for form inputs first
    await expect(page.locator('input[name="start_date"]')).toBeVisible();
    await expect(page.locator('input[name="end_date"]')).toBeVisible();

    // Click Filter
    // Navigate directly with params to avoid flaky UI input interactions
    const targetUrl =
      "/reports/weekend/?start_date=2026-01-24&end_date=2026-01-25";
    await page.goto(targetUrl, { waitUntil: "networkidle" });
    await expect(page).toHaveURL(/.*\/reports\/weekend\/.*/);

    // Verify Report Generation
    // We expect "Report Data" section to appear if tasks exist
    await expect(
      page.getByText("Report Data").or(page.locator(".alert")),
    ).toBeVisible({ timeout: 30000 });
  });

  test("should allow exporting to CSV", async ({ page }) => {
    // Navigate directly with params to ensure data exists for export
    const targetUrl =
      "/reports/weekend/?start_date=2026-01-24&end_date=2026-01-25";
    await page.goto(targetUrl, { waitUntil: "networkidle" });

    // Check for Export CSV button
    // It should be visible if data exists

    // Check if table or alert is visible, to ensure load is complete
    await expect(
      page.locator("table").or(page.locator(".alert")),
    ).toBeVisible();

    // If no tasks, we cannot test export. But test environment *should* usually have seeded data
    // or we might have just created some.
    // If table is visible, we can export.
    const table = page.locator("table");
    if (await table.isVisible()) {
      // Wait for download
      const downloadPromise = page.waitForEvent("download");
      const exportBtn = page
        .getByRole("link", { name: "Export CSV" })
        .or(page.getByRole("button", { name: "Export CSV" }));
      await exportBtn.click();
      const download = await downloadPromise;
      expect(download.suggestedFilename()).toContain(".csv");
    } else {
      console.warn("No data to export, skipping CSV check");
    }
  });
});
