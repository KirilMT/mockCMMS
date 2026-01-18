/* global initAdvancedTable */

/**
 * Render functions for Users table columns
 * Exported for testing purposes
 */

/**
 * Render user ID as a link to user detail page
 * @param {number|string} val - The ID value
 * @param {Object} row - The row data
 * @returns {string} HTML link string
 */
function renderUserId(val, row) {
  return `<a href="/users/${row.id}">${val}</a>`;
}

/**
 * Render username with warning icon for technicians without team assignment
 * @param {string} val - The username value
 * @param {Object} row - The row data containing is_technician and team_id
 * @returns {string} Username with optional warning icon
 */
function renderUsername(val, row) {
  if (row.is_technician && !row.team_id) {
    return (
      val +
      ' <span title="Technician not assigned to a shift team. Cannot be assigned weekend tasks." class="text-warning-custom">⚠️</span>'
    );
  }
  return val;
}

/**
 * Render team name or "Unassigned" placeholder
 * @param {string|null} val - The team name value
 * @returns {string} Team name or Unassigned span
 */
function renderTeam(val) {
  return val || '<span class="text-muted">Unassigned</span>';
}

/**
 * Render availability status badge for technicians
 * @param {string|null} val - The availability status
 * @param {Object} row - The row data containing is_technician
 * @returns {string} Badge HTML or dash for non-technicians
 */
function renderAvailability(val, row) {
  if (!row.is_technician) return "-";
  if (val === "Available")
    return '<span class="badge badge-success">Available</span>';
  if (val === "On Leave")
    return '<span class="badge badge-warning">On Leave</span>';
  if (val === "Sick") return '<span class="badge badge-danger">Sick</span>';
  return val || "-";
}

/**
 * Get column configuration for the Users table
 * @returns {Array} Column configuration array
 */
function getUsersColumns() {
  return [
    {
      key: "id",
      label: "ID",
      type: "number",
      render: renderUserId,
    },
    {
      key: "username",
      label: "Username",
      type: "text",
      render: renderUsername,
    },
    { key: "email", label: "Email", type: "text" },
    { key: "roles_display", label: "Roles", type: "text" },
    {
      key: "team_name",
      label: "Team",
      type: "text",
      render: renderTeam,
    },
    { key: "is_active", label: "Active", type: "text" },
    {
      key: "availability_status",
      label: "Availability",
      type: "text",
      render: renderAvailability,
    },
    { key: "created_at", label: "Created", type: "datetime" },
  ];
}

/**
 * Initialize Users table
 */
function initUsersTable() {
  const usersDataElement = document.getElementById("users-data");
  if (usersDataElement) {
    const usersData = JSON.parse(usersDataElement.textContent);
    initAdvancedTable("usersTable", usersData, getUsersColumns(), 0);
  }
}

// Initialize table on DOM load (browser only)
if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", initUsersTable);
}

// Export for testing (CommonJS)
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    renderUserId,
    renderUsername,
    renderTeam,
    renderAvailability,
    getUsersColumns,
    initUsersTable,
  };
}
