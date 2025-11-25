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

        // Store saved configurations to persist through renders
        this.savedConfigs = [];
        this.selectedConfigId = null;

        // Store default state for full reset capability
        this.defaultState = {
            columnOrder: [...this.columnOrder],
            hiddenColumns: new Set(this.hiddenColumns),
            currentSort: { ...this.currentSort },
            filters: {}
        };

        // Debounce timer for global search
        this.searchDebounceTimer = null;

        // Store both original and lowercase search term
        this.globalSearchTerm = null; // Lowercase for comparison
        this.globalSearchDisplay = ''; // Original case for display

        this.init();
    }

    init() {
        // Store instance reference globally BEFORE rendering
        window.advTable = this;
        this.render();
        this.loadConfiguration();
    }

    render() {
        const tableId = this.container.id || 'advTable';

        // Preserve search input value before render (original case for display)
        const currentSearchValue = this.globalSearchDisplay || '';

        this.container.innerHTML = `
            <div class="advanced-table-wrapper">
                <div class="table-controls">
                    <div class="table-actions">
                        <button class="btn btn-sm btn-outline-secondary" data-action="showColumnManager">
                            <i class="fas fa-columns"></i> Columns
                        </button>
                        <button class="btn btn-sm btn-outline-primary" data-action="showFilterManager">
                            <i class="fas fa-filter"></i> Filters
                        </button>
                        <button class="btn btn-sm btn-outline-danger" data-action="clearAllFilters">
                            <i class="fas fa-eraser"></i> Clear Filters
                        </button>
                        <button class="btn btn-sm btn-outline-success" data-action="exportData">
                            <i class="fas fa-download"></i> Export CSV
                        </button>
                        <div class="btn-group">
                            <button class="btn btn-sm btn-outline-info" data-action="saveConfiguration">
                                <i class="fas fa-save"></i> Save View
                            </button>
                            <select class="form-select form-select-sm" id="savedConfigsDropdown" style="max-width: 200px;">
                                <option value="" disabled selected>Select saved view...</option>
                            </select>
                        </div>
                    </div>
                    <div class="table-search">
                        <input type="text" class="form-control form-control-sm" placeholder="Search all columns..."
                               id="globalSearchInput" value="${currentSearchValue}">
                        <button class="btn btn-sm" type="button" id="clearSearchBtn" style="display: ${currentSearchValue ? 'block' : 'none'};">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
                <div class="table-responsive" style="max-height: 100%; overflow-y: auto; overflow-x: auto;">
                    <table class="table table-striped table-hover advanced-table" style="width: max-content; min-width: 100%;">
                        <thead class="table-dark sticky-top">
                            ${this.renderHeader()}
                        </thead>
                        <tbody>
                            ${this.renderBody()}
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        // Re-attach event listeners after DOM update
        this.attachEventListeners();

        // Repopulate config dropdown after render (it was destroyed by innerHTML)
        this.populateConfigDropdown();
    }

    renderHeader() {
        return `<tr>${this.columnOrder
            .filter(key => !this.hiddenColumns.has(key))
            .map(key => {
                const col = this.columns.find(c => c.key === key);
                const sortIcon = this.getSortIcon(key);
                return `
                    <th class="sortable" data-column="${key}">
                        ${col.label} ${sortIcon}
                    </th>
                `;
            }).join('')}</tr>`;
    }

    renderBody() {
        const filteredData = this.getFilteredData();
        const paginatedData = this.getPaginatedData(filteredData);

        return paginatedData.map(row => `
            <tr>
                ${this.columnOrder
                .filter(key => !this.hiddenColumns.has(key))
                .map(key => `<td>${this.formatCellValue(row[key], key, row)}</td>`)
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
        this.selectedConfigId = null; // Reset selected config since state changed
        this.currentPage = 1;
        this.render();
    }

    getFilteredData() {
        const filtered = this.data.filter(row => {
            // Apply global search
            if (this.globalSearchTerm) {
                // Build searchable text using FORMATTED values (what user sees), not raw data
                const searchableText = this.columnOrder
                    .filter(key => !this.hiddenColumns.has(key))
                    .map(key => {
                        // Use formatCellValue to get the displayed value, not raw data
                        const rawValue = row[key];
                        const col = this.columns.find(c => c.key === key);

                        // Format the value the same way it's displayed in the table
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

                const matches = searchableText.includes(this.globalSearchTerm);

                // Debug logging
                if (this.globalSearchTerm && this.globalSearchTerm.length < 3) {
                    console.log(`Row ${row.id}: "${searchableText.substring(0, 100)}..." ${matches ? 'MATCHES' : 'NO MATCH'} "${this.globalSearchTerm}"`);
                }

                if (!matches) return false;
            }

            // Apply column filters with AND/OR logic
            if (Object.keys(this.filters).length > 0) {
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
            // Handle empty search
            if (!searchTerm) {
                this.globalSearchTerm = null;
                this.globalSearchDisplay = '';
                this.currentPage = 1;
                this.render();
                return;
            }

            // Store original case for display, lowercase for comparison
            this.globalSearchDisplay = searchTerm;
            this.globalSearchTerm = searchTerm.toLowerCase();

            this.currentPage = 1;
            this.render();
        } catch (error) {
            console.error('Global search error:', error);
            // Don't break the UI if search fails
            this.globalSearchTerm = null;
            this.globalSearchDisplay = '';
            this.render();
        }
    }

    formatCellValue(value, column, row) {
        if (value === null || value === undefined) value = '';

        const col = this.columns.find(c => c.key === column);

        // Use custom render function if provided
        if (col && col.render && typeof col.render === 'function') {
            return col.render(value, row);
        }

        // Default formatting based on type
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

        if (!modal) {
            console.error('Column Manager modal not found in DOM');
            return;
        }
        if (!columnList) {
            console.error('Column List element not found in DOM');
            return;
        }

        // Populate column list
        columnList.innerHTML = '';
        this.columnOrder.forEach(key => {
            const col = this.columns.find(c => c.key === key);
            if (!col) return;

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

            // Add drag event listeners
            listItem.addEventListener('dragstart', (e) => {
                listItem.classList.add('dragging');
                e.dataTransfer.effectAllowed = 'move';
                e.dataTransfer.setData('text/plain', key);
            });

            listItem.addEventListener('dragend', () => {
                listItem.classList.remove('dragging');
            });

            listItem.addEventListener('dragover', (e) => {
                e.preventDefault();
                const dragging = columnList.querySelector('.dragging');
                const afterElement = this.getDragAfterElement(columnList, e.clientY);

                if (afterElement == null) {
                    columnList.appendChild(dragging);
                } else {
                    columnList.insertBefore(dragging, afterElement);
                }
            });

            columnList.appendChild(listItem);
        });

        modal.classList.add('show');
        console.log('Column Manager modal displayed');
    }

    getDragAfterElement(container, y) {
        const draggableElements = [...container.querySelectorAll('.column-item:not(.dragging)')];

        return draggableElements.reduce((closest, child) => {
            const box = child.getBoundingClientRect();
            const offset = y - box.top - box.height / 2;

            if (offset < 0 && offset > closest.offset) {
                return { offset: offset, element: child };
            } else {
                return closest;
            }
        }, { offset: Number.NEGATIVE_INFINITY }).element;
    }

    showFilterManager() {
        const modal = document.getElementById('filterManager');
        const filterRows = document.getElementById('filterRows');

        if (!modal) {
            console.error('Filter Manager modal not found in DOM');
            return;
        }
        if (!filterRows) {
            console.error('Filter Rows element not found in DOM');
            return;
        }

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
                <select class="form-select filter-column">
                    <option value="">Select Column</option>
                    ${this.columns.map(col =>
                `<option value="${col.key}" ${col.key === column ? 'selected' : ''}>${col.label}</option>`
            ).join('')}
                </select>
                <select class="form-select filter-operator">
                    <option value="contains" ${filter.operator === 'contains' ? 'selected' : ''}>Contains</option>
                    <option value="not_contains" ${filter.operator === 'not_contains' ? 'selected' : ''}>Does Not Contain</option>
                    <option value="equals" ${filter.operator === 'equals' ? 'selected' : ''}>Equals</option>
                    <option value="not_equals" ${filter.operator === 'not_equals' ? 'selected' : ''}>Not Equals</option>
                    <option value="starts_with" ${filter.operator === 'starts_with' ? 'selected' : ''}>Starts With</option>
                    <option value="ends_with" ${filter.operator === 'ends_with' ? 'selected' : ''}>Ends With</option>
                </select>
                <input type="text" class="form-control filter-value" placeholder="Filter value" value="${filter.value || ''}">
                <button type="button" class="btn btn-outline-danger btn-sm" onclick="this.closest('.filter-row').remove()">
                    <i class="fas fa-trash"></i>
                </button>
            `;
            filterRows.appendChild(filterRow);
        });

        // Add one empty row if no filters exist
        if (filterEntries.length === 0) {
            this.addFilterRow();
        }

        modal.classList.add('show');
        console.log('Filter Manager modal displayed');
    }

    closeColumnManager() {
        document.getElementById('columnManager').classList.remove('show');
    }

    closeFilterManager() {
        document.getElementById('filterManager').classList.remove('show');
    }

    applyColumnChanges() {
        const columnItems = document.querySelectorAll('#columnList .column-item');
        const newOrder = [];
        const newHidden = new Set();

        columnItems.forEach(item => {
            const columnKey = item.dataset.column;
            newOrder.push(columnKey);
            if (!item.querySelector('input[type="checkbox"]').checked) {
                newHidden.add(columnKey);
            }
        });

        this.columnOrder = newOrder;
        this.hiddenColumns = newHidden;

        // Reset selected config since state has changed
        this.selectedConfigId = null;

        this.render();
        this.closeColumnManager();
    }

    applyFilters() {
        const filterRows = document.querySelectorAll('#filterRows .filter-row');
        this.filters = {};

        console.log('Applying filters, found rows:', filterRows.length);

        filterRows.forEach(row => {
            const column = row.querySelector('.filter-column')?.value;
            const operator = row.querySelector('.filter-operator')?.value;
            const value = row.querySelector('.filter-value')?.value;

            console.log('Filter row:', { column, operator, value });

            if (column && value) {
                this.filters[column] = { operator, value };
            }
        });

        console.log('Filters applied:', this.filters);

        // Reset selected config since state has changed
        this.selectedConfigId = null;
        this.currentPage = 1; // Reset to first page
        this.render();
        this.closeFilterManager();
    }

    addFilterRow() {
        const filterRows = document.getElementById('filterRows');
        const existingRows = filterRows.querySelectorAll('.filter-row');

        // Add AND/OR logic if this is not the first row
        if (existingRows.length > 0) {
            const logicRow = document.createElement('div');
            logicRow.className = 'filter-logic';
            const logicId = Date.now(); // Unique ID for radio buttons
            logicRow.innerHTML = `
                <div class="btn-group" role="group">
                    <input type="radio" class="btn-check" name="logic${logicId}" id="and${logicId}" value="and" checked>
                    <label class="btn btn-outline-primary btn-sm" for="and${logicId}">AND</label>
                    <input type="radio" class="btn-check" name="logic${logicId}" id="or${logicId}" value="or">
                    <label class="btn btn-outline-primary btn-sm" for="or${logicId}">OR</label>
                </div>
            `;
            filterRows.appendChild(logicRow);
        }

        const filterRow = document.createElement('div');
        filterRow.className = 'filter-row';
        filterRow.innerHTML = `
            <select class="form-select filter-column">
                <option value="">Select Column</option>
                ${this.columns.map(col =>
            `<option value="${col.key}">${col.label}</option>`
        ).join('')}
            </select>
            <select class="form-select filter-operator">
                <option value="contains">Contains</option>
                <option value="not_contains">Does Not Contain</option>
                <option value="equals">Equals</option>
                <option value="not_equals">Not Equals</option>
                <option value="starts_with">Starts With</option>
                <option value="ends_with">Ends With</option>
            </select>
            <input type="text" class="form-control filter-value" placeholder="Filter value">
            <button type="button" class="btn btn-outline-danger btn-sm remove-filter-btn">
                <i class="fas fa-trash"></i>
            </button>
        `;

        // Add event listener for remove button
        const removeBtn = filterRow.querySelector('.remove-filter-btn');
        removeBtn.addEventListener('click', function () {
            const row = this.closest('.filter-row');
            // Also remove the previous logic element if it exists
            const prevSibling = row.previousElementSibling;
            if (prevSibling && prevSibling.classList.contains('filter-logic')) {
                prevSibling.remove();
            }
            row.remove();
        });

        filterRows.appendChild(filterRow);
    }

    clearAllFilters() {
        // Use full table reset instead of just clearing filters
        this.resetTableState();
        this.closeFilterManager();
    }

    resetTableState() {
        // Reset to default state
        this.columnOrder = [...this.defaultState.columnOrder];
        this.hiddenColumns = new Set(this.defaultState.hiddenColumns);
        this.currentSort = { ...this.defaultState.currentSort };
        this.filters = {};
        this.selectedConfigId = null;
        this.globalSearchTerm = null;
        this.globalSearchDisplay = '';
        this.currentPage = 1;
        this.render();
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

        // Check for duplicate names
        const duplicate = this.savedConfigs.find(c => c.config_name.toLowerCase() === name.trim().toLowerCase());
        if (duplicate) {
            ToastNotification.error(`Configuration name "${name.trim()}" already exists. Please choose a different name.`);
            return;
        }

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
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Silent success - just update dropdown (no toast)
                    this.selectedConfigId = data.id;
                    this.loadConfiguration();
                } else {
                    ToastNotification.error('Failed to save configuration: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error saving configuration:', error);
                ToastNotification.error('Error saving configuration: ' + error.message);
            });
    }

    loadConfiguration() {
        fetch('/api/table-config/' + this.pageName)
            .then(response => {
                if (!response.ok) {
                    // Not an error - just no configurations yet
                    if (response.status === 404 || response.status === 401) {
                        throw new Error('NO_CONFIGS');
                    }
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(configs => {
                // Store configurations in instance variable
                this.savedConfigs = configs || [];

                // Populate dropdown with saved configurations
                this.populateConfigDropdown();

                // Apply default configuration if exists (no toast for default load)
                const defaultConfig = configs.find(c => c.is_default);
                if (defaultConfig) {
                    this.applyConfiguration(defaultConfig);
                    // Don't show toast for default configuration auto-load
                }
            })
            .catch(error => {
                if (error.message === 'NO_CONFIGS') {
                    console.log('No saved configurations available');
                } else {
                    console.error('Error loading configurations:', error);
                    ToastNotification.warning('Could not load saved configurations');
                }
                this.savedConfigs = [];
            });
    }

    populateConfigDropdown() {
        const dropdown = document.getElementById('savedConfigsDropdown');
        if (!dropdown) return;

        // Clear dropdown
        dropdown.innerHTML = '';

        // Check if we have any saved configs
        const hasConfigs = Array.isArray(this.savedConfigs) && this.savedConfigs.length > 0;

        if (!hasConfigs) {
            // Scenario 1: No saved configs - disable dropdown and show placeholder
            const placeholder = document.createElement('option');
            placeholder.value = '';
            placeholder.selected = true;
            placeholder.disabled = true;
            placeholder.textContent = 'Select saved view...';
            dropdown.appendChild(placeholder);
            dropdown.disabled = true; // Disable the entire dropdown
            dropdown.style.color = '#999'; // Gray text
            return; // Exit early
        }

        // Enable dropdown since we have configs
        dropdown.disabled = false;

        // If nothing is selected, add a hidden placeholder option to show text in button
        if (this.selectedConfigId === null) {
            const placeholder = document.createElement('option');
            placeholder.value = '';
            placeholder.selected = true;
            placeholder.disabled = true;
            placeholder.hidden = true; // Hidden from dropdown list
            placeholder.textContent = 'Select saved view...';
            placeholder.style.display = 'none'; // Extra hiding
            dropdown.appendChild(placeholder);
        }

        // Add all saved configs (they will appear in dropdown list)
        this.savedConfigs.forEach(config => {
            const option = document.createElement('option');
            option.value = config.id;

            // Full label for title attribute
            const fullLabel = config.config_name + (config.is_default ? ' (Default)' : '');

            // Truncate if longer than 28 characters
            const displayLabel = fullLabel.length > 28
                ? fullLabel.substring(0, 27) + '…'
                : fullLabel;

            option.textContent = displayLabel;
            option.title = fullLabel; // Tooltip shows full name

            // Mark current selection
            if (config.id === this.selectedConfigId) {
                option.selected = true;
                option.className = 'current-config';
            } else {
                option.className = 'config-option';
            }

            dropdown.appendChild(option);
        });

        // Update dropdown button color
        if (this.selectedConfigId === null) {
            dropdown.style.color = '#999'; // Gray for placeholder
        } else {
            dropdown.style.color = '#212529'; // Black for selected
        }
    }

    loadSavedConfigurationsDropdown(configs) {
        // This method is deprecated - use populateConfigDropdown instead
        // Keeping for backward compatibility
        this.savedConfigs = configs || [];
        this.populateConfigDropdown();
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
        // Convert table ID to page name (e.g., 'usersTable' -> 'users', 'mosTable' -> 'maintenance_orders')
        let pagePath = this.pageName.replace('Table', '');

        // Special cases for routes that don't match table names
        if (pagePath === 'mos') {
            pagePath = 'maintenance_orders';
        } else if (pagePath === 'spareParts') {
            pagePath = 'spare_parts';
        }

        window.location.href = `/${pagePath}/${id}`;
    }

    attachEventListeners() {
        // Bind all buttons with data-action attributes
        const buttons = this.container.querySelectorAll('[data-action]');
        buttons.forEach(button => {
            const action = button.getAttribute('data-action');

            if (action === 'showColumnManager') {
                button.addEventListener('click', () => this.showColumnManager());
            } else if (action === 'showFilterManager') {
                button.addEventListener('click', () => this.showFilterManager());
            } else if (action === 'clearAllFilters') {
                button.addEventListener('click', () => this.resetTableState());
            } else if (action === 'exportData') {
                button.addEventListener('click', () => this.exportData('csv'));
            } else if (action === 'saveConfiguration') {
                button.addEventListener('click', () => this.saveConfiguration());
            }
            // Note: globalSearch is handled separately below since it's an input, not a button
        });

        // Bind global search input specifically
        const searchInput = document.getElementById('globalSearchInput');
        const clearSearchBtn = document.getElementById('clearSearchBtn');

        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                const value = e.target.value; // Keep original case for display

                // Show/hide clear button based on input value
                if (clearSearchBtn) {
                    clearSearchBtn.style.display = value ? 'block' : 'none';
                }

                // Debounce the search to avoid excessive re-renders
                if (this.searchDebounceTimer) {
                    clearTimeout(this.searchDebounceTimer);
                }
                this.searchDebounceTimer = setTimeout(() => {
                    this.globalSearch(value); // Pass original case value
                }, 450); // debounce [ms]
            });
        }

        // Bind clear search button
        if (clearSearchBtn) {
            clearSearchBtn.addEventListener('click', () => {
                if (searchInput) {
                    searchInput.value = '';
                    clearSearchBtn.style.display = 'none';
                    this.globalSearch('');
                }
            });
        }

        // Bind saved config dropdown for loading configurations
        const dropdown = document.getElementById('savedConfigsDropdown');
        if (dropdown) {
            dropdown.addEventListener('change', (e) => {
                const configId = parseInt(e.target.value);
                if (configId) {
                    const config = this.savedConfigs.find(c => c.id === configId);
                    if (config) {
                        this.selectedConfigId = configId;
                        this.applyConfiguration(config);
                        // Silent load - no toast notification
                    }
                } else {
                    // Reset to default view
                    this.selectedConfigId = null;
                }
            });
        }

        // Bind column headers for sorting
        const headers = this.container.querySelectorAll('.advanced-table th.sortable');
        headers.forEach(header => {
            header.addEventListener('click', () => {
                const column = header.getAttribute('data-column');
                this.sort(column);
            });
        });

        // Bind table rows for click navigation
        const rows = this.container.querySelectorAll('.advanced-table tbody tr');
        rows.forEach((row, index) => {
            row.style.cursor = 'pointer';
            row.addEventListener('click', () => {
                const filteredData = this.getFilteredData();
                const paginatedData = this.getPaginatedData(filteredData);
                const rowData = paginatedData[index];
                if (rowData && rowData.id) {
                    this.rowClick(rowData.id);
                }
            });
        });
    }
}

// Toast Notification Utility
class ToastNotification {
    static show(message, type = 'info', duration = 5000) {
        const container = document.getElementById('toastContainer');
        if (!container) {
            console.error('Toast container not found');
            return;
        }

        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };

        const titles = {
            success: 'Success',
            error: 'Error',
            warning: 'Warning',
            info: 'Info'
        };

        const toastId = 'toast-' + Date.now();
        const toast = document.createElement('div');
        toast.className = 'toast show'; // Add 'show' class immediately
        toast.id = toastId;
        toast.style.opacity = '1'; // Force visibility
        toast.innerHTML = `
            <div class="toast-header toast-${type}">
                <i class="toast-icon ${icons[type]}"></i>
                <strong class="toast-title">${titles[type]}</strong>
                <button type="button" class="toast-close" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <div class="toast-body">${message}</div>
        `;

        // Add close button handler
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => {
            ToastNotification.hide(toastId);
        });

        container.appendChild(toast);

        console.log('Toast created:', toastId, 'Duration:', duration, 'ms');

        // Auto-hide after duration
        if (duration > 0) {
            setTimeout(() => {
                console.log('Auto-hiding toast:', toastId);
                ToastNotification.hide(toastId);
            }, duration);
        }
    }

    static hide(toastId) {
        const toast = document.getElementById(toastId);
        if (toast) {
            console.log('Hiding toast:', toastId);
            toast.classList.add('hiding');
            toast.classList.remove('show');
            setTimeout(() => {
                toast.remove();
                console.log('Toast removed:', toastId);
            }, 300);
        }
    }

    static success(message, duration = 5000) {
        ToastNotification.show(message, 'success', duration);
    }

    static error(message, duration = 7000) {
        ToastNotification.show(message, 'error', duration);
    }

    static warning(message, duration = 6000) {
        ToastNotification.show(message, 'warning', duration);
    }

    static info(message, duration = 5000) {
        ToastNotification.show(message, 'info', duration);
    }
}

// Global helper function to initialize the advanced table
// This is the function that templates will call
function initAdvancedTable(containerId, data, columns, pageSize = 25) {
    console.log('initAdvancedTable called with:', containerId, 'data items:', data?.length);

    // Create a container if it doesn't exist
    let container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container with ID '${containerId}' not found`);
        return null;
    }

    // Initialize the advanced table
    const table = new AdvancedTable(containerId, {
        data: data,
        columns: columns,
        pageName: containerId,
        pageSize: pageSize
    });

    // Store reference globally so other functions can access it
    // This MUST be set here for the onclick handlers in the rendered HTML to work
    window.advTable = table;

    // Also set it as a global variable (without window prefix) for compatibility
    if (typeof advTable === 'undefined') {
        window.advTable = table;
    }

    console.log('Advanced table initialized, window.advTable is:', window.advTable);

    return table;
}

// Global instance for easy access
let advTable;
