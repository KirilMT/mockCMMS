
// Setup environment
const AdvancedTable = require('../../../../src/static/js/advanced-table/table-core.js');
const TableSidebar = require('../../../../src/static/js/advanced-table/table-sidebar.js');

// Ensure helpers are available
global.TableSidebar = TableSidebar;
global.ToastNotification = { error: jest.fn(), warning: jest.fn(), success: jest.fn(), info: jest.fn() };
global.showConfirmModal = jest.fn((msg, cb) => cb && cb());
global.showDeleteConfirm = jest.fn((e, m, cb) => cb && cb());
global.fetch = jest.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve({ success: true }) }));

// Mock localStorage
const localStorageMock = (() => {
    let store = {};
    return {
        getItem: jest.fn(key => store[key] || null),
        setItem: jest.fn((key, value) => { store[key] = value.toString(); }),
        clear: jest.fn(() => { store = {}; })
    };
})();
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

describe('TableSidebar Complex Logic', () => {
    let table;
    let sidebar;

    beforeEach(() => {
        // Setup DOM
        document.body.innerHTML = `
            <div id="table-container"></div>
            <div id="sidebar-container"></div>
        `;

        // Mock methods
        AdvancedTable.prototype.render = jest.fn();
        AdvancedTable.prototype.loadConfiguration = jest.fn();
        AdvancedTable.prototype.updateTable = jest.fn();
        AdvancedTable.prototype.saveTableState = jest.fn();
        AdvancedTable.prototype.showButtonLoading = jest.fn(() => ({ restore: jest.fn() }));

        table = new AdvancedTable('table-container', {
            columns: [
                { key: 'col1', label: 'Column 1' },
                { key: 'col2', label: 'Column 2' },
                { key: 'col3', label: 'Column 3' }
            ]
        });

        // Ensure table.filters is initialized
        table.filters = [];
        
        sidebar = table.sidebar;
        document.getElementById('sidebar-container').innerHTML = sidebar.generateHTML();
        
        // Ensure sidebar has reference to table
        sidebar.table = table;
    });

    describe('validateAllFilters Branch Coverage', () => {
        test('Should detect dirty state when length mismatch', () => {
            // Setup: 1 applied filter, 0 DOM filters
            table.filters = [{ column: 'col1', operator: 'contains', value: 'val1' }];
            // DOM is empty by default
            
            sidebar.validateAllFilters();
            
            const applyBtn = document.getElementById('applyFiltersBtn');
            // If dirty, button should be enabled (since length mismatch implies change)
            // Logic: if (!isDirty) disable. else enable if valid.
            // Here: isDirty=true. All DOM filters are valid (size 0). So valid=true.
            // Button should be ENABLED.
            expect(applyBtn.disabled).toBe(false);
        });

        test('Should detect dirty state when content mismatch', () => {
            // Setup: 1 applied filter
            table.filters = [{ column: 'col1', operator: 'contains', value: 'val1' }];
            
            // DOM: 1 filter but different value
            sidebar.addFilterRow('col1', 'contains', 'val2');
            
            sidebar.validateAllFilters();
            
            const applyBtn = document.getElementById('applyFiltersBtn');
            // isDirty=true (val1 != val2). valid=true.
            expect(applyBtn.disabled).toBe(false);
        });

        test('Should be clean (disabled apply) when matching exactly', () => {
             // Setup: 1 applied
             table.filters = [{ column: 'col1', operator: 'contains', value: 'val1' }];
             
             // DOM: 1 matching filter
             sidebar.addFilterRow('col1', 'contains', 'val1');
             
             sidebar.validateAllFilters();
             
             const applyBtn = document.getElementById('applyFiltersBtn');
             expect(applyBtn.disabled).toBe(true);
        });
        
        test('Should be disabled if invalid filters exist', () => {
            // Dirty but invalid
            table.filters = [];
            
            // Add invalid row (empty column)
            sidebar.addFilterRow('', 'contains', 'val');
            
            sidebar.validateAllFilters();
            
            const applyBtn = document.getElementById('applyFiltersBtn');
            expect(applyBtn.disabled).toBe(true);
        });

        test('Should enable Add button if no filters exist', () => {
             // 0 filters
             sidebar.validateAllFilters();
             const addBtn = document.getElementById('addFilterBtn');
             expect(addBtn.disabled).toBe(false);
        });

        test('Should disable Add button if invalid filter exists', () => {
             sidebar.addFilterRow('', '', '');
             sidebar.validateAllFilters();
             const addBtn = document.getElementById('addFilterBtn');
             expect(addBtn.disabled).toBe(true);
        });
    });

    describe('applyAllFilters Mute Logic', () => {
        test('Should mute filter if part of incomplete OR chain', () => {
            // Scenario: Row 1 (Valid) OR Row 2 (Incomplete)
            // Row 1 should be muted (not added to filters)
            
            // Add Row 1: Valid
            sidebar.addFilterRow('col1', 'contains', 'val1');
            
            // Add Row 2: Incomplete
            // We need to bypass addFilterRow valid checks or manipulate DOM directly
            // addFilterRow creates valid-ish HTML structure. Let's create Row 2 manually or use addFilterRow then clear value
            
            sidebar.addFilterRow('col2', 'contains', 'val2', 'OR');
            
            // Now clear value of Row 2 to make it incomplete
            const rows = document.querySelectorAll('.filter-row-sidebar');
            const row2Input = rows[1].querySelector('.filter-value');
            row2Input.value = ''; // Incomplete
            
            // Add class is-editing to simulate user typing (optional depending on logic)
            // Logic: if (!nextCol || !nextVal || nextIsEditing) -> muteThisRow
            // Empty value triggers it.
            
            sidebar.applyAllFilters();
            
            // Logic says: Mute this row (Row 1).
            // Row 2 is skipped because it's incomplete.
            // So filters should be empty.
            expect(table.filters.length).toBe(0);
        });

        test('Should NOT mute filter if OR chain is complete', () => {
             // Scenario: Row 1 (Valid) OR Row 2 (Valid)
             
             sidebar.addFilterRow('col1', 'contains', 'val1');
             sidebar.addFilterRow('col2', 'contains', 'val2', 'OR');
             
             sidebar.applyAllFilters();
             
             expect(table.filters.length).toBe(2);
             expect(table.filters[0].value).toBe('val1');
             expect(table.filters[1].value).toBe('val2');
        });

        test('Should NOT mute if connector is AND', () => {
             // Scenario: Row 1 (Valid) AND Row 2 (Incomplete)
             // Row 1 is valid and NOT in an OR chain. Row 2 is skipped.
             
             sidebar.addFilterRow('col1', 'contains', 'val1');
             sidebar.addFilterRow('col2', 'contains', 'val2', 'AND'); // Default
             
             // Make Row 2 incomplete
             const rows = document.querySelectorAll('.filter-row-sidebar');
             rows[1].querySelector('.filter-value').value = '';
             
             sidebar.applyAllFilters();
             
             expect(table.filters.length).toBe(1);
             expect(table.filters[0].value).toBe('val1');
        });
        
        test('Should mute if next valid row is being edited in OR chain', () => {
             // Scenario: Row 1 (Valid) OR Row 2 (Valid but Editing)
             
             sidebar.addFilterRow('col1', 'contains', 'val1');
             sidebar.addFilterRow('col2', 'contains', 'val2', 'OR');
             
             const rows = document.querySelectorAll('.filter-row-sidebar');
             rows[1].classList.add('is-editing');
             
             sidebar.applyAllFilters();
             
             // Row 1 muted because next is editing in OR chain
             // Row 2 skipped because editing
             expect(table.filters.length).toBe(0); 
        });
    });
    
    describe('Event Listeners Edge Cases', () => {
        test('ESC key reverts edits', () => {
             // Setup valid filter
             sidebar.addFilterRow('col1', 'contains', 'val1');
             const row = document.querySelector('.filter-row-sidebar');
             const input = row.querySelector('.filter-value');
             
             // Enter edit mode
             input.dispatchEvent(new Event('focus'));
             
             // Change value
             input.value = 'changed';
             
             // Press Escape
             const escEvent = new KeyboardEvent('keyup', { key: 'Escape' });
             input.dispatchEvent(escEvent);
             
             // Should revert
             expect(input.value).toBe('val1');
             expect(row.classList.contains('is-editing')).toBe(false);
        });

        test('Enter key applies filters', () => {
             // Setup valid filter
             sidebar.addFilterRow('col1', 'contains', 'val1');
             const row = document.querySelector('.filter-row-sidebar');
             const input = row.querySelector('.filter-value');
             
             // Simulate edit
             input.dispatchEvent(new Event('focus'));
             input.value = 'val1-mod';
             
             sidebar.applyAllFilters = jest.fn();
             
             const enterEvent = new KeyboardEvent('keypress', { key: 'Enter' });
             input.dispatchEvent(enterEvent);
             
             expect(sidebar.applyAllFilters).toHaveBeenCalled();
             expect(row.classList.contains('is-editing')).toBe(false);
        });
        
        test('Remove button removes logic connector', () => {
            sidebar.addFilterRow('col1', 'contains', 'val1');
            sidebar.addFilterRow('col2', 'contains', 'val2');
            
            // Should be 2 rows and 1 connector
            expect(document.querySelectorAll('.filter-logic-connector').length).toBe(1);
            
            // Remove 2nd row
            const rows = document.querySelectorAll('.filter-row-sidebar');
            rows[1].querySelector('.remove-filter-btn').click();
            
            expect(document.querySelectorAll('.filter-row-sidebar').length).toBe(1);
            expect(document.querySelectorAll('.filter-logic-connector').length).toBe(0);
        });
        
        test('Column change clears value and applies', () => {
             sidebar.addFilterRow('col1', 'contains', 'val1');
             const row = document.querySelector('.filter-row-sidebar');
             const colSelect = row.querySelector('.filter-column');
             const input = row.querySelector('.filter-value');
             
             sidebar.applyAllFilters = jest.fn();
             
             colSelect.value = 'col2';
             colSelect.dispatchEvent(new Event('change'));
             
             expect(input.value).toBe('');
             expect(sidebar.applyAllFilters).toHaveBeenCalled();
        });
    });
});
