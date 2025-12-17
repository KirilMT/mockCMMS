/**
 * Tests for table-render.js
 * Covers: render, renderHeader, renderBody, getSortIcon, formatCellValue, updateTable
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

// Load AdvancedTable and make it global BEFORE loading other modules
const AdvancedTable = require('../../../src/static/js/advanced-table/table-core');
global.AdvancedTable = AdvancedTable;

// Load ALL modules that extend AdvancedTable.prototype
require('../../../src/static/js/advanced-table/table-data');
require('../../../src/static/js/advanced-table/table-render');
require('../../../src/static/js/advanced-table/table-events');

describe('AdvancedTable Render Methods', () => {
    let table;
    let container;
    let localStorageMock;

    beforeEach(() => {
        // Setup DOM
        document.body.innerHTML = '<div id="test-container"></div>';
        container = document.getElementById('test-container');

        // Mock localStorage
        localStorageMock = {
            store: {},
            getItem: jest.fn((key) => localStorageMock.store[key] || null),
            setItem: jest.fn((key, value) => { localStorageMock.store[key] = value; }),
            removeItem: jest.fn(),
            clear: jest.fn(() => { localStorageMock.store = {}; })
        };
        Object.defineProperty(window, 'localStorage', { value: localStorageMock, writable: true });

        // Mock methods called in init
        AdvancedTable.prototype.loadConfiguration = jest.fn();

        table = new AdvancedTable('test-container', {
            columns: [
                { key: 'id', label: 'ID' },
                { key: 'name', label: 'Name' },
                { key: 'status', label: 'Status' }
            ],
            data: [
                { id: 1, name: 'Item 1', status: 'Active' },
                { id: 2, name: 'Item 2', status: 'Inactive' }
            ],
            pageName: 'testTable'
        });
    });

    afterEach(() => {
        document.body.innerHTML = '';
        jest.clearAllMocks();
    });

    describe('renderHeader', () => {
        test('should render column headers with sort icons', () => {
            const header = table.renderHeader();
            expect(header).toContain('ID');
            expect(header).toContain('Name');
            expect(header).toContain('Status');
            expect(header).toContain('fa-sort');
        });

        test('should show message when all columns hidden', () => {
            table.hiddenColumns = new Set(['id', 'name', 'status']);
            const header = table.renderHeader();
            expect(header).toContain('All columns are hidden');
        });

        test('should respect column order', () => {
            table.columnOrder = ['status', 'name', 'id'];
            const header = table.renderHeader();
            const statusIndex = header.indexOf('Status');
            const nameIndex = header.indexOf('Name');
            expect(statusIndex).toBeLessThan(nameIndex);
        });
    });

    describe('renderBody', () => {
        test('should render data rows', () => {
            const body = table.renderBody();
            expect(body).toContain('Item 1');
            expect(body).toContain('Item 2');
        });

        test('should show empty message when no data', () => {
            table.data = [];
            const body = table.renderBody();
            expect(body).toContain('No data available');
        });

        test('should show all columns hidden message', () => {
            table.hiddenColumns = new Set(['id', 'name', 'status']);
            const body = table.renderBody();
            expect(body).toContain('All columns are hidden');
        });
    });

    describe('getSortIcon', () => {
        test('should return neutral sort icon for unsorted column', () => {
            const icon = table.getSortIcon('name');
            expect(icon).toContain('fa-sort');
            expect(icon).toContain('text-muted');
        });

        test('should return ascending icon for asc sorted column', () => {
            table.currentSort = { column: 'name', direction: 'asc' };
            const icon = table.getSortIcon('name');
            expect(icon).toContain('fa-sort-up');
        });

        test('should return descending icon for desc sorted column', () => {
            table.currentSort = { column: 'name', direction: 'desc' };
            const icon = table.getSortIcon('name');
            expect(icon).toContain('fa-sort-down');
        });
    });

    describe('formatCellValue', () => {
        test('should return empty string for null/undefined', () => {
            expect(table.formatCellValue(null, 'name', {})).toBe('');
            expect(table.formatCellValue(undefined, 'name', {})).toBe('');
        });

        test('should return value as-is for regular columns', () => {
            expect(table.formatCellValue('Test Value', 'name', {})).toBe('Test Value');
        });

        test('should format date columns', () => {
            table.columns.push({ key: 'created', label: 'Created', type: 'date' });
            const result = table.formatCellValue('2025-12-17', 'created', {});
            expect(result).toContain('2025');
        });

        test('should use custom render function if provided', () => {
            table.columns.push({
                key: 'custom',
                label: 'Custom',
                render: (value) => `<b>${value}</b>`
            });
            const result = table.formatCellValue(true, 'custom', {});
            expect(result).toBe('<b>true</b>');
        });
    });

    describe('updateTable', () => {
        test('should update tbody content', () => {
            // First render the table
            table.render();

            // Modify data and update
            table.data = [{ id: 3, name: 'New Item', status: 'New' }];
            table.updateTable();

            const tbody = container.querySelector('tbody');
            expect(tbody.innerHTML).toContain('New Item');
        });
    });

    // Additional branch coverage tests
    describe('formatCellValue edge cases', () => {
        test('should format datetime columns', () => {
            table.columns.push({ key: 'updated', label: 'Updated', type: 'datetime' });
            const result = table.formatCellValue('2025-12-17T14:30:00', 'updated', {});
            expect(result).toContain('2025');
        });

        test('should handle empty string value', () => {
            const result = table.formatCellValue('', 'name', {});
            expect(result).toBe('');
        });

        test('should handle 0 as valid value', () => {
            const result = table.formatCellValue(0, 'count', {});
            expect(result).toBe(0);
        });

        test('should handle boolean false as valid value', () => {
            const result = table.formatCellValue(false, 'active', {});
            expect(result).toBe(false);
        });
    });



    describe('restoreSearchUI', () => {
        test('should restore search value if globalSearchDisplay exists', () => {
            table.globalSearchDisplay = 'Test Search';
            table.render();

            const searchInput = document.getElementById('globalSearchInput');
            expect(searchInput).not.toBeNull();
            expect(searchInput.value).toBe('Test Search');
        });

        test('should work with empty search display', () => {
            table.globalSearchDisplay = '';
            table.render();

            const searchInput = document.getElementById('globalSearchInput');
            expect(searchInput).not.toBeNull();
        });
    });

    describe('render initialization', () => {
        test('should call sidebar methods during render', () => {
            const populateColumnsSpy = jest.spyOn(table.sidebar, 'populateColumns');
            const populateSavedViewsSpy = jest.spyOn(table.sidebar, 'populateSavedViews');

            table.render();

            expect(populateColumnsSpy).toHaveBeenCalled();
            expect(populateSavedViewsSpy).toHaveBeenCalled();
        });

        test('should call initColumnResize if available', () => {
            table.initColumnResize = jest.fn();
            table.render();

            expect(table.initColumnResize).toHaveBeenCalled();
        });

        test('should call initResizeListener if available', () => {
            table.initResizeListener = jest.fn();
            table.render();

            expect(table.initResizeListener).toHaveBeenCalled();
        });
    });
});

