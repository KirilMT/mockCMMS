/* global initAdvancedTable */
document.addEventListener("DOMContentLoaded", function () {
  const columns = [
    {
      key: "id",
      label: "ID",
      type: "number",
      render: function (val, row) {
        return `<a href="/users/${row.id}">${val}</a>`;
      },
    },
    {
      key: "username",
      label: "Username",
      type: "text",
      render: function (val, row) {
        // Add warning icon if technician without team assignment
        if (row.is_technician && !row.team_id) {
          return (
            val +
            ' <span title="Technician not assigned to a shift team. Cannot be assigned weekend tasks." class="text-warning-custom">⚠️</span>'
          );
        }
        return val;
      },
    },
    { key: "email", label: "Email", type: "text" },
    { key: "roles_display", label: "Roles", type: "text" },
    {
      key: "team_name",
      label: "Team",
      type: "text",
      // eslint-disable-next-line no-unused-vars
      render: function (val, row) {
        // Show team for any user, not just technicians
        return val || '<span class="text-muted">Unassigned</span>';
      },
    },
    { key: "is_active", label: "Active", type: "text" },
    {
      key: "availability_status",
      label: "Availability",
      type: "text",
      render: function (val, row) {
        // Only show if user has Technician role
        if (!row.is_technician) return "-";
        if (val === "Available")
          return '<span class="badge badge-success">Available</span>';
        if (val === "On Leave")
          return '<span class="badge badge-warning">On Leave</span>';
        if (val === "Sick")
          return '<span class="badge badge-danger">Sick</span>';
        return val || "-";
      },
    },
    { key: "created_at", label: "Created", type: "datetime" },
  ];

  const usersData = JSON.parse(document.getElementById("users-data").textContent);

  // Use initAdvancedTable instead of direct instantiation
  initAdvancedTable("usersTable", usersData, columns, 25);
});
