// Assets list initialization
document.addEventListener("DOMContentLoaded", function () {
  const assetsDataElement = document.getElementById("assets-data");
  if (!assetsDataElement) return;

  try {
    const assetsData = JSON.parse(assetsDataElement.textContent);
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

    // Use initAdvancedTable instead of direct instantiation
    if (typeof initAdvancedTable === "function") {
      initAdvancedTable("assetsTable", assetsData, columns, 25);
    } else {
      console.error("initAdvancedTable is not defined");
    }
  } catch (error) {
    console.error("Error initializing assets table:", error);
  }
});
