const { test, expect } = require("@playwright/test");

/**
 * Planning App CRUD Tests (Technicians via API)
 */

const login = async (page) => {
  await page.goto("/login");
  await page.fill('input[name="username"]', "admin");
  await page.fill('input[name="password"]', "admin123");
  await page.click('button[type="submit"]');
  await page.waitForLoadState("networkidle");
};

test.describe("Planning App CRUD Tests", () => {
  test("E2E-P01: Create, Update, Delete Technician via API", async ({
    page,
  }) => {
    await login(page); // Authenticate session

    const techName = `E2E Tech ${Date.now()}`;
    const uniqueId = Date.now();
    let techId;

    // 1. CREATE
    await test.step("Create Technician", async () => {
      const response = await page.request.post("/planning/api/technicians", {
        data: {
          name: techName,
          satellite_point_id: 1, // Assuming ID 1 exists (Main)
        },
      });
      expect(response.status()).toBe(201);
      const data = await response.json();
      techId = data.technician.id;
      expect(data.technician.name).toBe(techName);
    });

    // 2. UPDATE
    await test.step("Update Technician", async () => {
      const newName = techName + " Updated";
      const response = await page.request.put(
        `/planning/api/technicians/${techId}`,
        {
          data: {
            name: newName,
          },
        },
      );
      expect(response.status()).toBe(200);
      const data = await response.json();
      expect(data.technician.name).toBe(newName);
    });

    // 3. DELETE
    await test.step("Delete Technician", async () => {
      const response = await page.request.delete(
        `/planning/api/technicians/${techId}`,
      );
      expect(response.status()).toBe(200);
    });

    // 4. VERIFY ABSENCE
    // Since GET /api/technicians returns a grouped dict, we check if our tech is gone
    await test.step("Verify Deletion", async () => {
      const response = await page.request.get("/planning/api/technicians");
      const data = await response.json();
      const allTechs = [];
      // Flatten the groups to find our tech
      Object.values(data).forEach((group) => {
        allTechs.push(...group);
      });
      const found = allTechs.find((t) => t === techName + " Updated"); // API returns names usually
      expect(found).toBeUndefined();
    });
  });
});
