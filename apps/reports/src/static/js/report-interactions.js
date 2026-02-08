(function () {
  "use strict";

  let editModal = null;
  let addModal = null;
  let deleteConfirmModal = null;

  // State to track what we are editing/deleting
  let currentContext = {
    section: null,
    index: null,
    action: null, // 'edit' or 'add'
  };

  document.addEventListener("DOMContentLoaded", function () {
    // Bootstrap 4 uses jQuery, no class initialization needed for these globals

    // Save Edit button
    const saveEditBtn = document.getElementById("saveEditBtn");
    if (saveEditBtn) saveEditBtn.addEventListener("click", handleSaveEdit);

    // Save Add button
    const saveAddBtn = document.getElementById("saveAddBtn");
    if (saveAddBtn) saveAddBtn.addEventListener("click", handleSaveAdd);

    // Confirm Delete button
    const confirmDelBtn = document.getElementById("confirmReportDeleteBtn");
    if (confirmDelBtn)
      confirmDelBtn.addEventListener("click", handleConfirmDelete);

    // Copy Markdown button
    const copyBtn = document.getElementById("copyMdBtn");
    if (copyBtn) copyBtn.addEventListener("click", handleCopyMarkdown);
  });

  /**
   * Opens the Edit Modal and populates fields based on section
   */
  window.openEditModal = function (section, title, dataJson, index) {
    currentContext.section = section;
    currentContext.index = index;
    currentContext.action = "edit";

    document.getElementById("editModalLabel").textContent = "Edit " + title;

    // Hide all form containers first
    hideAllForms("edit-forms");

    // ... existing parsing logic ...
    let content = dataJson;
    if (typeof dataJson === "string") {
      try {
        content = JSON.parse(dataJson);
      } catch (e) {
        content = { description: dataJson };
      }
    }

    // Populate specific form ... (reuse existing logic)
    populateEditForm(section, content);

    $("#editModal").modal("show");
  };

  /**
   * Opens the Add Modal
   */
  window.openAddModal = function (section, title) {
    currentContext.section = section;
    currentContext.action = "add";
    currentContext.index = null;

    document.getElementById("addModalLabel").textContent = "Add " + title;

    hideAllForms("add-forms");
    clearAllInputs("addModal");

    populateAddForm(section);

    $("#addModal").modal("show");
  };

  window.deleteItem = function (section, index) {
    currentContext.section = section;
    currentContext.index = index;
    currentContext.action = "delete";
    $("#reportDeleteConfirmModal").modal("show");
  };

  // ... helper functions ...

  function handleSaveEdit() {
    const data = getFormData("edit");
    sendUpdate(data);
    $("#editModal").modal("hide");
  }

  function handleSaveAdd() {
    const data = getFormData("add");
    sendUpdate(data);
    $("#addModal").modal("hide");
  }

  function handleConfirmDelete() {
    sendUpdate({});
    $("#reportDeleteConfirmModal").modal("hide");
  }

  // Refactored logic to separate population for clarity and reuse
  function populateEditForm(section, content) {
    if (section === "header") {
      showForm("edit-header-form");
      setVal("edit-header-date", content.date);
      setVal("edit-header-shift", content.shift);
      setVal("edit-header-team", content.team_name);
      setVal("edit-header-color", content.team_color || "#e74c3c");
    } else if (section === "metadata") {
      showForm("edit-metadata-form");
      setVal("edit-metadata-value", content.value || content);
      document.getElementById("edit-metadata-key").value = content.key || "";
    } else if (["handover_from", "handover_to", "handover"].includes(section)) {
      showForm("edit-handover-form");
      setVal("edit-handover-asset", content.asset || "");
      setVal("edit-handover-title", content.title || "");
      setVal(
        "edit-handover-desc",
        content.description || (typeof content === "string" ? content : ""),
      );
    } else if (section === "breakdown") {
      showForm("edit-breakdown-form");
      setVal("edit-bd-asset", content.equipment_line || content.asset || "");
      setVal("edit-bd-time", content.timestamp || "");
      setVal("edit-bd-duration", content.duration || "");
      setVal("edit-bd-fault", content.description || "");
      setVal("edit-bd-root", content.root_cause || "");
      setVal(
        "edit-bd-recovery",
        content.resolution_notes || content.recovery || "",
      );
    } else if (section === "activities") {
      showForm("edit-activity-form");
      setVal("edit-act-asset", content.asset || "");
      setVal("edit-act-desc", content.description || "");
    } else if (["pms", "mos", "additional"].includes(section)) {
      showForm("edit-simple-task-form");
      setVal("edit-task-asset", content.asset || "");
      setVal("edit-task-desc", content.description || "");
      setVal("edit-task-status", content.status || "");
      if (["mos", "additional"].includes(section)) {
        setVal("edit-task-id", content.id || "");
        document.getElementById("edit-task-id-group").style.display = "block";
      } else {
        document.getElementById("edit-task-id-group").style.display = "none";
      }
    } else {
      showForm("edit-generic-form");
      setVal(
        "edit-generic-content",
        typeof content === "string" ? content : JSON.stringify(content),
      );
    }
  }

  function populateAddForm(section) {
    if (["handover_from", "handover_to", "handover"].includes(section)) {
      showForm("add-handover-form");
    } else if (section === "breakdown") {
      showForm("add-breakdown-form");
      const now = new Date();
      const timeStr =
        now.getHours().toString().padStart(2, 0) +
        ":" +
        now.getMinutes().toString().padStart(2, 0);
      setVal("add-bd-time", timeStr);
    } else if (section === "activities") {
      showForm("add-activity-form");
    } else if (["pms", "mos", "additional"].includes(section)) {
      showForm("add-simple-task-form");
      if (["mos", "additional"].includes(section))
        document.getElementById("add-task-id-group").style.display = "block";
      else document.getElementById("add-task-id-group").style.display = "none";
    } else {
      showForm("add-generic-form");
    }
  }

  /* --- Markdown Copy --- */
  function handleCopyMarkdown() {
    const data = window.reportData; // This needs to be populated in template
    if (!data) return;

    let md = "";

    // Header
    const shiftInfo = data.shiftInfo || {};
    md += `# ${data.reportType === "shift" ? "Shift" : "Weekend"} Report\n`;
    md += `**Date:** ${shiftInfo.date || data.weekend_date || "N/A"}\n`;
    if (shiftInfo.shift) md += `**Shift:** ${shiftInfo.shift}\n`;
    md += `**Team:** ${data.teamName}\n\n`;

    // Metadata
    md += `**Attendance:** ${data.attendance}\n`;
    md += `**EHS incidents:** ${data.ehsIncidents}\n`;
    if (data.vigel) md += `**VIGEL:** ${data.vigel}\n`;
    if (data.mds) md += `**MDS:** ${data.mds}\n`;
    md += "\n";

    // Handover From (Shift)
    if (data.reportType === "shift") {
      md += "## Handover from previous Shift\n";
      renderList(shiftInfo.handover_from_previous);
      md += "\n";
    }

    // Breakdowns
    md += "## Breakdowns\n";
    if (data.breakdowns && data.breakdowns.length > 0) {
      data.breakdowns.forEach((bd) => {
        // Formatting: Line 1 - Time: Asset - Fault. related to..
        // The user wanted:
        // - **Line 1** - 2026-02-08 08:30: Seed Breakdown 1 - Robot Arm Stuck. Related to MO #101.
        // We will try our best with available fields
        let line = `- **${bd.equipment_line || bd.asset || "Unknown Asset"}**`;
        line += ` - ${bd.timestamp || ""}:`;
        line += ` ${bd.description || ""}`;
        if (bd.root_cause) line += ` - Root Cause: ${bd.root_cause}`;
        if (bd.resolution_notes) line += ` - Recovery: ${bd.resolution_notes}`;
        if (bd.duration) line += ` (Duration: ${bd.duration})`;
        md += line + "\n";
      });
    } else {
      md += "- No breakdowns\n";
    }
    md += "\n";

    // Activities / Engineering Support
    md += "## Engineering Support / Break Activities\n";
    renderSimpleList(data.activities);
    md += "\n";

    // PMs (Weekend)
    if (data.pms) {
      md += "## PMs\n";
      renderSimpleList(data.pms);
      md += "\n";
    }

    // MOs (Weekend)
    if (data.mos) {
      md += "## MOs/Tickets\n";
      renderSimpleList(data.mos);
      md += "\n";
    }

    // Handover To
    md += "## Handover to next Shift / Instructions\n";
    const hoTo = shiftInfo.handover_to_next || data.handover_instructions;
    renderList(hoTo);
    md += "\n";

    // Footer
    md += "---\n";
    md += `Generated by: **${data.generatedBy}**`;

    // Copy
    navigator.clipboard
      .writeText(md)
      .then(function () {
        if (window.ToastNotification)
          ToastNotification.success("Markdown copied to clipboard!");
        else alert("Copied!");
      })
      .catch(function (err) {
        console.error(err);
        if (window.ToastNotification) ToastNotification.error("Failed to copy");
      });

    function renderList(list) {
      if (list && list.length > 0) {
        list.forEach((item) => {
          if (typeof item === "string") {
            md += `- ${item}\n`;
          } else {
            md += `- **${item.asset || ""}**: ${item.title || ""} - ${item.description || ""}\n`;
          }
        });
      } else {
        md += "- None\n";
      }
    }

    function renderSimpleList(list) {
      if (list && list.length > 0) {
        list.forEach((item) => {
          md += `- **${item.asset || "Asset"}** - ${item.description || ""} ${item.status ? "(" + item.status + ")" : ""}\n`;
        });
      } else {
        md += "- None\n";
      }
    }
  }

  /* --- Helpers --- */

  function getFormData(type) {
    const data = {
      section: currentContext.section,
      index: currentContext.index,
      action: currentContext.action,
    };

    if (type === "edit") {
      if (currentContext.section === "header") {
        data.date = getVal("edit-header-date");
        data.shift = getVal("edit-header-shift");
        data.team_name = getVal("edit-header-team");
        // Color is now derived from team name, but we can send it if needed or handle in backend
        // We will send it for now to maintain compatibility if backend expects it
        data.team_color = getTeamColor(data.team_name);
      } else if (currentContext.section === "metadata") {
        data.key = getVal("edit-metadata-key");
        data.value = getVal("edit-metadata-value");
      } else if (
        ["handover_from", "handover_to", "handover"].includes(currentContext.section)
      ) {
        data.asset = getVal("edit-handover-asset");
        data.title = getVal("edit-handover-title");
        data.description = getVal("edit-handover-desc");
      } else if (currentContext.section === "breakdown") {
        data.asset = getVal("edit-bd-asset");
        data.timestamp = getVal("edit-bd-time");
        data.duration = getVal("edit-bd-duration");
        data.description = getVal("edit-bd-fault");
        data.root_cause = getVal("edit-bd-root");
        data.resolution_notes = getVal("edit-bd-recovery");
      } else if (currentContext.section === "activities") {
        data.asset = getVal("edit-act-asset");
        data.description = getVal("edit-act-desc");
      } else if (["pms", "mos", "additional"].includes(currentContext.section)) {
        data.asset = getVal("edit-task-asset");
        data.description = getVal("edit-task-desc");
        data.status = getVal("edit-task-status");
        if (["mos", "additional"].includes(currentContext.section)) {
          data.id = getVal("edit-task-id");
        }
      } else {
        // Generic JSON fallback
        try {
          data.content = JSON.parse(getVal("edit-generic-content"));
        } catch (e) {
          data.content = getVal("edit-generic-content");
        }
      }
    } else if (type === "add") {
      // Similar logic for Accessing Add Fields
      if (
        ["handover_from", "handover_to", "handover"].includes(currentContext.section)
      ) {
        data.asset = getVal("add-handover-asset");
        data.title = getVal("add-handover-title");
        data.description = getVal("add-handover-desc");
      } else if (currentContext.section === "breakdown") {
        data.asset = getVal("add-bd-asset");
        data.timestamp = getVal("add-bd-time");
        data.duration = getVal("add-bd-duration");
        data.description = getVal("add-bd-fault");
        data.root_cause = getVal("add-bd-root");
        data.resolution_notes = getVal("add-bd-recovery");
      } else if (currentContext.section === "activities") {
        data.asset = getVal("add-act-asset");
        data.description = getVal("add-act-desc");
      } else if (["pms", "mos", "additional"].includes(currentContext.section)) {
        data.asset = getVal("add-task-asset");
        data.description = getVal("add-task-desc");
        data.status = getVal("add-task-status");
        if (["mos", "additional"].includes(currentContext.section)) {
          data.id = getVal("add-task-id");
        }
      }
    }

    return data;
  }

  function getTeamColor(teamName) {
    // Standardize A=Blue, B=Yellow, C=Green, D=Red logic or similar
    // Based on user request 1.3: "Color of shit is related to colors assigned to Teams"
    // I need to know the mapping. Assuming standard for now or helper function.
    if (!teamName) return "#e74c3c"; // Default red
    const name = teamName.toLowerCase();
    if (name.includes("team a")) return "#3498db"; // Blue
    if (name.includes("team b")) return "#f1c40f"; // Yellow
    if (name.includes("team c")) return "#2ecc71"; // Green
    if (name.includes("team d")) return "#e74c3c"; // Red
    return "#95a5a6"; // Grey default
  }

  function sendUpdate(data) {
    const reportId = window.location.pathname.split("/").pop();
    const url = `/reports/${reportId}/update`;

    fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        // Add CSRF token if needed, usually in meta tag
        // 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
      },
      body: JSON.stringify(data),
    })
      .then((response) => response.json())
      .then((result) => {
        if (result.success) {
          if (window.ToastNotification)
            ToastNotification.success("Update successful");
          else alert("Update successful");
          // Reload to show changes
          setTimeout(() => location.reload(), 500);
        } else {
          if (window.ToastNotification)
            ToastNotification.error("Update failed: " + result.error);
          else alert("Update failed: " + result.error);
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        if (window.ToastNotification)
          ToastNotification.error("An error occurred");
        else alert("An error occurred");
      });
  }

  function hideAllForms(parentId) {
    // parentID is descriptive ID I imagined in HTML, we will rely on class
    // I will implement looking for .modal-form-content
    document
      .querySelectorAll(".modal-form-content")
      .forEach((el) => (el.style.display = "none"));
  }

  function showForm(id) {
    const el = document.getElementById(id);
    if (el) {
      el.closest(".modal-form-content").style.display = "block";
    }
    // Actually, if I wrap each form in a div with id...
    const formDiv = document.getElementById(id);
    if (formDiv) formDiv.style.display = "block";
  }

  function setVal(id, val) {
    const el = document.getElementById(id);
    if (el) el.value = val;
  }

  function getVal(id) {
    const el = document.getElementById(id);
    return el ? el.value : "";
  }

  function clearAllInputs(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal
        .querySelectorAll("input, textarea, select")
        .forEach((input) => (input.val = ""));
    }
  }
})();


