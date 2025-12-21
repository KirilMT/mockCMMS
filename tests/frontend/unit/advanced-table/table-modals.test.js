
const { JSDOM } = require('jsdom');

describe('Table Modals Logic', () => {
    let mod;

    beforeEach(() => {
        // Setup DOM using standard Jest environment
        document.body.innerHTML = `
            <div id="columnManager" class="show"></div>
            <div id="filterManager" class="show"></div>
            <ul id="columnList">
                <li class="column-item" data-column="id"><input type="checkbox" checked></li>
                <li class="column-item" data-column="name"><input type="checkbox"></li>
                <li class="column-item" data-column="status"><input type="checkbox"></li>
            </ul>
            <div id="filterRows"></div>
            <input id="configName" value="My Config">
            <input type="checkbox" id="setAsDefault">
            <meta name="csrf-token" content="token">
            <select id="savedConfigsDropdown">
                <option value="">Select</option>
            </select>
            <div id="saveConfigModal"></div>
        `;

        // Setup global advTable attached to window
        window.advTable = {
            columnOrder: ['id', 'name', 'status'],
            hiddenColumns: new Set(),
            render: jest.fn(),
            applyConfiguration: jest.fn(),
            columns: [
                { key: 'id', label: 'ID' },
                { key: 'name', label: 'Name' },
                { key: 'status', label: 'Status' }
            ],
            filters: {},
            currentSort: {},
            currentPage: 1,
            pageName: 'testPage',
            savedConfigs: []
        };

        // Setup ToastNotification
        global.ToastNotification = {
            error: jest.fn(),
            success: jest.fn()
        };
        window.ToastNotification = global.ToastNotification;

        // Setup Bootstrap mock
        global.bootstrap = {
            Modal: {
                getInstance: jest.fn(() => ({ hide: jest.fn() }))
            }
        };

        // Default fetch mock
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ success: true })
        }));

        jest.useFakeTimers();
        jest.resetModules();
        mod = require('../../../../src/static/js/advanced-table/table-modals.js');
    });

    afterEach(() => {
        jest.useRealTimers();
        jest.restoreAllMocks();
        document.body.innerHTML = '';
    });

    const flushPromises = () => new Promise(resolve => setTimeout(resolve, 0));

    test('applyColumnChanges should update advTable', () => {
        mod.applyColumnChanges();
        expect(window.advTable.columnOrder).toEqual(['id', 'name', 'status']);
    });

    test('applyColumnChanges should handle no table', () => {
        window.advTable = null;
        mod.applyColumnChanges(); // Should not crash
        expect(document.getElementById('columnManager').classList.contains('show')).toBe(false);
    });

    test('addFilterRow should add elements', () => {
        mod.addFilterRow();
        expect(document.querySelectorAll('.filter-row').length).toBe(1);
    });

    test('applyFilters should validate and apply', () => {
        mod.addFilterRow();
        const row = document.querySelector('.filter-row');
        row.querySelector('.column-select').value = 'id';
        row.querySelector('.filter-value').value = '123';

        mod.applyFilters();

        expect(window.advTable.filters).toEqual({
            'id': { operator: 'contains', value: '123' }
        });
    });

    test('applyFilters should handle no table', () => {
        window.advTable = null;
        mod.applyFilters();
        expect(global.ToastNotification.error).not.toHaveBeenCalled();
    });

    test('applyFilterRealTime should debounce and update', () => {
        jest.useFakeTimers();
        mod.addFilterRow();
        const row = document.querySelector('.filter-row');
        row.querySelector('.column-select').value = 'id';
        row.querySelector('.filter-value').value = 'search';

        mod.applyFilterRealTime();

        // Should not be called immediately
        expect(window.advTable.render).not.toHaveBeenCalled();

        jest.advanceTimersByTime(300);

        expect(window.advTable.render).toHaveBeenCalled();
    });

    test('applyFilterRealTime should handle no table', () => {
        jest.useFakeTimers();
        window.advTable = null;
        mod.applyFilterRealTime();
        jest.advanceTimersByTime(300);
        // Should not crash
    });

    test('saveTableConfiguration should post data', async () => {
         jest.useRealTimers();
         global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ success: true })
        }));

        mod.saveTableConfiguration();
        await flushPromises();
        expect(global.ToastNotification.success).toHaveBeenCalled();
    });

    test('saveTableConfiguration should handle missing table', () => {
        window.advTable = null;
        mod.saveTableConfiguration();
        expect(global.fetch).not.toHaveBeenCalled();
    });

    test('saveTableConfiguration should handle missing config name', () => {
        document.getElementById("configName").value = "";
        mod.saveTableConfiguration();
        expect(global.ToastNotification.error).toHaveBeenCalledWith("Please enter a configuration name");
    });

    test('loadSavedConfigurations should handle missing table', () => {
        window.advTable = null;
        mod.loadSavedConfigurations();
        expect(global.fetch).not.toHaveBeenCalled();
    });

    test('loadSavedConfigurations should handle fetch error', async () => {
        jest.useRealTimers();
        global.fetch = jest.fn(() => Promise.reject(new Error("Network")));

        const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
        mod.loadSavedConfigurations();
        await flushPromises();

        const dropdown = document.getElementById('savedConfigsDropdown');
        expect(dropdown.innerHTML).toContain('No saved views');
        consoleSpy.mockRestore();
    });

    test('loadSelectedConfiguration should handle missing config id', () => {
        document.getElementById("savedConfigsDropdown").value = "";
        const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
        mod.loadSelectedConfiguration();
        expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('No configuration selected'));
        consoleSpy.mockRestore();
    });

    test('loadSelectedConfiguration should handle missing table', () => {
        window.advTable = null;
        const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
        mod.loadSelectedConfiguration();
        expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('not ready'));
        consoleSpy.mockRestore();
    });
});
