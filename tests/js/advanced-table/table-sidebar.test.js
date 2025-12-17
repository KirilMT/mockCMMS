
// Setup environment
const AdvancedTable = require('../../../src/static/js/advanced-table/table-core.js');
const TableSidebar = require('../../../src/static/js/advanced-table/table-sidebar.js');

// Ensure TableSidebar is available globally because AdvancedTable uses it
global.TableSidebar = TableSidebar;

// Mock ToastNotification
global.ToastNotification = {
    error: jest.fn(),
    warning: jest.fn(),
    success: jest.fn(),
    info: jest.fn()
};

// Mock localStorage
const localStorageMock = (() => {
    let store = {};
    return {
        getItem: jest.fn(key => store[key] || null),
        setItem: jest.fn((key, value) => { store[key] = value.toString(); }),
        clear: jest.fn(() => { store = {}; })
    };
})();
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

describe('TableSidebar', () => {
    let table;
    let sidebar;

    beforeEach(() => {
        document.body.innerHTML = `
            <div id="table-container"></div>
            <div id="sidebar-container"></div>
        `;

        // Mock init methods
        AdvancedTable.prototype.render = jest.fn();
        AdvancedTable.prototype.loadConfiguration = jest.fn();
        AdvancedTable.prototype.updateTable = jest.fn();
        AdvancedTable.prototype.saveTableState = jest.fn();

        table = new AdvancedTable('table-container', {
            columns: [
                { key: 'name', label: 'Name' },
                { key: 'age', label: 'Age' }
            ]
        });

        // table.sidebar is created in constructor, but we want to test it in isolation or integration?
        // table-core.js creates `this.sidebar = new TableSidebar(this);`
        sidebar = table.sidebar;

        // Mount sidebar HTML
        document.getElementById('sidebar-container').innerHTML = sidebar.generateHTML();
    });

    test('TS-1.1: test_addFilterRow_creates_new_filter_UI', () => {
        // Find container
        const filterRows = document.getElementById('filterRows');
        expect(filterRows.children.length).toBe(1); // Empty state message

        sidebar.addFilterRow();

        // Should have added a row. The empty message might be hidden or removed?
        // Implementation: `noFiltersMsg.style.display = 'none';` and adds row.
        // So children count should be at least 2 (msg + row) or just row if msg removed?
        // The implementation appends child.

        const rows = filterRows.querySelectorAll('.filter-row-sidebar');
        expect(rows.length).toBe(1);
    });

    test('TS-1.2: test_removeFilterRow_deletes_filter', () => {
        sidebar.addFilterRow();
        const rows = document.querySelectorAll('.filter-row-sidebar');
        expect(rows.length).toBe(1);

        const removeBtn = rows[0].querySelector('.remove-filter-btn');
        removeBtn.click();

        const rowsAfter = document.querySelectorAll('.filter-row-sidebar');
        expect(rowsAfter.length).toBe(0);
    });

    test('TS-1.3: test_applyAllFilters_returns_filter_config', () => {
        sidebar.addFilterRow();
        const row = document.querySelector('.filter-row-sidebar');

        const colSelect = row.querySelector('.filter-column');
        const valInput = row.querySelector('.filter-value');

        colSelect.value = 'name';
        valInput.value = 'Alice';

        sidebar.applyAllFilters();

        expect(table.filters).toEqual([
            { column: 'name', operator: 'contains', value: 'Alice' }
        ]);
        expect(table.updateTable).toHaveBeenCalled();
    });

    test('TS-1.4: test_clearAllFilters_resets_state', () => {
        table.filters = [{ column: 'name', operator: 'contains', value: 'Alice' }];
        sidebar.clearAllFilters();

        expect(table.filters).toEqual([]);
        expect(table.updateTable).toHaveBeenCalled();
        const rows = document.querySelectorAll('.filter-row-sidebar');
        expect(rows.length).toBe(0);
    });

    test('TS-1.5: test_populateColumns_shows_all_columns', () => {
        sidebar.populateColumns();
        const list = document.getElementById('columnList');
        expect(list.children.length).toBe(2); // Name, Age
        expect(list.children[0].textContent.trim()).toContain('Name');
    });

    test('TS-1.6: test_toggleColumn_visibility', () => {
        sidebar.populateColumns();
        const list = document.getElementById('columnList');
        const checkbox = list.children[0].querySelector('input[type="checkbox"]');

        // Uncheck
        checkbox.checked = false;

        sidebar.applyColumnChanges();

        expect(table.hiddenColumns.has('name')).toBe(true);
    });

    test('TS-1.7: test_resetColumns_restores_defaults', () => {
        table.hiddenColumns.add('name');
        sidebar.resetColumns();

        expect(table.hiddenColumns.size).toBe(0);
        expect(table.updateTable).toHaveBeenCalled();
    });

    test('TS-1.8: test_toggleSidebar_updates_state', () => {
        sidebar.sidebarCollapsed = false;

        // Clear body first because beforeEach adds a container, and previous tests might modify things
        // BUT sidebar is initialized in beforeEach attached to 'sidebar-container'.
        // TableSidebar.generateHTML uses a class 'table-sidebar'.
        // So document.querySelector('.table-sidebar') should find it!

        const sidebarEl = document.querySelector('.table-sidebar');
        expect(sidebarEl).not.toBeNull();

        // Mock collapse button icon if needed, though generateHTML creates it inside .sidebar-header
        // The collapse button has class .btn-collapse.
        const collapseBtn = sidebarEl.querySelector('.btn-collapse');
        const icon = collapseBtn.querySelector('i');

        // Before toggle
        expect(sidebarEl.classList.contains('collapsed')).toBe(false);

        sidebar.toggleSidebar();

        expect(sidebar.sidebarCollapsed).toBe(true); // toggled
        expect(sidebarEl.classList.contains('collapsed')).toBe(true);
        expect(localStorage.getItem('tableSidebarCollapsed')).toBe('true');
        expect(icon.className).toBe('fas fa-chevron-right');
    });

    test('TS-1.9: test_toggleSection_updates_state', () => {
        // Setup DOM for section
        document.getElementById('sidebar-container').innerHTML = `
            <div class="sidebar-section" data-section="filters">
                <div class="section-header expanded"></div>
                <div class="section-content"></div>
            </div>
        `;
        sidebar.expandedSections = ['filters'];

        sidebar.toggleSection('filters');

        expect(sidebar.expandedSections).not.toContain('filters');
        const header = document.querySelector('.section-header');
        expect(header.classList.contains('expanded')).toBe(false);
        expect(localStorage.getItem('tableSidebarSections')).toBe('[]');
    });

    test('TS-1.10: test_saveView_calls_api', async () => {
        // Mock prompt
        global.prompt = jest.fn(() => 'My View');
        table.showButtonLoading = jest.fn(() => ({ restore: jest.fn() }));
        table.fetchWithRetry = jest.fn().mockResolvedValue({
            ok: true,
            json: () => Promise.resolve({ success: true, id: 99 })
        });

        // Add button to DOM
        const btn = document.createElement('button');
        btn.id = 'saveViewBtn';
        document.body.appendChild(btn);

        await sidebar.saveView();

        // Wait for promises
        await new Promise(resolve => setTimeout(resolve, 0));

        expect(table.fetchWithRetry).toHaveBeenCalledWith('/api/table-config/default', expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('My View')
        }));
        expect(table.selectedConfigId).toBe(99);
    });

    test('TS-1.11: test_deleteView_calls_api', async () => {
        global.confirm = jest.fn(() => true);
        table.showButtonLoading = jest.fn(() => ({ restore: jest.fn() }));
        table.fetchWithRetry = jest.fn().mockResolvedValue({
            ok: true,
            json: () => Promise.resolve({ success: true })
        });

        // Add view item to DOM
        const viewsList = document.createElement('div');
        viewsList.id = 'savedViewsList';
        const viewItem = document.createElement('div');
        viewItem.className = 'saved-view-item';
        viewItem.dataset.configId = '55';

        const delBtn = document.createElement('button');
        delBtn.className = 'delete-view-btn';
        viewItem.appendChild(delBtn);
        viewsList.appendChild(viewItem);
        document.body.appendChild(viewsList);

        const config = { id: 55, config_name: 'Test View' };
        await sidebar.deleteView(config);

        expect(table.fetchWithRetry).toHaveBeenCalledWith('/api/table-config/55', expect.objectContaining({
            method: 'DELETE'
        }));
    });
});
