// Core AdvancedTable class
class AdvancedTable {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.data = options.data || [];
        this.columns = options.columns || [];
        this.pageName = options.pageName || 'default';
        this.currentSort = { column: null, direction: 'asc' };
        this.filters = [];
        this.hiddenColumns = new Set();
        this.columnOrder = [...this.columns.map(col => col.key)];
        this.currentPage = 1;
        this.pageSize = options.pageSize || 25;

        this.savedConfigs = [];
        this.selectedConfigId = null; // Current active view (matches config exactly)
        this.lastLoadedConfigId = null; // Last loaded view (for Update button)

        this.defaultState = {
            columnOrder: [...this.columnOrder],
            hiddenColumns: new Set(this.hiddenColumns),
            currentSort: { ...this.currentSort },
            filters: []
        };

        this.searchDebounceTimer = null;
        this.globalSearchTerm = null;
        this.globalSearchDisplay = '';

        this.sidebar = new TableSidebar(this);
        this.init();
    }

    init() {
        window.advTable = this;
        this.restoreTableState(); // Bug #4 fix: Restore state before rendering
        this.render();
        this.loadConfiguration();
    }

    // Bug #4 Fix: Save table state to localStorage
    saveTableState() {
        const state = {
            currentSort: this.currentSort,
            filters: this.filters,
            hiddenColumns: Array.from(this.hiddenColumns),
            columnOrder: this.columnOrder,
            currentPage: this.currentPage,
            globalSearchTerm: this.globalSearchTerm,
            selectedConfigId: this.selectedConfigId,
            timestamp: Date.now()
        };

        try {
            const key = `tableState_${this.pageName}`;
            localStorage.setItem(key, JSON.stringify(state));
        } catch (e) {
            console.warn('Failed to save table state:', e);
        }
    }

    // Bug #4 Fix: Restore table state from localStorage
    restoreTableState() {
        try {
            const key = `tableState_${this.pageName}`;
            const savedState = localStorage.getItem(key);

            if (!savedState) return;

            const state = JSON.parse(savedState);

            // Check if state is too old (older than 24 hours)
            const maxAge = 24 * 60 * 60 * 1000;
            if (state.timestamp && (Date.now() - state.timestamp > maxAge)) {
                localStorage.removeItem(key);
                return;
            }

            // Restore state
            if (state.currentSort) {
                this.currentSort = state.currentSort;
            }
            if (state.filters && Array.isArray(state.filters)) {
                this.filters = state.filters;
            }
            if (state.hiddenColumns && Array.isArray(state.hiddenColumns)) {
                this.hiddenColumns = new Set(state.hiddenColumns);
            }
            if (state.columnOrder && Array.isArray(state.columnOrder)) {
                this.columnOrder = state.columnOrder;
            }
            if (state.currentPage) {
                this.currentPage = state.currentPage;
            }
            if (state.globalSearchTerm !== undefined) {
                this.globalSearchTerm = state.globalSearchTerm;
            }
            if (state.selectedConfigId) {
                this.selectedConfigId = state.selectedConfigId;
            }
        } catch (e) {
            console.warn('Failed to restore table state:', e);
        }
    }

    // Bug #4 Fix: Restore search UI after render
    restoreSearchUI() {
        const searchInput = document.getElementById('globalSearchInput');
        const clearSearchBtn = document.getElementById('clearSearchBtn');
        const applySearchBtn = document.getElementById('applySearchBtn');

        if (searchInput && this.globalSearchTerm) {
            searchInput.value = this.globalSearchDisplay || this.globalSearchTerm;

            if (clearSearchBtn) {
                clearSearchBtn.style.display = 'inline-block';
            }
            if (applySearchBtn) {
                applySearchBtn.disabled = false;
            }
        }
    }
}