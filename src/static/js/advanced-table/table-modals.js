// Table Modal Functions (Column Manager, Filter Manager, Save Config)

// Column Manager Functions
function closeColumnManager() {
  document.getElementById("columnManager").classList.remove("show");
}

function applyColumnChanges() {
  const columnItems = document.querySelectorAll("#columnList .column-item");
  const newOrder = [];
  const newHidden = new Set();

  columnItems.forEach((item) => {
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
}

// Initialize drag and drop for column manager
function initializeDragAndDrop() {
  const columnList = document.getElementById("columnList");
  if (!columnList) return;

  let draggedElement = null;

  columnList.addEventListener("dragstart", function (e) {
    if (e.target.classList.contains("column-item")) {
      draggedElement = e.target;
      e.target.classList.add("dragging");
      e.dataTransfer.effectAllowed = "move";
    }
  });

  columnList.addEventListener("dragover", function (e) {
    e.preventDefault();
    const afterElement = getDragAfterElement(columnList, e.clientY);
    if (afterElement == null) {
      columnList.appendChild(draggedElement);
    } else {
      columnList.insertBefore(draggedElement, afterElement);
    }
  });

  columnList.addEventListener("dragend", function (e) {
    if (e.target.classList.contains("column-item")) {
      e.target.classList.remove("dragging");
    }
  });
}

function getDragAfterElement(container, y) {
  const draggableElements = [
    ...container.querySelectorAll(".column-item:not(.dragging)"),
  ];

  return draggableElements.reduce(
    (closest, child) => {
      const box = child.getBoundingClientRect();
      const offset = y - box.top - box.height / 2;

      if (offset < 0 && offset > closest.offset) {
        return { offset: offset, element: child };
      } else {
        return closest;
      }
    },
    { offset: Number.NEGATIVE_INFINITY },
  ).element;
}

// Filter Manager Functions
function closeFilterManager() {
  document.getElementById("filterManager").classList.remove("show");
}

function addFilterRow() {
  const filterRows = document.getElementById("filterRows");
  const rowCount = filterRows.children.length;

  // Add logic selector if this is not the first row
  if (rowCount > 0) {
    const logicRow = document.createElement("div");
    logicRow.className = "filter-logic";
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

  const filterRow = document.createElement("div");
  filterRow.className = "filter-row";
  const columns = window.advTable ? window.advTable.columns : [];

  filterRow.innerHTML = `
        <select class="form-select column-select" onchange="toggleFilterValue(this)">
            <option value="">Select Column</option>
            ${columns.map((col) => `<option value="${col.key}">${col.label}</option>`).join("")}
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
}

function toggleFilterValue(columnSelect) {
  const filterRow = columnSelect.closest(".filter-row");
  const filterValue = filterRow.querySelector(".filter-value");

  if (columnSelect.value) {
    filterValue.disabled = false;
    filterValue.focus();
  } else {
    filterValue.disabled = true;
    filterValue.value = "";
  }
}

function applyFilterRealTime() {
  // Apply filters in real-time as user types
  setTimeout(() => {
    if (!window.advTable) return;

    const filterRows = document.querySelectorAll("#filterRows .filter-row");
    const newFilters = {};

    filterRows.forEach((row) => {
      const columnSelect = row.querySelector(".column-select");
      const operatorSelect = row.querySelector(".operator-select");
      const valueInput = row.querySelector(".filter-value");

      const column = columnSelect.value;
      const operator = operatorSelect.value;
      const value = valueInput.value.trim();

      if (column && operator && value) {
        newFilters[column] = { operator, value };
      }
    });

    window.advTable.filters = newFilters;
    window.advTable.currentPage = 1;
    window.advTable.render();
  }, 300); // Debounce for 300ms
}

function removeFilterRow(button) {
  const filterRow = button.closest(".filter-row");
  const prevElement = filterRow.previousElementSibling;

  // Remove logic selector if it exists
  if (prevElement && prevElement.classList.contains("filter-logic")) {
    prevElement.remove();
  }

  filterRow.remove();
}

function clearAllFilters() {
  document.getElementById("filterRows").innerHTML = "";
  if (window.advTable) {
    window.advTable.filters = {};
    window.advTable.render();
  }
  // Don't close the manager, just clear and add one empty row
  addFilterRow();
}

function applyFilters() {
  if (!window.advTable) return;

  const filterRows = document.querySelectorAll("#filterRows .filter-row");
  const newFilters = {};
  let hasValidFilter = false;

  filterRows.forEach((row) => {
    const columnSelect = row.querySelector(".column-select");
    const operatorSelect = row.querySelector(".operator-select");
    const valueInput = row.querySelector(".filter-value");

    const column = columnSelect.value;
    const operator = operatorSelect.value;
    const value = valueInput.value.trim();

    if (column && operator && value) {
      newFilters[column] = { operator, value };
      hasValidFilter = true;
    } else if (column && !value) {
      // Highlight incomplete filter
      valueInput.classList.add("is-invalid");
      setTimeout(() => valueInput.classList.remove("is-invalid"), 3000);
    }
  });

  if (hasValidFilter || Object.keys(newFilters).length === 0) {
    window.advTable.filters = newFilters;
    window.advTable.currentPage = 1;
    window.advTable.render();
    closeFilterManager();
  } else {
    if (typeof ToastNotification !== "undefined") {
      ToastNotification.error(
        "Please complete all filter criteria or remove incomplete filters.",
      );
    } else {
      alert(
        "Please complete all filter criteria or remove incomplete filters.",
      );
    }
  }
}

// Configuration Save Functions
function saveTableConfiguration() {
  const configName = document.getElementById("configName").value;
  const setAsDefault = document.getElementById("setAsDefault").checked;

  if (!configName) {
    if (typeof ToastNotification !== "undefined") {
      ToastNotification.error("Please enter a configuration name");
    } else {
      alert("Please enter a configuration name");
    }
    return;
  }

  if (!window.advTable) return;

  const config = {
    config_name: configName,
    column_order: JSON.stringify(window.advTable.columnOrder),
    hidden_columns: JSON.stringify(Array.from(window.advTable.hiddenColumns)),
    filters: JSON.stringify(window.advTable.filters),
    sort_config: JSON.stringify(window.advTable.currentSort),
    is_default: setAsDefault,
  };

  const csrfTokenMeta = document.querySelector("meta[name=csrf-token]");
  const csrfToken = csrfTokenMeta ? csrfTokenMeta.getAttribute("content") : "";

  fetch(`/api/table-config/${window.advTable.pageName}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken,
    },
    body: JSON.stringify(config),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        if (typeof ToastNotification !== "undefined") {
          ToastNotification.success("Configuration saved successfully!");
        }
        document.getElementById("configName").value = "";
        document.getElementById("setAsDefault").checked = false;
        // Close modal
        const modalEl = document.getElementById("saveConfigModal");
        if (modalEl) {
          const modal = bootstrap.Modal.getInstance(modalEl);
          if (modal) modal.hide();
          else $(modalEl).modal("hide"); // Fallback to jQuery
        }
        loadSavedConfigurations();
      } else {
        if (typeof ToastNotification !== "undefined") {
          ToastNotification.error("Error saving configuration: " + data.error);
        }
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      if (typeof ToastNotification !== "undefined") {
        ToastNotification.error("Error saving configuration");
      }
    });
}

