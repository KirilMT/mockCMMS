/**
 * Tests for pages/assets.js render functions
 */

// Mock global initAdvancedTable to prevent ReferenceError if DOMContentLoaded fires
global.initAdvancedTable = jest.fn();

const {
  renderAssetId,
  getAssetsColumns,
  initAssetsTable,
} = require("../../../../src/static/js/pages/assets");

describe("Assets Page - Render Functions", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Initialization", () => {
    test("initializes table with data", () => {
      document.body.innerHTML = '<div id="assets-data">[{"id":1}]</div>';
      initAssetsTable();
      expect(global.initAdvancedTable).toHaveBeenCalledWith(
        "assetsTable",
        [{ id: 1 }],
        expect.any(Array),
        25,
      );
    });

    test("does not initialize if data element missing", () => {
      document.body.innerHTML = "";
      initAssetsTable();
      expect(global.initAdvancedTable).not.toHaveBeenCalled();
    });
  });

  describe("renderAssetId", () => {
    test("renders ID as link to asset detail page", () => {
      const result = renderAssetId(42, { id: 42 });
      expect(result).toBe('<a href="/assets/42">42</a>');
    });

    test("handles string ID value", () => {
      const result = renderAssetId("100", { id: 100 });
      expect(result).toContain("/assets/100");
      expect(result).toContain(">100<");
    });

    test("handles large ID values", () => {
      const result = renderAssetId(999999, { id: 999999 });
      expect(result).toBe('<a href="/assets/999999">999999</a>');
    });
  });

  describe("getAssetsColumns", () => {
    test("returns correct number of columns", () => {
      const columns = getAssetsColumns();
      expect(columns).toHaveLength(7);
    });

    test("includes all required column keys", () => {
      const columns = getAssetsColumns();
      const keys = columns.map((col) => col.key);
      expect(keys).toEqual([
        "id",
        "asset_code",
        "name",
        "description",
        "asset_type",
        "cost_center",
        "status",
      ]);
    });

    test("id column has render function", () => {
      const columns = getAssetsColumns();
      const idCol = columns.find((col) => col.key === "id");
      expect(typeof idCol.render).toBe("function");
    });

    test("id column render function works correctly", () => {
      const columns = getAssetsColumns();
      const idCol = columns.find((col) => col.key === "id");
      const result = idCol.render(5, { id: 5 });
      expect(result).toBe('<a href="/assets/5">5</a>');
    });
  });
});
