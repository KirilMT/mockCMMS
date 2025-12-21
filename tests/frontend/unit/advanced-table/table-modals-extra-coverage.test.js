
const { JSDOM } = require('jsdom');

describe('Table Modals Extra Branch Coverage', () => {
    let mod;

    beforeEach(() => {
        document.body.innerHTML = `
            <div id="filterRows"></div>
            <div id="columnList"></div>
            <div id="filterManager"></div>
            <div id="columnManager"></div>
        `;

        window.advTable = {
            filters: {},
            render: jest.fn(),
            columnOrder: [],
            hiddenColumns: new Set(),
            columns: [],
            currentPage: 1
        };

        jest.resetModules();
        mod = require('../../../../src/static/js/advanced-table/table-modals.js');
    });

    test('initializeDragAndDrop listeners and dragover logic', () => {
        mod.initializeDragAndDrop();
        const list = document.getElementById('columnList');

        const item1 = document.createElement('div');
        item1.className = 'column-item';
        list.appendChild(item1);

        const item2 = document.createElement('div');
        item2.className = 'column-item';
        list.appendChild(item2);

        const dragStartEvent = new Event('dragstart', { bubbles: true });
        Object.defineProperty(dragStartEvent, 'dataTransfer', { value: { effectAllowed: null } });
        item1.dispatchEvent(dragStartEvent);

        Element.prototype.getBoundingClientRect = jest.fn(() => ({
            top: 0,
            bottom: 50,
            height: 50,
            width: 100
        }));

        const dragOverBottom = new Event('dragover', { bubbles: true });
        Object.defineProperty(dragOverBottom, 'clientY', { value: 100 });
        list.dispatchEvent(dragOverBottom);
        expect(list.lastElementChild).toBe(item1);

        const dragOverTop = new Event('dragover', { bubbles: true });
        Object.defineProperty(dragOverTop, 'clientY', { value: -10 });
        list.dispatchEvent(dragOverTop);
        expect(list.firstElementChild).toBe(item1);
    });

    test('removeFilterRow handles logic connector removal', () => {
        const rows = document.getElementById('filterRows');
        const connector = document.createElement('div');
        connector.className = 'filter-logic';
        rows.appendChild(connector);
        const row = document.createElement('div');
        row.className = 'filter-row';
        rows.appendChild(row);
        const btn = document.createElement('button');
        row.appendChild(btn);
        mod.removeFilterRow(btn);
        expect(rows.children.length).toBe(0);
    });

    test('applyFilterRealTime populates filters', () => {
        jest.useFakeTimers();
        const row = document.createElement('div');
        row.className = 'filter-row';
        row.innerHTML = `
            <select class="column-select"><option value="id" selected>ID</option></select>
            <select class="operator-select"><option value="equals" selected>Eq</option></select>
            <input class="filter-value" value="123">
        `;
        document.getElementById('filterRows').appendChild(row);
        mod.applyFilterRealTime();
        jest.advanceTimersByTime(300);
        expect(window.advTable.render).toHaveBeenCalled();
        expect(window.advTable.filters['id']).toEqual({ operator: 'equals', value: '123' });
        jest.useRealTimers();
    });
});
