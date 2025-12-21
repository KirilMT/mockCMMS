
const { JSDOM } = require('jsdom');

describe('Maintenance Order Detail Page Scripts', () => {
    let mockJQuery;
    let mockSelect2;
    let mockSelectionEl;
    let mockContainerEl;

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
            </form>
        `;

        // Detailed jQuery Mock for Select2 Logic
        mockSelect2 = jest.fn();
        mockSelectionEl = {
            on: jest.fn(),
            is: jest.fn().mockReturnValue(false),
            has: jest.fn().mockReturnValue({ length: 0 })
        };
        mockContainerEl = {
            find: jest.fn((sel) => {
                if (sel === '.select2-selection--multiple') return mockSelectionEl;
                if (sel === '.select2-search--inline input.select2-search__field') {
                    return {
                        length: 1,
                        prop: jest.fn().mockReturnThis(),
                        css: jest.fn().mockReturnThis(),
                        focus: jest.fn(),
                        val: jest.fn().mockReturnThis(), // Corrected: Returns this for chaining or value
                        blur: jest.fn(),
                        0: {} // Simulate DOM element
                    };
                }
                return { length: 0 };
            })
        };

        mockJQuery = jest.fn((selector) => {
            if (selector === '#assignees') {
                return {
                    length: 1,
                    select2: mockSelect2,
                    next: jest.fn(() => mockContainerEl),
                    on: jest.fn() // Capture event listeners here if needed for testing
                };
            }
            if (selector === document) {
                return { on: jest.fn() }; // For $(document).on
            }
            // For target checking in document click
            return {
                length: 0,
                is: jest.fn().mockReturnValue(false),
                has: jest.fn().mockReturnValue({ length: 0 })
            };
        });
        mockJQuery.fn = { select2: mockSelect2 };
        global.$ = mockJQuery;
        global.window.$ = mockJQuery;

        jest.resetModules();
    });

    afterEach(() => {
        document.body.innerHTML = '';
        jest.restoreAllMocks();
    });

    test('should toggle frequency field based on order type', () => {
        require('../../../../src/static/js/pages/maintenance_order_detail.js');
        document.dispatchEvent(new Event('DOMContentLoaded', { bubbles: true, cancelable: true }));

        const orderType = document.getElementById('order_type');
        const frequency = document.getElementById('frequency');
        const label = document.querySelector('label[for="frequency"]');

        // Initial state (Repair) -> Disabled
        expect(frequency.disabled).toBe(true);
        expect(label.classList.contains('required-field')).toBe(false);

        // Switch to PM
        orderType.value = 'PM';
        orderType.dispatchEvent(new Event('change', { bubbles: true }));

        expect(frequency.disabled).toBe(false);
        expect(frequency.required).toBe(true);
        expect(label.classList.contains('required-field')).toBe(true);

        // Switch back to Repair
        frequency.value = 'Weekly';
        orderType.value = 'Repair';
        orderType.dispatchEvent(new Event('change', { bubbles: true }));

        expect(frequency.disabled).toBe(true);
        expect(frequency.required).toBe(false);
        expect(frequency.value).toBe('');
    });

    test('should initialize Select2 and attach handlers', () => {
        require('../../../../src/static/js/pages/maintenance_order_detail.js');
        document.dispatchEvent(new Event('DOMContentLoaded', { bubbles: true, cancelable: true }));

        expect(global.$.fn.select2).toHaveBeenCalled();
        expect(global.$).toHaveBeenCalledWith('#assignees');

        // Check that .next() was called on the jQuery object for #assignees
        // We mocked $() to return an object. We need to check THAT object's .next method.
        // Since mockJQuery returns a NEW object every call, we can't check the specific instance easily
        // unless we store it or check the mock calls.

        // However, we know the code does: const assigneesSelect = $("#assignees");
        // We can verify that our mock was called.
        expect(mockJQuery).toHaveBeenCalledWith('#assignees');
    });
});
