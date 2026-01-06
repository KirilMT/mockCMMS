/* global initAdvancedTable */

/**
 * Render functions for Spare Parts table columns
 * Exported for testing purposes
 */

/**
 * Render spare part ID as a link to detail page
 * @param {number|string} val - The ID value
 * @param {Object} row - The row data
 * @returns {string} HTML link string
 */
function renderSparePartId(val, row) {
  return `<a href="/spare_parts/${row.id}">${val}</a>`;
}

/**
 * Get column configuration for Spare Parts table
 * @returns {Array} Column configuration array
 */
function getSparePartsColumns() {
  return [
    {
      key: "id",
      label: "ID",
      type: "number",
      render: renderSparePartId,
    },
    { key: "description", label: "Description", type: "text" },
    { key: "manufacturer", label: "Manufacturer", type: "text" },
    { key: "manufacturer_part_id", label: "Part ID", type: "text" },
    { key: "stock_quantity", label: "Stock Qty", type: "number" },
    { key: "location", label: "Location", type: "text" },
    { key: "min_quantity", label: "Min Qty", type: "number" },
  ];
}

/**
 * Initialize Spare Parts table
 */
function initSparePartsTable() {
  const sparePartsDataElement = document.getElementById("spare-parts-data");
  if (sparePartsDataElement) {
    const sparePartsData = JSON.parse(sparePartsDataElement.textContent);
    initAdvancedTable(
      "sparePartsTable",
      sparePartsData,
      getSparePartsColumns(),
      25,
    );
  }
}

// Initialize table on DOM load (browser only)
if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", initSparePartsTable);
}

// Export for testing (CommonJS)
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    renderSparePartId,
    getSparePartsColumns,
    initSparePartsTable,
  };
}
