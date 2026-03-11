/**
 * Unit tests for apps/reports/src/static/js/pages/reports.js
 * Tests render functions and table configuration.
 */

// Mock global initAdvancedTable to prevent ReferenceError
global.initAdvancedTable = jest.fn();

const {
  renderReportId,
  renderReportType,
  renderShift,
  getReportsColumns,
  initReportsTable,
} = require("../../../src/static/js/pages/reports");

describe("Reports Page", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("renderReportId", () => {
    test("renders ID as a link to report detail", () => {
      const result = renderReportId(42, { id: 42 });
      expect(result).toBe('<a href="/reports/42">42</a>');
    });

    test("renders string ID correctly", () => {
      const result = renderReportId("7", { id: 7 });
      expect(result).toContain("/reports/7");
    });
  });

  describe("renderReportType", () => {
    test("renders shift_report with primary badge", () => {
      const result = renderReportType("shift_report");
      expect(result).toContain("bg-primary");
      expect(result).toContain("Shift Report");
    });

    test("renders weekend_report with success badge", () => {
      const result = renderReportType("weekend_report");
      expect(result).toContain("bg-success");
      expect(result).toContain("Weekend Report");
    });

    test("renders unknown type with secondary badge", () => {
      const result = renderReportType("unknown_type");
      expect(result).toContain("bg-secondary");
    });
  });

  describe("renderShift", () => {
    test("renders Early shift with warning badge", () => {
      const result = renderShift("Early");
      expect(result).toContain("bg-warning");
      expect(result).toContain("Early");
    });

    test("renders Night shift with dark badge", () => {
      const result = renderShift("Night");
      expect(result).toContain("bg-dark");
      expect(result).toContain("Night");
    });

    test("returns N/A for falsy value", () => {
      expect(renderShift(null)).toBe("N/A");
      expect(renderShift("")).toBe("N/A");
      expect(renderShift(undefined)).toBe("N/A");
    });

    test("renders unknown shift with secondary badge", () => {
      const result = renderShift("Afternoon");
      expect(result).toContain("bg-secondary");
    });
  });

  describe("getReportsColumns", () => {
    test("returns an array of column definitions", () => {
      const columns = getReportsColumns();
      expect(Array.isArray(columns)).toBe(true);
      expect(columns.length).toBeGreaterThan(0);
    });

    test("includes id column with render function", () => {
      const columns = getReportsColumns();
      const idCol = columns.find((c) => c.key === "id");
      expect(idCol).toBeDefined();
      expect(typeof idCol.render).toBe("function");
    });

    test("includes report_type column with render function", () => {
      const columns = getReportsColumns();
      const typeCol = columns.find((c) => c.key === "report_type");
      expect(typeCol).toBeDefined();
      expect(typeof typeCol.render).toBe("function");
    });

    test("includes shift column with render function", () => {
      const columns = getReportsColumns();
      const shiftCol = columns.find((c) => c.key === "shift");
      expect(shiftCol).toBeDefined();
      expect(typeof shiftCol.render).toBe("function");
    });

    test("includes title, generated_by_name, generated_on columns", () => {
      const columns = getReportsColumns();
      const keys = columns.map((c) => c.key);
      expect(keys).toContain("title");
      expect(keys).toContain("generated_by_name");
      expect(keys).toContain("generated_on");
    });
  });

  describe("initReportsTable", () => {
    test("initializes table when data element exists", () => {
      document.body.innerHTML =
        '<script id="reports-data" type="application/json">[{"id":1,"title":"Test"}]</script>';
      initReportsTable();
      expect(global.initAdvancedTable).toHaveBeenCalledWith(
        "reportsTable",
        [{ id: 1, title: "Test" }],
        expect.any(Array),
        25,
      );
    });

    test("does not initialize when data element missing", () => {
      document.body.innerHTML = "";
      initReportsTable();
      expect(global.initAdvancedTable).not.toHaveBeenCalled();
    });
  });
});
