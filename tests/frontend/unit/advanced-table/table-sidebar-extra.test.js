
const { JSDOM } = require('jsdom');

describe('Table Sidebar Logic (Extra Coverage)', () => {
    let TableSidebar;
    let sidebarInstance;

    beforeEach(() => {
        // Setup complex DOM for sidebar using standard Jest environment
        document.body.innerHTML = `
            <div class="table-sidebar">
                <div class="sidebar-header">
                     <button class="btn-collapse"></button>
                </div>
                <div class="sidebar-section" data-section="filters">
                    <div class="section-header"></div>
                    <div class="section-content">
                         <div id="filterRows">
                            <p class="empty-state-message" id="noFiltersMessage">No applied filters</p>
                         </div>
                    </div>
                </div>
                 <div class="sidebar-section" data-section="columns">
                    <div class="section-header"></div>
                    <div class="section-content">
                         <div id="columnList"></div>
                    </div>
                </div>
                 <div class="sidebar-section" data-section="configs">
                    <div class="section-header"></div>
                    <div class="section-content">
                         <div id="savedViewsList"></div>
                    </div>
                </div>
            </div>
            <button class="btn-toggle-sidebar"></button>
            <button id="addFilterBtn"></button>
            <button id="applyFiltersBtn"></button>
            <button id="clearFiltersBtn"></button>
            <button id="applyColumnsBtn"></button>
            <button id="resetColumnsBtn"></button>
            <button id="saveViewBtn"></button>
            <button id="updateViewBtn"></button>
            <meta name="csrf-token" content="token">
        `;

        // Mock global advTable
        window.advTable = {
            columns: [
                { key: 'id', label: 'ID' },
                { key: 'name', label: 'Name' },
                { key: 'status', label: 'Status' }
            ],
            filters: [],
            columnOrder: ['id', 'name', 'status'],
            hiddenColumns: new Set(),
            render: jest.fn(),
            updateTable: jest.fn(),
            saveTableState: jest.fn(),
            pageName: 'testPage',
            savedConfigs: [],
            selectedConfigId: null,
            lastLoadedConfigId: null,
            showButtonLoading: jest.fn(() => ({ restore: jest.fn() })),
            fetchWithRetry: jest.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve({ success: true, id: 123 }) })),
            loadConfiguration: jest.fn(),
            applyConfiguration: jest.fn(),
            defaultState: { columnOrder: ['id', 'name', 'status'] }
        };
        global.advTable = window.advTable;

        global.ToastNotification = {
            error: jest.fn(),
            success: jest.fn(),
            warning: jest.fn()
        };

        // Mock global showConfirmModal
        global.showConfirmModal = jest.fn((msg, cb) => cb());

        // Mock localStorage
        const localStorageMock = (function() {
          let store = {};
          return {
            getItem: function(key) {
              return store[key] || null;
            },
            setItem: function(key, value) {
              store[key] = value.toString();
            },
            clear: function() {
              store = {};
            },
            removeItem: function(key) {
              delete store[key];
            }
          };
        })();
        Object.defineProperty(window, 'localStorage', { value: localStorageMock, configurable: true });

        jest.resetModules();
        TableSidebar = require('../../../../src/static/js/advanced-table/table-sidebar.js');
        sidebarInstance = new TableSidebar(window.advTable);
    });

    afterEach(() => {
        document.body.innerHTML = '';
        jest.restoreAllMocks();
    });

    test('generateHTML should return sidebar HTML', () => {
        const html = sidebarInstance.generateHTML();
        expect(html).toContain('table-sidebar');
        expect(html).toContain('Filters');
        expect(html).toContain('Columns');
    });

    test('toggleSidebar should toggle class and save to localStorage', () => {
        sidebarInstance.toggleSidebar();
        const sidebar = document.querySelector('.table-sidebar');
        expect(sidebar.classList.contains('collapsed')).toBe(true);
        expect(localStorage.getItem('tableSidebarCollapsed')).toBe('true');

        sidebarInstance.toggleSidebar();
        expect(sidebar.classList.contains('collapsed')).toBe(false);
        expect(localStorage.getItem('tableSidebarCollapsed')).toBe('false');
    });

    test('populateColumns should render checkbox list', () => {
        sidebarInstance.populateColumns();
        const list = document.getElementById('columnList');
        expect(list.children.length).toBe(3); // 3 columns
        expect(list.innerHTML).toContain('ID');
        expect(list.innerHTML).toContain('Name');
    });

    test('applyColumnChanges should update advTable', () => {
        sidebarInstance.populateColumns();
        const list = document.getElementById('columnList');
        // Uncheck the 'name' column
        const checkbox = list.querySelector('li[data-column="name"] input');
        checkbox.checked = false;

        sidebarInstance.applyColumnChanges();

        expect(window.advTable.hiddenColumns.has('name')).toBe(true);
        expect(window.advTable.updateTable).toHaveBeenCalled();
    });

    test('resetColumns should restore defaults', () => {
        window.advTable.hiddenColumns.add('name');

        sidebarInstance.resetColumns();

        expect(window.advTable.hiddenColumns.size).toBe(0);
        expect(window.advTable.updateTable).toHaveBeenCalled();
    });

    test('addFilterRow and remove logic', () => {
        // Add one filter
        sidebarInstance.addFilterRow('name', 'contains', 'abc');
        const filterRows = document.getElementById('filterRows');
        expect(filterRows.querySelectorAll('.filter-row-sidebar').length).toBe(1);

        // Add second filter (should add connector)
        sidebarInstance.addFilterRow('status', 'equals', 'active');
        expect(filterRows.querySelectorAll('.filter-row-sidebar').length).toBe(2);

        // Check for connector
        const connector = filterRows.querySelector('.filter-logic-connector');
        expect(connector).not.toBeNull();

        // Remove first filter
        const firstRow = filterRows.querySelector('.filter-row-sidebar');
        const removeBtn = firstRow.querySelector('.remove-filter-btn');
        removeBtn.click();

        expect(filterRows.querySelectorAll('.filter-row-sidebar').length).toBe(1);
    });

     test('applyAllFilters should parse DOM and update table', () => {
        sidebarInstance.addFilterRow('name', 'contains', 'xyz');
        sidebarInstance.applyAllFilters();

        expect(window.advTable.filters.length).toBe(1);
        expect(window.advTable.filters[0].value).toBe('xyz');
        expect(window.advTable.updateTable).toHaveBeenCalled();
    });

    test('saveView should make API call', () => {
        // Mock showInputModal
        sidebarInstance.showInputModal = (msg, cb) => cb('My View');

        sidebarInstance.saveView();

        expect(window.advTable.fetchWithRetry).toHaveBeenCalledWith(
            expect.stringContaining('/api/table-config/'),
            expect.objectContaining({ method: 'POST' })
        );
    });
});
