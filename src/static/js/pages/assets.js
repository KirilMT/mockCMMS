/* global initAdvancedTable */

/**
 * Render functions for Assets table columns
 * Exported for testing purposes
 */

/**
 * Render asset ID as a link to asset detail page
 * @param {number|string} val - The ID value
 * @param {Object} row - The row data
 * @returns {string} HTML link string
 */
function renderAssetId(val, row) {
  return `<a href="/assets/${row.id}">${val}</a>`;
}

/**
 * Get column configuration for Assets table
 * @returns {Array} Column configuration array
 */
function getAssetsColumns() {
  return [
    {
      key: "id",
      label: "ID",
      type: "number",
      render: renderAssetId,
    },
    { key: "asset_code", label: "Asset Code", type: "text" },
    { key: "name", label: "Name", type: "text" },
    { key: "description", label: "Description", type: "text" },
    { key: "asset_type", label: "Type", type: "text" },
    { key: "cost_center", label: "Cost Center", type: "text" },
    { key: "status", label: "Status", type: "text" },
  ];
}

/**
 * Initialize Assets table
 */
function initAssetsTable() {
  const assetsDataElement = document.getElementById("assets-data");
  if (assetsDataElement) {
    const assetsData = JSON.parse(assetsDataElement.textContent);
    initAdvancedTable("assetsTable", assetsData, getAssetsColumns(), 25);
  }
}

// Initialize table on DOM load (browser only)
if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", initAssetsTable);
}

// Export for testing (CommonJS)
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    renderAssetId,
    getAssetsColumns,
    initAssetsTable,
  };
}
