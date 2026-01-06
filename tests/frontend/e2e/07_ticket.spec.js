const { test, expect } = require("@playwright/test");

/**
 * Ticket Page Functional Tests
 *
 * Coverage:
 * - Page loading
 * - Ticket ID display
 */

test.describe("Ticket Page Tests", () => {
  test("TKT-01: Page loads with correct Ticket ID", async ({ page }) => {
    const ticketId = "TICKET-12345";
    await page.goto(`/tickets/${ticketId}`);

    // Verify title
    await expect(page).toHaveTitle(new RegExp(`Mock CMMS Ticket: ${ticketId}`));
    await expect(page.locator("h1")).toHaveText("Mock CMMS Ticket Details");

    // Verify Ticket ID is displayed
    await expect(page.locator(".ticket-info")).toContainText(ticketId);

    // Verify back link
    await expect(page.locator('a[href="/"]')).toBeVisible();
  });
});
