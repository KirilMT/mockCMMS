/* global initAdvancedTable */
document.addEventListener("DOMContentLoaded", function () {
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

  const sparePartsData = JSON.parse(
    document.getElementById("spare-parts-data").textContent,
  );

  // Use initAdvancedTable instead of direct instantiation
  initAdvancedTable("sparePartsTable", sparePartsData, columns, 25);
});
