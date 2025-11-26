/**
 * Sidebar functionality for Advanced Table
 * Handles sidebar toggle, section expand/collapse, and state persistence
 */

class TableSidebar {
    constructor(advancedTable) {
        this.table = advancedTable;
        this.sidebarCollapsed = localStorage.getItem('tableSidebarCollapsed') === 'true';
        this.expandedSections = JSON.parse(localStorage.getItem('tableSidebarSections') || '["filters"]');
    }

    /**
     * Generate sidebar HTML structure
     */
    generateHTML() {
        return `
            <div class="table-sidebar ${this.sidebarCollapsed ? 'collapsed' : ''}">
                <div class="sidebar-header">
                    <h6>Table Controls</h6>
                    <button class="btn-collapse" title="Collapse sidebar">
                        <i class="fas fa-chevron-left"></i>
                    </button>
                </div>

                <!-- Filters Section -->
                <div class="sidebar-section" data-section="filters">
                    <div class="section-header ${this.expandedSections.includes('filters') ? 'expanded' : ''}">
                        <i class="fas fa-filter"></i>
                        <span>Filters</span>
                        <span class="badge">0</span>
                        <i class="fas fa-chevron-down toggle-icon"></i>
                    </div>
                    <div class="section-content ${this.expandedSections.includes('filters') ? '' : 'collapsed'}">
                        <div id="filterRows">
                            <!-- Filter rows will be populated here -->
                        </div>
                        <div class="filter-actions" style="display: flex; gap: 0.5rem; margin-top: 0.75rem;">
                            <button class="btn btn-sm btn-outline-primary" id="addFilterBtn" style="flex: 1;">
                                <i class="fas fa-plus"></i> Add
                            </button>
                            <button class="btn btn-sm btn-primary" id="applyFiltersBtn" style="flex: 2;">
                                <i class="fas fa-check"></i> Apply
                            </button>
                            <button class="btn btn-sm btn-outline-danger" id="clearFiltersBtn" style="flex: 1;">
                                <i class="fas fa-times"></i> Clear
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Columns Section -->
                <div class="sidebar-section" data-section="columns">
                    <div class="section-header ${this.expandedSections.includes('columns') ? 'expanded' : ''}">
                        <i class="fas fa-columns"></i>
                        <span>Columns</span>
                        <i class="fas fa-chevron-down toggle-icon"></i>
                    </div>
                    <div class="section-content ${this.expandedSections.includes('columns') ? '' : 'collapsed'}">
                        <p class="text-muted text-center">Column management will be added in Sub-task 2.2c</p>
                    </div>
                </div>

                <!-- Saved Views Section -->
                <div class="sidebar-section" data-section="configs">
                    <div class="section-header ${this.expandedSections.includes('configs') ? 'expanded' : ''}">
                        <i class="fas fa-save"></i>
                        <span>Saved Views</span>
                        <i class="fas fa-chevron-down toggle-icon"></i>
                    </div>
                    <div class="section-content ${this.expandedSections.includes('configs') ? '' : 'collapsed'}">
                        <p class="text-muted text-center">Saved configurations will be added in Sub-task 2.2c</p>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Attach event listeners to sidebar elements
     */
    attachEventListeners() {
        // Toggle sidebar collapse
        const collapseBtn = document.querySelector('.btn-collapse');
        if (collapseBtn) {
            collapseBtn.addEventListener('click', () => this.toggleSidebar());
        }

        const toggleBtn = document.querySelector('.btn-toggle-sidebar');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggleSidebar());
        }

        // Section expand/collapse
        const sectionHeaders = document.querySelectorAll('.section-header');
        sectionHeaders.forEach(header => {
            header.addEventListener('click', () => {
                const section = header.closest('.sidebar-section').dataset.section;
                this.toggleSection(section);
            });
        });

        // Add Filter button
        const addFilterBtn = document.getElementById('addFilterBtn');
        if (addFilterBtn) {
            addFilterBtn.addEventListener('click', () => this.addFilterRow());
        }

        // Apply Filters button
        const applyFiltersBtn = document.getElementById('applyFiltersBtn');
        if (applyFiltersBtn) {
            applyFiltersBtn.addEventListener('click', () => this.applyAllFilters());
        }

        // Clear All Filters button
        const clearFiltersBtn = document.getElementById('clearFiltersBtn');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => this.clearAllFilters());
        }

        // Validate filters to set initial button states
        this.validateAllFilters();
    }

    /**
     * Toggle sidebar collapsed state
     */
    toggleSidebar() {
        const sidebar = document.querySelector('.table-sidebar');
        if (!sidebar) return;

        this.sidebarCollapsed = !this.sidebarCollapsed;
        sidebar.classList.toggle('collapsed');

        // Update collapse button icon
        const collapseBtn = document.querySelector('.btn-collapse i');
        if (collapseBtn) {
            collapseBtn.className = this.sidebarCollapsed ? 'fas fa-chevron-right' : 'fas fa-chevron-left';
        }

        // Save state
        localStorage.setItem('tableSidebarCollapsed', this.sidebarCollapsed);
    }

    /**
     * Toggle section expanded state
     */
    toggleSection(sectionName) {
        const section = document.querySelector(`.sidebar-section[data-section="${sectionName}"]`);
        if (!section) return;

        const header = section.querySelector('.section-header');
        const content = section.querySelector('.section-content');

        const isExpanded = header.classList.contains('expanded');

        if (isExpanded) {
            // Collapse
            header.classList.remove('expanded');
            content.classList.add('collapsed');
            this.expandedSections = this.expandedSections.filter(s => s !== sectionName);
        } else {
            // Expand
            header.classList.add('expanded');
            content.classList.remove('collapsed');
            if (!this.expandedSections.includes(sectionName)) {
                this.expandedSections.push(sectionName);
            }
        }

        // Save state
        localStorage.setItem('tableSidebarSections', JSON.stringify(this.expandedSections));
    }

    /**
     * Load existing filters from table into sidebar
     */
    loadExistingFilters() {
        const filterRows = document.getElementById('filterRows');
        if (!filterRows) return;

        // Clear existing rows
        filterRows.innerHTML = '';

        // Add rows for each existing filter (array format)
        if (Array.isArray(this.table.filters) && this.table.filters.length > 0) {
            this.table.filters.forEach((filter, index) => {
                // Pass logic for all rows (addFilterRow handles showing/hiding based on index/existence)
                // But wait, addFilterRow checks DOM length.
                // Since we are adding sequentially, the first one will see 0 children, subsequent will see > 0.
                // So we just need to pass the logic value.
                this.addFilterRow(filter.column, filter.operator, filter.value, filter.logic);
            });
        }

        // Update badge
        const count = Array.isArray(this.table.filters) ? this.table.filters.length : 0;
        this.updateFilterBadge(count);

        // ALWAYS validate after loading to set correct button states (even if no filters)
        // Use setTimeout to ensure DOM is fully updated
        setTimeout(() => this.validateAllFilters(), 0);
    }

    /**
     * Add a filter row to the sidebar
     */
    addFilterRow(column = '', operator = 'contains', value = '', logic = 'AND') {
        const filterRows = document.getElementById('filterRows');
        if (!filterRows) return;

        const isFirstRow = filterRows.children.length === 0;
        const filterRow = document.createElement('div');
        filterRow.className = 'filter-row-sidebar';
        filterRow.style.cssText = 'display: flex; gap: 0.5rem; margin-bottom: 0.75rem; padding: 0.75rem; background: #f8f9fa; border-radius: 4px; align-items: flex-start;';

        // For non-first rows, add margin-top to create space for the connector
        if (!isFirstRow) {
            filterRow.style.marginTop = '0.5rem';
        }

        filterRow.innerHTML = `
            <div class="filter-inputs" style="flex: 1; display: flex; flex-direction: column; gap: 0.5rem;">
                <select class="form-select form-select-sm filter-column">
                    <option value="">Select Column</option>
                    ${this.table.columns.map(col =>
            `<option value="${col.key}" ${col.key === column ? 'selected' : ''}>${col.label}</option>`
        ).join('')}
                </select>
                <select class="form-select form-select-sm filter-operator" ${!column ? 'disabled' : ''}>
                    <option value="contains" ${operator === 'contains' ? 'selected' : ''}>Contains</option>
                    <option value="not_contains" ${operator === 'not_contains' ? 'selected' : ''}>Does Not Contain</option>
                    <option value="equals" ${operator === 'equals' ? 'selected' : ''}>Equals</option>
                    <option value="not_equals" ${operator === 'not_equals' ? 'selected' : ''}>Not Equals</option>
                    <option value="starts_with" ${operator === 'starts_with' ? 'selected' : ''}>Starts With</option>
                    <option value="ends_with" ${operator === 'ends_with' ? 'selected' : ''}>Ends With</option>
                </select>
                <input type="text" class="form-control form-control-sm filter-value" 
                       placeholder="Enter value..." value="${value || ''}" ${!column ? 'disabled' : ''}>
            </div>
            <button class="btn btn-sm btn-outline-danger remove-filter-btn" style="align-self: center;">
                <i class="fas fa-times"></i>
            </button>
        `;

        // Add logic connector BETWEEN rows (as a separate element before this row)
        if (!isFirstRow) {
            const connector = document.createElement('div');
            connector.className = 'filter-logic-connector';
            connector.style.cssText = 'display: flex; align-items: center; justify-content: center; margin: 0.5rem 0; gap: 12px; font-size: 0.75rem; color: #6c757d;';
            connector.innerHTML = `
                <div style="flex: 1; height: 1px; background: #dee2e6;"></div>
                <div style="display: flex; gap: 12px; background: white; padding: 2px 12px; border-radius: 4px; border: 1px solid #dee2e6;">
                    <label style="display: flex; align-items: center; gap: 4px; margin: 0; cursor: default;">
                        <input type="radio" class="filter-logic-radio" name="logic-${Date.now()}" value="AND" ${logic !== 'OR' ? 'checked' : ''}>
                        <span style="pointer-events: none; user-select: none;">AND</span>
                    </label>
                    <label style="display: flex; align-items: center; gap: 4px; margin: 0; cursor: default;">
                        <input type="radio" class="filter-logic-radio" name="logic-${Date.now()}" value="OR" ${logic === 'OR' ? 'checked' : ''}>
                        <span style="pointer-events: none; user-select: none;">OR</span>
                    </label>
                </div>
                <div style="flex: 1; height: 1px; background: #dee2e6;"></div>
            `;
            // Insert connector before the current filter row
            filterRows.appendChild(connector);
        }

        // Insert filter row into container
        filterRows.appendChild(filterRow);

        // Attach event listeners to this row
        this.attachFilterRowListeners(filterRow);

        // Update filter count - only count actual filter rows, not connectors
        const actualFilterRows = filterRows.querySelectorAll('.filter-row-sidebar');
        this.updateFilterBadge(actualFilterRows.length);

        // Re-validate to update button states
        this.validateAllFilters();
    }

    /**
     * Attach event listeners to a filter row
     */
    attachFilterRowListeners(filterRow) {
        const columnSelect = filterRow.querySelector('.filter-column');
        const operatorSelect = filterRow.querySelector('.filter-operator');
        const valueInput = filterRow.querySelector('.filter-value');
        const removeBtn = filterRow.querySelector('.remove-filter-btn');
        const logicRadios = filterRow.querySelectorAll('.filter-logic-radio');

        // Column selection change
        columnSelect.addEventListener('change', () => {
            const column = columnSelect.value;
            operatorSelect.disabled = !column;
            valueInput.disabled = !column;
            valueInput.placeholder = column ? 'Filter value' : 'Select a column first';
            if (!column) {
                valueInput.value = '';
            }
            this.validateAllFilters();
        });

        // Operator change
        operatorSelect.addEventListener('change', () => {
            this.validateAllFilters();
        });

        // Value input
        valueInput.addEventListener('input', () => {
            this.validateAllFilters();
        });

        // Logic change
        logicRadios.forEach(radio => {
            radio.addEventListener('change', () => {
                // No validation needed for logic change, but good to have hook
            });
        });

        // Enter key on value input - apply all filters
        valueInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const applyBtn = document.getElementById('applyFiltersBtn');
                if (applyBtn && !applyBtn.disabled) {
                    this.applyAllFilters();
                    // Blur the input to exit edit mode
                    valueInput.blur();
                }
            }
        });

        // Remove button click
        removeBtn.addEventListener('click', () => {
            const filterRows = document.getElementById('filterRows');

            // Find the connector that belongs to this row (the one right before it)
            let previousSibling = filterRow.previousElementSibling;
            if (previousSibling && previousSibling.classList.contains('filter-logic-connector')) {
                previousSibling.remove();
            }

            // Remove the filter row itself
            filterRow.remove();

            // Clean up: ensure first element is always a filter row, not a connector
            if (filterRows && filterRows.children.length > 0) {
                // Keep removing connectors from the start until we hit a filter row
                while (filterRows.children.length > 0 &&
                    filterRows.children[0].classList.contains('filter-logic-connector')) {
                    filterRows.children[0].remove();
                }

                // Reset margin on the first filter row
                if (filterRows.children.length > 0 &&
                    filterRows.children[0].classList.contains('filter-row-sidebar')) {
                    filterRows.children[0].style.marginTop = '0';
                }
            }

            // Update badge count - only count actual filter rows, not connectors
            const actualFilterRows = filterRows ? filterRows.querySelectorAll('.filter-row-sidebar') : [];
            this.updateFilterBadge(actualFilterRows.length);
            this.validateAllFilters();
        });

        // Initial validation
        this.validateAllFilters();
    }

    /**
     * Validate all filters and enable/disable Apply button
     */
    validateAllFilters() {
        const filterRows = document.querySelectorAll('#filterRows .filter-row-sidebar');
        const applyBtn = document.getElementById('applyFiltersBtn');
        const clearBtn = document.getElementById('clearFiltersBtn');

        if (!applyBtn) return;

        // Manage Clear button state
        // Only enable if there are actually applied filters in the table
        if (clearBtn) {
            clearBtn.disabled = !Array.isArray(this.table.filters) || this.table.filters.length === 0;
        }

        // If no filter rows, disable Apply button
        if (filterRows.length === 0) {
            applyBtn.disabled = true;
            return;
        }

        let allValid = true;
        let hasAtLeastOneCompleteFilter = false;

        filterRows.forEach(row => {
            const column = row.querySelector('.filter-column').value;
            const value = row.querySelector('.filter-value').value.trim();

            if (column && value) {
                // This row is complete
                hasAtLeastOneCompleteFilter = true;
            } else {
                // Any row that is NOT complete (missing column OR missing value) makes the set invalid
                // This forces the user to complete or remove empty rows before applying
                allValid = false;
            }
        });

        // Enable button only if:
        // 1. All rows are complete (allValid)
        // 2. At least one complete filter exists (redundant if allValid is true and length > 0, but safe)
        applyBtn.disabled = !allValid || !hasAtLeastOneCompleteFilter;
    }

    /**
     * Apply all filters from sidebar
     */
    applyAllFilters() {
        const filterRows = document.querySelectorAll('#filterRows .filter-row-sidebar');
        const filters = [];

        filterRows.forEach((row, index) => {
            const column = row.querySelector('.filter-column').value;
            const operator = row.querySelector('.filter-operator').value;
            const value = row.querySelector('.filter-value').value.trim();

            // Get logic from the connector BEFORE this row (if it exists)
            let logic = 'AND';
            if (index > 0) {
                // Logic radios are in the connector element before this row
                let previousSibling = row.previousElementSibling;
                if (previousSibling && previousSibling.classList.contains('filter-logic-connector')) {
                    const logicChecked = previousSibling.querySelector('.filter-logic-radio:checked');
                    if (logicChecked) {
                        logic = logicChecked.value;
                    }
                }
            }

            if (column && value) {
                // First filter doesn't have logic, subsequent filters use selected logic
                if (index === 0) {
                    filters.push({ column, operator, value });
                } else {
                    filters.push({ logic, column, operator, value });
                }
            }
        });

        console.log('Applying filters:', filters);

        // Update table filters (array format)
        this.table.filters = filters;
        this.table.currentPage = 1; // Reset to first page

        // Use updateTable instead of render to preserve sidebar state (filter rows)
        this.table.updateTable();

        // Update badge to show applied filters count
        this.updateFilterBadge(filters.length);

        // Update button states (specifically Clear button)
        this.validateAllFilters();
    }

    /**
     * Clear all filters
     */
    clearAllFilters() {
        const filterRows = document.getElementById('filterRows');
        if (filterRows) {
            filterRows.innerHTML = '';
        }
        this.table.filters = []; // Array format
        this.table.updateTable(); // Use updateTable instead of render
        this.updateFilterBadge(0);
        this.validateAllFilters(); // Update button states
    }

    /**
     * Update filter badge count
     */
    updateFilterBadge(count) {
        const badge = document.querySelector('.sidebar-section[data-section="filters"] .badge');
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline-block' : 'none';
        }
    }
}

// Export for use in advanced-table.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TableSidebar;
}
