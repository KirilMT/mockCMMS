(function () {
  "use strict";

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

    // Cleanup Select2 when modals are hidden
    $("#editModal").on("hidden.bs.modal", function () {
      const selectors = [
        "#edit-handover-asset",
        "#edit-bd-asset",
        "#edit-act-asset",
        "#edit-task-asset",
      ];
      selectors.forEach((selector) => {
        const $el = $(selector);
        if ($el.length && $el.hasClass("select2-hidden-accessible")) {
          try {
            $el.select2("destroy");
          } catch (e) {
            // Silently ignore if already destroyed
            console.debug("Select2 cleanup:", selector, e.message);
          }
        }
      });
    });
    $("#addModal").on("hidden.bs.modal", function () {
      const selectors = [
        "#add-handover-asset",
        "#add-bd-asset",
        "#add-act-asset",
        "#add-task-asset",
      ];
      selectors.forEach((selector) => {
        const $el = $(selector);
        if ($el.length && $el.hasClass("select2-hidden-accessible")) {
          try {
            $el.select2("destroy");
          } catch (e) {
            // Silently ignore if already destroyed
            console.debug("Select2 cleanup:", selector, e.message);
          }
        }
      });
    });
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

    // Validation for Metadata Totals
    if (currentContext.section === "metadata") {
      const valInput = document.getElementById("edit-metadata-value");
      const maxTotal = valInput.getAttribute("data-max-total");
      if (maxTotal) {
        const numVal = parseInt(data.value);
        const numMax = parseInt(maxTotal);
        if (!isNaN(numVal) && !isNaN(numMax)) {
          if (numVal > numMax) {
            if (window.ToastNotification)
              ToastNotification.error(`Value cannot exceed total (${numMax})`);
            else alert(`Value cannot exceed total (${numMax})`);
            return; // Stop save
          }
        }
      }
    }

    if (!data || Object.keys(data).length <= 3) {
      if (window.ToastNotification) ToastNotification.error("No data to save");
      return;
    }
    sendUpdate(data);
    $("#editModal").modal("hide");
  }

  function handleSaveAdd() {
    const data = getFormData("add");
    if (!data || Object.keys(data).length <= 3) {
      if (window.ToastNotification)
        ToastNotification.error("Please fill in the required fields");
      return;
    }
    sendUpdate(data);
    $("#addModal").modal("hide");
  }

  function handleConfirmDelete() {
    const data = {
      section: currentContext.section,
      index: currentContext.index,
      action: "delete",
    };
    sendUpdate(data);
    $("#reportDeleteConfirmModal").modal("hide");
  }

  // Refactored logic to separate population for clarity and reuse
  function populateEditForm(section, content) {
    // Helper to handle [object Object] serialization issues
    const safeVal = (val) =>
      typeof val === "object" && val !== null ? val.value || "" : val || "";

    if (section === "header") {
      showForm("edit-header-form");
      setVal("edit-header-date", content.date || "");
      setVal("edit-header-shift", content.shift || "Early");
      setVal("edit-header-team", content.team_name || "");
      // Color is hidden and derived from team
      setVal("edit-header-color", content.team_color || "");
    } else if (section === "metadata") {
      showForm("edit-metadata-form");
      // Handle the value - it might be passed as {key: "attendance", value: "N/A", total: ...}
      let actualValue = "";
      let metadataTotal = null;

      if (typeof content === "object" && content !== null) {
        // Fix for fallback to key: If value is undefined or null, use empty string.
        // Only if value is strictly missing from object we might consider something else,
        // but content.value || content.key was causing the bug where key name appeared.
        actualValue =
          content.value !== undefined && content.value !== null
            ? content.value
            : "";
        document.getElementById("edit-metadata-key").value = content.key || "";
        if (content.total) metadataTotal = content.total;
      } else {
        actualValue = safeVal(content);
      }
      setVal("edit-metadata-value", actualValue);

      // Store total in a data attribute on the input for validation later
      const inputEl = document.getElementById("edit-metadata-value");
      if (metadataTotal !== null) {
        inputEl.setAttribute("data-max-total", metadataTotal);
        inputEl.placeholder = `Max: ${metadataTotal}`;
      } else {
        inputEl.removeAttribute("data-max-total");
        inputEl.placeholder = "Enter value";
      }
    } else if (["handover_from", "handover_to", "handover"].includes(section)) {
      showForm("edit-handover-form");
      // Handle both string and object formats
      if (typeof content === "string") {
        setVal("edit-handover-asset", "");
        setVal("edit-handover-title", "");
        setVal("edit-handover-desc", content);
      } else {
        setVal("edit-handover-asset", content.asset || "");
        setVal("edit-handover-title", content.title || "");
        setVal("edit-handover-desc", content.description || "");
      }
      // Initialize Select2 for asset dropdown
      setTimeout(() => {
        $("#edit-handover-asset").select2({
          tags: true,
          placeholder: "Select Asset or type custom...",
          dropdownParent: $("#editModal"),
        });
      }, 100);
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
      // Initialize Select2 for asset dropdown
      setTimeout(() => {
        $("#edit-bd-asset").select2({
          tags: true,
          placeholder: "Select Asset or type custom...",
          dropdownParent: $("#editModal"),
        });
      }, 100);
    } else if (section === "activities") {
      showForm("edit-activity-form");
      const actType = content.type || "flux_ticket";
      setVal("edit-act-type", actType);
      setVal("edit-act-asset", content.asset || "");
      setVal("edit-act-mo-id", content.mo_id || "");
      setVal("edit-act-title", content.title || "");
      setVal("edit-act-desc", content.description || "");
      setVal("edit-act-status", content.status || "");

      // Toggle fields based on type
      setTimeout(() => {
        // Initialize Select2 for asset dropdown
        $("#edit-act-asset").select2({
          tags: true,
          placeholder: "Select Asset or type custom...",
          dropdownParent: $("#editModal"),
        });
        toggleActivityFields("edit");
        $("#edit-act-type").on("change", () => toggleActivityFields("edit"));
      }, 50);
    } else if (section === "flux_tickets") {
      showForm("edit-activity-form");
      // Force type to flux_ticket
      setVal("edit-act-type", "flux_ticket");
      setVal("edit-act-asset", content.asset || "");
      setVal("edit-act-mo-id", content.mo_id || "");
      setVal("edit-act-desc", content.description || "");
      setVal("edit-act-status", content.status || "");

      // Hide type selector if editing specific item? Or allow changing?
      // For now, allow changing, but default to flux_ticket.

      setTimeout(() => {
        $("#edit-act-asset").select2({
          tags: true,
          dropdownParent: $("#editModal"),
        });
        toggleActivityFields("edit");
        $("#edit-act-type").on("change", () => toggleActivityFields("edit"));
      }, 50);
    } else if (section === "engineering_support") {
      showForm("edit-activity-form");
      // Force type
      setVal("edit-act-type", "engineering_support");
      setVal("edit-act-asset", content.asset || "");
      setVal("edit-act-title", content.title || "");
      setVal("edit-act-desc", content.description || "");

      setTimeout(() => {
        $("#edit-act-asset").select2({
          tags: true,
          dropdownParent: $("#editModal"),
        });
        toggleActivityFields("edit");
        $("#edit-act-type").on("change", () => toggleActivityFields("edit"));
      }, 50);
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
      // Initialize Select2 for asset dropdown
      setTimeout(() => {
        $("#edit-task-asset").select2({
          tags: true,
          placeholder: "Select Asset or type custom...",
          dropdownParent: $("#editModal"),
        });
      }, 100);
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
      // Initialize Select2 for asset dropdown
      setTimeout(() => {
        $("#add-handover-asset").select2({
          tags: true,
          placeholder: "Select Asset or type custom...",
          dropdownParent: $("#addModal"),
        });
      }, 100);
    } else if (section === "breakdown") {
      showForm("add-breakdown-form");
      const now = new Date();
      const timeStr =
        now.getHours().toString().padStart(2, 0) +
        ":" +
        now.getMinutes().toString().padStart(2, 0);
      setVal("add-bd-time", timeStr);
      // Initialize Select2 for asset dropdown
      setTimeout(() => {
        $("#add-bd-asset").select2({
          tags: true,
          placeholder: "Select Asset or type custom...",
          dropdownParent: $("#addModal"),
        });
      }, 100);
    } else if (section === "activities") {
      showForm("add-activity-form");
      // Set up type change handler
      setTimeout(() => {
        // Initialize Select2 for asset dropdown
        $("#add-act-asset").select2({
          tags: true,
          placeholder: "Select Asset or type custom...",
          dropdownParent: $("#addModal"),
        });
        toggleActivityFields("add");
        $("#add-act-type").on("change", () => toggleActivityFields("add"));
      }, 50);
    } else if (["pms", "mos", "additional"].includes(section)) {
      showForm("add-simple-task-form");
      if (["mos", "additional"].includes(section))
        document.getElementById("add-task-id-group").style.display = "block";
      else document.getElementById("add-task-id-group").style.display = "none";
      // Initialize Select2 for asset dropdown
      setTimeout(() => {
        $("#add-task-asset").select2({
          tags: true,
          placeholder: "Select Asset or type custom...",
          dropdownParent: $("#addModal"),
        });
      }, 100);
    } else {
      showForm("add-generic-form");
    }
  }

  /* --- Markdown Copy --- */
  function handleCopyMarkdown() {
    const data = window.reportData; // This needs to be populated in template
    if (!data) return;

    let html = "";

    // Header
    const shiftInfo = data.shiftInfo || {};
    html += `<h2><strong>${data.reportType === "shift" ? "Shift" : "Weekend"} Report</strong></h2>`;
    html += `<p><strong>Date:</strong> ${shiftInfo.date || data.weekend_date || "N/A"}<br>`;
    if (shiftInfo.shift)
      html += `<strong>Shift:</strong> ${shiftInfo.shift}<br>`;
    html += `<strong>Team:</strong> ${data.teamName}</p>`;

    // Metadata
    html += `<p><strong>Attendance:</strong> ${data.attendance}<br>`;

    // EHS incidents with conditional color
    const ehsColor = data.ehsIncidents >= 1 ? "#dc3545" : "#28a745"; // red or green
    html += `<strong>EHS incidents:</strong> <span style="color: ${ehsColor}; font-weight: bold;">${data.ehsIncidents}</span><br>`;

    if (data.vigel) html += `<strong>VIGEL:</strong> ${data.vigel}<br>`;
    if (data.mds) html += `<strong>MDS:</strong> ${data.mds}</p>`;

    // Handover From (Shift)
    if (data.reportType === "shift") {
      html +=
        '<h3 style="color: #558b2f;"><strong>Handover from previous Shift</strong></h3>';
      html += renderListHTML(shiftInfo.handover_from_previous);
    }

    // Breakdowns
    html += '<h3 style="color: #558b2f;"><strong>Breakdowns:</strong></h3>';
    if (data.breakdowns && data.breakdowns.length > 0) {
      data.breakdowns.forEach((bd, index) => {
        const lineNum = index + 1;
        const asset = bd.equipment_line || bd.asset || `Line ${lineNum}`;

        // Extract time only (HH:MM format)
        let timeOnly = "";
        if (bd.timestamp) {
          // If timestamp includes date (YYYY-MM-DD HH:MM), extract time part
          if (bd.timestamp.includes(" ")) {
            timeOnly = bd.timestamp.split(" ")[1] || bd.timestamp;
          } else {
            timeOnly = bd.timestamp;
          }
          // Remove seconds if present (HH:MM:SS -> HH:MM)
          if (timeOnly.split(":").length === 3) {
            timeOnly = timeOnly.substring(0, 5);
          }
        }

        // Format: {asset_code} - {start_time} - {duration} min:
        let line = `<p><strong>${asset}</strong>`;
        if (timeOnly) line += ` - ${timeOnly}`;
        if (bd.duration) {
          // Extract just the number from duration (e.g., "30min" -> "30")
          const durationNum = bd.duration.toString().replace(/[^0-9]/g, "");
          if (durationNum) line += ` - ${durationNum} min`;
        }
        line += ":</p>";

        // Add bullet points for Fault, Root cause, Recovery with colors
        html += line;
        html += "<ul>";
        if (bd.description)
          html += `<li><strong style="color: #e67e22;">Fault:</strong> ${bd.description}</li>`;
        if (bd.root_cause)
          html += `<li><strong style="color: #e67e22;">Root cause:</strong> ${bd.root_cause}</li>`;
        if (bd.resolution_notes)
          html += `<li><strong style="color: #e67e22;">Recovery:</strong> ${bd.resolution_notes}</li>`;
        html += "</ul>";
      });
    } else {
      html += "<p>No breakdowns recorded.</p>";
    }

    // Activities / Engineering Support
    html +=
      '<h3 style="color: #558b2f;"><strong>Engineering support/ FLUX Tickets / Break Activities:</strong></h3>';
    html += "<h4><strong>FLUX Tickets/MOs:</strong></h4>";

    // Filter flux tickets from break_activities
    const fluxTickets = (data.break_activities || []).filter(
      (a) => a.type === "flux_ticket" || a.mo_id,
    );
    if (fluxTickets.length > 0) {
      html += "<ol>";
      fluxTickets.forEach((item) => {
        const assetCode = item.asset || "ASSET_CODE";
        const title = item.title || item.description || "Title";
        const moId = item.mo_id ? item.mo_id : "Num.";
        const details = item.description || "details";
        // Pattern: {ASSET_CODE} – {Title} (MO/Ticket ID: {Num.}): {details} {Status}
        // Updated Pattern: Bold Asset, Italic Title, Normal ID, Normal Details
        html += `<li><strong>${assetCode}</strong> - <em>${title}</em> (MO/Ticket ID: ${moId}): ${details} ${item.status || ""}</li>`;
      });
      html += "</ol>";
    } else {
      html += "<p><em>MO/Ticket ID: N/A</em></p>";
    }

    html += "<h4><strong>Engineering Support:</strong></h4>";

    // Use engineering_support array
    const engineeringSupport = data.engineering_support || [];
    if (engineeringSupport.length > 0) {
      html += "<ol>";
      engineeringSupport.forEach((item) => {
        const assetCode = item.asset || "ASSET_CODE";
        const title = item.title || "Title";
        const details = item.description || "details";
        // Pattern: {ASSET_CODE} – {Title}: {details}
        // Updated Pattern: Bold Asset, Italic Title, Normal Details
        html += `<li><strong>${assetCode}</strong> - <em>${title}</em>: ${details}</li>`;
      });
      html += "</ol>";
    } else {
      html += "<p><em>None recorded.</em></p>";
    }

    // PMs (Weekend)
    if (data.pms) {
      html += '<h3 style="color: #558b2f;"><strong>PMs</strong></h3>';
      html += renderSimpleListHTML(data.pms);
    }

    // MOs (Weekend)
    if (data.mos) {
      html += '<h3 style="color: #558b2f;"><strong>MOs/Tickets</strong></h3>';
      html += renderSimpleListHTML(data.mos);
    }

    // Handover To
    html +=
      '<h3 style="color: #558b2f;"><strong>Handover to next Shift / Instructions</strong></h3>';
    const hoTo = shiftInfo.handover_to_next || data.handover_instructions;
    html += renderListHTML(hoTo);

    // Footer
    html += "<hr>";
    html += `<p>Generated by: <strong>${data.generatedBy}</strong></p>`;

    // Copy as HTML for Teams - Robust Method
    try {
      // Create formatted plain text representation manually to ensure newlines
      // browser innerText relies on layout, which might not be computed for detached elements
      let plainText = html;
      plainText = plainText.replace(/<br\s*\/?>/gi, "\r\n");
      plainText = plainText.replace(/<\/p>/gi, "\r\n\r\n");
      plainText = plainText.replace(/<\/div>/gi, "\r\n");
      plainText = plainText.replace(/<\/li>/gi, "\r\n");
      plainText = plainText.replace(/<li[^>]*>/gi, "• ");
      plainText = plainText.replace(/<[^>]+>/g, ""); // Strip remaining tags
      plainText = plainText.replace(/&nbsp;/g, " ");
      // Decode entities if needed (basic ones)
      const txt = document.createElement("textarea");
      txt.innerHTML = plainText;
      plainText = txt.value;

      // Prepare HTML with wrapper for better compatibility with Teams/Outlook
      const fullHtml = `<html><body>${html}</body></html>`;

      const blobHtml = new Blob([fullHtml], { type: "text/html" });
      const blobText = new Blob([plainText], { type: "text/plain" });

      const clipboardItem = new ClipboardItem({
        "text/html": blobHtml,
        "text/plain": blobText,
      });

      navigator.clipboard
        .write([clipboardItem])
        .then(function () {
          if (window.ToastNotification)
            ToastNotification.success(
              "Report copied to clipboard with formatting!",
            );
          else alert("Copied!");
        })
        .catch(function (err) {
          console.error("Clipboard write failed (secure context?):", err);
          // Fallback for non-secure contexts (e.g. HTTP IP) or limited support
          fallbackCopy(fullHtml);
        });
    } catch (e) {
      console.error("Clipboard creation error:", e);
      fallbackCopy(`<html><body>${html}</body></html>`);
    }

    function fallbackCopy(htmlContent) {
      // Fallback using legacy execCommand
      // Fixed positioning in view ensures it's "visible" to browser selection logic
      const tempDiv = document.createElement("div");
      tempDiv.contentEditable = true;
      tempDiv.style.position = "fixed";
      tempDiv.style.left = "0px";
      tempDiv.style.top = "0px";
      tempDiv.style.opacity = "0.01";
      tempDiv.style.pointerEvents = "none";
      tempDiv.style.zIndex = "9999";
      tempDiv.innerHTML = htmlContent;
      document.body.appendChild(tempDiv);

      try {
        const range = document.createRange();
        range.selectNodeContents(tempDiv);
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);

        const successful = document.execCommand("copy");
        if (successful) {
          if (window.ToastNotification)
            ToastNotification.success("Copied (Fallback Mode)!");
          else alert("Copied!");
        } else {
          alert("Copy failed. Please manually select and copy.");
        }
      } catch (err) {
        console.error("Fallback copy failed", err);
        alert("Copy failed. Browser may not support this.");
      } finally {
        document.body.removeChild(tempDiv);
      }
    }

    function renderListHTML(list) {
      let result = "";
      if (list && list.length > 0) {
        result += "<ul>";
        list.forEach((item) => {
          if (typeof item === "string") {
            result += `<li>${item}</li>`;
          } else {
            result += `<li><strong>${item.asset || ""}</strong>: <em>${item.title || ""}</em> - ${item.description || ""}</li>`;
          }
        });
        result += "</ul>";
      } else {
        result += "<p>None</p>";
      }
      return result;
    }

    function renderSimpleListHTML(list) {
      let result = "";
      if (list && list.length > 0) {
        result += "<ul>";
        list.forEach((item) => {
          result += `<li><strong>${item.asset || "Asset"}</strong> - ${item.description || ""} ${item.status ? "(" + item.status + ")" : ""}</li>`;
        });
        result += "</ul>";
      } else {
        result += "<p>None</p>";
      }
      return result;
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
        ["handover_from", "handover_to", "handover"].includes(
          currentContext.section,
        )
      ) {
        const asset = getVal("edit-handover-asset");
        const title = getVal("edit-handover-title");
        const desc = getVal("edit-handover-desc");
        // Always create an object with separate fields
        data.asset = asset;
        data.title = title;
        data.description = desc;
      } else if (currentContext.section === "breakdown") {
        data.asset = getVal("edit-bd-asset");
        data.timestamp = getVal("edit-bd-time");
        data.duration = getVal("edit-bd-duration");
        data.description = getVal("edit-bd-fault");
        data.root_cause = getVal("edit-bd-root");
        data.resolution_notes = getVal("edit-bd-recovery");
      } else if (
        ["activities", "flux_tickets", "engineering_support"].includes(
          currentContext.section,
        )
      ) {
        data.type = getVal("edit-act-type");
        data.asset = getVal("edit-act-asset");
        data.mo_id = getVal("edit-act-mo-id");
        data.title = getVal("edit-act-title");
        data.description = getVal("edit-act-desc");
        data.status = getVal("edit-act-status");
      } else if (
        ["pms", "mos", "additional"].includes(currentContext.section)
      ) {
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
        ["handover_from", "handover_to", "handover"].includes(
          currentContext.section,
        )
      ) {
        const asset = getVal("add-handover-asset");
        const title = getVal("add-handover-title");
        const desc = getVal("add-handover-desc");
        // Always create an object with separate fields
        data.asset = asset;
        data.title = title;
        data.description = desc;
      } else if (currentContext.section === "breakdown") {
        data.asset = getVal("add-bd-asset");
        data.timestamp = getVal("add-bd-time");
        data.duration = getVal("add-bd-duration");
        data.description = getVal("add-bd-fault");
        data.root_cause = getVal("add-bd-root");
        data.resolution_notes = getVal("add-bd-recovery");
      } else if (currentContext.section === "activities") {
        data.type = getVal("add-act-type");
        data.asset = getVal("add-act-asset");
        data.mo_id = getVal("add-act-mo-id");
        data.title = getVal("add-act-title");
        data.description = getVal("add-act-desc");
        data.status = getVal("add-act-status");
      } else if (
        ["pms", "mos", "additional"].includes(currentContext.section)
      ) {
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
    const formDiv = document.getElementById(id);
    if (formDiv) {
      formDiv.style.display = "block";
    }
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
        .forEach((input) => (input.value = ""));
    }
  }

  function toggleActivityFields(prefix) {
    const type = getVal(`${prefix}-act-type`);
    const moGroup = document.getElementById(`${prefix}-act-mo-group`);
    const titleGroup = document.getElementById(`${prefix}-act-title-group`);
    const statusGroup = document.getElementById(`${prefix}-act-status-group`);

    if (type === "flux_ticket") {
      // Show MO ID and Status, hide Title
      if (moGroup) moGroup.style.display = "block";
      if (titleGroup) titleGroup.style.display = "none";
      if (statusGroup) statusGroup.style.display = "block";
    } else {
      // Engineering Support: Show Title, hide MO ID and Status
      if (moGroup) moGroup.style.display = "none";
      if (titleGroup) titleGroup.style.display = "block";
      if (statusGroup) statusGroup.style.display = "none";
    }
  }

  // Focus management: Focus first input on show
  $("#editModal, #addModal").on("shown.bs.modal", function () {
    // Modified selector to exclude select2 hidden inputs
    const visibleInputs = $(this)
      .find(".modal-form-content:visible")
      .find("input:visible, select:visible, textarea:visible")
      .not(".select2-hidden-accessible"); // EXCLUDE SELECT2

    if (visibleInputs.length > 0) {
      const first = visibleInputs.first();
      first.focus();
      // Select text if it's an input or textarea
      if (first.is("input") || first.is("textarea")) {
        first.select();
      }
    }
  });

  // Enter key to save (for single-line inputs only)
  $("#editModal, #addModal").on("keydown", "input", function (e) {
    if (e.key === "Enter") {
      e.preventDefault();
      // Trigger the save button click
      const modalId = $(this).closest(".modal").attr("id");
      if (modalId === "editModal") {
        $("#saveEditBtn").click();
      } else if (modalId === "addModal") {
        $("#saveAddBtn").click();
      }
    }
  });

  // Fix ARIA warning: invalid aria-hidden on focused element
  $("#editModal, #addModal, #reportDeleteConfirmModal").on(
    "hide.bs.modal",
    function () {
      // Blur any active element (like select2 hidden input) to prevent focus retention in hidden modal
      if (document.activeElement) {
        try {
          document.activeElement.blur();
        } catch (e) {
          /* ignore */
        }
      }
      // Force focus to body as a fallback
      try {
        document.body.focus();
      } catch (e) {
        /* ignore */
      }
    },
  );
})();