function loadSavedConfigurations() {
  if (!window.advTable || !window.advTable.pageName) {
    console.log("AdvTable not ready for loading configurations");
    return;
  }

  fetch(`/api/table-config/${window.advTable.pageName}`)
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then((configs) => {
      const dropdown = document.getElementById("savedConfigsDropdown");
      if (dropdown && Array.isArray(configs)) {
        const currentValue = dropdown.value;
        dropdown.innerHTML = '<option value="">Select saved view...</option>';
        configs.forEach((config) => {
          const option = document.createElement("option");
          option.value = config.id;
          option.textContent =
            config.config_name + (config.is_default ? " (Default)" : "");
          dropdown.appendChild(option);
        });
        // Restore selection if it still exists
        if (
          currentValue &&
          dropdown.querySelector(`option[value="${currentValue}"]`)
        ) {
          dropdown.value = currentValue;
        }
      }
    })
    .catch((error) => {
      console.log("Error loading configurations:", error.message);
      const dropdown = document.getElementById("savedConfigsDropdown");
      if (dropdown) {
        dropdown.innerHTML = '<option value="">No saved views</option>';
      }
    });
}

function loadSelectedConfiguration() {
  const dropdown = document.getElementById("savedConfigsDropdown");
  const configId = dropdown.value;
  if (!configId || !window.advTable) {
    console.log("No configuration selected or advTable not ready");
    return;
  }

  fetch(`/api/table-config/${window.advTable.pageName}`)
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then((configs) => {
      const config = configs.find((c) => c.id == configId);
      if (config) {
        window.advTable.applyConfiguration(config);
        console.log("Configuration applied:", config.config_name);
      } else {
        console.error("Configuration not found:", configId);
        dropdown.value = "";
      }
    })
    .catch((error) => {
      console.error("Error loading configuration:", error.message);
      if (typeof ToastNotification !== "undefined") {
        ToastNotification.error("Error loading saved view: " + error.message);
      }
      dropdown.value = "";
    });
}

// Initialize configurations when page loads
document.addEventListener("DOMContentLoaded", function () {
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

// Export functions for potential module usage (though mostly global)
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    applyColumnChanges,
    initializeDragAndDrop,
    applyFilters,
    saveTableConfiguration,
    loadSavedConfigurations,
    loadSelectedConfiguration,
  };
} else {
  // Expose to window for inline HTML handlers
  window.closeColumnManager = closeColumnManager;
  window.applyColumnChanges = applyColumnChanges;
  window.initializeDragAndDrop = initializeDragAndDrop;
  window.getDragAfterElement = getDragAfterElement;
  window.closeFilterManager = closeFilterManager;
  window.addFilterRow = addFilterRow;
  window.toggleFilterValue = toggleFilterValue;
  window.applyFilterRealTime = applyFilterRealTime;
  window.removeFilterRow = removeFilterRow;
  window.clearAllFilters = clearAllFilters;
  window.applyFilters = applyFilters;
  window.saveTableConfiguration = saveTableConfiguration;
  window.loadSavedConfigurations = loadSavedConfigurations;
  window.loadSelectedConfiguration = loadSelectedConfiguration;
}
