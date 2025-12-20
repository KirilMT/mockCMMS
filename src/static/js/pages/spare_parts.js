// Spare Parts list initialization
document.addEventListener("DOMContentLoaded", function () {
  const sparePartsDataElement = document.getElementById("spare-parts-data");
  if (!sparePartsDataElement) return;

  try {
    const sparePartsData = JSON.parse(sparePartsDataElement.textContent);
    const columns = [
      {
        key: "id",
        label: "ID",
        type: "number",
        render: function (val, row) {
          return `<a href="/spare_parts/${row.id}">${val}</a>`;
        },
      },
      { key: "description", label: "Description", type: "text" },
      { key: "manufacturer", label: "Manufacturer", type: "text" },
      { key: "manufacturer_part_id", label: "Part ID", type: "text" },
      { key: "stock_quantity", label: "Stock Qty", type: "number" },
      { key: "location", label: "Location", type: "text" },
      { key: "min_quantity", label: "Min Qty", type: "number" },
    ];

    // Use initAdvancedTable instead of direct instantiation
    if (typeof initAdvancedTable === "function") {
      initAdvancedTable("sparePartsTable", sparePartsData, columns, 25);
    } else {
      console.error("initAdvancedTable is not defined");
    }
  } catch (error) {
    console.error("Error initializing spare parts table:", error);
  }
});
