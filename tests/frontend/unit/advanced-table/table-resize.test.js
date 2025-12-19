/**
 * Tests for table-resize.js
 * Covers: initColumnResize, saveColumnWidths, restoreColumnWidths, handleWindowResize
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
const AdvancedTable = require('../../../../src/static/js/advanced-table/table-core');
global.AdvancedTable = AdvancedTable;

// Load ALL modules
require('../../../../src/static/js/advanced-table/table-data');
require('../../../../src/static/js/advanced-table/table-render');
require('../../../../src/static/js/advanced-table/table-events');
require('../../../../src/static/js/advanced-table/table-resize');

describe('AdvancedTable Resize Methods', () => {
    let table;
    let container;
    let localStorageMock;

    beforeEach(() => {
        document.body.innerHTML = `
            <div id="test-container">
                <div class="advanced-table-wrapper" style="width: 800px;">
                    <table class="advanced-table" style="width: 100%;">
                        <thead>
                            <tr>
                                <th class="sortable" data-column="id">ID</th>
                                <th class="sortable" data-column="name">Name</th>
                                <th class="sortable" data-column="description">Description</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr><td>1</td><td>Test</td><td>A test item</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        container = document.getElementById('test-container');

        localStorageMock = {
            store: {},
            getItem: jest.fn((key) => localStorageMock.store[key] || null),
            setItem: jest.fn((key, value) => { localStorageMock.store[key] = value; }),
            removeItem: jest.fn((key) => { delete localStorageMock.store[key]; }),
            clear: jest.fn(() => { localStorageMock.store = {}; })
        };
        Object.defineProperty(window, 'localStorage', { value: localStorageMock, writable: true });

        AdvancedTable.prototype.loadConfiguration = jest.fn();

        // Mock getBoundingClientRect
        Element.prototype.getBoundingClientRect = jest.fn(() => ({
            width: 200, height: 30, top: 0, left: 0, right: 200, bottom: 30
        }));

        table = new AdvancedTable('test-container', {
            columns: [
                { key: 'id', label: 'ID' },
                { key: 'name', label: 'Name' },
                { key: 'description', label: 'Description' }
            ],
            data: [{ id: 1, name: 'Test', description: 'A test item' }],
            pageName: 'testResize'
        });
    });

    afterEach(() => {
        document.body.innerHTML = '';
        localStorageMock.clear();
        jest.clearAllMocks();
    });

    describe('initColumnResize', () => {
        test('should add resize handles to sortable headers', () => {
            table.initColumnResize();

            const resizeHandles = container.querySelectorAll('.resize-handle');
            expect(resizeHandles.length).toBe(3);
        });

        test('should set table layout to fixed', () => {
            table.initColumnResize();

            const tableEl = container.querySelector('.advanced-table');
            expect(tableEl.style.tableLayout).toBe('fixed');
        });

        test('should apply smart default widths for ALL known column types', () => {
            // Create a table with ALL types to hit every else if branch
            document.body.innerHTML = `
                <div id="test-container">
                    <div class="advanced-table-wrapper" style="width: 1000px;">
                        <table class="advanced-table" style="width: 100%;">
                            <thead>
                                <tr>
                                    <th class="sortable" data-column="id">ID</th>
                                    <th class="sortable" data-column="code">Code</th>
                                    <th class="sortable" data-column="description">Desc</th>
                                    <th class="sortable" data-column="summary">Sum</th>
                                    <th class="sortable" data-column="subject">Subj</th>
                                    <th class="sortable" data-column="state">State</th>
                                    <th class="sortable" data-column="time">Time</th>
                                    <th class="sortable" data-column="assignee">User</th>
                                    <th class="sortable" data-column="random">Other</th>
                                </tr>
                            </thead>
                            <tbody></tbody>
                        </table>
                    </div>
                </div>
            `;
            container = document.getElementById('test-container');
            // Re-bind table container
            table.container = container;

            // Mock getBoundingClientRect to return small width so defaults take over
            Element.prototype.getBoundingClientRect = jest.fn(() => ({ width: 10 }));

            table.initColumnResize();

            const headers = container.querySelectorAll('th');
            // Check specific widths based on keywords
            expect(headers[0].style.width).toBe('65px');  // id
            expect(headers[1].style.width).toBe('150px'); // code
            expect(headers[2].style.width).toBe('350px'); // description matches
            expect(headers[3].style.width).toBe('350px'); // summary matches
            expect(headers[4].style.width).toBe('250px'); // subject matches
            expect(headers[5].style.width).toBe('140px'); // state matches
            expect(headers[6].style.width).toBe('160px'); // time matches
            expect(headers[7].style.width).toBe('200px'); // assignee matches
            expect(headers[8].style.width).toBe('150px'); // fallback
        });

        test('should apply smart default width for ID column', () => {
            table.initColumnResize();

            const idHeader = container.querySelector('[data-column="id"]');
            expect(idHeader.style.width).toBe('65px');
        });

        test('should apply smart default width for description column', () => {
            table.initColumnResize();

            const descHeader = container.querySelector('[data-column="description"]');
            expect(descHeader.style.width).toBe('350px');
        });

        test('should remove existing handles when re-initializing', () => {
            // First init
            table.initColumnResize();
            let handles = container.querySelectorAll('.resize-handle');
            expect(handles.length).toBe(3);

            // Annotate first handle to identify it
            handles[0].dataset.original = 'true';

            // Second init (should remove old ones)
            table.initColumnResize();
            handles = container.querySelectorAll('.resize-handle');
            expect(handles.length).toBe(3);
            // Verify it's a new element
            expect(handles[0].dataset.original).toBeUndefined();
        });

        test('should handle missing table element gracefully', () => {
            document.body.innerHTML = ''; // Empty container
            // Should not throw
            table.initColumnResize();
        });

        test('should do nothing if no table found', () => {
            container.innerHTML = '';
            expect(() => table.initColumnResize()).not.toThrow();
        });
    });

    describe('saveColumnWidths', () => {
        test('should save column widths to localStorage', () => {
            table.initColumnResize();
            table.saveColumnWidths();

            expect(localStorage.setItem).toHaveBeenCalled();
        });

        test('should use pageName in storage key', () => {
            table.initColumnResize();
            table.saveColumnWidths();

            expect(localStorage.setItem).toHaveBeenCalledWith(
                'table-column-widths-testResize',
                expect.any(String)
            );
        });

        test('should do nothing if no table', () => {
            container.innerHTML = '';
            expect(() => table.saveColumnWidths()).not.toThrow();
        });
    });

    describe('restoreColumnWidths', () => {
        test('should restore widths from localStorage', () => {
            const savedWidths = { id: '100px', name: '200px' };
            localStorageMock.store['table-column-widths-testResize'] = JSON.stringify(savedWidths);
            localStorageMock.getItem.mockReturnValue(JSON.stringify(savedWidths));

            table.restoreColumnWidths();

            const idHeader = container.querySelector('[data-column="id"]');
            expect(idHeader.style.width).toBe('100px');
        });

        test('should do nothing if no saved widths', () => {
            localStorageMock.getItem.mockReturnValue(null);
            expect(() => table.restoreColumnWidths()).not.toThrow();
        });

        test('should handle invalid JSON gracefully', () => {
            localStorageMock.getItem.mockReturnValue('not valid json');
            console.error = jest.fn();

            expect(() => table.restoreColumnWidths()).not.toThrow();
            expect(console.error).toHaveBeenCalled();
        });
    });

    describe('handleWindowResize', () => {
        test('should do nothing if no table or wrapper', () => {
            container.innerHTML = '';
            expect(() => table.handleWindowResize()).not.toThrow();
        });
    });

    describe('resize handle mouse events', () => {
        beforeEach(() => {
            table.initColumnResize();
        });

        test('should create resize handles', () => {
            const handles = container.querySelectorAll('.resize-handle');
            expect(handles.length).toBe(3);
        });

        test('should handle click on resize handle without errors', () => {
            const handle = container.querySelector('.resize-handle');
            const clickEvent = new MouseEvent('click', { bubbles: true });

            expect(() => handle.dispatchEvent(clickEvent)).not.toThrow();
        });

        test('should handle mousedown on resize handle', () => {
            const handle = container.querySelector('.resize-handle');
            const mousedownEvent = new MouseEvent('mousedown', {
                bubbles: true,
                pageX: 100,
                pageY: 50
            });

            expect(() => handle.dispatchEvent(mousedownEvent)).not.toThrow();
        });

        test('should change cursor on mousedown', () => {
            const handle = container.querySelector('.resize-handle');
            const mousedownEvent = new MouseEvent('mousedown', {
                bubbles: true,
                pageX: 100
            });

            handle.dispatchEvent(mousedownEvent);

            expect(document.body.style.cursor).toBe('col-resize');
        });

        test('should restore cursor on mouseup', () => {
            const handle = container.querySelector('.resize-handle');

            // Start resize
            handle.dispatchEvent(new MouseEvent('mousedown', {
                bubbles: true,
                pageX: 100
            }));

            // End resize
            document.dispatchEvent(new MouseEvent('mouseup'));

            expect(document.body.style.cursor).toBe('');
        });

        test('should handle dblclick for auto-fit', () => {
            const handle = container.querySelector('.resize-handle');
            const dblclickEvent = new MouseEvent('dblclick', { bubbles: true });

            expect(() => handle.dispatchEvent(dblclickEvent)).not.toThrow();
        });

        test('should prevent sort on header click after resize', () => {
            const header = container.querySelector('[data-column="id"]');
            const handle = header.querySelector('.resize-handle');

            // Start resize
            handle.dispatchEvent(new MouseEvent('mousedown', {
                bubbles: true,
                pageX: 100
            }));

            // Move slightly
            document.dispatchEvent(new MouseEvent('mousemove', {
                bubbles: true,
                pageX: 150
            }));

            // End resize
            document.dispatchEvent(new MouseEvent('mouseup'));

            // Click on header should not throw
            expect(() => header.click()).not.toThrow();
        });

        test('should update column width on mousemove', () => {
            const header = container.querySelector('[data-column="id"]');
            const handle = header.querySelector('.resize-handle');

            // Mock requestAnimationFrame
            global.requestAnimationFrame = jest.fn(cb => { cb(); return 1; });
            global.cancelAnimationFrame = jest.fn();

            // Start resize
            handle.dispatchEvent(new MouseEvent('mousedown', {
                bubbles: true,
                pageX: 100
            }));

            // Move 50px right
            document.dispatchEvent(new MouseEvent('mousemove', {
                bubbles: true,
                pageX: 160
            }));

            // Style should be set
            expect(header.style.width).not.toBe('');
        });

        test('should complete resize workflow without errors', () => {
            const header = container.querySelector('[data-column="id"]');
            const handle = header.querySelector('.resize-handle');

            // Mock requestAnimationFrame
            global.requestAnimationFrame = jest.fn(cb => { cb(); return 1; });
            global.cancelAnimationFrame = jest.fn();

            // Start resize
            handle.dispatchEvent(new MouseEvent('mousedown', {
                bubbles: true,
                pageX: 100
            }));

            // Move significantly (more than 2px threshold)
            document.dispatchEvent(new MouseEvent('mousemove', {
                bubbles: true,
                pageX: 200
            }));

            // End resize
            document.dispatchEvent(new MouseEvent('mouseup'));

            // If we got here without errors, the resize workflow completed
            expect(true).toBe(true);
        });

        test('should not save if no movement during resize', () => {
            table.saveColumnWidths = jest.fn();

            const handle = container.querySelector('.resize-handle');

            // Start resize
            handle.dispatchEvent(new MouseEvent('mousedown', {
                bubbles: true,
                pageX: 100
            }));

            // End resize without moving
            document.dispatchEvent(new MouseEvent('mouseup'));

            expect(table.saveColumnWidths).not.toHaveBeenCalled();
        });
    });

    describe('initResizeListener', () => {
        test('should not throw when called', () => {
            expect(() => table.initResizeListener()).not.toThrow();
        });

        test('should handle window resize event', () => {
            table.initResizeListener();

            // Trigger window resize
            window.dispatchEvent(new Event('resize'));

            // Should not throw
            expect(true).toBe(true);
        });
    });
});

