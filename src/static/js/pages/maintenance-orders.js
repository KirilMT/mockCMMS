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
    { key: "title", label: "Title", type: "text" },
    { key: "description", label: "Description", type: "text" },
    { key: "order_type", label: "Type", type: "text" },
    { key: "category", label: "Category", type: "text" },
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
 * Cleanup old table state if 'assignees' column is missing from saved state
 * @param {Storage} storage - The storage object (localStorage)
 * @param {string} tableStateKey - The key for table state
 * @returns {string} 'removed' | 'kept' | 'no_state' | 'error_cleared'
 */
function cleanupTableState() {
  const tableStateKey = "tableState_maintenance_orders";
  try {
    // Use StorageManager for robust access if available
    // Use StorageManager for robust access if available
    const storage = window.StorageManager || {
      get: () => null,
      remove: () => null,
    };

    const savedStateJSON = storage.get(tableStateKey);
    if (savedStateJSON) {
      const savedState = JSON.parse(savedStateJSON);
      if (
        savedState.columnOrder &&
        !savedState.columnOrder.includes("assignees")
      ) {
        // If the specific table state is outdated, remove it.
        storage.remove(tableStateKey);
        return "removed";
      }
      return "kept";
    }
    return "no_state";
  } catch (e) {
    console.warn("localStorage processing failed:", e);
    // Attempt manual cleanup if everything else fails
    // Attempt manual cleanup via SafeStorage if everything else fails
    // Just accessing the object to ensure it's loaded, though not doing anything with it
    // as we can't reliably iterate keys without direct access.
    const ignore = window.StorageManager || {
      get: () => null,
      remove: () => null,
    };

    // If we are here, StorageManager failed or threw.
    // We should NOT try direct localStorage access again as it will likely throw.
    console.warn("Storage cleanup skipped due to error.");
    return "error_cleared";
  }
}

/**
 * Initialize Maintenance Orders table
 */
function initMaintenanceOrdersTable() {
  // Clear localStorage if saved state is outdated (missing 'assignees' column)
  cleanupTableState();

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
