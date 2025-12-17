
// Mock dependencies
global.TableSidebar = class {
    constructor(table) {
        this.table = table;
    }
};

// Setup environment
const AdvancedTable = require('../../../src/static/js/advanced-table/table-core.js');
global.AdvancedTable = AdvancedTable;
require('../../../src/static/js/advanced-table/table-data.js');

describe('TableData Module', () => {
    let table;
    const testData = [
        { id: 1, name: 'Alice', age: 30, role: 'Engineer' },
        { id: 2, name: 'Bob', age: 25, role: 'Designer' },
        { id: 3, name: 'Charlie', age: 35, role: 'Manager' },
        { id: 4, name: 'David', age: 28, role: 'Engineer' },
        { id: 5, name: 'Eve', age: null, role: 'Intern' }
    ];

    const columns = [
        { key: 'id', type: 'number' },
        { key: 'name', type: 'string' },
        { key: 'age', type: 'number' },
        { key: 'role', type: 'string' }
    ];

    beforeEach(() => {
        document.body.innerHTML = '<div id="table-container"></div>';

        // Mock init methods to avoid full render
        AdvancedTable.prototype.render = jest.fn();
        AdvancedTable.prototype.loadConfiguration = jest.fn();

        table = new AdvancedTable('table-container', {
            data: [...testData], // Copy to avoid mutation
            columns: columns,
            pageSize: 2
        });
    });

    test('TD-1.1: test_filter_by_single_condition', () => {
        table.filters = [
            { column: 'role', operator: 'equals', value: 'Engineer' }
        ];

        const result = table.getFilteredData();
        expect(result.length).toBe(2);
        expect(result.map(r => r.name).sort()).toEqual(['Alice', 'David']);
    });

    test('TD-1.2: test_filter_by_multiple_AND_conditions', () => {
        // Engineer AND Age > 29 (Contains 3 in age is not robust, let's use what we have)
        // Operators: contains, not_contains, equals, not_equals, starts_with, ends_with

        table.filters = [
            { column: 'role', operator: 'equals', value: 'Engineer', logic: 'AND' },
            { column: 'name', operator: 'starts_with', value: 'A', logic: 'AND' } // Logic for second filter relates to first?
            // In table-data.js:
            // if (index === 0) currentChain.push(filter)
            // else if (filter.logic === 'AND') start new chain
            // else add to current chain (OR)

            // Wait, the logic implementation in table-data.js seems to be:
            // "filter.logic" is how it connects to the PREVIOUS filter?
            // "if (filter.logic === 'AND')" -> new chain.

            // Let's re-read table-data.js logic:
            // if (filter.logic === 'AND') { chains.push(currentChain); currentChain = [filter]; }
            // So if I want (A AND B), I need A, then B with logic='AND'?
            // No, that would make [[A], [B]]. Chains are ANDed together.
            // Items WITHIN a chain are ORed?
            // "for (const chain of chains) { ... let chainResult = false; for (const filter of chain) { ... chainResult = true; break; } ... }"
            // Yes, items in a chain are ORed. Chains are ANDed.

            // So for (A AND B), I want [[A], [B]].
            // Filter 1: A
            // Filter 2: B, logic: 'AND' -> pushes A to chains, starts new chain with B.
        ];

        table.filters = [
            { column: 'role', operator: 'equals', value: 'Engineer' },
            { column: 'name', operator: 'starts_with', value: 'A', logic: 'AND' }
        ];

        const result = table.getFilteredData();
        expect(result.length).toBe(1);
        expect(result[0].name).toBe('Alice');
    });

    test('TD-1.3: test_filter_by_OR_conditions', () => {
        // Engineer OR Designer
        // Same chain = OR.
        // Filter 1: Engineer
        // Filter 2: Designer, logic: 'OR' (anything other than AND)

        table.filters = [
            { column: 'role', operator: 'equals', value: 'Engineer' },
            { column: 'role', operator: 'equals', value: 'Designer', logic: 'OR' }
        ];

        const result = table.getFilteredData();
        expect(result.length).toBe(3); // Alice (Eng), Bob (Des), David (Eng)
    });

    test('TD-1.4: test_filter_chain_logic_AND_OR_combination', () => {
        // (Engineer OR Designer) AND (Age > 25)
        // Group 1: Engineer, Designer (OR)
        // Group 2: Age > 25 (AND to previous)

        table.filters = [
            { column: 'role', operator: 'equals', value: 'Engineer' }, // Chain 1, Item 1
            { column: 'role', operator: 'equals', value: 'Designer', logic: 'OR' }, // Chain 1, Item 2
            { column: 'age', operator: 'gt', value: 25, logic: 'AND' } // Chain 2, Item 1 (Wait, default operator 'gt' covered?)
            // table-data.js has operators: contains, not_contains, equals, not_equals, starts_with, ends_with.
            // It does NOT have 'gt' (greater than).
            // Let's check table-data.js operators again (I viewed lines 1-168).
            // Lines 100+ usually have the switch.
        ];
        // I need to check supported operators first. If GT not supported, use 'not_equals'.
        // (Engineer OR Designer) AND (Name starts with 'A' OR Name starts with 'B')

        table.filters = [
            { column: 'role', operator: 'equals', value: 'Engineer' },
            { column: 'role', operator: 'equals', value: 'Designer', logic: 'OR' },
            { column: 'name', operator: 'starts_with', value: 'A', logic: 'AND' },
            { column: 'name', operator: 'starts_with', value: 'B', logic: 'OR' }
        ];
        // Logic: (Engineer OR Designer) AND (Name starts with A OR Name starts with B)
        // Alice (Eng, A) -> Match
        // Bob (Des, B) -> Match
        // David (Eng, D) -> Fail Group 2
        // Charlie (Mgr, C) -> Fail Group 1

        const result = table.getFilteredData();
        expect(result.length).toBe(2);
        const names = result.map(r => r.name).sort();
        expect(names).toEqual(['Alice', 'Bob']);
    });


    test('TD-1.4: test_sort_ascending_string_column', () => {
        table.currentSort = { column: 'name', direction: 'asc' };
        const result = table.getFilteredData();

        expect(result[0].name).toBe('Alice');
        expect(result[4].name).toBe('Eve');
    });

    test('TD-1.5: test_sort_descending_numeric_column', () => {
        table.currentSort = { column: 'age', direction: 'desc' };
        const result = table.getFilteredData();

        // Ages: 30, 25, 35, 28, null
        // Desc: 35, 30, 28, 25, null (or null first/last depending on implementation)

        // Implementation: localeCompare with numeric: true.
        // aVal.toString().localeCompare(bVal.toString())
        // null becomes '' -> 0 ? or empty string.

        // '35'.localeCompare('30') -> 1
        // ''.localeCompare('35') -> -1 (empty string comes before numbers)

        // If desc: -comparison.
        // So 35 comes before 30.
        // Empty string comes last?
        // '35' vs '' -> 1. Negated -> -1. So 35 comes before ''.

        expect(result[0].name).toBe('Charlie'); // 35
        expect(result[1].name).toBe('Alice'); // 30
    });

    test('TD-1.6: test_sort_handles_null_values', () => {
        table.currentSort = { column: 'age', direction: 'asc' };
        const result = table.getFilteredData();

        // '' vs '25' -> -1.
        // So nulls (empty strings) should be first in asc.

        expect(result[0].name).toBe('Eve'); // age: null
        expect(result[1].name).toBe('Bob'); // age: 25
    });

    test('TD-1.7: test_paginate_returns_correct_slice', () => {
        // Page size 2 (set in beforeEach)
        table.currentPage = 1;
        let pageData = table.getPaginatedData(testData);
        expect(pageData.length).toBe(2);
        expect(pageData[0].id).toBe(1);
        expect(pageData[1].id).toBe(2);

        table.currentPage = 2;
        pageData = table.getPaginatedData(testData);
        expect(pageData.length).toBe(2);
        expect(pageData[0].id).toBe(3);
        expect(pageData[1].id).toBe(4);

        table.currentPage = 3;
        pageData = table.getPaginatedData(testData);
        expect(pageData.length).toBe(1);
        expect(pageData[0].id).toBe(5);
    });

    test('TD-1.8: test_paginate_handles_empty_data', () => {
        table.currentPage = 1;
        const result = table.getPaginatedData([]);
        expect(result).toEqual([]);
    });

    test('TD-1.9: test_globalSearch_filters_rows', () => {
        table.updateTable = jest.fn();
        table.saveTableState = jest.fn();

        table.globalSearch('Alice');

        expect(table.globalSearchTerm).toBe('alice');
        expect(table.currentPage).toBe(1);
        expect(table.updateTable).toHaveBeenCalled();
        expect(table.saveTableState).toHaveBeenCalled();

        const result = table.getFilteredData();
        expect(result.length).toBe(1);
        expect(result[0].name).toBe('Alice');
    });

    test('TD-1.10: test_globalSearch_clears_filter', () => {
        table.updateTable = jest.fn();
        table.saveTableState = jest.fn();

        // First search
        table.globalSearch('Alice');
        expect(table.globalSearchTerm).toBe('alice');

        // Clear search
        table.globalSearch('');
        expect(table.globalSearchTerm).toBeNull();
        expect(table.globalSearchDisplay).toBe('');
        expect(table.updateTable).toHaveBeenCalledTimes(2);
    });

    test('TD-1.11: test_applyFilter_operators', () => {
        // Test various operators in isolation via getFilteredData with 1 filter

        // contains
        table.filters = [{ column: 'name', operator: 'contains', value: 'li' }];
        let result = table.getFilteredData(); // Alice, Charlie
        expect(result.map(r => r.name).sort()).toEqual(['Alice', 'Charlie']);

        // not_contains
        // Data: Alice, Bob, Charlie, David, Eve
        // 'a' is in Alice, Charlie, David
        // Bob has no 'a' (Wait, Bob does not have 'a').
        // Eve has no 'a'.
        // So expected result is Bob and Eve.

        table.filters = [{ column: 'name', operator: 'not_contains', value: 'a' }];
        result = table.getFilteredData();
        expect(result.length).toBe(2);
        const names = result.map(r => r.name).sort();
        expect(names).toEqual(['Bob', 'Eve']);

        // starts_with
        table.filters = [{ column: 'name', operator: 'starts_with', value: 'D' }];
        result = table.getFilteredData(); // David
        expect(result.length).toBe(1);
        expect(result[0].name).toBe('David');

        // ends_with
        table.filters = [{ column: 'name', operator: 'ends_with', value: 'e' }];
        result = table.getFilteredData(); // Alice, Charlie, Eve
        expect(result.length).toBe(3);

        // not_equals
        table.filters = [{ column: 'age', operator: 'not_equals', value: '30' }];
        result = table.getFilteredData();
        expect(result.find(r => r.name === 'Alice')).toBeUndefined();
        expect(result.length).toBe(4); // Bob, Charlie, David, Eve (null != 30)
    });

    test('TD-2.1: test_pageSize_affects_pagination', () => {
        // 5 items, page size 2
        table.pageSize = 2;
        table.currentPage = 1;
        let result = table.getPaginatedData(table.data);
        expect(result.length).toBe(2);

        // Page size 5 = all on one page
        table.pageSize = 5;
        result = table.getPaginatedData(table.data);
        expect(result.length).toBe(5);
    });

    test('TD-2.2: test_sort_toggles_direction', () => {
        table.updateTable = jest.fn();
        table.saveTableState = jest.fn();

        // First click - sets ascending
        table.sort('name');
        expect(table.currentSort).toEqual({ column: 'name', direction: 'asc' });

        // Second click - toggles to descending
        table.sort('name');
        expect(table.currentSort).toEqual({ column: 'name', direction: 'desc' });

        // Third click - removes sort
        table.sort('name');
        expect(table.currentSort.column).toBeNull();
    });

    test('TD-2.3: test_sort_changes_column', () => {
        table.updateTable = jest.fn();
        table.saveTableState = jest.fn();

        table.sort('name');
        expect(table.currentSort.column).toBe('name');

        // Click different column
        table.sort('age');
        expect(table.currentSort.column).toBe('age');
        expect(table.currentSort.direction).toBe('asc'); // Resets to asc
    });

    test('TD-2.4: test_complex_filter_chain_AND_OR', () => {
        // (Engineer OR Designer) AND starts_with 'A' or 'B'
        // Expected: Alice (Engineer, A), Bob (Designer, B)

        table.filters = [
            { column: 'role', operator: 'equals', value: 'Engineer' },
            { column: 'role', operator: 'equals', value: 'Designer', logic: 'OR' },
            { column: 'name', operator: 'starts_with', value: 'A', logic: 'AND' },
            { column: 'name', operator: 'starts_with', value: 'B', logic: 'OR' }
        ];

        const result = table.getFilteredData();
        const names = result.map(r => r.name).sort();
        expect(names).toEqual(['Alice', 'Bob']);
    });

    test('TD-2.5: test_globalSearch_case_insensitive', () => {
        table.updateTable = jest.fn();
        table.saveTableState = jest.fn();

        table.globalSearch('ALICE');
        const result = table.getFilteredData();

        expect(result.length).toBe(1);
        expect(result[0].name).toBe('Alice');
    });

    test('TD-2.6: test_globalSearch_across_all_columns', () => {
        table.updateTable = jest.fn();
        table.saveTableState = jest.fn();

        // Search for role value
        table.globalSearch('Manager');
        const result = table.getFilteredData();

        expect(result.length).toBe(1);
        expect(result[0].name).toBe('Charlie');
    });

    test('TD-2.7: test_filter_with_empty_value_ignored', () => {
        table.filters = [
            { column: 'name', operator: 'contains', value: '' }
        ];

        const result = table.getFilteredData();
        // Empty filter should be ignored, returning all data
        expect(result.length).toBe(5);
    });

    test('TD-2.8: test_pagination_with_filtered_data', () => {
        table.filters = [{ column: 'role', operator: 'equals', value: 'Engineer' }];
        table.pageSize = 1;
        table.currentPage = 1;

        const filtered = table.getFilteredData();
        expect(filtered.length).toBe(2); // Alice, David

        const paginated = table.getPaginatedData(filtered);
        expect(paginated.length).toBe(1);
    });

    test('TD-2.9: test_filter_null_values', () => {
        // Test filtering on column with null values
        table.filters = [{ column: 'age', operator: 'equals', value: '' }];

        const result = table.getFilteredData();
        // Empty value comparison with null
        expect(result.find(r => r.name === 'Eve')).toBeDefined();
    });

    test('TD-2.10: test_no_filters_returns_all_data', () => {
        table.filters = [];
        table.globalSearchTerm = null;

        const result = table.getFilteredData();
        expect(result.length).toBe(5);
    });

    // Additional branch coverage tests
    test('TD-3.1: test_filter_date_column', () => {
        const tableWithDates = new AdvancedTable('table-container', {
            data: [
                { id: 1, name: 'Test1', created: '2024-01-15' },
                { id: 2, name: 'Test2', created: '2024-02-20' }
            ],
            columns: [
                { key: 'id', type: 'number' },
                { key: 'name', type: 'string' },
                { key: 'created', type: 'date' }
            ],
            pageSize: 10
        });

        tableWithDates.globalSearchTerm = '2024';
        const result = tableWithDates.getFilteredData();
        expect(result.length).toBeGreaterThan(0);
    });

    test('TD-3.2: test_filter_datetime_column', () => {
        const tableWithDatetime = new AdvancedTable('table-container', {
            data: [
                { id: 1, name: 'Event1', timestamp: '2024-01-15T10:30:00' },
                { id: 2, name: 'Event2', timestamp: '2024-02-20T14:45:00' }
            ],
            columns: [
                { key: 'id', type: 'number' },
                { key: 'name', type: 'string' },
                { key: 'timestamp', type: 'datetime' }
            ],
            pageSize: 10
        });

        tableWithDatetime.globalSearchTerm = 'event';
        const result = tableWithDatetime.getFilteredData();
        expect(result.length).toBeGreaterThan(0);
    });

    test('TD-3.3: test_globalSearch_clears_search', () => {
        table.updateTable = jest.fn();
        table.saveTableState = jest.fn();
        table.globalSearchTerm = 'test';

        table.globalSearch('');

        expect(table.globalSearchTerm).toBeNull();
        expect(table.currentPage).toBe(1);
    });

    test('TD-3.4: test_globalSearch_sets_display_value', () => {
        table.updateTable = jest.fn();
        table.saveTableState = jest.fn();

        table.globalSearch('Alice');

        expect(table.globalSearchDisplay).toBe('Alice');
        expect(table.globalSearchTerm).toBe('alice');
    });

    test('TD-3.5: test_sort_desc_to_none', () => {
        table.updateTable = jest.fn();
        table.saveTableState = jest.fn();

        table.currentSort = { column: 'name', direction: 'desc' };
        table.sort('name');

        expect(table.currentSort.column).toBeNull();
    });

    test('TD-3.6: test_applyFiltersWithLogic_empty_filters', () => {
        table.filters = [];

        const result = table.applyFiltersWithLogic({ name: 'Alice' });

        expect(result).toBe(true);
    });

    test('TD-3.7: test_applyFilter_default_case', () => {
        const result = table.applyFilter('test', {
            value: 'test',
            operator: 'unknown_operator'
        });

        expect(result).toBe(true);
    });

    test('TD-3.8: test_getPaginatedData_no_pageSize', () => {
        table.pageSize = 0;

        const result = table.getPaginatedData(table.data);

        expect(result.length).toBe(5);
    });

    test('TD-3.9: test_getPaginatedData_negative_pageSize', () => {
        table.pageSize = -1;

        const result = table.getPaginatedData(table.data);

        expect(result.length).toBe(5);
    });

    test('TD-3.10: test_globalSearch_null_value_in_data', () => {
        table.globalSearchTerm = 'eve';

        const result = table.getFilteredData();

        // Eve has null age, should still be searchable by name
        expect(result.find(r => r.name === 'Eve')).toBeDefined();
    });

    test('TD-3.11: test_sort_resets_currentPage', () => {
        table.updateTable = jest.fn();
        table.saveTableState = jest.fn();
        table.currentPage = 5;

        table.sort('name');

        expect(table.currentPage).toBe(1);
    });

    test('TD-3.12: test_sort_clears_selectedConfigId', () => {
        table.updateTable = jest.fn();
        table.saveTableState = jest.fn();
        table.selectedConfigId = 123;

        table.sort('name');

        expect(table.selectedConfigId).toBeNull();
    });

    test('TD-3.13: test_filter_operators', () => {
        const testRows = [
            { id: 1, val: 'apple' },
            { id: 2, val: 'banana' },
            { id: 3, val: 'cherry' },
            { id: 4, val: 'date' }
        ];

        const operatorTable = new AdvancedTable('table-container', {
            data: testRows,
            columns: [{ key: 'val', type: 'string' }]
        });

        // Test not_contains
        operatorTable.filters = [{ column: 'val', operator: 'not_contains', value: 'a' }];
        let res = operatorTable.getFilteredData();
        expect(res.length).toBe(1); // cherry

        // Test not_equals
        operatorTable.filters = [{ column: 'val', operator: 'not_equals', value: 'apple' }];
        res = operatorTable.getFilteredData();
        expect(res.length).toBe(3);

        // Test starts_with
        operatorTable.filters = [{ column: 'val', operator: 'starts_with', value: 'b' }];
        res = operatorTable.getFilteredData();
        expect(res.length).toBe(1);

        // Test ends_with
        operatorTable.filters = [{ column: 'val', operator: 'ends_with', value: 'e' }];
        res = operatorTable.getFilteredData();
        expect(res.map(r => r.val).sort()).toEqual(['apple', 'date']);
    });

    test('TD-3.14: test_filter_case_insensitive', () => {
        const operatorTable = new AdvancedTable('table-container', {
            data: [{ id: 1, val: 'Apple' }],
            columns: [{ key: 'val', type: 'string' }]
        });

        operatorTable.filters = [{ column: 'val', operator: 'equals', value: 'apple' }];
        const res = operatorTable.getFilteredData();
        expect(res.length).toBe(1);
    });

    test('TD-1.7: globalSearch matches formatted date/datetime', () => {
        const dateTable = new AdvancedTable('table-container', {
            data: [{ id: 1, createdAt: '2025-12-17T10:00:00', dob: '1990-01-01' }],
            columns: [
                { key: 'createdAt', label: 'Created', type: 'datetime' },
                { key: 'dob', label: 'DOB', type: 'date' }
            ]
        });

        dateTable.globalSearchTerm = '2025';
        let result = dateTable.getFilteredData();
        expect(result.length).toBe(1);

        dateTable.globalSearchTerm = '1990';
        result = dateTable.getFilteredData();
        expect(result.length).toBe(1);

        dateTable.globalSearchTerm = 'NotFound';
        result = dateTable.getFilteredData();
        expect(result.length).toBe(0);
    });
});

