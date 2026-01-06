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

      // Spy on localStorage (mocked globally or via JSDOM)
      const setItemSpy = jest.spyOn(Storage.prototype, "setItem");

      initMaintenanceOrdersTable();

      expect(global.initAdvancedTable).toHaveBeenCalledWith(
        "mosTable",
        [{ id: 1 }],
        expect.any(Array),
        25,
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
    let mockStorage;
    const tableStateKey = "tableState_mosTable";

    beforeEach(() => {
      mockStorage = {
        data: {},
        getItem: jest.fn((key) => mockStorage.data[key] || null),
        setItem: jest.fn((key, value) => {
          mockStorage.data[key] = value;
        }),
        removeItem: jest.fn((key) => {
          delete mockStorage.data[key];
        }),
      };
    });

    test("returns no_state when no saved state exists", () => {
      expect(cleanupTableState(mockStorage, tableStateKey)).toBe("no_state");
      expect(mockStorage.getItem).toHaveBeenCalledWith(tableStateKey);
    });

    test("keeps state when columnOrder includes assignees", () => {
      const state = { columnOrder: ["id", "assignees", "status"] };
      mockStorage.data[tableStateKey] = JSON.stringify(state);

      expect(cleanupTableState(mockStorage, tableStateKey)).toBe("kept");
      expect(mockStorage.removeItem).not.toHaveBeenCalled();
    });

    test("removes state when columnOrder exists but missing assignees", () => {
      const state = { columnOrder: ["id", "status", "priority"] };
      mockStorage.data[tableStateKey] = JSON.stringify(state);

      expect(cleanupTableState(mockStorage, tableStateKey)).toBe("removed");
      expect(mockStorage.removeItem).toHaveBeenCalledWith(tableStateKey);
    });

    test("keeps state when columnOrder does not exist", () => {
      const state = { filters: {}, sortBy: "id" };
      mockStorage.data[tableStateKey] = JSON.stringify(state);

      expect(cleanupTableState(mockStorage, tableStateKey)).toBe("kept");
      expect(mockStorage.removeItem).not.toHaveBeenCalled();
    });

    test("clears corrupted state on parse error", () => {
      mockStorage.data[tableStateKey] = "invalid json {[";

      const consoleSpy = jest
        .spyOn(console, "error")
        .mockImplementation(() => {});
      expect(cleanupTableState(mockStorage, tableStateKey)).toBe(
        "error_cleared",
      );
      expect(mockStorage.removeItem).toHaveBeenCalledWith(tableStateKey);
      consoleSpy.mockRestore();
    });

    test("keeps state when columnOrder is empty array", () => {
      const state = { columnOrder: [] };
      mockStorage.data[tableStateKey] = JSON.stringify(state);

      // Empty array has no 'assignees', should be removed
      expect(cleanupTableState(mockStorage, tableStateKey)).toBe("removed");
    });
  });

  describe("getMaintenanceOrdersColumns", () => {
    test("returns correct number of columns", () => {
      const columns = getMaintenanceOrdersColumns();
      expect(columns).toHaveLength(12);
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
