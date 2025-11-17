class AdvancedTable {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.data = options.data || [];
        this.columns = options.columns || [];
        this.pageName = options.pageName || 'default';
        this.currentSort = { column: null, direction: 'asc' };
        this.filters = {};
        this.hiddenColumns = new Set();
        this.columnOrder = [...this.columns.map(col => col.key)];
        this.currentPage = 1;
        this.pageSize = options.pageSize || 25;
        
        this.init();
    }

    init() {
        this.render();
        this.attachEventListeners();
        this.loadConfiguration();
    }

    render() {
        this.container.innerHTML = `
            <div class="advanced-table-wrapper">
                <div class="table-controls">
                    <div class="table-actions">
                        <button class="btn btn-sm btn-outline-secondary" onclick="advTable.showColumnManager()">
                            <i class="fas fa-columns"></i> Columns
                        </button>
                        <button class="btn btn-sm btn-outline-secondary" onclick="advTable.showFilterManager()">
                            <i class="fas fa-filter"></i> Filters
                        </button>
                        <button class="btn btn-sm btn-outline-secondary" onclick="advTable.exportData('csv')">
                            <i class="fas fa-download"></i> Export CSV
                        </button>
                        <div class="btn-group">
                            <button class="btn btn-sm btn-outline-secondary" onclick="advTable.saveConfiguration()">
                                <i class="fas fa-save"></i> Save View
                            </button>
                            <select class="form-select form-select-sm" id="savedConfigsDropdown" onchange="loadSelectedConfiguration()" style="max-width: 200px;">
                                <option value="">Select saved view...</option>
                            </select>
                        </div>
                    </div>
                    <div class="table-search">
                        <input type="text" class="form-control form-control-sm" placeholder="Search all columns..." 
                               oninput="advTable.globalSearch(this.value)" id="globalSearchInput">
                    </div>
                </div>
                <div class="table-responsive" style="max-height: 75vh; overflow-y: auto; overflow-x: auto;">
                    <table class="table table-striped table-hover advanced-table" style="width: max-content; min-width: 100%;">
                        <thead class="table-dark sticky-top">
                            ${this.renderHeader()}
                        </thead>
                        <tbody>
                            ${this.renderBody()}
                        </tbody>
                    </table>
                </div>
                <div class="table-pagination">
                    ${this.renderPagination()}
                </div>
            </div>
        `;
    }

    renderHeader() {
        return `<tr>${this.columnOrder
            .filter(key => !this.hiddenColumns.has(key))
            .map(key => {
                const col = this.columns.find(c => c.key === key);
                const sortIcon = this.getSortIcon(key);
                return `
                    <th class="sortable" data-column="${key}" onclick="advTable.sort('${key}')">
                        ${col.label} ${sortIcon}
                    </th>
                `;
            }).join('')}</tr>`;
    }

    renderBody() {
        const filteredData = this.getFilteredData();
        const paginatedData = this.getPaginatedData(filteredData);
        
        return paginatedData.map(row => `
            <tr onclick="advTable.rowClick(${row.id})">
                ${this.columnOrder
                    .filter(key => !this.hiddenColumns.has(key))
                    .map(key => `<td>${this.formatCellValue(row[key], key)}</td>`)
                    .join('')}
            </tr>
        `).join('');
    }

    renderPagination() {
        // Pagination removed
        return '';
    }

    getSortIcon(column) {
        if (this.currentSort.column !== column) return '<i class="fas fa-sort text-muted"></i>';
        return this.currentSort.direction === 'asc' 
            ? '<i class="fas fa-sort-up text-primary"></i>' 
            : '<i class="fas fa-sort-down text-primary"></i>';
    }

    sort(column) {
        if (this.currentSort.column === column) {
            this.currentSort.direction = this.currentSort.direction === 'asc' ? 'desc' : 'asc';
        } else {
            this.currentSort.column = column;
            this.currentSort.direction = 'asc';
        }
        this.currentPage = 1;
        this.render();
    }

    getFilteredData() {
        return this.data.filter(row => {
            // Apply global search
            if (this.globalSearchTerm) {
                const searchableText = this.columnOrder
                    .filter(key => !this.hiddenColumns.has(key))
                    .map(key => (row[key] || '').toString().toLowerCase())
                    .join(' ');
                if (!searchableText.includes(this.globalSearchTerm)) return false;
            }
            
            // Apply column filters with AND/OR logic
            if (Object.keys(this.filters).length > 0) {
                return this.applyFiltersWithLogic(row);
            }
            return true;
        }).sort((a, b) => {
            if (!this.currentSort.column) return 0;
            
            const aVal = a[this.currentSort.column] || '';
            const bVal = b[this.currentSort.column] || '';
            
            const comparison = aVal.toString().localeCompare(bVal.toString(), undefined, { numeric: true });
            return this.currentSort.direction === 'asc' ? comparison : -comparison;
        });
    }

    applyFiltersWithLogic(row) {
        const filterEntries = Object.entries(this.filters);
        if (filterEntries.length === 0) return true;
        
        // For now, use AND logic (can be enhanced later for OR)
        return filterEntries.every(([column, filter]) => 
            this.applyFilter(row[column], filter)
        );
    }

    getPaginatedData(data) {
        // Return all data since pagination is removed
        return data;
    }

    applyFilter(value, filter) {
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
    }

    globalSearch(searchTerm) {
        try {
            this.globalSearchTerm = searchTerm ? searchTerm.toLowerCase().trim() : null;
            this.currentPage = 1;
            this.render();
        } catch (error) {
            console.error('Global search error:', error);
        }
    }

    formatCellValue(value, column) {
        if (value === null || value === undefined) return '';
        
        const col = this.columns.find(c => c.key === column);
        if (col && col.type === 'date' && value) {
            return new Date(value).toLocaleDateString();
        }
        if (col && col.type === 'datetime' && value) {
            return new Date(value).toLocaleString();
        }
        return value;
    }

    showColumnManager() {
        const modal = document.getElementById('columnManager');
        const columnList = document.getElementById('columnList');
        
        // Populate column list
        columnList.innerHTML = '';
        this.columnOrder.forEach(key => {
            const col = this.columns.find(c => c.key === key);
            const isVisible = !this.hiddenColumns.has(key);
            
            const listItem = document.createElement('li');
            listItem.className = 'column-item';
            listItem.dataset.column = key;
            listItem.draggable = true;
            listItem.innerHTML = `
                <input type="checkbox" ${isVisible ? 'checked' : ''}>
                <span>${col.label}</span>
                <i class="fas fa-grip-vertical drag-handle"></i>
            `;
            columnList.appendChild(listItem);
        });
        
        modal.classList.add('show');
        
        // Initialize drag and drop
        setTimeout(() => {
            if (typeof initializeDragAndDrop === 'function') {
                initializeDragAndDrop();
            }
        }, 100);
    }

    showFilterManager() {
        const modal = document.getElementById('filterManager');
        const filterRows = document.getElementById('filterRows');
        
        // Clear existing display
        filterRows.innerHTML = '';
        
        // Add existing filters
        const filterEntries = Object.entries(this.filters);
        filterEntries.forEach(([column, filter], index) => {
            if (index > 0) {
                // Add AND/OR logic for subsequent filters
                const logicRow = document.createElement('div');
                logicRow.className = 'filter-logic';
                logicRow.innerHTML = `
                    <div class="btn-group" role="group">
                        <input type="radio" class="btn-check" name="logic${index}" id="and${index}" value="and" checked>
                        <label class="btn btn-outline-primary btn-sm" for="and${index}">AND</label>
                        <input type="radio" class="btn-check" name="logic${index}" id="or${index}" value="or">
                        <label class="btn btn-outline-primary btn-sm" for="or${index}">OR</label>
                    </div>
                `;
                filterRows.appendChild(logicRow);
            }
            
            const filterRow = document.createElement('div');
            filterRow.className = 'filter-row';
            filterRow.innerHTML = `
                <select class="form-select">
                    <option value="">Select Column</option>
                    ${this.columns.map(col => 
                        `<option value="${col.key}" ${col.key === column ? 'selected' : ''}>${col.label}</option>`
                    ).join('')}
                </select>
                <select class="form-select">
                    <option value="contains" ${filter.operator === 'contains' ? 'selected' : ''}>Contains</option>
                    <option value="not_contains" ${filter.operator === 'not_contains' ? 'selected' : ''}>Does Not Contain</option>
                    <option value="equals" ${filter.operator === 'equals' ? 'selected' : ''}>Equals</option>
                    <option value="not_equals" ${filter.operator === 'not_equals' ? 'selected' : ''}>Not Equals</option>
                    <option value="starts_with" ${filter.operator === 'starts_with' ? 'selected' : ''}>Starts With</option>
                    <option value="ends_with" ${filter.operator === 'ends_with' ? 'selected' : ''}>Ends With</option>
                </select>
                <input type="text" class="form-control" placeholder="Filter value" value="${filter.value || ''}">
                <button type="button" class="btn btn-outline-danger btn-sm" onclick="removeFilterRow(this)">
                    <i class="fas fa-trash"></i>
                </button>
            `;
            filterRows.appendChild(filterRow);
        });
        
        // Add one empty row if no filters exist
        if (filterEntries.length === 0) {
            addFilterRow();
        }
        
        modal.classList.add('show');
    }

    addFilterRowWithData(column, operator, value) {
        const filterRows = document.getElementById('filterRows');
        const rowCount = filterRows.children.length;
        
        const filterRow = document.createElement('div');
        filterRow.className = 'filter-row';
        filterRow.innerHTML = `
            <select class="form-select">
                <option value="">Select Column</option>
                ${this.columns.map(col => 
                    `<option value="${col.key}" ${col.key === column ? 'selected' : ''}>${col.label}</option>`
                ).join('')}
            </select>
            <select class="form-select">
                <option value="contains" ${operator === 'contains' ? 'selected' : ''}>Contains</option>
                <option value="not_contains" ${operator === 'not_contains' ? 'selected' : ''}>Does Not Contain</option>
                <option value="equals" ${operator === 'equals' ? 'selected' : ''}>Equals</option>
                <option value="not_equals" ${operator === 'not_equals' ? 'selected' : ''}>Not Equals</option>
                <option value="starts_with" ${operator === 'starts_with' ? 'selected' : ''}>Starts With</option>
                <option value="ends_with" ${operator === 'ends_with' ? 'selected' : ''}>Ends With</option>
            </select>
            <input type="text" class="form-control" placeholder="Filter value" value="${value || ''}">
            <button type="button" class="btn btn-outline-danger btn-sm" onclick="removeFilterRow(this)">
                <i class="fas fa-trash"></i>
            </button>
        `;
        
        filterRows.appendChild(filterRow);
    }

    exportData(format) {
        const filteredData = this.getFilteredData();
        if (format === 'csv') {
            this.exportCSV(filteredData);
        }
    }

    exportCSV(data) {
        const visibleColumns = this.columnOrder.filter(key => !this.hiddenColumns.has(key));
        const headers = visibleColumns.map(key => this.columns.find(c => c.key === key).label);
        
        let csv = headers.join(',') + '\n';
        data.forEach(row => {
            const values = visibleColumns.map(key => {
                const value = row[key] || '';
                return `"${value.toString().replace(/"/g, '""')}"`;
            });
            csv += values.join(',') + '\n';
        });
        
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${this.pageName}_export.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
    }

    saveConfiguration() {
        const name = prompt('Enter configuration name:');
        if (!name || !name.trim()) return;
        
        const config = {
            config_name: name.trim(),
            column_order: JSON.stringify(this.columnOrder),
            hidden_columns: JSON.stringify(Array.from(this.hiddenColumns)),
            filters: JSON.stringify(this.filters),
            sort_config: JSON.stringify(this.currentSort),
            is_default: false
        };
        
        const csrfToken = document.querySelector('meta[name=csrf-token]')?.getAttribute('content');
        fetch('/api/table-config/' + this.pageName, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(config)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Configuration saved successfully!');
                this.loadConfiguration(); // Refresh dropdown
            } else {
                alert('Error saving configuration: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error saving configuration: ' + error.message);
        });
    }

    loadConfiguration() {
        fetch('/api/table-config/' + this.pageName)
            .then(response => {
                if (response.ok) {
                    return response.json();
                }
                throw new Error('Failed to load configurations');
            })
            .then(configs => {
                // Load saved configurations into dropdown
                this.loadSavedConfigurationsDropdown(configs);
                
                // Apply default configuration if exists
                const defaultConfig = configs.find(c => c.is_default);
                if (defaultConfig) {
                    this.applyConfiguration(defaultConfig);
                }
            })
            .catch(error => {
                console.log('No saved configurations available:', error);
            });
    }

    loadSavedConfigurationsDropdown(configs) {
        const dropdown = document.getElementById('savedConfigsDropdown');
        if (dropdown && Array.isArray(configs)) {
            dropdown.innerHTML = '<option value="">Select saved view...</option>';
            configs.forEach(config => {
                const option = document.createElement('option');
                option.value = config.id;
                option.textContent = config.config_name + (config.is_default ? ' (Default)' : '');
                dropdown.appendChild(option);
            });
        }
    }

    applyConfiguration(config) {
        if (config.column_order) this.columnOrder = JSON.parse(config.column_order);
        if (config.hidden_columns) this.hiddenColumns = new Set(JSON.parse(config.hidden_columns));
        if (config.filters) this.filters = JSON.parse(config.filters);
        if (config.sort_config) this.currentSort = JSON.parse(config.sort_config);
        this.render();
    }

    goToPage(page) {
        const filteredData = this.getFilteredData();
        const totalPages = Math.ceil(filteredData.length / this.pageSize);
        
        if (page >= 1 && page <= totalPages) {
            this.currentPage = page;
            this.render();
        }
    }

    rowClick(id) {
        // Navigate to detail page
        window.location.href = `/${this.pageName}/${id}`;
    }

    attachEventListeners() {
        // Additional event listeners can be added here
    }
}

// Global instance for easy access
let advTable;