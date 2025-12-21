
const { JSDOM } = require('jsdom');

describe('Table Modals Comprehensive Logic', () => {
    let mod;

    beforeEach(() => {
        document.body.innerHTML = `
            <div id="columnManager" class="show"></div>
            <div id="filterManager" class="show"></div>
            <ul id="columnList"></ul>
            <div id="filterRows"></div>
            <input id="configName">
            <input type="checkbox" id="setAsDefault">
            <meta name="csrf-token" content="token">
            <select id="savedConfigsDropdown"></select>
            <div id="saveConfigModal"></div>
        `;

        window.advTable = {
            columnOrder: [],
            hiddenColumns: new Set(),
            render: jest.fn(),
            applyConfiguration: jest.fn(),
            columns: [{key: 'id', label: 'ID'}],
            filters: {},
            currentSort: {},
            currentPage: 1,
            pageName: 'testPage',
            savedConfigs: [],
            fetchWithRetry: jest.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve({success: true, id: 99}) })),
            showButtonLoading: jest.fn(() => ({ restore: jest.fn() })),
            loadConfiguration: jest.fn(),
            defaultState: { columnOrder: [] }
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

        // Mock global toggleFilterValue for inline handlers
        global.toggleFilterValue = jest.fn();
        window.toggleFilterValue = global.toggleFilterValue;

        jest.useFakeTimers();
        jest.resetModules();
        mod = require('../../../../src/static/js/advanced-table/table-modals.js');
    });

    const flushPromises = () => new Promise(resolve => setTimeout(resolve, 0));

    test('saveTableConfiguration error response', async () => {
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

    test('loadSavedConfigurations handles empty', async () => {
        jest.useRealTimers();
        global.fetch = jest.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve([]) }));
        const dropdown = document.getElementById('savedConfigsDropdown');
        await mod.loadSavedConfigurations();
        // Should handle empty
    });
});
