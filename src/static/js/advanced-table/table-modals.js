// Refactoring Note:
// This file is a placeholder for the verified refactor of "Task 5.16" which removes inline scripts from advanced_table.html.

/**
 * Manages the legacy modal-based UI for Advanced Table.
 */

// Define as local functions first
const closeColumnManager = function() {
    const el = document.getElementById('columnManager');
    if(el) el.classList.remove('show');
};

const applyColumnChanges = function() {
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

    if (window.advTable) {
        window.advTable.columnOrder = newOrder;
        window.advTable.hiddenColumns = newHidden;
        window.advTable.render();
    }
    closeColumnManager();
};

const getDragAfterElement = function(container, y) {
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

const initializeDragAndDrop = function() {
    const columnList = document.getElementById('columnList');
    if (!columnList) return;

    let draggedElement = null;

    columnList.addEventListener('dragstart', function (e) {
        if (e.target.classList.contains('column-item')) {
            draggedElement = e.target;
            e.target.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
        }
    });

    columnList.addEventListener('dragover', function (e) {
        e.preventDefault();
        const afterElement = getDragAfterElement(columnList, e.clientY);
        if (afterElement == null) {
            columnList.appendChild(draggedElement);
        } else {
            columnList.insertBefore(draggedElement, afterElement);
        }
    });

    columnList.addEventListener('dragend', function (e) {
        if (e.target.classList.contains('column-item')) {
            e.target.classList.remove('dragging');
        }
    });
};

const closeFilterManager = function() {
    const el = document.getElementById('filterManager');
    if(el) el.classList.remove('show');
};

const toggleFilterValue = function(columnSelect) {
    const filterRow = columnSelect.closest('.filter-row');
    const filterValue = filterRow.querySelector('.filter-value');

    if (columnSelect.value) {
        filterValue.disabled = false;
        filterValue.focus();
    } else {
        filterValue.disabled = true;
        filterValue.value = '';
    }
};

const removeFilterRow = function(button) {
    const filterRow = button.closest('.filter-row');
    const prevElement = filterRow.previousElementSibling;

    // Remove logic selector if it exists
    if (prevElement && prevElement.classList.contains('filter-logic')) {
        prevElement.remove();
    }

    filterRow.remove();
};

const applyFilterRealTime = function() {
    // Apply filters in real-time as user types
    setTimeout(() => {
        const filterRows = document.querySelectorAll('#filterRows .filter-row');
        const newFilters = {};

        filterRows.forEach(row => {
            const columnSelect = row.querySelector('.column-select');
            const operatorSelect = row.querySelector('.operator-select');
            const valueInput = row.querySelector('.filter-value');

            const column = columnSelect.value;
            const operator = operatorSelect.value;
            const value = valueInput.value.trim();

            if (column && operator && value) {
                newFilters[column] = { operator, value };
            }
        });

        if (window.advTable) {
            window.advTable.filters = newFilters;
            window.advTable.currentPage = 1;
            window.advTable.render();
        }
    }, 300); // Debounce for 300ms
};

const addFilterRow = function() {
    const filterRows = document.getElementById('filterRows');
    if(!filterRows) return;

    const rowCount = filterRows.children.length;

    // Add logic selector if this is not the first row
    if (rowCount > 0) {
        const logicRow = document.createElement('div');
        logicRow.className = 'filter-logic';
        logicRow.innerHTML = `
        <div class="btn-group" role="group">
            <input type="radio" class="btn-check" name="logic${rowCount}" id="and${rowCount}" value="and" checked>
            <label class="btn btn-outline-primary btn-sm" for="and${rowCount}">AND</label>
            <input type="radio" class="btn-check" name="logic${rowCount}" id="or${rowCount}" value="or">
            <label class="btn btn-outline-primary btn-sm" for="or${rowCount}">OR</label>
        </div>
    `;
        filterRows.appendChild(logicRow);
    }

    const filterRow = document.createElement('div');
    filterRow.className = 'filter-row';

    const columns = window.advTable ? window.advTable.columns : [];
    const options = columns.map(col => `<option value="${col.key}">${col.label}</option>`).join('');

    filterRow.innerHTML = `
    <select class="form-select column-select" onchange="toggleFilterValue(this)">
        <option value="">Select Column</option>
        ${options}
    </select>
    <select class="form-select operator-select">
        <option value="contains">Contains</option>
        <option value="not_contains">Does Not Contain</option>
        <option value="equals">Equals</option>
        <option value="not_equals">Not Equals</option>
        <option value="starts_with">Starts With</option>
        <option value="ends_with">Ends With</option>
    </select>
    <input type="text" class="form-control filter-value" placeholder="Filter value" disabled oninput="applyFilterRealTime()">
    <button type="button" class="btn btn-outline-danger btn-sm" onclick="removeFilterRow(this)">
        <i class="fas fa-trash"></i>
    </button>
`;

    filterRows.appendChild(filterRow);
};

const clearAllFilters = function() {
    const fr = document.getElementById('filterRows');
    if(fr) fr.innerHTML = '';
    if (window.advTable) {
        window.advTable.filters = {};
        window.advTable.render();
    }
    // Don't close the manager, just clear and add one empty row
    addFilterRow();
};

const applyFilters = function() {
    const filterRows = document.querySelectorAll('#filterRows .filter-row');
    const newFilters = {};
    let hasValidFilter = false;
    let hasIncompleteFilter = false;

    filterRows.forEach(row => {
        const columnSelect = row.querySelector('.column-select');
        const operatorSelect = row.querySelector('.operator-select');
        const valueInput = row.querySelector('.filter-value');

        const column = columnSelect.value;
        const operator = operatorSelect.value;
        const value = valueInput.value.trim();

        if (column && operator && value) {
            newFilters[column] = { operator, value };
            hasValidFilter = true;
        } else if (column && !value) {
            // Highlight incomplete filter
            valueInput.classList.add('is-invalid');
            setTimeout(() => valueInput.classList.remove('is-invalid'), 3000);
            hasIncompleteFilter = true;
        }
    });

    if (!hasIncompleteFilter && (hasValidFilter || Object.keys(newFilters).length === 0)) {
        if (window.advTable) {
            window.advTable.filters = newFilters;
            window.advTable.currentPage = 1;
            window.advTable.render();
        }
        closeFilterManager();
    } else {
        if(window.ToastNotification) {
            window.ToastNotification.error('Please complete all filter criteria or remove incomplete filters.');
        }
    }
};

const fetchTableConfigs = function(pageName) {
    return fetch(`/api/table-config/${pageName}`)
        .then(response => {
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.json();
        });
};

const loadSavedConfigurations = function() {
    if (!window.advTable || !window.advTable.pageName) {
        return Promise.resolve();
    }

    return fetchTableConfigs(window.advTable.pageName)
        .then(configs => {
            const dropdown = document.getElementById('savedConfigsDropdown');
            if (dropdown && Array.isArray(configs)) {
                const currentValue = dropdown.value;
                dropdown.innerHTML = '<option value="">Select saved view...</option>';
                configs.forEach(config => {
                    const option = document.createElement('option');
                    option.value = config.id;
                    option.textContent = config.config_name + (config.is_default ? ' (Default)' : '');
                    dropdown.appendChild(option);
                });
                // Restore selection if it still exists
                if (currentValue && dropdown.querySelector(`option[value="${currentValue}"]`)) {
                    dropdown.value = currentValue;
                }
            }
        })
        .catch(error => {
            console.error('Error loading configurations:', error.message);
            const dropdown = document.getElementById('savedConfigsDropdown');
            if (dropdown) {
                dropdown.innerHTML = '<option value="">No saved views</option>';
            }
        });
};

const saveTableConfiguration = function() {
    const configName = document.getElementById('configName').value;
    const setAsDefault = document.getElementById('setAsDefault').checked;

    if (!configName) {
        if(window.ToastNotification) window.ToastNotification.error('Please enter a configuration name');
        return Promise.resolve(); // Return resolved promise for testing
    }

    if (!window.advTable) return Promise.resolve();

    const config = {
        config_name: configName,
        column_order: JSON.stringify(window.advTable.columnOrder),
        hidden_columns: JSON.stringify(Array.from(window.advTable.hiddenColumns)),
        filters: JSON.stringify(window.advTable.filters),
        sort_config: JSON.stringify(window.advTable.currentSort),
        is_default: setAsDefault
    };

    return fetch(`/api/table-config/${window.advTable.pageName}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name=csrf-token]')?.getAttribute('content')
        },
        body: JSON.stringify(config)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if(window.ToastNotification) window.ToastNotification.success('Configuration saved successfully!');
                document.getElementById('configName').value = '';
                document.getElementById('setAsDefault').checked = false;
                return loadSavedConfigurations(); // Return this promise too
            } else {
                if(window.ToastNotification) window.ToastNotification.error('Error saving configuration: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if(window.ToastNotification) window.ToastNotification.error('Error saving configuration');
        });
};

const loadSelectedConfiguration = function() {
    const dropdown = document.getElementById('savedConfigsDropdown');
    const configId = dropdown.value;
    if (!configId || !window.advTable) {
        return Promise.resolve();
    }

    return fetchTableConfigs(window.advTable.pageName)
        .then(configs => {
            const config = configs.find(c => c.id == configId);
            if (config) {
                window.advTable.applyConfiguration(config);
            } else {
                dropdown.value = '';
            }
        })
        .catch(error => {
            if(window.ToastNotification) window.ToastNotification.error('Error loading saved view: ' + error.message);
        });
};

// Assign to window for browser usage
if (typeof window !== 'undefined') {
    window.closeColumnManager = closeColumnManager;
    window.applyColumnChanges = applyColumnChanges;
    window.initializeDragAndDrop = initializeDragAndDrop;
    window.getDragAfterElement = getDragAfterElement;
    window.closeFilterManager = closeFilterManager;
    window.addFilterRow = addFilterRow;
    window.toggleFilterValue = toggleFilterValue;
    window.removeFilterRow = removeFilterRow;
    window.applyFilterRealTime = applyFilterRealTime;
    window.clearAllFilters = clearAllFilters;
    window.applyFilters = applyFilters;
    window.saveTableConfiguration = saveTableConfiguration;
    window.loadSavedConfigurations = loadSavedConfigurations;
    window.loadSelectedConfiguration = loadSelectedConfiguration;
}

// Initialize configurations when DOM is ready
if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', function () {
        // Wait for advTable to be initialized
        const checkAdvTable = setInterval(() => {
            if (window.advTable && window.advTable.pageName) {
                loadSavedConfigurations();
                clearInterval(checkAdvTable);
            }
        }, 100);

        // Clear interval after 10 seconds to prevent infinite loop
        setTimeout(() => {
            clearInterval(checkAdvTable);
        }, 10000);
    });
}

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        closeColumnManager,
        applyColumnChanges,
        initializeDragAndDrop,
        getDragAfterElement,
        closeFilterManager,
        addFilterRow,
        toggleFilterValue,
        removeFilterRow,
        applyFilterRealTime,
        clearAllFilters,
        applyFilters,
        saveTableConfiguration,
        loadSavedConfigurations,
        loadSelectedConfiguration
    };
}
