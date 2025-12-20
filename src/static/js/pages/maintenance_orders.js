// Maintenance Orders list initialization
document.addEventListener("DOMContentLoaded", function () {
  const mosDataElement = document.getElementById("mos-data");
  if (!mosDataElement) return;

  try {
    const mosData = JSON.parse(mosDataElement.textContent);

    // Bug #29: Clear localStorage if 'assignees' column is missing
    const tableStateKey = "tableState_mosTable";
    try {
      const savedStateJSON = localStorage.getItem(tableStateKey);
      if (savedStateJSON) {
        const savedState = JSON.parse(savedStateJSON);
        // Check if columnOrder exists and if 'assignees' is missing from it
        if (
          savedState.columnOrder &&
          !savedState.columnOrder.includes("assignees")
        ) {
          localStorage.removeItem(tableStateKey);
          console.log(
            "Cleared outdated table state for 'mosTable' to show new 'Assignees' column.",
          );
        }
      }
    } catch (e) {
      console.error("Error processing table state from localStorage:", e);
      localStorage.removeItem(tableStateKey); // Clear corrupted state
    }

    const columns = [
      {
        key: "id",
        label: "ID",
        type: "number",
        render: function (val, row) {
          return `<a href="/maintenance_orders/${row.id}">${val}</a>`;
        },
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

    // Use initAdvancedTable instead of direct instantiation
    if (typeof initAdvancedTable === "function") {
      initAdvancedTable("mosTable", mosData, columns, 25);
    } else {
      console.error("initAdvancedTable is not defined");
    }
  } catch (error) {
    console.error("Error initializing maintenance orders table:", error);
  }
});
