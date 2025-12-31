/* global initAdvancedTable */
document.addEventListener("DOMContentLoaded", function () {
  const columns = [
    {
      key: "id",
      label: "ID",
      type: "number",
      render: function (val, row) {
        return `<a href="/assets/${row.id}">${val}</a>`;
      },
    },
    { key: "asset_code", label: "Asset Code", type: "text" },
    { key: "name", label: "Name", type: "text" },
    { key: "description", label: "Description", type: "text" },
    { key: "asset_type", label: "Type", type: "text" },
    { key: "cost_center", label: "Cost Center", type: "text" },
    { key: "status", label: "Status", type: "text" },
  ];

  const assetsData = JSON.parse(
    document.getElementById("assets-data").textContent,
  );

  // Use initAdvancedTable instead of direct instantiation
  initAdvancedTable("assetsTable", assetsData, columns, 25);
});
