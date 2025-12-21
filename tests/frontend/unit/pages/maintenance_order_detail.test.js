
const { JSDOM } = require('jsdom');

describe('Maintenance Order Detail Page Scripts', () => {
    let handlers = {};
    let docHandlers = {};
    let mockJQuery;
    let mockSelect2;
    let createMockElement;

    beforeEach(() => {
        document.body.innerHTML = `
            <form>
                <select id="order_type">
                    <option value="Repair">Repair</option>
                    <option value="PM">PM</option>
                </select>
                <input id="frequency" disabled>
                <label for="frequency">Frequency</label>

                <select id="assignees" multiple>
                    <option value="1">User 1</option>
                </select>
                <div class="select2-container">
                    <div class="select2-selection--multiple"></div>
                    <div class="select2-search--inline">
                        <input class="select2-search__field">
                    </div>
                </div>
                <div class="select2-container--open"></div>
            </form>
        `;

        handlers = {};
        docHandlers = {};

        mockSelect2 = jest.fn((action) => {
            if (action === 'close') {
                if (handlers['select2:close']) handlers['select2:close']();
            }
        });

        // Mock jQuery elements
        createMockElement = (selector) => ({
            length: 1,
            select2: mockSelect2,
            next: jest.fn((sel) => createMockElement('.select2-container')),
            find: jest.fn((sel) => createMockElement(sel)),
            on: jest.fn((event, selectorOrHandler, handler) => {
                let evtName = event.split('.')[0];
                let cb = typeof selectorOrHandler === 'function' ? selectorOrHandler : handler;
                handlers[event] = cb;
                handlers[evtName] = cb;
            }),
            prop: jest.fn().mockReturnThis(),
            css: jest.fn().mockReturnThis(),
            focus: jest.fn(),
            val: jest.fn().mockReturnThis(),
            blur: jest.fn(),
            is: jest.fn((other) => {
                // Logic for click target check
                if (selector === '.select2-selection--multiple' && other === '.select2-selection--multiple') return true;
                if (selector === '.select2-container--open' && other === '.select2-container--open') return true;
                // If checking against a mock object passed as 'other'
                if (typeof other === 'object' && other.selector === selector) return true;
                return false;
            }),
            has: jest.fn((target) => {
                // If target is inside me
                if (selector === '.select2-selection--multiple' && target === 'inside-selection') return { length: 1 };
                if (selector === '.select2-container--open' && target === 'inside-dropdown') return { length: 1 };
                return { length: 0 };
            }),
            0: {},
            selector: selector // Store selector for 'is' check
        });

        mockJQuery = jest.fn((selector) => {
            if (selector === '#assignees') return createMockElement('#assignees');
            if (selector === '.select2-container--open') return createMockElement('.select2-container--open');
            if (selector === document) {
                return {
                    on: jest.fn((evt, cb) => {
                        docHandlers[evt] = cb;
                    })
                };
            }
            // If selector is an object (like event.target)
            if (typeof selector === 'object') return selector; // Assume it's already a mock or DOM element

            // Default mock
            return createMockElement(selector);
        });

        mockJQuery.fn = { select2: mockSelect2 };
        global.$ = mockJQuery;
        global.window.$ = mockJQuery;

        jest.resetModules();
        jest.useFakeTimers();
    });

    afterEach(() => {
        document.body.innerHTML = '';
        jest.restoreAllMocks();
        jest.useRealTimers();
    });

    test('should toggle frequency field based on order type', () => {
        require('../../../../src/static/js/pages/maintenance_order_detail.js');
        document.dispatchEvent(new Event('DOMContentLoaded', { bubbles: true, cancelable: true }));

        const orderType = document.getElementById('order_type');
        const frequency = document.getElementById('frequency');

        orderType.value = 'PM';
        orderType.dispatchEvent(new Event('change', { bubbles: true }));
        expect(frequency.disabled).toBe(false);
    });

    test('should handle Select2 events correctly', () => {
        require('../../../../src/static/js/pages/maintenance_order_detail.js');
        document.dispatchEvent(new Event('DOMContentLoaded', { bubbles: true, cancelable: true }));

        if (handlers['select2:open']) handlers['select2:open']();
        if (handlers['select2:select']) handlers['select2:select']();

        const preventDefault = jest.fn();
        if (handlers['select2:closing']) handlers['select2:closing']({ preventDefault });
        expect(preventDefault).toHaveBeenCalled();

        jest.advanceTimersByTime(250);
        preventDefault.mockClear();
        if (handlers['select2:closing']) handlers['select2:closing']({ preventDefault });
        expect(preventDefault).not.toHaveBeenCalled();
    });

    test('document click logic', () => {
        require('../../../../src/static/js/pages/maintenance_order_detail.js');
        document.dispatchEvent(new Event('DOMContentLoaded', { bubbles: true, cancelable: true }));

        if (handlers['select2:open']) handlers['select2:open']();

        const cb = docHandlers['mousedown.select2Close'];

        // 1. Click on selectionEl (should NOT close)
        // We mock $(event.target) to return selectionEl mock
        const selectionMock = createMockElement('.select2-selection--multiple');
        cb({ target: selectionMock });
        expect(mockSelect2).not.toHaveBeenCalledWith('close');

        // 2. Click elsewhere (should close)
        const otherMock = createMockElement('other');
        otherMock.is = jest.fn().mockReturnValue(false);
        cb({ target: otherMock });
        expect(mockSelect2).toHaveBeenCalledWith('close');
    });
});
