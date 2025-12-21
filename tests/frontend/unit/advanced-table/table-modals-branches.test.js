
const { JSDOM } = require('jsdom');

describe('Table Modals Branch Coverage', () => {
    let mod;

    beforeEach(() => {
        document.body.innerHTML = `
            <div id="filterRows"></div>
            <div id="columnManager"></div>
            <div id="filterManager"></div>
            <div id="savedConfigsDropdown"></div>
            <input id="configName">
            <input type="checkbox" id="setAsDefault">
            <meta name="csrf-token" content="token">
        `;

        window.advTable = {
            filters: {},
            render: jest.fn(),
            pageName: 'testPage',
            columnOrder: [],
            hiddenColumns: new Set(),
            savedConfigs: [],
            columns: [{key: 'id', label: 'ID'}]
        };

        global.ToastNotification = {
            error: jest.fn(),
            success: jest.fn()
        };
        window.ToastNotification = global.ToastNotification;

        global.fetch = jest.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve({}) }));

        jest.resetModules();
        mod = require('../../../../src/static/js/advanced-table/table-modals.js');
    });

    const flushPromises = () => new Promise(resolve => setTimeout(resolve, 0));

    test('addFilterRow should add logic connector for 2nd row', () => {
        mod.addFilterRow();
        mod.addFilterRow();
        const rows = document.getElementById('filterRows');
        expect(rows.querySelector('.filter-logic')).not.toBeNull();
    });

    test('removeFilterRow should remove logic connector', () => {
        mod.addFilterRow();
        mod.addFilterRow();

        const rows = document.querySelectorAll('.filter-row');
        const btn = rows[1].querySelector('button'); // 2nd row

        mod.removeFilterRow(btn);

        const logic = document.querySelector('.filter-logic');
        expect(logic).toBeNull();
    });

    test('applyFilters should handle incomplete row highlighting', () => {
        mod.addFilterRow();
        const row = document.querySelector('.filter-row');
        row.querySelector('.column-select').value = 'id';
        // value empty

        jest.useFakeTimers();
        mod.applyFilters();

        expect(row.querySelector('.filter-value').classList.contains('is-invalid')).toBe(true);

        jest.advanceTimersByTime(3000);
        expect(row.querySelector('.filter-value').classList.contains('is-invalid')).toBe(false);
        jest.useRealTimers();
    });

    test('loadSavedConfigurations should handle error', async () => {
        jest.useRealTimers();
        global.fetch = jest.fn(() => Promise.reject('Error'));
        const consoleSpy = jest.spyOn(console, 'log').mockImplementation();

        mod.loadSavedConfigurations();
        await flushPromises();

        expect(document.getElementById('savedConfigsDropdown').innerHTML).toContain('No saved views');
        consoleSpy.mockRestore();
    });
});
