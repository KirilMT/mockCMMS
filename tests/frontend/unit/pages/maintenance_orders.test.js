/**
 * Tests for pages/maintenance_orders.js render functions and localStorage cleanup
 */

// Mock global initAdvancedTable to prevent ReferenceError if DOMContentLoaded fires
global.initAdvancedTable = jest.fn();

const {
  renderOrderId,
  getMaintenanceOrdersColumns,
  cleanupTableState,
  initMaintenanceOrdersTable,
} = require("../../../../src/static/js/pages/maintenance-orders");

describe("Maintenance Orders Page", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Initialization", () => {
    test("initializes table with data", () => {
      document.body.innerHTML = '<div id="mos-data">[{"id":1}]</div>';

      initMaintenanceOrdersTable();

      expect(global.initAdvancedTable).toHaveBeenCalledWith(
        "mosTable",
        [{ id: 1 }],
        expect.any(Array),
        0,
      );
    });

    test("does not initialize if data element missing", () => {
      document.body.innerHTML = "";
      initMaintenanceOrdersTable();
      expect(global.initAdvancedTable).not.toHaveBeenCalled();
    });
  });

  describe("renderOrderId", () => {
    test("renders ID as link to order detail page", () => {
      const result = renderOrderId(123, { id: 123 });
      expect(result).toBe('<a href="/maintenance_orders/123">123</a>');
    });

    test("handles string ID value", () => {
      const result = renderOrderId("456", { id: 456 });
      expect(result).toContain("/maintenance_orders/456");
    });
  });

  describe("cleanupTableState", () => {
    // The function uses window.StorageManager with the hardcoded key.
    const tableStateKey = "tableState_maintenance_orders";
    let storageData;

    beforeEach(() => {
      storageData = {};
      window.StorageManager = {
        get: jest.fn((key) => storageData[key] || null),
        set: jest.fn((key, value) => {
          storageData[key] = value;
        }),
        remove: jest.fn((key) => {
          delete storageData[key];
        }),
      };
    });

    afterEach(() => {
      delete window.StorageManager;
    });

    test("returns no_state when no saved state exists", () => {
      expect(cleanupTableState()).toBe("no_state");
      expect(window.StorageManager.get).toHaveBeenCalledWith(tableStateKey);
    });

    test("keeps state when columnOrder includes assignees", () => {
      const state = { columnOrder: ["id", "assignees", "status"] };
      storageData[tableStateKey] = JSON.stringify(state);

      expect(cleanupTableState()).toBe("kept");
      expect(window.StorageManager.remove).not.toHaveBeenCalled();
    });

    test("removes state when columnOrder exists but missing assignees", () => {
      const state = { columnOrder: ["id", "status", "priority"] };
      storageData[tableStateKey] = JSON.stringify(state);

      expect(cleanupTableState()).toBe("removed");
      expect(window.StorageManager.remove).toHaveBeenCalledWith(tableStateKey);
    });

    test("keeps state when columnOrder does not exist", () => {
      const state = { filters: {}, sortBy: "id" };
      storageData[tableStateKey] = JSON.stringify(state);

      expect(cleanupTableState()).toBe("kept");
      expect(window.StorageManager.remove).not.toHaveBeenCalled();
    });

    test("returns error_cleared on parse error", () => {
      storageData[tableStateKey] = "invalid json {[";

      const consoleSpy = jest
        .spyOn(console, "warn")
        .mockImplementation(() => {});
      expect(cleanupTableState()).toBe("error_cleared");
      consoleSpy.mockRestore();
    });

    test("keeps state when columnOrder is empty array", () => {
      const state = { columnOrder: [] };
      storageData[tableStateKey] = JSON.stringify(state);

      // Empty array has no 'assignees', should be removed
      expect(cleanupTableState()).toBe("removed");
    });
  });

  describe("getMaintenanceOrdersColumns", () => {
    test("returns correct number of columns", () => {
      const columns = getMaintenanceOrdersColumns();
      expect(columns).toHaveLength(14);
    });

    test("includes assignees column (Bug #29)", () => {
      const columns = getMaintenanceOrdersColumns();
      const keys = columns.map((col) => col.key);
      expect(keys).toContain("assignees");
    });

    test("id column has render function", () => {
      const columns = getMaintenanceOrdersColumns();
      const idCol = columns.find((col) => col.key === "id");
      expect(typeof idCol.render).toBe("function");
    });
  });
});
