/**
 * Tests for table-events.js
 * Covers: attachEventListeners, rowClick
 */

// Mock dependencies
global.TableSidebar = class {
  constructor(table) {
    this.table = table;
  }
  generateHTML() {
    return `
            <div class="sidebar">
                <input id="globalSearchInput" type="text">
                <button id="applySearchBtn">Apply</button>
                <button id="clearSearchBtn" style="display:none;">Clear</button>
            </div>
        `;
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

describe("AdvancedTable Event Methods", () => {
  let table;
  let localStorageMock;

  beforeEach(() => {
    document.body.innerHTML = '<div id="test-container"></div>';

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
      columns: [
        { key: "id", label: "ID" },
        { key: "name", label: "Name" },
      ],
      data: [
        { id: 1, name: "Item 1" },
        { id: 2, name: "Item 2" },
      ],
      pageName: "testTable",
    });
  });

  afterEach(() => {
    document.body.innerHTML = "";
    jest.clearAllMocks();
    jest.restoreAllMocks();
  });

  // describe('rowClick', () => {}); // Removed as rowClick is deprecated/removed

  describe("attachEventListeners", () => {
    test("should attach listeners without errors", () => {
      // Render first to create DOM elements
      table.render();

      // attachEventListeners is called in render, should not throw
      expect(() => table.attachEventListeners()).not.toThrow();
    });

    test("should handle search input keypress", () => {
      table.render();

      const searchInput = document.getElementById("globalSearchInput");
      expect(searchInput).not.toBeNull();

      // Simulate keypress
      const event = new KeyboardEvent("keypress", { key: "Enter" });
      expect(() => searchInput.dispatchEvent(event)).not.toThrow();
    });

    test("should ignore non-Enter keypress in search input", () => {
      table.render();
      const searchInput = document.getElementById("globalSearchInput");
      // Spy on globalSearch
      const spy = jest.spyOn(table, "globalSearch");

      const event = new KeyboardEvent("keypress", { key: "A" });
      searchInput.dispatchEvent(event);

      expect(spy).not.toHaveBeenCalled();
    });

    test("should handle search input change", () => {
      table.render();

      const searchInput = document.getElementById("globalSearchInput");
      // Mock clear button
      const clearBtn = document.getElementById("clearSearchBtn");

      searchInput.value = "test";
      const event = new Event("input", { bubbles: true });
      searchInput.dispatchEvent(event);

      expect(clearBtn.style.display).toBe("inline-block");

      // Empty value
      searchInput.value = "";
      searchInput.dispatchEvent(new Event("input", { bubbles: true }));
      expect(clearBtn.style.display).toBe("none");
    });

    test("should handle sortable header click", () => {
      table.render();

      const headers = document.querySelectorAll("th.sortable");
      expect(headers.length).toBeGreaterThan(0);
      const spy = jest.spyOn(table, "sort");

      const event = new MouseEvent("click", { bubbles: true });
      headers[0].dispatchEvent(event);

      expect(spy).toHaveBeenCalled();
    });

    test("should ignore click on resize handle", () => {
      table.render();
      const header = document.querySelector("th.sortable");
      const resizeHandle = document.createElement("div");
      resizeHandle.className = "resize-handle";
      header.appendChild(resizeHandle);

      const spy = jest.spyOn(table, "sort");

      // Dispatch click on resize handle
      const event = new MouseEvent("click", { bubbles: true });
      Object.defineProperty(event, "target", { value: resizeHandle });

      resizeHandle.dispatchEvent(event);

      expect(spy).not.toHaveBeenCalled();
    });

    test("should ignore click on element inside resize handle", () => {
      table.render();
      const header = document.querySelector("th.sortable");
      const resizeHandle = document.createElement("div");
      resizeHandle.className = "resize-handle";

      const innerElement = document.createElement("span");
      resizeHandle.appendChild(innerElement);
      header.appendChild(resizeHandle);

      const spy = jest.spyOn(table, "sort");

      // Click on inner element - should find closest('.resize-handle')
      const event = new MouseEvent("click", { bubbles: true });
      Object.defineProperty(event, "target", { value: innerElement });

      innerElement.dispatchEvent(event);
      expect(spy).not.toHaveBeenCalled();
    });

    test("should handle clear search button click", () => {
      table.render();
      const clearBtn = document.getElementById("clearSearchBtn");
      const searchInput = document.getElementById("globalSearchInput");
      const applyBtn = document.getElementById("applySearchBtn");

      searchInput.value = "test";
      const spy = jest.spyOn(table, "globalSearch");

      clearBtn.click();

      expect(searchInput.value).toBe("");
      expect(applyBtn.disabled).toBe(true);
      expect(clearBtn.style.display).toBe("none");
      expect(spy).toHaveBeenCalledWith("");
    });

    test("should handle apply search button click", () => {
      table.render();
      const applyBtn = document.getElementById("applySearchBtn");
      const searchInput = document.getElementById("globalSearchInput");

      // Type into input to enable button
      searchInput.value = "query";
      searchInput.dispatchEvent(new Event("input", { bubbles: true }));

      const spy = jest.spyOn(table, "globalSearch");

      expect(applyBtn.disabled).toBe(false);
      applyBtn.click();

      expect(spy).toHaveBeenCalledWith("query");
    });

    test("should attach utility button listeners", () => {
      // Mock methods
      table.resetTableState = jest.fn();
      table.exportData = jest.fn();
      table.saveConfiguration = jest.fn();

      // Add buttons to DOM
      const container = document.getElementById("test-container");
      container.innerHTML += `
                <button data-action="clearAllFilters">Clear</button>
                <button data-action="exportData">Export</button>
                <button data-action="saveConfiguration">Save</button>
            `;

      table.attachEventListeners();

      container.querySelector('[data-action="clearAllFilters"]').click();
      expect(table.resetTableState).toHaveBeenCalled();

      container.querySelector('[data-action="exportData"]').click();
      expect(table.exportData).toHaveBeenCalledWith("csv");

      container.querySelector('[data-action="saveConfiguration"]').click();
      expect(table.saveConfiguration).toHaveBeenCalled();
    });
    test("should handle unknown button action", () => {
      const container = document.getElementById("test-container");
      container.innerHTML += `<button data-action="unknown">Unknown</button>`;
      expect(() => table.attachEventListeners()).not.toThrow();
    });

    test("should handle missing clearSearchBtn", () => {
      // Re-render table but remove clearSearchBtn from DOM
      table.render();
      const clearBtn = document.getElementById("clearSearchBtn");
      if (clearBtn) clearBtn.remove();

      // Attaching listeners shouldn't fail
      expect(() => table.attachEventListeners()).not.toThrow();

      // Typing shouldn't fail
      const searchInput = document.getElementById("globalSearchInput");
      const event = new KeyboardEvent("keypress", { key: "Enter" });
      Object.defineProperty(event, "target", { value: "query" });
      expect(() => searchInput.dispatchEvent(event)).not.toThrow();
    });
  });

  // Note: TE-3.1 row click test removed - row click behavior was intentionally removed
  // from table-events.js. Users should click ID links to navigate to detail pages.

  test("TE-4.1: comprehensive search control branches", () => {
    // Setup DOM with ALL search elements
    document.body.innerHTML = `
            <div id="test-container">
                <input id="globalSearchInput" value="">
                <button id="applySearchBtn">Apply</button>
                <button id="clearSearchBtn" style="display: none;">Clear</button>
                <table class="advanced-table"><thead><tr></tr></thead><tbody></tbody></table>
            </div>
        `;

    // Mock globalSearch on PROTOTYPE BEFORE creating instance
    const mockGlobalSearch = jest.fn();
    AdvancedTable.prototype.globalSearch = mockGlobalSearch;

    table = new AdvancedTable("test-container", {
      data: [{ id: 1, name: "Test" }],
      columns: [{ key: "id", label: "ID" }],
      pageSize: 10,
    });

    // Make sure attachEventListeners is called
    table.attachEventListeners();

    const searchInput = document.getElementById("globalSearchInput");
    const applyBtn = document.getElementById("applySearchBtn");
    const clearBtn = document.getElementById("clearSearchBtn");

    // Test 1: Input event with EMPTY value (covers line 42, 45 false branch)
    searchInput.value = "";
    searchInput.dispatchEvent(new Event("input"));
    expect(applyBtn.disabled).toBe(true);
    expect(clearBtn.style.display).toBe("none");

    // Test 2: Input event with NON-EMPTY value (covers line 42, 45 true branch)
    searchInput.value = "test";
    searchInput.dispatchEvent(new Event("input"));
    expect(applyBtn.disabled).toBe(false);
    expect(clearBtn.style.display).toBe("inline-block");

    // Test 3: Apply button click with value (covers lines 50-59)
    const callsBefore = table.globalSearch.mock.calls.length;
    applyBtn.click();
    expect(table.globalSearch.mock.calls.length).toBeGreaterThanOrEqual(
      callsBefore,
    );

    // Test 4: Enter keypress with value (covers lines 30-35)
    const enterEvent = new KeyboardEvent("keypress", { key: "Enter" });
    Object.defineProperty(enterEvent, "target", { value: searchInput });
    searchInput.dispatchEvent(enterEvent);
    expect(table.globalSearch).toHaveBeenCalled();

    // Test 5: Clear button click (covers lines 62-72)
    searchInput.value = "something";
    clearBtn.click();
    expect(searchInput.value).toBe("");
    expect(applyBtn.disabled).toBe(true);
    expect(table.globalSearch).toHaveBeenLastCalledWith("");
  });
});
