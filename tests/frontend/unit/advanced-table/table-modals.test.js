const fs = require('fs');
const path = require('path');

// Mock DOM environment
document.body.innerHTML = `
    <div id="filterRows"></div>
    <div id="columnList"></div>
    <select id="savedConfigsDropdown"></select> <!-- Changed to select for options collection -->
    <input id="configName" />
    <input type="checkbox" id="setAsDefault" />
    <meta name="csrf-token" content="mock-token">
    <!-- Managers -->
    <div id="columnManager" class="show"></div>
    <div id="filterManager" class="show"></div>
`;

// Mock ToastNotification
window.ToastNotification = {
    error: jest.fn(),
    success: jest.fn()
};

// Mock AdvancedTable
window.advTable = {
    columns: [{ key: 'col1', label: 'Column 1' }, { key: 'col2', label: 'Column 2' }],
    columnOrder: ['col1', 'col2'],
    hiddenColumns: new Set(),
    filters: {},
    currentSort: {},
    pageName: 'testPage',
    render: jest.fn(),
    applyConfiguration: jest.fn()
};

// Load the script
const scriptContent = fs.readFileSync(path.resolve(__dirname, '../../../../src/static/js/advanced-table/table-modals.js'), 'utf8');
eval(scriptContent);

describe('Table Modals (Legacy)', () => {
    beforeEach(() => {
        // Reset DOM
        document.getElementById('filterRows').innerHTML = '';
        document.getElementById('columnList').innerHTML = '';
        document.getElementById('savedConfigsDropdown').innerHTML = ''; // Reset dropdown
        if(document.getElementById('columnManager')) document.getElementById('columnManager').className = 'show';
        if(document.getElementById('filterManager')) document.getElementById('filterManager').className = 'show';

        window.advTable.filters = {};
        window.advTable.render.mockClear();
        window.advTable.applyConfiguration.mockClear();
        window.ToastNotification.error.mockClear();
        window.ToastNotification.success.mockClear();
        global.fetch = jest.fn();

        // Reset console spies
        jest.spyOn(console, 'error').mockImplementation(() => {});
        jest.spyOn(console, 'log').mockImplementation(() => {});
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    test('addFilterRow adds a new row', () => {
        window.addFilterRow();
        expect(document.querySelectorAll('.filter-row').length).toBe(1);
    });

    test('addFilterRow adds logic selector for subsequent rows', () => {
        window.addFilterRow();
        window.addFilterRow();
        expect(document.querySelectorAll('.filter-logic').length).toBe(1);
        expect(document.querySelectorAll('.filter-row').length).toBe(2);
    });

    test('toggleFilterValue enables/disables input', () => {
        window.addFilterRow();
        const row = document.querySelector('.filter-row');
        const select = row.querySelector('.column-select');
        const input = row.querySelector('.filter-value');

        // Initial state
        expect(input.disabled).toBe(true);

        // Select column
        select.value = 'col1';
        window.toggleFilterValue(select);
        expect(input.disabled).toBe(false);

        // Deselect column
        select.value = '';
        window.toggleFilterValue(select);
        expect(input.disabled).toBe(true);
        expect(input.value).toBe('');
    });

    test('removeFilterRow removes row and logic', () => {
        window.addFilterRow();
        window.addFilterRow();

        const rows = document.querySelectorAll('.filter-row');
        const btn = rows[1].querySelector('button'); // Remove second row

        window.removeFilterRow(btn);

        expect(document.querySelectorAll('.filter-row').length).toBe(1);
        expect(document.querySelectorAll('.filter-logic').length).toBe(0);
    });

    test('clearAllFilters resets filters', () => {
        window.addFilterRow();
        window.advTable.filters = { col1: { operator: 'equals', value: 'test' } };

        window.clearAllFilters();

        expect(window.advTable.filters).toEqual({});
        expect(window.advTable.render).toHaveBeenCalled();
        expect(document.querySelectorAll('.filter-row').length).toBe(1); // Adds one empty row
    });

    test('applyFilters applies valid filters', () => {
        window.addFilterRow();
        const row = document.querySelector('.filter-row');
        row.querySelector('.column-select').value = 'col1';
        row.querySelector('.operator-select').value = 'equals';
        row.querySelector('.filter-value').value = 'test';

        window.applyFilters();

        expect(window.advTable.filters).toEqual({
            col1: { operator: 'equals', value: 'test' }
        });
        expect(window.advTable.render).toHaveBeenCalled();
        expect(document.getElementById('filterManager').classList.contains('show')).toBe(false);
    });

    test('applyFilters handles empty/invalid filters', () => {
        // 1. Completely empty (should just clear/close)
        window.addFilterRow(); // One empty row is essentially "no filter"
        window.applyFilters();
        expect(window.advTable.filters).toEqual({});
        expect(window.advTable.render).toHaveBeenCalled();
        expect(window.ToastNotification.error).not.toHaveBeenCalled();

        // 2. Partial filled (should error)
        window.clearAllFilters(); // Reset
        window.addFilterRow();
        const row = document.querySelector('.filter-row');
        row.querySelector('.column-select').value = 'col1';
        // Value remains empty

        window.applyFilters();
        expect(window.ToastNotification.error).toHaveBeenCalled();
    });

    test('saveTableConfiguration calls API and handles success', async () => {
        document.getElementById('configName').value = 'Test Config';
        document.getElementById('setAsDefault').checked = true;

        global.fetch.mockResolvedValue({
            json: () => Promise.resolve({ success: true })
        });

        // Mock loadSavedConfigurations since it's called on success
        const originalLoadSaved = window.loadSavedConfigurations;
        window.loadSavedConfigurations = jest.fn(() => Promise.resolve());

        await window.saveTableConfiguration();

        expect(global.fetch).toHaveBeenCalledWith('/api/table-config/testPage', expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('"config_name":"Test Config"')
        }));

        expect(window.ToastNotification.success).toHaveBeenCalled();
        expect(window.loadSavedConfigurations).toHaveBeenCalled();

        // Restore
        window.loadSavedConfigurations = originalLoadSaved;
    });

    test('saveTableConfiguration handles API error', async () => {
        document.getElementById('configName').value = 'Test Config';
        global.fetch.mockResolvedValue({
            json: () => Promise.resolve({ success: false, error: 'Failed' })
        });

        await window.saveTableConfiguration();

        expect(window.ToastNotification.error).toHaveBeenCalledWith(expect.stringContaining('Failed'));
    });

    test('saveTableConfiguration handles fetch error', async () => {
        document.getElementById('configName').value = 'Test Config';
        global.fetch.mockRejectedValue(new Error('Network error'));

        await window.saveTableConfiguration();

        expect(window.ToastNotification.error).toHaveBeenCalledWith('Error saving configuration');
    });

    test('saveTableConfiguration validation', async () => {
        document.getElementById('configName').value = '';
        await window.saveTableConfiguration();
        expect(window.ToastNotification.error).toHaveBeenCalledWith('Please enter a configuration name');
    });

    test('loadSavedConfigurations populates dropdown', async () => {
        global.fetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve([
                { id: 1, config_name: 'View 1', is_default: false },
                { id: 2, config_name: 'View 2', is_default: true }
            ])
        });

        await window.loadSavedConfigurations();

        const dropdown = document.getElementById('savedConfigsDropdown');
        expect(dropdown.children.length).toBe(3); // Default option + 2 configs
        // JSDOM select options collection works correctly
        expect(dropdown.options[1].textContent).toBe('View 1');
        expect(dropdown.options[2].textContent).toBe('View 2 (Default)');
    });

    test('loadSavedConfigurations handles error', async () => {
        global.fetch.mockRejectedValue(new Error('Failed'));

        await window.loadSavedConfigurations();

        const dropdown = document.getElementById('savedConfigsDropdown');
        expect(dropdown.options[0].textContent).toBe('No saved views');
    });

    // Coverage Tests
    test('closeColumnManager closes modal', () => {
        window.closeColumnManager();
        expect(document.getElementById('columnManager').classList.contains('show')).toBe(false);
    });

    test('closeFilterManager closes modal', () => {
        window.closeFilterManager();
        expect(document.getElementById('filterManager').classList.contains('show')).toBe(false);
    });

    test('applyColumnChanges updates columns', () => {
        // Setup column list
        const list = document.getElementById('columnList');
        const item1 = document.createElement('li');
        item1.className = 'column-item';
        item1.dataset.column = 'col1';
        item1.innerHTML = '<input type="checkbox" checked>';

        const item2 = document.createElement('li');
        item2.className = 'column-item';
        item2.dataset.column = 'col2';
        item2.innerHTML = '<input type="checkbox">'; // Unchecked

        list.appendChild(item1);
        list.appendChild(item2);

        window.applyColumnChanges();

        expect(window.advTable.columnOrder).toEqual(['col1', 'col2']);
        expect(window.advTable.hiddenColumns.has('col2')).toBe(true);
        expect(window.advTable.render).toHaveBeenCalled();
        expect(document.getElementById('columnManager').classList.contains('show')).toBe(false);
    });

    test('initializeDragAndDrop attaches listeners', () => {
        // Can't easily test drag events in JSDOM, but we can verify it doesn't crash
        window.initializeDragAndDrop();
    });

    test('getDragAfterElement calculation', () => {
        const list = document.getElementById('columnList');
        const item1 = document.createElement('li');
        item1.className = 'column-item';
        item1.getBoundingClientRect = () => ({ top: 10, height: 20 });

        const item2 = document.createElement('li');
        item2.className = 'column-item';
        item2.getBoundingClientRect = () => ({ top: 40, height: 20 });

        list.appendChild(item1);
        list.appendChild(item2);

        const after = window.getDragAfterElement(list, 20); // Between 1 and 2
        // offset: 20 - 40 - 10 = -30 for item 2.
        // offset: 20 - 10 - 10 = 0 for item 1.
        // It returns element with closest negative offset.
        expect(after).toBe(item2);
    });

    test('applyFilterRealTime uses debounce', () => {
        jest.useFakeTimers();
        window.applyFilterRealTime();

        expect(window.advTable.render).not.toHaveBeenCalled();

        jest.runAllTimers();

        expect(window.advTable.render).toHaveBeenCalled();
        jest.useRealTimers();
    });

    test('loadSelectedConfiguration applies config', async () => {
        const dropdown = document.getElementById('savedConfigsDropdown');
        const opt = document.createElement('option');
        opt.value = '1';
        dropdown.appendChild(opt);
        dropdown.value = '1';

        global.fetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve([
                { id: 1, config_name: 'View 1' }
            ])
        });

        await window.loadSelectedConfiguration();

        expect(window.advTable.applyConfiguration).toHaveBeenCalledWith(expect.objectContaining({ id: 1 }));
    });

    test('loadSelectedConfiguration handles missing config', async () => {
        const dropdown = document.getElementById('savedConfigsDropdown');
        dropdown.value = '99';

        global.fetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve([
                { id: 1, config_name: 'View 1' }
            ])
        });

        await window.loadSelectedConfiguration();

        expect(dropdown.value).toBe('');
    });
});
