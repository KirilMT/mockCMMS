/**
 * Core AdvancedTable class for managing dynamic table functionality.
 * Handles state, configuration, and initialization of table components.
 */
class AdvancedTable {
  /**
   * Create a new AdvancedTable instance.
   * @param {string} containerId - The ID of the container element.
   * @param {Object} options - Configuration options.
   * @param {Array} options.data - Initial data array.
   * @param {Array} options.columns - Column definitions.
   * @param {string} options.pageName - Unique identifier for the page/table (used for state persistence).
   * @param {number} options.pageSize - Number of rows per page.
   */
  constructor(containerId, options = {}) {
    this.container = document.getElementById(containerId);
    this.data = options.data || [];
    this.columns = options.columns || [];
    this.pageName = options.pageName || "default";
    this.currentSort = { column: null, direction: "asc" };
    this.filters = [];
    this.hiddenColumns = new Set();
    this.columnOrder = [...this.columns.map((col) => col.key)];
    this.currentPage = 1;
    this.pageSize = options.pageSize || 25;

    this.savedConfigs = [];
    this.selectedConfigId = null; // Current active view (matches config exactly)
    this.lastLoadedConfigId = null; // Last loaded view (for Update button)

    this.defaultState = {
      columnOrder: [...this.columnOrder],
      hiddenColumns: new Set(this.hiddenColumns),
      currentSort: { ...this.currentSort },
      filters: [],
    };

    this.searchDebounceTimer = null;
    this.globalSearchTerm = null;
    this.globalSearchDisplay = "";

    // Defer sidebar initialization until after core properties are set
    // Note: TableSidebar must be available in the scope (window.TableSidebar or imported)
    if (typeof TableSidebar !== "undefined") {
      this.sidebar = new TableSidebar(this);
    }

    this.init();
  }

  /**
   * Initialize the table.
   * Sets up global reference, restores state, renders the table, and loads configuration.
   */
  init() {
    window.advTable = this;
    this.restoreTableState();
    this.render();
    this.loadConfiguration();
  }

  /**
   * Save the current table state (sort, filters, hidden columns, etc.) to localStorage.
   */
  saveTableState() {
    const state = {
      currentSort: this.currentSort,
      filters: this.filters,
      hiddenColumns: Array.from(this.hiddenColumns),
      columnOrder: this.columnOrder,
      currentPage: this.currentPage,
      globalSearchTerm: this.globalSearchTerm,
      selectedConfigId: this.selectedConfigId,
      timestamp: Date.now(),
    };

    const key = `tableState_${this.pageName}`;
    try {
      const SafeStorage = window.StorageManager || {
        get: () => null,
        set: () => {},
        remove: () => {},
      };
      SafeStorage.set(key, JSON.stringify(state));
    } catch (e) {
      console.warn("Failed to save table state:", e);
    }
  }

  /**
   * Restore the table state from localStorage.
   */
  restoreTableState() {
    const key = `tableState_${this.pageName}`;
    try {
      const SafeStorage = window.StorageManager || {
        get: () => null,
        set: () => {},
        remove: () => {},
      };

      const savedState = SafeStorage.get(key);

      if (!savedState) return;

      const state = JSON.parse(savedState);

      // Discard state older than 24 hours to avoid stale data.
      const maxAge = 24 * 60 * 60 * 1000;
      if (state.timestamp && Date.now() - state.timestamp > maxAge) {
        SafeStorage.remove(key);
        return;
      }

      // Restore basic properties
      this.currentSort = state.currentSort || this.currentSort;
      this.filters = state.filters || this.filters;
      this.currentPage = state.currentPage || 1;
      this.globalSearchTerm = state.globalSearchTerm || "";
      this.selectedConfigId = state.selectedConfigId || null;

      if (state.hiddenColumns && Array.isArray(state.hiddenColumns)) {
        this.hiddenColumns = new Set(state.hiddenColumns);
      }

      if (state.columnOrder && Array.isArray(state.columnOrder)) {
        // Filter out stale column keys that don't exist in current columns
        const validKeys = this.columns.map((c) => c.key);
        const filteredOrder = state.columnOrder.filter((key) =>
          validKeys.includes(key),
        );
        // Add any new columns that weren't in the saved state
        validKeys.forEach((key) => {
          if (!filteredOrder.includes(key)) {
            filteredOrder.push(key);
          }
        });
        this.columnOrder = filteredOrder;
      }
    } catch (e) {
      console.warn("Failed to restore table state:", e);
    }
  }

  /**
   * Restore the state of the search UI elements.
   */
  restoreSearchUI() {
    const searchInput = document.getElementById("globalSearchInput");
    const clearSearchBtn = document.getElementById("clearSearchBtn");
    const applySearchBtn = document.getElementById("applySearchBtn");

    if (searchInput && this.globalSearchTerm) {
      searchInput.value = this.globalSearchDisplay || this.globalSearchTerm;

      if (clearSearchBtn) {
        clearSearchBtn.style.display = "inline-block";
      }
      if (applySearchBtn) {
        applySearchBtn.disabled = false;
      }
    }
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = AdvancedTable;
} else {
  window.AdvancedTable = AdvancedTable;
}
