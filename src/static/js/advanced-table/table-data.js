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

    let result = this.applyFilter(row[this.filters[0].column], this.filters[0]);

    for (let i = 1; i < this.filters.length; i++) {
        const filter = this.filters[i];
        const currentResult = this.applyFilter(row[filter.column], filter);

        if (filter.logic === 'AND') {
            result = result && currentResult;
        } else if (filter.logic === 'OR') {
            result = result || currentResult;
        }
    }

    return result;
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
    return data;
};

AdvancedTable.prototype.globalSearch = function (searchTerm) {
    try {
        if (!searchTerm) {
            this.globalSearchTerm = null;
            this.globalSearchDisplay = '';
            this.currentPage = 1;
            this.updateTable(); // Use updateTable instead of render
            return;
        }

        this.globalSearchDisplay = searchTerm;
        this.globalSearchTerm = searchTerm.toLowerCase();

        this.currentPage = 1;
        this.updateTable(); // Use updateTable instead of render
    } catch (error) {
        console.error('Global search error:', error);
        this.globalSearchTerm = null;
        this.globalSearchDisplay = '';
        this.updateTable(); // Use updateTable instead of render
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
};