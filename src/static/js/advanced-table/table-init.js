/**
 * Initialize an AdvancedTable instance.
 * @param {string} containerId - The ID of the container element.
 * @param {Array} data - The data array.
 * @param {Array} columns - The column definitions.
 * @param {number} [pageSize=25] - The number of rows per page.
 * @returns {AdvancedTable|null} The initialized table instance or null if container not found.
 */
function initAdvancedTable(containerId, data, columns, pageSize = 0) {
  const container = document.getElementById(containerId);
  if (!container) {
    console.error(`Container with ID '${containerId}' not found`);
    return null;
  }

  // Note: AdvancedTable constructor sets window.advTable
  return new AdvancedTable(containerId, {
    data: data,
    columns: columns,
    pageName: containerId,
    pageSize: pageSize,
  });
}

// Export for testing
if (typeof module !== "undefined" && module.exports) {
  module.exports = { initAdvancedTable };
}
