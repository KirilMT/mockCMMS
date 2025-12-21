
const { JSDOM } = require('jsdom');

describe('Table Modals Logic', () => {
    let mod;

    beforeEach(() => {
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
            savedConfigs: [],
            fetchWithRetry: jest.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve({success: true, id: 99}) })),
            showButtonLoading: jest.fn(() => ({ restore: jest.fn() })),
            loadConfiguration: jest.fn(),
            defaultState: { columnOrder: ['id', 'name', 'status'] }
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
        expect(window.advTable.hiddenColumns.has('name')).toBe(true);
        expect(window.advTable.render).toHaveBeenCalled();
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
        expect(window.advTable.render).toHaveBeenCalled();
    });

    test('saveTableConfiguration success path', async () => {
        jest.useRealTimers();
        document.getElementById('configName').value = 'Test';
        mod.saveTableConfiguration();
        // Wait for fetch
        await flushPromises();
        await flushPromises();
        expect(global.ToastNotification.success).toHaveBeenCalled();
        expect(global.fetch).toHaveBeenCalledTimes(2);
    });

    test('loadSelectedConfiguration logic', async () => {
        jest.useRealTimers();
        const configs = [{ id: 100, config_name: 'My Config', is_default: false }];
        global.fetch = jest.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve(configs) }));

        const dropdown = document.getElementById('savedConfigsDropdown');
        const option = document.createElement('option');
        option.value = "100";
        dropdown.appendChild(option);
        dropdown.value = "100";

        mod.loadSelectedConfiguration();
        // Wait for fetch
        await flushPromises();
        await flushPromises();

        expect(window.advTable.applyConfiguration).toHaveBeenCalledWith(configs[0]);
    });
});
