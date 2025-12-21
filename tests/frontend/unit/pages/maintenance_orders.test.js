
const { JSDOM } = require('jsdom');

describe('Maintenance Orders Page Scripts', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <script type="application/json" id="mos-data">
                [{"id": 1, "description": "Fix it"}]
            </script>
            <div id="mosTable"></div>
        `;

        global.initAdvancedTable = jest.fn();
        window.initAdvancedTable = global.initAdvancedTable;

        // Mock localStorage
        const localStorageMock = (function() {
          let store = {};
          return {
            getItem: function(key) {
              return store[key] || null;
            },
            setItem: function(key, value) {
              store[key] = value.toString();
            },
            clear: function() {
              store = {};
            },
            removeItem: function(key) {
              delete store[key];
            }
          };
        })();
        Object.defineProperty(window, 'localStorage', { value: localStorageMock });

        jest.resetModules();
    });

    afterEach(() => {
        document.body.innerHTML = '';
        jest.restoreAllMocks();
        window.localStorage.clear();
    });

    test('should initialize table', () => {
        require('../../../../src/static/js/pages/maintenance_orders.js');
        document.dispatchEvent(new Event('DOMContentLoaded', { bubbles: true, cancelable: true }));

        expect(global.initAdvancedTable).toHaveBeenCalledWith(
            'mosTable',
            [{ id: 1, description: "Fix it" }],
            expect.any(Array),
            25
        );
    });

    test('should clear localStorage if assignees column is missing', () => {
        // Setup bad state in localStorage
        const stateKey = "tableState_mosTable";
        window.localStorage.setItem(stateKey, JSON.stringify({
            columnOrder: ['id', 'description'] // Missing assignees
        }));

        require('../../../../src/static/js/pages/maintenance_orders.js');
        document.dispatchEvent(new Event('DOMContentLoaded', { bubbles: true, cancelable: true }));

        // Should have removed the item
        expect(window.localStorage.getItem(stateKey)).toBeNull();
    });

     test('should NOT clear localStorage if assignees column is present', () => {
        const stateKey = "tableState_mosTable";
        const validState = JSON.stringify({
            columnOrder: ['id', 'assignees', 'description']
        });
        window.localStorage.setItem(stateKey, validState);

        require('../../../../src/static/js/pages/maintenance_orders.js');
        document.dispatchEvent(new Event('DOMContentLoaded', { bubbles: true, cancelable: true }));

        expect(window.localStorage.getItem(stateKey)).toBe(validState);
    });
});
