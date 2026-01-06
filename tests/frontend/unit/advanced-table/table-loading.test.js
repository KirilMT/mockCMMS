/**
 * Tests for table-loading.js
 * Covers: showButtonLoading, showTableLoading, hideTableLoading, withLoading
 */

// Mock dependencies
global.TableSidebar = class {
  constructor(table) {
    this.table = table;
  }
  generateHTML() {
    return '<div class="sidebar"></div>';
  }
  attachEventListeners() {}
  populateColumns() {}
  populateSavedViews() {}
  restoreFilterUI() {}
};

// Load AdvancedTable and make it global
const AdvancedTable = require("../../../../src/static/js/advanced-table/table-core");
global.AdvancedTable = AdvancedTable;

// Load ALL modules
require("../../../../src/static/js/advanced-table/table-data");
require("../../../../src/static/js/advanced-table/table-render");
require("../../../../src/static/js/advanced-table/table-events");
require("../../../../src/static/js/advanced-table/table-loading");

describe("AdvancedTable Loading Methods", () => {
  let table;
  let container;
  let localStorageMock;

  beforeEach(() => {
    document.body.innerHTML = `
            <div id="test-container">
                <div class="table-responsive">
                    <table><tbody></tbody></table>
                </div>
            </div>
        `;
    container = document.getElementById("test-container");

    localStorageMock = {
      store: {},
      getItem: jest.fn((key) => localStorageMock.store[key] || null),
      setItem: jest.fn((key, value) => {
        localStorageMock.store[key] = value;
      }),
      removeItem: jest.fn(),
      clear: jest.fn(),
    };
    Object.defineProperty(window, "localStorage", {
      value: localStorageMock,
      writable: true,
    });

    AdvancedTable.prototype.loadConfiguration = jest.fn();

    table = new AdvancedTable("test-container", {
      columns: [{ key: "id", label: "ID" }],
      data: [{ id: 1 }],
      pageName: "testLoading",
    });
  });

  afterEach(() => {
    document.body.innerHTML = "";
    jest.clearAllMocks();
  });

  describe("showButtonLoading", () => {
    test("should return restore function for null button", () => {
      const result = table.showButtonLoading(null);
      expect(result.restore).toBeDefined();
      expect(typeof result.restore).toBe("function");
    });

    test("should disable button and show spinner", () => {
      const button = document.createElement("button");
      button.innerHTML = "Save";
      button.disabled = false;
      document.body.appendChild(button);

      table.showButtonLoading(button, "Saving...");

      expect(button.disabled).toBe(true);
      expect(button.innerHTML).toContain("spinner-border");
    });

    test("should restore button to original state", () => {
      const button = document.createElement("button");
      button.innerHTML = "Original";
      button.disabled = false;
      document.body.appendChild(button);

      const { restore } = table.showButtonLoading(button);
      restore();

      expect(button.disabled).toBe(false);
      expect(button.innerHTML).toBe("Original");
    });
  });

  describe("showTableLoading", () => {
    test("should add loading overlay to table-responsive", () => {
      table.showTableLoading("Loading data...");

      const overlay = container.querySelector(".table-loading-overlay");
      expect(overlay).not.toBeNull();
      expect(overlay.innerHTML).toContain("Loading data...");
    });

    test("should use default message", () => {
      table.showTableLoading();

      const overlay = container.querySelector(".table-loading-overlay");
      expect(overlay.innerHTML).toContain("Loading...");
    });
  });

  describe("hideTableLoading", () => {
    test("should remove loading overlay", () => {
      table.showTableLoading();
      table.hideTableLoading();

      const overlay = container.querySelector(".table-loading-overlay");
      expect(overlay).toBeNull();
    });

    test("should do nothing if no overlay exists", () => {
      expect(() => table.hideTableLoading()).not.toThrow();
    });
  });

  describe("withLoading", () => {
    test("should execute operation and return result", async () => {
      const operation = jest.fn().mockResolvedValue("success");

      const result = await table.withLoading(operation);

      expect(result).toBe("success");
      expect(operation).toHaveBeenCalled();
    });

    test("should restore state on error", async () => {
      const button = document.createElement("button");
      button.innerHTML = "Action";
      document.body.appendChild(button);

      const operation = jest.fn().mockRejectedValue(new Error("Failed"));

      await expect(
        table.withLoading(operation, { button, showTableOverlay: true }),
      ).rejects.toThrow("Failed");

      expect(button.disabled).toBe(false);
    });
  });
  test("TL-1.5: showTableLoading fallback to container", () => {
    // Remove table-responsive
    container.innerHTML = "<div>No table-responsive</div>";

    table.showTableLoading("Fallback");

    const overlay = container.querySelector(".table-loading-overlay");
    expect(overlay).not.toBeNull();
    expect(overlay.parentNode).toBe(container);
  });

  test("TL-1.6: withLoading uses defaults", async () => {
    const operation = jest.fn().mockResolvedValue(true);
    await table.withLoading(operation);
    expect(operation).toHaveBeenCalled();
  });

  test("TL-1.7: hideTableLoading finds overlay in container", () => {
    // Setup overlay in container (fallback)
    container.innerHTML = '<div class="table-loading-overlay"></div>';

    table.hideTableLoading();

    expect(container.querySelector(".table-loading-overlay")).toBeNull();
  });
});
