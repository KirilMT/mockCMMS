
const { JSDOM } = require('jsdom');

describe('Table Modals Comprehensive Branch Coverage', () => {
    let mod;

    beforeEach(() => {
        document.body.innerHTML = `
            <div id="filterRows"></div>
            <div id="columnList"></div>
            <div id="filterManager"></div>
            <div id="columnManager"></div>
            <input id="configName">
            <input type="checkbox" id="setAsDefault">
            <div id="saveConfigModal"></div>
            <select id="savedConfigsDropdown"></select>
            <meta name="csrf-token" content="token">
        `;

        window.advTable = {
            filters: {},
            render: jest.fn(),
            columnOrder: [],
            hiddenColumns: new Set(),
            columns: [{key: 'id', label: 'ID'}],
            currentPage: 1,
            pageName: 'testPage',
            savedConfigs: [],
            applyConfiguration: jest.fn(),
            currentSort: {}
        };

        global.ToastNotification = {
            error: jest.fn(),
            success: jest.fn()
        };
        window.ToastNotification = global.ToastNotification;

        global.bootstrap = {
            Modal: {
                getInstance: jest.fn(() => ({ hide: jest.fn() }))
            }
        };

        global.fetch = jest.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve({ success: true }) }));

        jest.resetModules();
        mod = require('../../../../src/static/js/advanced-table/table-modals.js');
    });

    const flushPromises = () => new Promise(resolve => setTimeout(resolve, 0));

    test('applyFilterRealTime with valid table and filters', () => {
        jest.useFakeTimers();
        // Setup a valid filter row
        const row = document.createElement('div');
        row.className = 'filter-row';
        row.innerHTML = `
            <select class="column-select"><option value="id" selected>ID</option></select>
            <select class="operator-select"><option value="equals" selected>Eq</option></select>
            <input class="filter-value" value="test">
        `;
        document.getElementById('filterRows').appendChild(row);

        mod.applyFilterRealTime();
        jest.advanceTimersByTime(300);

        expect(window.advTable.render).toHaveBeenCalled();
        expect(window.advTable.filters['id']).toBeDefined();
        jest.useRealTimers();
    });

    test('applyFilterRealTime missing table (early return)', () => {
        jest.useFakeTimers();
        window.advTable = null;
        mod.applyFilterRealTime();
        jest.advanceTimersByTime(300);
        // Should safe exit
        jest.useRealTimers();
    });

    test('saveTableConfiguration missing table (early return)', () => {
        window.advTable = null;
        document.getElementById('configName').value = 'Test';
        mod.saveTableConfiguration();
        expect(global.fetch).not.toHaveBeenCalled();
    });

    test('saveTableConfiguration success path (branches)', async () => {
        jest.useRealTimers();
        document.getElementById('configName').value = 'Test';

        mod.saveTableConfiguration();
        await flushPromises();

        expect(global.ToastNotification.success).toHaveBeenCalled();
        expect(global.bootstrap.Modal.getInstance).toHaveBeenCalled();
        // loadSavedConfigurations is called after success, which triggers another fetch
        expect(global.fetch).toHaveBeenCalledTimes(2);
    });

    test('saveTableConfiguration error response path', async () => {
        jest.useRealTimers();
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ success: false, error: 'Fail' })
        }));

        document.getElementById('configName').value = 'Test';
        mod.saveTableConfiguration();
        await flushPromises();

        expect(global.ToastNotification.error).toHaveBeenCalledWith(expect.stringContaining('Fail'));
    });

    test('saveTableConfiguration fetch failure path', async () => {
        jest.useRealTimers();
        global.fetch = jest.fn(() => Promise.reject('Net Error'));

        document.getElementById('configName').value = 'Test';
        const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
        mod.saveTableConfiguration();
        await flushPromises();

        expect(global.ToastNotification.error).toHaveBeenCalledWith('Error saving configuration');
        consoleSpy.mockRestore();
    });

    test('loadSavedConfigurations selects current value if exists', async () => {
        jest.useRealTimers();
        const configs = [{ id: 10, config_name: 'Existing', is_default: false }];
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            json: () => Promise.resolve(configs)
        }));

        const dropdown = document.getElementById('savedConfigsDropdown');
        const opt = document.createElement('option');
        opt.value = "10";
        dropdown.appendChild(opt);
        dropdown.value = "10";

        await mod.loadSavedConfigurations();

        expect(dropdown.value).toBe("10");
    });
});
