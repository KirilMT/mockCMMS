
const { JSDOM } = require('jsdom');

describe('Table Sidebar Branch Coverage', () => {
    let TableSidebar;
    let sidebarInstance;

    beforeEach(() => {
        document.body.innerHTML = `
            <div class="table-sidebar">
                <div class="sidebar-section" data-section="filters">
                    <div class="section-header"></div>
                    <div class="section-content">
                        <div id="filterRows"></div>
                        <span class="badge">0</span>
                    </div>
                </div>
                <div class="sidebar-section" data-section="columns"></div>
                <div class="sidebar-section" data-section="configs"></div>
            </div>
            <button class="btn-collapse"></button>
            <button id="addFilterBtn"></button>
            <button id="applyFiltersBtn"></button>
            <button id="clearFiltersBtn"></button>
        `;

        const advTable = {
            filters: [],
            columnOrder: ['id', 'name'],
            hiddenColumns: new Set(),
            columns: [{key: 'id', label: 'ID'}, {key: 'name', label: 'Name'}, {key: 'status', label: 'Status'}],
            updateTable: jest.fn(),
            saveTableState: jest.fn(),
            fetchWithRetry: jest.fn(),
            showButtonLoading: jest.fn(() => ({ restore: jest.fn() })),
            defaultState: { columnOrder: ['id', 'name'] }
        };

        const localStorageMock = (function() {
          let store = {};
          return {
            getItem: function(key) { return store[key] || null; },
            setItem: function(key, value) { store[key] = value.toString(); },
            clear: function() { store = {}; },
            removeItem: function(key) { delete store[key]; }
          };
        })();
        Object.defineProperty(window, 'localStorage', { value: localStorageMock, configurable: true });

        jest.resetModules();
        TableSidebar = require('../../../../src/static/js/advanced-table/table-sidebar.js');
        sidebarInstance = new TableSidebar(advTable);
    });

    test('addFilterRow logic for 2nd filter (auto-apply)', () => {
        sidebarInstance.addFilterRow('id', 'equals', '1');
        const firstRow = document.querySelector('.filter-row-sidebar');
        firstRow.querySelector('.filter-column').value = 'id';
        firstRow.querySelector('.filter-value').value = '1';
        sidebarInstance.addFilterRow();
        expect(sidebarInstance.table.updateTable).toHaveBeenCalled();
    });

    test('toggleSection expanded/collapsed', () => {
        sidebarInstance.toggleSection('filters');
        expect(sidebarInstance.expandedSections).toContain('filters');
        sidebarInstance.toggleSection('filters');
        expect(sidebarInstance.expandedSections).not.toContain('filters');
    });

    test('applyAllFilters with chained logic', () => {
        sidebarInstance.addFilterRow('id', 'equals', '1');
        sidebarInstance.addFilterRow('name', 'contains', 'x', 'OR');

        sidebarInstance.applyAllFilters();

        const filters = sidebarInstance.table.filters;
        expect(filters.length).toBeGreaterThanOrEqual(1);
    });

    test('validateAllFilters dirty check', () => {
        sidebarInstance.table.filters = [{ column: 'id', operator: 'equals', value: '1' }];
        sidebarInstance.loadExistingFilters();
        sidebarInstance.validateAllFilters();
        const applyBtn = document.getElementById('applyFiltersBtn');
        expect(applyBtn.disabled).toBe(true);
        const row = document.querySelector('.filter-row-sidebar');
        row.querySelector('.filter-operator').value = 'contains';
        sidebarInstance.validateAllFilters();
        expect(applyBtn.disabled).toBe(false);
    });
});
