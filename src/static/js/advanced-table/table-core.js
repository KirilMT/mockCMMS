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
        this.render();
        this.loadConfiguration();
    }
}