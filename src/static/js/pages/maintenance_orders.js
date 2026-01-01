/* global initAdvancedTable */

/**
 * Render functions for Maintenance Orders table columns
 * Exported for testing purposes
 */

/**
 * Render order ID as a link to detail page
 * @param {number|string} val - The ID value
 * @param {Object} row - The row data
 * @returns {string} HTML link string
 */
function renderOrderId(val, row) {
  return `<a href="/maintenance_orders/${row.id}">${val}</a>`;
}

/**
 * Get column configuration for Maintenance Orders table
 * @returns {Array} Column configuration array
 */
function getMaintenanceOrdersColumns() {
  return [
    {
      key: "id",
      label: "ID",
      type: "number",
      render: renderOrderId,
    },
    { key: "asset_name", label: "Asset", type: "text" },
    { key: "description", label: "Description", type: "text" },
    { key: "order_type", label: "Type", type: "text" },
    { key: "status", label: "Status", type: "text" },
    { key: "priority", label: "Priority", type: "text" },
    { key: "due_date", label: "Due Date", type: "date" },
    { key: "assignees", label: "Assignees", type: "text" },
    { key: "schedule_name", label: "Schedule", type: "text" },
    { key: "frequency", label: "Frequency", type: "text" },
    {
      key: "estimated_completion_time",
      label: "Est. Time (min)",
      type: "number",
    },
    { key: "labour_count", label: "Labour Count", type: "number" },
  ];
}

/**
 * Cleanup old table state if 'assignees' column is missing (Bug #29 fix)
 * @param {Storage} storage - The storage object (localStorage)
 * @param {string} tableStateKey - The key for table state
 * @returns {string} 'removed' | 'kept' | 'no_state' | 'error_cleared'
 */
function cleanupTableState(storage, tableStateKey) {
  try {
    const savedStateJSON = storage.getItem(tableStateKey);
    if (savedStateJSON) {
      const savedState = JSON.parse(savedStateJSON);
      if (
        savedState.columnOrder &&
        !savedState.columnOrder.includes("assignees")
      ) {
        storage.removeItem(tableStateKey);
        return "removed";
      }
      return "kept";
    }
    return "no_state";
  } catch (e) {
    console.error("Error processing table state from localStorage:", e);
    storage.removeItem(tableStateKey);
    return "error_cleared";
  }
}

/**
 * Initialize Maintenance Orders table
 */
function initMaintenanceOrdersTable() {
  const tableStateKey = "tableState_mosTable";

  // Bug #29: Clear localStorage if 'assignees' column is missing
  if (typeof localStorage !== "undefined") {
    cleanupTableState(localStorage, tableStateKey);
  }

  const mosDataElement = document.getElementById("mos-data");
  if (mosDataElement) {
    const mosData = JSON.parse(mosDataElement.textContent);
    initAdvancedTable("mosTable", mosData, getMaintenanceOrdersColumns(), 25);
  }
}

// Initialize table on DOM load (browser only)
if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", initMaintenanceOrdersTable);
}

// Export for testing (CommonJS)
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    renderOrderId,
    getMaintenanceOrdersColumns,
    cleanupTableState,
    initMaintenanceOrdersTable,
  };
}
