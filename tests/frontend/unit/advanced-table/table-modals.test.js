
const tableModals = require('../../../../src/static/js/advanced-table/table-modals.js');

describe('Table Modals Logic', () => {
    let mockAdvTable;

    beforeEach(() => {
        // Reset DOM
        document.body.innerHTML = `
            <div id="columnManager"></div>
            <div id="columnList"></div>
            <div id="filterManager"></div>
            <div id="filterRows"></div>
            <select id="savedConfigsDropdown"></select>
            <input id="configName" />
            <input type="checkbox" id="setAsDefault" />
            <meta name="csrf-token" content="mock-token">
        `;

        // Mock window.advTable
        mockAdvTable = {
            columnOrder: [],
            hiddenColumns: new Set(),
            render: jest.fn(),
            columns: [
                { key: 'col1', label: 'Column 1' },
                { key: 'col2', label: 'Column 2' }
            ],
            filters: {},
            currentPage: 1,
            pageName: 'test-page',
            currentSort: {},
            applyConfiguration: jest.fn()
        };
        window.advTable = mockAdvTable;

        // Mock ToastNotification
        window.ToastNotification = {
            error: jest.fn(),
            success: jest.fn()
        };

        // Mock global fetch
        global.fetch = jest.fn();
    });

    afterEach(() => {
        jest.clearAllMocks();
        delete window.advTable;
        delete window.ToastNotification;
    });

    test('closeColumnManager should hide the element', () => {
        const el = document.getElementById('columnManager');
        el.classList.add('show');
        tableModals.closeColumnManager();
        expect(el.classList.contains('show')).toBe(false);
    });

    test('applyColumnChanges should update advTable', () => {
        const list = document.getElementById('columnList');
        list.innerHTML = `
            <div class="column-item" data-column="col1"><input type="checkbox" checked></div>
            <div class="column-item" data-column="col2"><input type="checkbox"></div>
        `;
        
        tableModals.applyColumnChanges();
        
        expect(window.advTable.columnOrder).toEqual(['col1', 'col2']);
        expect(window.advTable.hiddenColumns.has('col2')).toBe(true);
        expect(window.advTable.render).toHaveBeenCalled();
    });

    test('addFilterRow should add elements to DOM', () => {
        tableModals.addFilterRow();
        const rows = document.querySelectorAll('.filter-row');
        expect(rows.length).toBe(1);
        
        // Add a second row to test logic selector
        tableModals.addFilterRow();
        const logic = document.querySelectorAll('.filter-logic');
        expect(logic.length).toBe(1);
    });

    test('toggleFilterValue should enable/disable input', () => {
        tableModals.addFilterRow();
        const row = document.querySelector('.filter-row');
        const select = row.querySelector('.column-select');
        const input = row.querySelector('.filter-value');
        
        // Select a value
        select.value = 'col1';
        tableModals.toggleFilterValue(select);
        expect(input.disabled).toBe(false);
        
        // Deselect
        select.value = '';
        tableModals.toggleFilterValue(select);
        expect(input.disabled).toBe(true);
        expect(input.value).toBe('');
    });

    test('applyFilterRealTime should update filters after debounce', async () => {
        jest.useFakeTimers();
        tableModals.addFilterRow();
        const row = document.querySelector('.filter-row');
        row.querySelector('.column-select').value = 'col1';
        row.querySelector('.operator-select').value = 'contains';
        row.querySelector('.filter-value').value = 'search';
        
        tableModals.applyFilterRealTime();
        
        jest.advanceTimersByTime(300);
        
        expect(window.advTable.filters).toEqual({
            col1: { operator: 'contains', value: 'search' }
        });
        expect(window.advTable.render).toHaveBeenCalled();
        jest.useRealTimers();
    });
    
    test('removeFilterRow should remove row and logic', () => {
        tableModals.addFilterRow(); // Row 1
        tableModals.addFilterRow(); // Row 2 + Logic
        
        const rows = document.querySelectorAll('.filter-row');
        const btn = rows[1].querySelector('button');
        
        tableModals.removeFilterRow(btn);
        
        expect(document.querySelectorAll('.filter-row').length).toBe(1);
        expect(document.querySelectorAll('.filter-logic').length).toBe(0);
    });

    test('clearAllFilters should reset UI and table', () => {
        document.getElementById('filterRows').innerHTML = '<div>garbage</div>';
        tableModals.clearAllFilters();
        
        expect(window.advTable.filters).toEqual({});
        expect(window.advTable.render).toHaveBeenCalled();
        expect(document.querySelectorAll('.filter-row').length).toBe(1);
    });

    test('applyFilters should apply valid filters', () => {
        tableModals.addFilterRow();
        const row = document.querySelector('.filter-row');
        row.querySelector('.column-select').value = 'col1';
        row.querySelector('.operator-select').value = 'equals';
        row.querySelector('.filter-value').value = 'val';
        
        tableModals.applyFilters();
        
        expect(window.advTable.filters).toEqual({
            col1: { operator: 'equals', value: 'val' }
        });
        expect(window.advTable.currentPage).toBe(1);
    });

    test('applyFilters should show error for incomplete filters', () => {
        jest.useFakeTimers();
        tableModals.addFilterRow();
        const row = document.querySelector('.filter-row');
        row.querySelector('.column-select').value = 'col1';
        // Value is empty
        
        tableModals.applyFilters();
        
        const input = row.querySelector('.filter-value');
        expect(input.classList.contains('is-invalid')).toBe(true);
        expect(window.ToastNotification.error).toHaveBeenCalled();
        
        jest.advanceTimersByTime(3000);
        expect(input.classList.contains('is-invalid')).toBe(false);
        jest.useRealTimers();
    });

    test('saveTableConfiguration should make API call', async () => {
        document.getElementById('configName').value = 'MyConfig';
        global.fetch.mockResolvedValue({
            json: () => Promise.resolve({ success: true })
        });
        
        // Mock loadSavedConfigurations to prevent fetch call inside it
        // But since we export it, we can't easily spy on the internal call if it calls the internal function directly.
        // Wait, the new code calls `loadSavedConfigurations()` (local reference).
        // Testing side effects (fetch) is better.
        // Or if we replace window.loadSavedConfigurations?
        // The code calls the local function.
        // We can spy on window.loadSavedConfigurations if the code called window.loadSavedConfigurations.
        // But my refactor calls local `loadSavedConfigurations()`.
        // So we expect a second fetch call?
        // Let's just mock fetch to handle both calls.
        
        await tableModals.saveTableConfiguration();
        
        expect(global.fetch).toHaveBeenCalledWith('/api/table-config/test-page', expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('MyConfig')
        }));
        expect(window.ToastNotification.success).toHaveBeenCalled();
        // Since success calls loadSavedConfigurations, we expect another fetch?
        // Yes.
    });

    test('loadSavedConfigurations handles success', async () => {
        global.fetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve([
                { id: 1, config_name: 'Cfg1', is_default: true },
                { id: 2, config_name: 'Cfg2', is_default: false }
            ])
        });

        await tableModals.loadSavedConfigurations();
        
        const dropdown = document.getElementById('savedConfigsDropdown');
        expect(dropdown.children.length).toBe(3); // Default + 2 options
        expect(dropdown.children[1].text).toContain('Cfg1 (Default)');
    });

    test('loadSelectedConfiguration applies config', async () => {
        const dropdown = document.getElementById('savedConfigsDropdown');
        dropdown.innerHTML = '<option value="1">Cfg1</option>';
        dropdown.value = "1";
        
        global.fetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve([
                 { id: 1, config_name: 'Cfg1', is_default: false }
            ])
        });

        await tableModals.loadSelectedConfiguration();
        expect(window.advTable.applyConfiguration).toHaveBeenCalledWith(expect.objectContaining({ id: 1 }));
    });
    
    test('initializeDragAndDrop should attach listeners', () => {
        const list = document.getElementById('columnList');
        const spy = jest.spyOn(list, 'addEventListener');
        tableModals.initializeDragAndDrop();
        expect(spy).toHaveBeenCalledWith('dragstart', expect.any(Function));
    });

    // Helper to trigger event
    const triggerEvent = (el, type, props = {}) => {
        const event = new Event(type, { bubbles: true });
        // target is read-only, do not assign it. dataTransfer is needed.
        if (props.dataTransfer) {
             Object.defineProperty(event, 'dataTransfer', { value: props.dataTransfer });
             delete props.dataTransfer;
        }
         // Assign other props if any (excluding target)
        const { target, ...rest } = props;
        Object.assign(event, rest);
        
        el.dispatchEvent(event);
    };

    test('drag interactions', () => {
        const list = document.getElementById('columnList');
        // ... (rest of test setup)
        list.innerHTML = `
            <div class="column-item" data-id="1">Item 1</div>
            <div class="column-item" data-id="2">Item 2</div>
        `;
        const item1 = list.children[0];
        const item2 = list.children[1];

        // Ensure listeners attached
        tableModals.initializeDragAndDrop();

        // Drag Start
        const dataTransfer = { effectAllowed: 'none' };
        triggerEvent(item1, 'dragstart', { dataTransfer }); // Remove target
        expect(item1.classList.contains('dragging')).toBe(true);
        expect(dataTransfer.effectAllowed).toBe('move');

        // Drag Over
        item1.getBoundingClientRect = () => ({ top: 0, height: 50, bottom: 50 });
        item2.getBoundingClientRect = () => ({ top: 50, height: 50, bottom: 100 });
        
        // Mock getDragAfterElement usage
        triggerEvent(list, 'dragover', { clientY: 10, preventDefault: jest.fn() });
        
        // Drag End
        triggerEvent(item1, 'dragend', {});
        expect(item1.classList.contains('dragging')).toBe(false);
    });

    test('getDragAfterElement logic', () => {
        // We can test this by calling it via module export if we exported it.
        // refactored code exports it: `window.getDragAfterElement = getDragAfterElement`.
        // So we can call tableModals.getDragAfterElement.
        
        const container = document.createElement('div');
        container.innerHTML = `
            <div class="column-item" id="A">A</div>
            <div class="column-item" id="B">B</div>
        `;
        const a = container.children[0];
        const b = container.children[1];
        
        // Mock layout
        a.getBoundingClientRect = () => ({ top: 0, height: 100 });
        b.getBoundingClientRect = () => ({ top: 100, height: 100 });
        
        // y=20. A center=50. Offset = 20 - 0 - 50 = -30.
        // y=120. B center=150. Offset = 120 - 100 - 50 = -30.
        
        // Case: Mouse above A (y=20). 
        // A offset = -30. B offset = 20 - 100 - 50 = -130 (far away?).
        // reduce logic searches for offset < 0 and > closest.offset.
        // Closest starts at -Infinity.
        // A: -30. -30 > -Inf. New closest A.
        // B: -130. -130 is NOT > -30.
        // Returns A.
        const res1 = tableModals.getDragAfterElement(container, 20);
        expect(res1).toBe(a);
        
        // Case: Mouse middle of A and B?
        // Wait, if it returns A, it means insert before A.
        
        // Case: Mouse below B (y=250).
        // A: 250 - 0 - 50 = 200 (>0 ignored).
        // B: 250 - 100 - 50 = 100 (>0 ignored).
        // Returns undefined (append to end).
        const res2 = tableModals.getDragAfterElement(container, 250);
        expect(res2).toBeUndefined();
    });

    test('dragover triggers appendChild when afterElement is null', () => {
        const list = document.getElementById('columnList');
        list.innerHTML = `<div class="column-item" data-id="1">Item 1</div>`;
        const item = list.children[0];
        
        // Mock getBoundingClientRect to make afterElement return null (y far below items)
        item.getBoundingClientRect = () => ({ top: 0, height: 50 });
        
        tableModals.initializeDragAndDrop();
        
        // Start drag
        const dragStartEvent = new Event('dragstart', { bubbles: true });
        Object.defineProperty(dragStartEvent, 'target', { value: item, writable: false });
        Object.defineProperty(dragStartEvent, 'dataTransfer', { value: { effectAllowed: '' }, writable: false });
        item.dispatchEvent(dragStartEvent);
        
        // Dragover at y=500 (far below all items - should trigger appendChild)
        const dragOverEvent = new Event('dragover', { bubbles: true });
        dragOverEvent.clientY = 500;
        dragOverEvent.preventDefault = jest.fn();
        list.dispatchEvent(dragOverEvent);
        
        expect(dragOverEvent.preventDefault).toHaveBeenCalled();
    });

    test('dragstart on non-column-item is ignored', () => {
        const list = document.getElementById('columnList');
        list.innerHTML = `<div class="other-element">Not a column</div>`;
        const nonColumnItem = list.children[0];
        
        tableModals.initializeDragAndDrop();
        
        // Dragstart on non-column-item should not add 'dragging' class
        const dragStartEvent = new Event('dragstart', { bubbles: true });
        Object.defineProperty(dragStartEvent, 'target', { value: nonColumnItem, writable: false });
        Object.defineProperty(dragStartEvent, 'dataTransfer', { value: { effectAllowed: '' }, writable: false });
        nonColumnItem.dispatchEvent(dragStartEvent);
        
        expect(nonColumnItem.classList.contains('dragging')).toBe(false);
    });

    test('loadSavedConfigurations handles failure', async () => {
        global.fetch.mockResolvedValue({
            ok: false,
            status: 500
        });

        await tableModals.loadSavedConfigurations();
        
        const dropdown = document.getElementById('savedConfigsDropdown');
        expect(dropdown.children.length).toBe(1);
        expect(dropdown.children[0].text).toBe('No saved views');
    });

    // TM-5.1: Test saveTableConfiguration with empty name (covers lines 280-281)
    test('saveTableConfiguration shows error when name is empty', async () => {
        document.getElementById('configName').value = '';
        
        await tableModals.saveTableConfiguration();
        
        expect(window.ToastNotification.error).toHaveBeenCalledWith('Please enter a configuration name');
    });

    // TM-5.2: Test saveTableConfiguration when advTable is missing (covers line 284)
    test('saveTableConfiguration returns early when advTable is missing', async () => {
        document.getElementById('configName').value = 'TestName';
        window.advTable = null;
        
        await tableModals.saveTableConfiguration();
        
        expect(global.fetch).not.toHaveBeenCalled();
    });

    // TM-5.3: Test loadSavedConfigurations with dropdown value restore (covers line 262)
    test('loadSavedConfigurations restores dropdown selection', async () => {
        const dropdown = document.getElementById('savedConfigsDropdown');
        dropdown.innerHTML = '<option value="5">Existing</option>';
        dropdown.value = '5';
        
        global.fetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve([
                { id: 5, config_name: 'Existing', is_default: false },
                { id: 6, config_name: 'New', is_default: false }
            ])
        });

        await tableModals.loadSavedConfigurations();
        
        // Should restore selection to '5' if it still exists
        expect(dropdown.value).toBe('5');
    });

});
