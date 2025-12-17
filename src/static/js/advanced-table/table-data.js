// Data filtering, sorting, and search methods
AdvancedTable.prototype.getFilteredData = function () {
    const filtered = this.data.filter(row => {
        if (this.globalSearchTerm) {
            const searchableText = this.columnOrder
                .filter(key => !this.hiddenColumns.has(key))
                .map(key => {
                    const rawValue = row[key];
                    const col = this.columns.find(c => c.key === key);

                    let displayValue;
                    if (col && col.type === 'date' && rawValue) {
                        displayValue = new Date(rawValue).toLocaleDateString();
                    } else if (col && col.type === 'datetime' && rawValue) {
                        displayValue = new Date(rawValue).toLocaleString();
                    } else {
                        displayValue = (rawValue || '').toString();
                    }

                    return displayValue.toLowerCase();
                })
                .join(' ');

            if (!searchableText.includes(this.globalSearchTerm)) return false;
        }

        // Check if filters exist and apply them (array format)
        if (Array.isArray(this.filters) && this.filters.length > 0) {
            return this.applyFiltersWithLogic(row);
        }
        return true;
    });

    return filtered.sort((a, b) => {
        if (!this.currentSort.column) return 0;

        const aVal = a[this.currentSort.column] || '';
        const bVal = b[this.currentSort.column] || '';

        const comparison = aVal.toString().localeCompare(bVal.toString(), undefined, { numeric: true });
        return this.currentSort.direction === 'asc' ? comparison : -comparison;
    });
};

AdvancedTable.prototype.applyFiltersWithLogic = function (row) {
    if (!Array.isArray(this.filters) || this.filters.length === 0) {
        return true;
    }

    // Phase 1: Group filters into OR-blocks
    // Example: A OR B AND C OR D -> [[A, B], [C, D]]
    // Logic: Execute (A OR B) AND (C OR D)
    const chains = [];
    let currentChain = [];

    this.filters.forEach((filter, index) => {
        if (index === 0) {
            currentChain.push(filter);
        } else {
            // Check logic of this filter (it defines relation to previous)
            // But wait, the filter.logic property is "how this filter connects to the PREVIOUS one"
            if (filter.logic === 'AND') {
                // Start new chain
                chains.push(currentChain);
                currentChain = [filter];
            } else {
                // OR - add to current chain
                currentChain.push(filter);
            }
        }
    });
    // Push the last chain
    if (currentChain.length > 0) {
        chains.push(currentChain);
    }

    // Phase 2: Evaluate Chains (AND between chains)
    // If ANY chain returns false, the whole row is false (Short-circuit)
    for (const chain of chains) {
        // Evaluate Chain (OR between items in chain)
        // If ANY item in chain is true, chain is true
        let chainResult = false;

        for (const filter of chain) {
            if (this.applyFilter(row[filter.column], filter)) {
                chainResult = true;
                break; // Short-circuit OR
            }
        }

        if (!chainResult) {
            return false; // Chain failed, so AND fails
        }
    }

    return true; // All chains passed
};

AdvancedTable.prototype.applyFilter = function (value, filter) {
    const val = (value || '').toString().toLowerCase();
    const filterVal = filter.value.toLowerCase();

    switch (filter.operator) {
        case 'contains': return val.includes(filterVal);
        case 'not_contains': return !val.includes(filterVal);
        case 'equals': return val === filterVal;
        case 'not_equals': return val !== filterVal;
        case 'starts_with': return val.startsWith(filterVal);
        case 'ends_with': return val.endsWith(filterVal);
        default: return true;
    }
};

AdvancedTable.prototype.getPaginatedData = function (data) {
    if (!this.pageSize || this.pageSize <= 0) return data;

    const startIndex = (this.currentPage - 1) * this.pageSize;
    const endIndex = startIndex + this.pageSize;

    return data.slice(startIndex, endIndex);
};

AdvancedTable.prototype.globalSearch = function (searchTerm) {
    try {
        if (!searchTerm) {
            this.globalSearchTerm = null;
            this.globalSearchDisplay = '';
            this.currentPage = 1;
            this.updateTable();
            this.saveTableState(); // Bug #4: Persist state after clearing search
            return;
        }

        this.globalSearchDisplay = searchTerm;
        this.globalSearchTerm = searchTerm.toLowerCase();

        this.currentPage = 1;
        this.updateTable();
        this.saveTableState(); // Bug #4: Persist state after search
    } catch (error) {
        console.error('Global search error:', error);
        this.globalSearchTerm = null;
        this.globalSearchDisplay = '';
        this.updateTable();
        this.saveTableState(); // Bug #4: Persist state after error
    }
};

AdvancedTable.prototype.sort = function (column) {
    if (this.currentSort.column === column) {
        // Cycle: asc → desc → none
        if (this.currentSort.direction === 'asc') {
            this.currentSort.direction = 'desc';
        } else if (this.currentSort.direction === 'desc') {
            // Third click: remove sort
            this.currentSort.column = null;
            this.currentSort.direction = 'asc';
        }
    } else {
        // First click on new column: set to asc
        this.currentSort.column = column;
        this.currentSort.direction = 'asc';
    }
    this.selectedConfigId = null;
    this.currentPage = 1;
    this.updateTable();
    this.saveTableState(); // Bug #4: Persist state after sorting
};