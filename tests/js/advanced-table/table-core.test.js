
// Mock dependencies
global.TableSidebar = class {
    constructor(table) {
        this.table = table;
    }
};

// Load the class under test
const AdvancedTable = require('../../../src/static/js/advanced-table/table-core.js');

describe('AdvancedTable', () => {
    let tableContainer;
    let localStorageMock;

    beforeEach(() => {
        // Setup DOM
        document.body.innerHTML = '<div id="table-container"></div>';
        tableContainer = document.getElementById('table-container');

        // Mock methods called in init()
        AdvancedTable.prototype.render = jest.fn();
        AdvancedTable.prototype.loadConfiguration = jest.fn();

        // Mock localStorage
        localStorageMock = (() => {
            let store = {};
            return {
                getItem: jest.fn(key => store[key] || null),
                setItem: jest.fn((key, value) => {
                    store[key] = value.toString();
                }),
                removeItem: jest.fn(key => {
                    delete store[key];
                }),
                clear: jest.fn(() => {
                    store = {};
                })
            };
        })();

        Object.defineProperty(window, 'localStorage', {
            value: localStorageMock
        });

        // Reset mocks
        jest.clearAllMocks();
    });

    test('TC-1.1: constructor initializes default state', () => {
        const table = new AdvancedTable('table-container');

        expect(table.container).toBe(tableContainer);
        expect(table.currentPage).toBe(1);
        expect(table.pageSize).toBe(25);
        expect(table.sortColumn).toBeUndefined(); // It is not set in constructor default options, but in currentSort
        expect(table.currentSort).toEqual({ column: null, direction: 'asc' });
        expect(table.pageName).toBe('default');
        expect(table.sidebar).toBeDefined();
        expect(table.render).toHaveBeenCalled();
        expect(table.loadConfiguration).toHaveBeenCalled();
    });

    test('TC-1.2: constructor accepts custom options', () => {
        const options = {
            pageSize: 50,
            pageName: 'customPage',
            data: [1, 2, 3],
            columns: [{ key: 'id' }]
        };
        const table = new AdvancedTable('table-container', options);

        expect(table.pageSize).toBe(50);
        expect(table.pageName).toBe('customPage');
        expect(table.data).toEqual([1, 2, 3]);
        expect(table.columns).toEqual([{ key: 'id' }]);
    });

    test('TC-1.3: saveTableState persists to localStorage', () => {
        const table = new AdvancedTable('table-container');
        table.currentPage = 3;
        table.currentSort = { column: 'name', direction: 'desc' };

        table.saveTableState();

        expect(localStorage.setItem).toHaveBeenCalled();
        const callArgs = localStorage.setItem.mock.calls[0];
        expect(callArgs[0]).toBe('tableState_default');

        const savedState = JSON.parse(callArgs[1]);
        expect(savedState.currentPage).toBe(3);
        expect(savedState.currentSort).toEqual({ column: 'name', direction: 'desc' });
        expect(savedState.timestamp).toBeDefined();
    });

    test('TC-1.4: restoreTableState loads from localStorage', () => {
        const savedState = {
            currentPage: 5,
            currentSort: { column: 'age', direction: 'asc' },
            timestamp: Date.now()
        };

        localStorage.getItem.mockReturnValue(JSON.stringify(savedState));

        const table = new AdvancedTable('table-container');

        // restoreTableState is called in init()
        expect(table.currentPage).toBe(5);
        expect(table.currentSort).toEqual({ column: 'age', direction: 'asc' });
    });

    test('TC-1.5: saveTableState handles localStorage quota error', () => {
        const table = new AdvancedTable('table-container');
        const consoleSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});

        localStorage.setItem.mockImplementation(() => {
            throw new Error('QuotaExceededError');
        });

        table.saveTableState();

        expect(consoleSpy).toHaveBeenCalledWith('Failed to save table state:', expect.any(Error));
        consoleSpy.mockRestore();
    });

    test('TC-1.6: restoreTableState handles corrupted data', () => {
        localStorage.getItem.mockReturnValue('invalid json');
        const consoleSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});

        const table = new AdvancedTable('table-container');

        // Should rely on defaults if restore fails
        expect(table.currentPage).toBe(1);
        expect(consoleSpy).toHaveBeenCalledWith('Failed to restore table state:', expect.any(Error));
        consoleSpy.mockRestore();
    });
});
