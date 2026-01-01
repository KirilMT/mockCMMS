const fs = require('fs');
const path = require('path');

// Mock DOM environment
document.body.innerHTML = `
    <div id="filterRows"></div>
    <div id="columnList"></div>
    <div id="savedConfigsDropdown"></div>
    <input id="configName" />
    <input type="checkbox" id="setAsDefault" />
    <meta name="csrf-token" content="mock-token">
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
        window.advTable.filters = {};
        window.advTable.render.mockClear();
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
    });

    test('applyFilters handles empty/invalid filters', () => {
        // 1. Completely empty (should just clear)
        window.addFilterRow();
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
        window.loadSavedConfigurations = jest.fn();

        await window.saveTableConfiguration();

        expect(global.fetch).toHaveBeenCalledWith('/api/table-config/testPage', expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('"config_name":"Test Config"')
        }));

        // Wait for promise chain to resolve
        await new Promise(process.nextTick);

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
        await new Promise(process.nextTick);

        expect(window.ToastNotification.error).toHaveBeenCalledWith(expect.stringContaining('Failed'));
    });

    test('saveTableConfiguration handles fetch error', async () => {
        document.getElementById('configName').value = 'Test Config';
        global.fetch.mockRejectedValue(new Error('Network error'));

        await window.saveTableConfiguration();
        await new Promise(process.nextTick);

        expect(window.ToastNotification.error).toHaveBeenCalledWith('Error saving configuration');
    });

    test('saveTableConfiguration validation', () => {
        document.getElementById('configName').value = '';
        window.saveTableConfiguration();
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
        await new Promise(process.nextTick); // Wait for microtasks

        const dropdown = document.getElementById('savedConfigsDropdown');
        expect(dropdown.children.length).toBe(3); // Default option + 2 configs
        expect(dropdown.options[1].text).toBe('View 1');
        expect(dropdown.options[2].text).toBe('View 2 (Default)');
    });

    test('loadSavedConfigurations handles error', async () => {
        global.fetch.mockRejectedValue(new Error('Failed'));

        await window.loadSavedConfigurations();
        await new Promise(process.nextTick);

        const dropdown = document.getElementById('savedConfigsDropdown');
        expect(dropdown.options[0].text).toBe('No saved views');
    });
});
