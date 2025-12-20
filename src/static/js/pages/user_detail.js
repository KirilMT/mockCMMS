// User Detail Page Scripts
document.addEventListener("DOMContentLoaded", function () {
  const rolesSelect = document.getElementById("roles");
  const teamGroup = document.getElementById("team-group");

  function updateFields() {
    const selectedOptions = Array.from(rolesSelect.selectedOptions).map(
      (opt) => opt.value,
    );
    if (selectedOptions.includes("Technician")) {
      teamGroup.style.display = "block";
    } else {
      teamGroup.style.display = "none";
    }
  }

  // Run on load
  if (rolesSelect && teamGroup) {
    updateFields();
    // Run on change
    rolesSelect.addEventListener("change", updateFields);
  }
});
