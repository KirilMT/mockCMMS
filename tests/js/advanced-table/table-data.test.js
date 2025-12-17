
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
        expect(result.length).toBe(3); // Alice, David, Bob
        const names = result.map(r => r.name).sort();
        expect(names).toEqual(['Alice', 'Bob', 'David']);
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
});
