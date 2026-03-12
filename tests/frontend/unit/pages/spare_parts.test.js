/**
 * Tests for pages/spare_parts.js render functions
 */

// Mock global initAdvancedTable to prevent ReferenceError if DOMContentLoaded fires
global.initAdvancedTable = jest.fn();

const {
  renderSparePartId,
  getSparePartsColumns,
  initSparePartsTable,
} = require("../../../../src/static/js/pages/spare-parts");

describe("Spare Parts Page - Render Functions", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Initialization", () => {
    test("initializes table with data", () => {
      document.body.innerHTML = '<div id="spare-parts-data">[{"id":1}]</div>';
      initSparePartsTable();
      expect(global.initAdvancedTable).toHaveBeenCalledWith(
        "sparePartsTable",
        [{ id: 1 }],
        expect.any(Array),
        0,
      );
    });

    test("does not initialize if data element missing", () => {
      document.body.innerHTML = "";
      initSparePartsTable();
      expect(global.initAdvancedTable).not.toHaveBeenCalled();
    });
  });

  describe("renderSparePartId", () => {
    test("renders ID as link to spare part detail page", () => {
      const result = renderSparePartId(55, { id: 55 });
      expect(result).toBe('<a href="/spare_parts/55">55</a>');
    });

    test("handles string ID value", () => {
      const result = renderSparePartId("200", { id: 200 });
      expect(result).toContain("/spare_parts/200");
    });

    test("handles large ID values", () => {
      const result = renderSparePartId(12345, { id: 12345 });
      expect(result).toBe('<a href="/spare_parts/12345">12345</a>');
    });
  });

  describe("getSparePartsColumns", () => {
    test("returns correct number of columns", () => {
      const columns = getSparePartsColumns();
      expect(columns).toHaveLength(7);
    });

    test("includes all required column keys", () => {
      const columns = getSparePartsColumns();
      const keys = columns.map((col) => col.key);
      expect(keys).toEqual([
        "id",
        "description",
        "manufacturer",
        "manufacturer_part_id",
        "stock_quantity",
        "location",
        "min_quantity",
      ]);
    });

    test("id column has render function", () => {
      const columns = getSparePartsColumns();
      const idCol = columns.find((col) => col.key === "id");
      expect(typeof idCol.render).toBe("function");
    });

    test("id column render function works correctly", () => {
      const columns = getSparePartsColumns();
      const idCol = columns.find((col) => col.key === "id");
      const result = idCol.render(10, { id: 10 });
      expect(result).toBe('<a href="/spare_parts/10">10</a>');
    });
  });
});
