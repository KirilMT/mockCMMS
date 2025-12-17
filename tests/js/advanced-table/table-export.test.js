/**
 * Tests for table-export.js
 * Covers: exportData, exportCSV, goToPage
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
require('../../../src/static/js/advanced-table/table-export');

describe('AdvancedTable Export Methods', () => {
    let table;
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

        // Mock URL methods
        global.URL.createObjectURL = jest.fn(() => 'blob:mock-url');
        global.URL.revokeObjectURL = jest.fn();

        AdvancedTable.prototype.loadConfiguration = jest.fn();

        table = new AdvancedTable('test-container', {
            columns: [
                { key: 'id', label: 'ID' },
                { key: 'name', label: 'Name' },
                { key: 'status', label: 'Status' }
            ],
            data: [
                { id: 1, name: 'Item 1', status: 'Active' },
                { id: 2, name: 'Item 2', status: 'Inactive' },
                { id: 3, name: 'Item 3', status: 'Active' }
            ],
            pageName: 'testExport'
        });
    });

    afterEach(() => {
        document.body.innerHTML = '';
        jest.clearAllMocks();
    });

    describe('exportData', () => {
        test('should call exportCSV for csv format', () => {
            table.exportCSV = jest.fn();
            table.exportData('csv');
            expect(table.exportCSV).toHaveBeenCalled();
        });

        test('should default to csv format', () => {
            table.exportCSV = jest.fn();
            table.exportData();
            expect(table.exportCSV).toHaveBeenCalled();
        });

        test('should not call exportCSV for non-csv format', () => {
            // Covers the else branch of format === 'csv'
            table.exportCSV = jest.fn();
            table.exportData('json');
            expect(table.exportCSV).not.toHaveBeenCalled();
        });
    });

    describe('exportCSV', () => {
        test('should generate CSV with headers', () => {
            let capturedCSV = '';
            global.Blob = jest.fn((content) => {
                capturedCSV = content[0];
                return { type: 'text/csv' };
            });

            const mockAnchor = { click: jest.fn(), href: '', download: '' };
            const originalCreateElement = document.createElement.bind(document);
            document.createElement = jest.fn((tag) => {
                if (tag === 'a') return mockAnchor;
                return originalCreateElement(tag);
            });

            table.exportCSV(table.data);

            expect(capturedCSV).toContain('ID,Name,Status');
        });
    });

    describe('goToPage', () => {
        beforeEach(() => {
            table.pageSize = 2;
            table.currentPage = 1;
            table.render = jest.fn();
        });

        test('should change page when valid', () => {
            table.goToPage(2);
            expect(table.currentPage).toBe(2);
            expect(table.render).toHaveBeenCalled();
        });

        test('should not go to page 0', () => {
            table.goToPage(0);
            expect(table.currentPage).toBe(1);
            expect(table.render).not.toHaveBeenCalled();
        });

        test('should not go beyond total pages', () => {
            table.goToPage(10);
            expect(table.currentPage).toBe(1);
            expect(table.render).not.toHaveBeenCalled();
        });
    });
});
