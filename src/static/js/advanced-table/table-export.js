// Export and utility methods

/**
 * Exports the current filtered table data.
 * @param {string} format - The format to export to (default: "csv").
 */
AdvancedTable.prototype.exportData = function (format = "csv") {
  const filteredData = this.getFilteredData();
  if (format === "csv") {
    this.exportCSV(filteredData);
  }
};

/**
 * Exports data to CSV format and triggers a file download.
 * @param {Array<Object>} data - The data to export.
 */
AdvancedTable.prototype.exportCSV = function (data) {
  const visibleColumns = this.columnOrder.filter(
    (key) => !this.hiddenColumns.has(key),
  );
  const headers = visibleColumns.map(
    (key) => this.columns.find((c) => c.key === key).label,
  );

  let csv = headers.join(",") + "\n";
  data.forEach((row) => {
    const values = visibleColumns.map((key) => {
      const value = row[key] || "";
      return `"${value.toString().replace(/"/g, '""')}"`;
    });
    csv += values.join(",") + "\n";
  });

  // Generate filename with date and time
  const now = new Date();
  const dateStr = now.toISOString().slice(0, 10); // YYYY-MM-DD
  const timeStr = now.toTimeString().slice(0, 8).replace(/:/g, "-"); // HH-MM-SS
  const filename = `${this.pageName}_${dateStr}_${timeStr}.csv`;

  const blob = new Blob([csv], { type: "text/csv" });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  window.URL.revokeObjectURL(url);
};

/**
 * Navigates the table to a specific page.
 * @param {number} page - The page number to navigate to (1-based).
 */
AdvancedTable.prototype.goToPage = function (page) {
  const filteredData = this.getFilteredData();
  const totalPages = Math.ceil(filteredData.length / this.pageSize);

  if (page >= 1 && page <= totalPages) {
    this.currentPage = page;
    this.render();
  }
};
