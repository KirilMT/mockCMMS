
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
        expect(window.advTable.hiddenColumns.has('name')).toBe(true);
        expect(window.advTable.render).toHaveBeenCalled();
        expect(document.getElementById('columnManager').classList.contains('show')).toBe(false);
    });

    test('addFilterRow should add elements', () => {
        mod.addFilterRow();
        expect(document.querySelectorAll('.filter-row').length).toBe(1);
        mod.addFilterRow();
        expect(document.querySelectorAll('.filter-row').length).toBe(2);
        expect(document.querySelectorAll('.filter-logic').length).toBe(1);
    });

    test('applyFilters should validate and apply', () => {
        mod.addFilterRow();
        const row = document.querySelector('.filter-row');
        row.querySelector('.column-select').value = 'id';
        // Operator default is 'contains'
        row.querySelector('.filter-value').value = '123';

        mod.applyFilters();

        expect(window.advTable.filters).toEqual({
            'id': { operator: 'contains', value: '123' }
        });
        expect(window.advTable.render).toHaveBeenCalled();
        expect(document.getElementById('filterManager').classList.contains('show')).toBe(false);
    });

    test('applyFilters should show error if incomplete', () => {
        mod.addFilterRow();
        const row = document.querySelector('.filter-row');
        row.querySelector('.column-select').value = 'id';
        // Value is empty by default

        mod.applyFilters();

        expect(global.ToastNotification.error).toHaveBeenCalled();
        expect(window.advTable.render).not.toHaveBeenCalled();
    });

    test('removeFilterRow should remove element and logic', () => {
        mod.addFilterRow(); // Row 1
        mod.addFilterRow(); // Row 2 (with logic)

        const rows = document.querySelectorAll('.filter-row');
        const btn2 = rows[1].querySelector('.btn-outline-danger');

        mod.removeFilterRow(btn2);

        expect(document.querySelectorAll('.filter-row').length).toBe(1);
        expect(document.querySelectorAll('.filter-logic').length).toBe(0);
    });

    test('clearAllFilters should reset state', () => {
        window.advTable.filters = { id: { operator: 'contains', value: '1' } };
        mod.clearAllFilters();

        expect(window.advTable.filters).toEqual({});
        expect(window.advTable.render).toHaveBeenCalled();
        expect(document.querySelectorAll('.filter-row').length).toBe(1); // Adds one empty row
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
        expect(window.advTable.filters.id.value).toBe('search');
    });

    test('initializeDragAndDrop and perform drag', () => {
        mod.initializeDragAndDrop();

        const columnList = document.getElementById('columnList');
        const firstItem = columnList.children[0];
        const lastItem = columnList.children[2];

        // Trigger dragstart with dataTransfer
        const dragStartEvent = new Event('dragstart', { bubbles: true });
        Object.defineProperty(dragStartEvent, 'dataTransfer', {
            value: { effectAllowed: null }
        });

        firstItem.dispatchEvent(dragStartEvent);
        expect(firstItem.classList.contains('dragging')).toBe(true);

        // Trigger dragover on last item
        // We need to mock getBoundingClientRect for getDragAfterElement logic
        Element.prototype.getBoundingClientRect = jest.fn(() => ({
            top: 0,
            bottom: 50,
            height: 50,
            width: 100
        }));

        const dragOverEvent = new Event('dragover', { bubbles: true });
        Object.defineProperty(dragOverEvent, 'clientY', { value: 25 }); // Middle of rect

        columnList.dispatchEvent(dragOverEvent);

        // Trigger dragend
        const dragEndEvent = new Event('dragend', { bubbles: true });
        firstItem.dispatchEvent(dragEndEvent);
        expect(firstItem.classList.contains('dragging')).toBe(false);
    });

    test('loadSavedConfigurations should populate dropdown', async () => {
        jest.useRealTimers(); // Ensure promises work
        const configs = [
            { id: 1, config_name: 'View 1', is_default: false },
            { id: 2, config_name: 'View 2', is_default: true }
        ];

        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            json: () => Promise.resolve(configs)
        }));

        mod.loadSavedConfigurations();
        await flushPromises();

        const dropdown = document.getElementById('savedConfigsDropdown');
        expect(dropdown.children.length).toBe(3); // Default + 2 configs
        expect(dropdown.children[2].textContent).toContain('(Default)');
    });

    test('loadSelectedConfiguration should fetch and apply config', async () => {
         jest.useRealTimers();
         const configs = [
            { id: 100, config_name: 'My Config', is_default: false }
        ];

        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            json: () => Promise.resolve(configs)
        }));

        const dropdown = document.getElementById('savedConfigsDropdown');
        const option = document.createElement('option');
        option.value = "100";
        dropdown.appendChild(option);
        dropdown.value = "100";

        mod.loadSelectedConfiguration();
        await flushPromises();

        expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/api/table-config/'));
        expect(window.advTable.applyConfiguration).toHaveBeenCalledWith(configs[0]);
    });

    test('saveTableConfiguration should post data', async () => {
         jest.useRealTimers();
         global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ success: true })
        }));

        mod.saveTableConfiguration();
        await flushPromises();

        expect(global.fetch).toHaveBeenCalledWith(
             expect.stringContaining('/api/table-config/'),
             expect.objectContaining({ method: 'POST' })
        );
        expect(global.ToastNotification.success).toHaveBeenCalled();
    });

    test('saveTableConfiguration should handle errors', async () => {
        jest.useRealTimers();
        global.fetch = jest.fn(() => Promise.resolve({
           ok: true,
           json: () => Promise.resolve({ success: false, error: 'Failed' })
       }));

       mod.saveTableConfiguration();
       await flushPromises();

       expect(global.ToastNotification.error).toHaveBeenCalledWith(expect.stringContaining('Failed'));
   });
});
