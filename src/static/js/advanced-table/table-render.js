// Table rendering methods
AdvancedTable.prototype.render = function () {
    const currentSearchValue = this.globalSearchDisplay || '';

    this.container.innerHTML = `
        <div class="advanced-table-wrapper">
            <div class="table-layout">
                ${this.sidebar.generateHTML()}
                
                <div class="table-main">
                    <div class="table-controls">
                        <div class="d-flex align-items-center gap-2">
                            <button class="btn-toggle-sidebar" title="Toggle sidebar">
                                <i class="fas fa-bars"></i>
                            </button>
                            <div class="table-search">
                                <input type="text" class="form-control form-control-sm" placeholder="Search all columns..."
                                       id="globalSearchInput" value="${currentSearchValue}">
                                <button class="btn btn-sm btn-outline-secondary" type="button" id="clearSearchBtn" style="display: ${currentSearchValue ? 'inline-block' : 'none'};" title="Clear search">
                                    <i class="fas fa-times"></i>
                                </button>
                                <button class="btn btn-sm btn-primary" type="button" id="applySearchBtn" title="Apply search">
                                    <i class="fas fa-search"></i>
                                </button>
                            </div>
                        </div>
                        <div class="table-info">
                            <span class="row-count">Showing <strong>${this.getFilteredData().length}</strong> of <strong>${this.data.length}</strong> rows</span>
                        </div>
                        <div class="table-actions">
                            <button class="btn btn-sm btn-outline-success" data-action="exportData">
                                <i class="fas fa-download"></i> Export CSV
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
            </div>
        </div>
    `;

    this.attachEventListeners();
    this.sidebar.attachEventListeners();
    this.populateConfigDropdown();
};

AdvancedTable.prototype.renderHeader = function () {
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
};

AdvancedTable.prototype.renderBody = function () {
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
};

AdvancedTable.prototype.getSortIcon = function (column) {
    if (this.currentSort.column !== column) return '<i class="fas fa-sort text-muted"></i>';
    return this.currentSort.direction === 'asc'
        ? '<i class="fas fa-sort-up text-primary"></i>'
        : '<i class="fas fa-sort-down text-primary"></i>';
};

AdvancedTable.prototype.formatCellValue = function (value, column, row) {
    if (value === null || value === undefined) value = '';

    const col = this.columns.find(c => c.key === column);

    if (col && col.render && typeof col.render === 'function') {
        return col.render(value, row);
    }

    if (col && col.type === 'date' && value) {
        return new Date(value).toLocaleDateString();
    }
    if (col && col.type === 'datetime' && value) {
        return new Date(value).toLocaleString();
    }
    return value;
};

// Update table data without recreating the entire HTML (preserves sidebar state)
AdvancedTable.prototype.updateTable = function () {
    // Update table body
    const tbody = this.container.querySelector('.advanced-table tbody');
    if (tbody) {
        tbody.innerHTML = this.renderBody();
    }

    // Update row count
    const rowCount = this.container.querySelector('.row-count');
    if (rowCount) {
        rowCount.innerHTML = `Showing <strong>${this.getFilteredData().length}</strong> of <strong>${this.data.length}</strong> rows`;
    }

    // Update header sort icons
    const thead = this.container.querySelector('.advanced-table thead');
    if (thead) {
        thead.innerHTML = this.renderHeader();
        // Re-attach sort listeners
        thead.querySelectorAll('.sortable').forEach(th => {
            th.addEventListener('click', () => {
                const column = th.dataset.column;
                this.sort(column);
            });
        });
    }
};