// Export and utility methods
AdvancedTable.prototype.exportData = function(format = 'csv') {
    const filteredData = this.getFilteredData();
    if (format === 'csv') {
        this.exportCSV(filteredData);
    }
};

AdvancedTable.prototype.exportCSV = function(data) {
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
};

AdvancedTable.prototype.showColumnManager = function() {
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
};

AdvancedTable.prototype.getDragAfterElement = function(container, y) {
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
};

AdvancedTable.prototype.goToPage = function(page) {
    const filteredData = this.getFilteredData();
    const totalPages = Math.ceil(filteredData.length / this.pageSize);

    if (page >= 1 && page <= totalPages) {
        this.currentPage = page;
        this.render();
    }
};