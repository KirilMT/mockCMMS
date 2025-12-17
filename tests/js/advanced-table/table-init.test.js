/**
 * Tests for table-init.js
 * Tests AdvancedTable instantiation patterns used by initAdvancedTable
 */

// Mock dependencies
global.TableSidebar = class {
    constructor(table) { this.table = table; }
    generateHTML() { return '<div class="sidebar"></div>'; }
    attachEventListeners() { }
    populateColumns() { }
    populateSavedViews() { }
    restoreFilterUI() { }
};

// Load AdvancedTable and make it global
const AdvancedTable = require('../../../src/static/js/advanced-table/table-core');
global.AdvancedTable = AdvancedTable;

// Load ALL modules
require('../../../src/static/js/advanced-table/table-data');
require('../../../src/static/js/advanced-table/table-render');
require('../../../src/static/js/advanced-table/table-events');

describe('AdvancedTable initialization patterns', () => {
    let localStorageMock;

    beforeEach(() => {
        document.body.innerHTML = '<div id="test-container"></div>';

        localStorageMock = {
            store: {},
            getItem: jest.fn((key) => localStorageMock.store[key] || null),
            setItem: jest.fn((key, value) => { localStorageMock.store[key] = value; }),
            removeItem: jest.fn(),
            clear: jest.fn()
        };
        Object.defineProperty(window, 'localStorage', { value: localStorageMock, writable: true });

        AdvancedTable.prototype.loadConfiguration = jest.fn();
    });

    afterEach(() => {
        document.body.innerHTML = '';
    });

    describe('Direct instantiation', () => {
        test('should create instance with valid container', () => {
            const columns = [{ key: 'id', label: 'ID' }];
            const data = [{ id: 1 }];

            const table = new AdvancedTable('test-container', {
                data: data,
                columns: columns,
                pageName: 'test-container',
                pageSize: 25
            });

            expect(table).toBeDefined();
            expect(table).toBeInstanceOf(AdvancedTable);
        });

        test('should set pageSize from options', () => {
            const table = new AdvancedTable('test-container', {
                data: [{ id: 1 }],
                columns: [{ key: 'id', label: 'ID' }],
                pageName: 'test-container',
                pageSize: 50
            });

            expect(table.pageSize).toBe(50);
        });

        test('should set pageName from options', () => {
            const table = new AdvancedTable('test-container', {
                data: [{ id: 1 }],
                columns: [{ key: 'id', label: 'ID' }],
                pageName: 'custom-page',
                pageSize: 25
            });

            expect(table.pageName).toBe('custom-page');
        });

        test('should store data in instance', () => {
            const data = [{ id: 1 }, { id: 2 }];

            const table = new AdvancedTable('test-container', {
                data: data,
                columns: [{ key: 'id', label: 'ID' }],
                pageName: 'test',
                pageSize: 25
            });

            expect(table.data).toEqual(data);
        });

        test('should store columns in instance', () => {
            const columns = [
                { key: 'id', label: 'ID' },
                { key: 'name', label: 'Name' }
            ];

            const table = new AdvancedTable('test-container', {
                data: [{ id: 1, name: 'Test' }],
                columns: columns,
                pageName: 'test',
                pageSize: 25
            });

            expect(table.columns).toEqual(columns);
        });

        test('should initialize with empty filters', () => {
            const table = new AdvancedTable('test-container', {
                data: [{ id: 1 }],
                columns: [{ key: 'id', label: 'ID' }],
                pageName: 'test',
                pageSize: 25
            });

            expect(table.filters).toEqual([]);
        });
    });

    describe('initAdvancedTable Global Function', () => {
        // Require the module directly to ensure coverage instrumentation
        const { initAdvancedTable } = require('../../../src/static/js/advanced-table/table-init');

        test('should define initAdvancedTable', () => {
            expect(typeof initAdvancedTable).toBe('function');
        });

        test('should return null if container missing', () => {
            const result = initAdvancedTable('non-existent-id', [], []);
            expect(result).toBeNull();
        });

        test('should initialize table if container exists', () => {
            const table = initAdvancedTable('test-container', [], []);
            expect(table).toBeInstanceOf(AdvancedTable);
            expect(table.pageName).toBe('test-container');
        });
    });
});

