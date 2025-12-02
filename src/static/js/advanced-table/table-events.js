// Event handling methods
AdvancedTable.prototype.attachEventListeners = function () {
    const buttons = this.container.querySelectorAll('[data-action]');
    buttons.forEach(button => {
        const action = button.getAttribute('data-action');

        if (action === 'clearAllFilters') {
            button.addEventListener('click', () => this.resetTableState());
        } else if (action === 'exportData') {
            button.addEventListener('click', () => this.exportData('csv'));
        } else if (action === 'saveConfiguration') {
            button.addEventListener('click', () => this.saveConfiguration());
        }
    });

    const searchInput = document.getElementById('globalSearchInput');
    const applySearchBtn = document.getElementById('applySearchBtn');
    const clearSearchBtn = document.getElementById('clearSearchBtn');

    if (searchInput && applySearchBtn) {
        // Initial state
        applySearchBtn.disabled = !searchInput.value.trim();

        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const value = e.target.value;
                this.globalSearch(value);
                if (clearSearchBtn) {
                    clearSearchBtn.style.display = value ? 'inline-block' : 'none';
                }
            }
        });

        searchInput.addEventListener('input', (e) => {
            const value = e.target.value;
            // Update Apply button state
            applySearchBtn.disabled = !value.trim();

            if (clearSearchBtn) {
                clearSearchBtn.style.display = value ? 'inline-block' : 'none';
            }
        });
    }

    if (applySearchBtn) {
        applySearchBtn.addEventListener('click', () => {
            if (searchInput) {
                const value = searchInput.value;
                this.globalSearch(value);
                if (clearSearchBtn) {
                    clearSearchBtn.style.display = value ? 'inline-block' : 'none';
                }
            }
        });
    }

    if (clearSearchBtn) {
        clearSearchBtn.addEventListener('click', () => {
            if (searchInput) {
                searchInput.value = '';
                // Disable Apply button when cleared
                if (applySearchBtn) applySearchBtn.disabled = true;

                clearSearchBtn.style.display = 'none';
                this.globalSearch('');
            }
        });
    }


    const headers = this.container.querySelectorAll('.advanced-table th.sortable');
    headers.forEach(header => {
        header.addEventListener('click', (e) => {
            // Ignore clicks that originated from resize handle
            if (e.target.classList.contains('resize-handle') ||
                e.target.closest('.resize-handle')) {
                e.stopPropagation();
                e.preventDefault();
                return;
            }

            const column = header.getAttribute('data-column');
            this.sort(column);
        });
    });

    // Bug #14 Fix: Use event delegation instead of attaching to individual rows
    // This ensures clicks work even after table re-renders (sorting, column changes)
    const tbody = this.container.querySelector('.advanced-table tbody');
    if (tbody) {
        tbody.addEventListener('click', (e) => {
            // Find the clicked row (handle clicks on td or nested elements)
            const row = e.target.closest('tr');
            if (!row || !tbody.contains(row)) return;

            // Ignore clicks on buttons or links (Edit/Delete actions)
            if (e.target.closest('button, a, .btn, .inline-form')) {
                return;
            }

            // Get the row index within the current page
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const rowIndex = rows.indexOf(row);

            if (rowIndex === -1) return;

            // Get the data for this row
            const filteredData = this.getFilteredData();
            const paginatedData = this.getPaginatedData(filteredData);
            const rowData = paginatedData[rowIndex];

            if (rowData && rowData.id) {
                this.rowClick(rowData.id);
            }
        });
    }
};

AdvancedTable.prototype.rowClick = function (id) {
    let pagePath = this.pageName.replace('Table', '');

    if (pagePath === 'mos') {
        pagePath = 'maintenance_orders';
    } else if (pagePath === 'spareParts') {
        pagePath = 'spare_parts';
    }

    window.location.href = `/${pagePath}/${id}`;
};