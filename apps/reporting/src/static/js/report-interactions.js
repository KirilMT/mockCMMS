/* istanbul ignore file */
/* global $ */
(function () {
  "use strict";

  // State to track what we are editing/deleting
  let currentContext = {
    section: null,
    index: null,
    action: null, // 'edit' or 'add'
  };

  // DOM dependent initializations
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

    // Destroy Select2 instance safely
    function destroySelect2(selector) {
      const $el = $(selector);
      if ($el.length && $el.hasClass("select2-hidden-accessible")) {
        try {
          $el.select2("destroy");
        } catch {
          // Silently ignore
        }
      }
    }

    // Consolidated modal hide handler: destroy Select2, blur, then return focus to body
    function cleanupModalOnHide(select2Selectors) {
      select2Selectors.forEach(destroySelect2);
      // Explicitly blur any focused element within the modal before it's hidden
      if (document.activeElement && document.activeElement.closest(".modal")) {
        try {
          document.activeElement.blur();
        } catch {
          /* ignore */
        }
      }
    }

    // Use 'hide' event (start of animation) to blur focus
    $(".modal").on("hide.bs.modal", function () {
      if (document.activeElement && this.contains(document.activeElement)) {
        try {
          document.activeElement.blur();
        } catch {
          /* ignore */
        }
      }
    });

    // Use 'show' event to prepare state
    $("#editModal, #addModal").on("show.bs.modal", function () {
      // Remove aria-hidden BEFORE it becomes visible to avoid accessibility warnings during transition
      this.removeAttribute("aria-hidden");
    });

    // Use 'shown' event for focus and Select2 initialization
    $("#editModal, #addModal").on("shown.bs.modal", function () {
      const isEdit = this.id === "editModal";
      const prefix = isEdit ? "edit" : "add";

      // Initialize Select2 based on visible form
      const visibleSection = $(this)
        .find(".modal-form-content:visible")
        .attr("id");
      if (visibleSection) {
        let select2Selector = null;
        if (visibleSection.includes("handover"))
          select2Selector = `#${prefix}-handover-asset`;
        else if (visibleSection.includes("breakdown"))
          select2Selector = `#${prefix}-bd-asset`;
        else if (visibleSection.includes("activity"))
          select2Selector = `#${prefix}-act-asset`;
        else if (visibleSection.includes("simple-task"))
          select2Selector = `#${prefix}-task-asset`;

        if (select2Selector && $(select2Selector).length) {
          $(select2Selector).select2({
            tags: true,
            placeholder: "Select Asset or type custom...",
            dropdownParent: $(this),
            width: "100%", // Ensure it fills container
          });
        }
      }

      // Focus management
      const visibleInputs = $(this)
        .find(".modal-form-content:visible")
        .find("input:visible, select:visible, textarea:visible")
        .not(".select2-hidden-accessible");

      if (visibleInputs.length > 0) {
        const first = visibleInputs.first();
        first.focus();
        if (first.is("input") || first.is("textarea")) {
          first.select();
        }
      }
    });

    $("#editModal").on("hidden.bs.modal", function () {
      cleanupModalOnHide([
        "#edit-handover-asset",
        "#edit-bd-asset",
        "#edit-act-asset",
        "#edit-task-asset",
      ]);
      // Restore aria-hidden on hide for standard compliance
      this.setAttribute("aria-hidden", "true");
    });

    $("#addModal").on("hidden.bs.modal", function () {
      cleanupModalOnHide([
        "#add-handover-asset",
        "#add-bd-asset",
        "#add-act-asset",
        "#add-task-asset",
      ]);
      this.setAttribute("aria-hidden", "true");
    });

    $("#reportDeleteConfirmModal").on("hidden.bs.modal", function () {
      cleanupModalOnHide([]);
      this.setAttribute("aria-hidden", "true");
    });
  });

  // ... (context tracking remains) ...

  /**
   * Opens the Edit Modal and populates fields based on section
   */
  window.openEditModal = function (section, title, dataJson, index) {
    currentContext.section = section;
    currentContext.index = index;
    currentContext.action = "edit";

    const label = document.getElementById("editModalLabel");
    if (label) label.textContent = "Edit " + title;

    const editModal = document.getElementById("editModal");
    const modalDialog = editModal?.querySelector(".modal-dialog");
    if (modalDialog) {
      if (section === "metadata") {
        modalDialog.classList.remove("modal-lg");
        modalDialog.classList.add("modal-sm");
      } else {
        modalDialog.classList.remove("modal-sm");
        modalDialog.classList.add("modal-lg");
      }
    }

    hideAllForms("edit-forms");

    let content = dataJson;
    if (typeof dataJson === "string") {
      try {
        content = JSON.parse(dataJson);
      } catch {
        content = { description: dataJson };
      }
    }

    populateEditForm(section, content);
    $("#editModal").modal("show");
  };

  /**
   * Helper that reads from data-attributes to avoid complex inline JS
   */
  window.openEditModalFromData = function (el) {
    const section = el.getAttribute("data-type");
    const title = el.getAttribute("data-title");
    const dataStr = el.getAttribute("data-params");
    const indexStr = el.getAttribute("data-index");
    const index = indexStr !== null ? parseInt(indexStr) : null;

    let data = dataStr;
    try {
      data = JSON.parse(dataStr);
    } catch {
      // Fallback to raw string if it was just a string
    }

    window.openEditModal(section, title, data, index);
  };

  /**
   * Opens the Add Modal
   */
  window.openAddModal = function (section, title) {
    currentContext.section = section;
    currentContext.action = "add";
    currentContext.index = null;

    const label = document.getElementById("addModalLabel");
    if (label) label.textContent = "Add " + title;

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

  /**
   * Helper that reads from data-attributes to avoid complex inline JS
   */
  window.deleteItemFromData = function (el) {
    const section = el.getAttribute("data-type");
    const indexStr = el.getAttribute("data-index");
    if (section && indexStr !== null) {
      window.deleteItem(section, parseInt(indexStr));
    }
  };

  function handleSaveEdit() {
    const data = getFormData("edit");

    // Validation for Metadata Totals
    if (currentContext.section === "metadata") {
      const valInput = document.getElementById("edit-metadata-value");
      const maxTotal = valInput.getAttribute("data-max-total");
      if (maxTotal && parseInt(maxTotal) > 0) {
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
      const totalTextEl = document.getElementById("edit-metadata-total-text");
      if (metadataTotal !== null) {
        inputEl.setAttribute("data-max-total", metadataTotal);
        inputEl.placeholder = `Max: ${metadataTotal}`;
        inputEl.style.width = "80px"; // Narrow width for small numbers
        if (totalTextEl) {
          totalTextEl.textContent = `/ ${metadataTotal}`;
          totalTextEl.style.display = "inline";
          totalTextEl.style.marginLeft = "8px";
          totalTextEl.style.fontSize = "1rem";
          totalTextEl.style.fontWeight = "normal";
        }
      } else {
        inputEl.removeAttribute("data-max-total");
        inputEl.placeholder = "Enter value";
        inputEl.style.width = ""; // Reset to default
        if (totalTextEl) {
          totalTextEl.textContent = "";
          totalTextEl.style.display = "none";
        }
      }
    } else if (
      [
        "handover_from",
        "handover_from_previous",
        "handover_to",
        "handover_to_next",
        "handover",
      ].includes(section)
    ) {
      showForm("edit-handover-form");
      // Handle both string and object formats
      let assetVal = "";
      let titleVal = "";
      let descVal = "";

      if (typeof content === "string") {
        descVal = content;
      } else {
        assetVal = content.asset || "";
        titleVal = content.title || "";
        descVal = content.description || "";
      }

      setVal("edit-handover-title", titleVal);
      setVal("edit-handover-desc", descVal);

      // Initialize Select2 FIRST, then set value
      setTimeout(() => {
        const $select = $("#edit-handover-asset");
        $select.select2({
          tags: true,
          placeholder: "Select Asset or type custom...",
          dropdownParent: $("#editModal"),
        });
        // Set value AFTER Select2 initialization
        if (assetVal) {
          $select.val(assetVal).trigger("change");
        }
      }, 100);
    } else if (section === "breakdown") {
      showForm("edit-breakdown-form");
      const assetVal = content.equipment_line || content.asset || "";
      const timeVal = content.timestamp || "";
      const durationVal = content.duration || "";
      const faultVal = content.description || "";
      const rootVal = content.root_cause || "";
      const recoveryVal = content.resolution_notes || content.recovery || "";

      setVal("edit-bd-time", timeVal);
      setVal("edit-bd-duration", durationVal);
      setVal("edit-bd-fault", faultVal);
      setVal("edit-bd-root", rootVal);
      setVal("edit-bd-recovery", recoveryVal);

      // Initialize Select2 FIRST, then set value
      setTimeout(() => {
        const $select = $("#edit-bd-asset");
        $select.select2({
          tags: true,
          placeholder: "Select Asset or type custom...",
          dropdownParent: $("#editModal"),
        });
        // Set value AFTER Select2 initialization
        if (assetVal) {
          $select.val(assetVal).trigger("change");
        }
      }, 100);
    } else if (section === "activities") {
      showForm("edit-activity-form");
      const actType = content.type || "flux_ticket";
      const assetVal = content.asset || "";

      setVal("edit-act-type", actType);
      setVal("edit-act-mo-id", content.mo_id || "");
      setVal("edit-act-title", content.title || "");
      setVal("edit-act-desc", content.description || "");
      setVal("edit-act-status", content.status || "");

      // Initialize Select2 FIRST, then set value, then toggle fields
      setTimeout(() => {
        const $select = $("#edit-act-asset");
        $select.select2({
          tags: true,
          placeholder: "Select Asset or type custom...",
          dropdownParent: $("#editModal"),
        });
        // Set value AFTER Select2 initialization
        if (assetVal) {
          $select.val(assetVal).trigger("change");
        }
        toggleActivityFields("edit");
        $("#edit-act-type").on("change", () => toggleActivityFields("edit"));
      }, 50);
    } else if (section === "flux_tickets") {
      showForm("edit-activity-form");
      const assetVal = content.asset || "";

      // Force type to flux_ticket
      setVal("edit-act-type", "flux_ticket");
      setVal("edit-act-mo-id", content.mo_id || "");
      setVal("edit-act-desc", content.description || "");
      setVal("edit-act-status", content.status || "");

      setTimeout(() => {
        const $select = $("#edit-act-asset");
        $select.select2({
          tags: true,
          dropdownParent: $("#editModal"),
        });
        // Set value AFTER Select2 initialization
        if (assetVal) {
          $select.val(assetVal).trigger("change");
        }
        toggleActivityFields("edit");
        $("#edit-act-type").on("change", () => toggleActivityFields("edit"));
      }, 50);
    } else if (section === "engineering_support") {
      showForm("edit-activity-form");
      const assetVal = content.asset || "";

      // Force type
      setVal("edit-act-type", "engineering_support");
      setVal("edit-act-title", content.title || "");
      setVal("edit-act-desc", content.description || "");

      setTimeout(() => {
        const $select = $("#edit-act-asset");
        $select.select2({
          tags: true,
          dropdownParent: $("#editModal"),
        });
        // Set value AFTER Select2 initialization
        if (assetVal) {
          $select.val(assetVal).trigger("change");
        }
        toggleActivityFields("edit");
        $("#edit-act-type").on("change", () => toggleActivityFields("edit"));
      }, 50);
    } else if (["pms", "mos", "additional"].includes(section)) {
      showForm("edit-simple-task-form");
      const assetVal = content.asset || "";

      setVal("edit-task-desc", content.description || "");
      setVal("edit-task-status", content.status || "");
      if (["mos", "additional"].includes(section)) {
        setVal("edit-task-id", content.id || "");
        document.getElementById("edit-task-id-group").style.display = "block";
      } else {
        document.getElementById("edit-task-id-group").style.display = "none";
      }
      // Initialize Select2 FIRST, then set value
      setTimeout(() => {
        const $select = $("#edit-task-asset");
        $select.select2({
          tags: true,
          placeholder: "Select Asset or type custom...",
          dropdownParent: $("#editModal"),
        });
        // Set value AFTER Select2 initialization
        if (assetVal) {
          $select.val(assetVal).trigger("change");
        }
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
    if (
      [
        "handover_from",
        "handover_from_previous",
        "handover_to",
        "handover_to_next",
        "handover",
      ].includes(section)
    ) {
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

  /* --- Teams Copy (Semantic HTML) --- */
  /* --- Teams Copy (Semantic HTML) --- */
  function normalizeReportType(reportType) {
    return reportType === "weekend_report" ? "weekend_report" : "shift_report";
  }

  function itemToText(item) {
    if (typeof item === "string") {
      return item.trim();
    }
    const asset = item?.asset || "ASSET";
    const title = item?.title || "Instruction";
    const description = item?.description || "";
    return `${asset} - ${title}: ${description}`.trim();
  }

  function buildPlainTextReport(
    data,
    reportType,
    reportDate,
    reportShift,
    teamName,
    sections,
  ) {
    const lines = [];
    lines.push(
      `${reportType === "weekend_report" ? "Weekend Shift Report" : "Shift Report"} - ${reportDate} - ${reportShift} - ${teamName}`,
    );
    lines.push("");
    lines.push(`Attendance: ${sections.attendance}`);
    lines.push(`EHS incidents: ${sections.ehs}`);
    lines.push(`VIGEL: ${sections.vigel}`);
    lines.push(`MDS: ${sections.mds}`);
    lines.push("");

    lines.push("Handover from previous Shift:");
    if (sections.handoverFrom.length > 0) {
      sections.handoverFrom.forEach((entry) => lines.push(itemToText(entry)));
    } else {
      lines.push("No notes from previous shift.");
    }
    lines.push("");

    if (reportType === "shift_report") {
      lines.push("Breakdowns:");
      if (sections.breakdowns.length > 0) {
        sections.breakdowns.forEach((bd) => {
          const asset = bd.equipment_line || bd.asset || "Line";
          const time = (bd.timestamp || bd.start_time || "")
            .toString()
            .replace(/start time:/i, "")
            .replace(/time:/i, "")
            .trim();
          const duration = (bd.duration || "")
            .toString()
            .replace(/duration:/i, "")
            .trim();
          lines.push(
            `${asset}${time ? ` - ${time}` : ""}${duration ? ` - ${duration} min` : ""}`,
          );
          if (bd.description) lines.push(`- Fault: ${bd.description}`);
          if (bd.root_cause) lines.push(`- Root cause: ${bd.root_cause}`);
          if (bd.resolution_notes)
            lines.push(`- Recovery: ${bd.resolution_notes}`);
          lines.push("");
        });
      } else {
        lines.push("No breakdowns recorded.");
        lines.push("");
      }

      lines.push("Engineering support / FLUX Tickets / Break Activities:");
      const flux = (sections.activities || []).filter(
        (a) => a.type === "flux_ticket" || a.mo_id,
      );
      if (flux.length > 0) {
        lines.push("FLUX Tickets/MOs:");
        flux.forEach((a) => {
          lines.push(
            `${a.asset || "ASSET"} - ${a.title || "Title"} (MO/Ticket ID: ${a.mo_id || "N/A"}): ${a.description || ""} ${a.status || ""}`.trim(),
          );
        });
      }
      if (sections.engineeringSupport.length > 0) {
        lines.push("Engineering Support:");
        sections.engineeringSupport.forEach((supp) => {
          lines.push(
            `${supp.asset || "ASSET"} - ${supp.title || "Title"}: ${supp.description || ""}`.trim(),
          );
        });
      }
      lines.push("");
    }

    if (reportType === "weekend_report") {
      lines.push("PMs:");
      if (sections.pms.length > 0) {
        sections.pms.forEach((pm) =>
          lines.push(
            `${pm.asset || "ASSET"} - ${pm.description || ""} (${pm.status || "Completed"})`.trim(),
          ),
        );
      } else {
        lines.push("No PMs recorded.");
      }
      lines.push("");

      lines.push("MOs/Tickets:");
      if (sections.mos.length > 0) {
        sections.mos.forEach((mo) =>
          lines.push(
            `${mo.asset || "ASSET"} - ${mo.description || ""} (ID: ${mo.mo_id || mo.id || "N/A"})`.trim(),
          ),
        );
      } else {
        lines.push("No MOs/Tickets recorded.");
      }
      lines.push("");

      if (sections.additionalTickets.length > 0) {
        lines.push("Additional Tickets:");
        sections.additionalTickets.forEach((t) =>
          lines.push(
            `${t.asset || "ASSET"} - ${t.description || ""} (ID: ${t.id || "N/A"})`.trim(),
          ),
        );
        lines.push("");
      }
    }

    lines.push("Handover to next Shift:");
    if (sections.handoverTo.length > 0) {
      sections.handoverTo.forEach((entry) => lines.push(itemToText(entry)));
    } else {
      lines.push("No instructions provided.");
    }
    lines.push("");
    lines.push("Have a good shift,");
    lines.push(data.generatedBy || "Technician");

    return lines.join("\n");
  }

  function handleCopyMarkdown() {
    const data = window.reportData;
    if (!data) {
      if (window.ToastNotification)
        ToastNotification.error("Report data is not available yet.");
      return;
    }

    const normalizedType = normalizeReportType(data.reportType);
    const reportDate =
      data.reportInfo?.date || data.date || data.weekend_date || "N/A";
    const reportShift = data.reportInfo?.shift || data.shift || "N/A";
    const teamName =
      data.teamName || data.reportInfo?.team_name || "Weekend Team";
    const teamColor = getTeamColor(teamName);

    const attTotal = data.attendance_total || 20;
    const vigelTotal = data.vigel_total || 10;
    const mdsTotal = data.mds_total || 15;

    const attVal = parseInt(data.attendance, 10) || 0;
    const ehsVal = parseInt(data.ehsIncidents, 10) || 0;
    const vigelVal = parseInt(data.vigel, 10) || 0;
    const mdsVal = parseInt(data.mds, 10) || 0;

    const sections = {
      attendance: `${attVal}/${attTotal}`,
      ehs: `${ehsVal}`,
      vigel: `${vigelVal}/${vigelTotal}`,
      mds: `${mdsVal}/${mdsTotal}`,
      handoverFrom:
        data.reportInfo?.handover_from_previous ||
        data.handover_from_previous ||
        [],
      handoverTo:
        data.reportInfo?.handover_to_next ||
        data.handover_to_next ||
        data.handover_instructions ||
        [],
      breakdowns: data.breakdowns || [],
      activities: data.activities || [],
      engineeringSupport: data.engineering_support || [],
      pms: data.pms || [],
      mos: data.mos || data.mos_tickets || [],
      additionalTickets: data.additional_tickets || [],
    };

    const moDataMap = data.mo_data_map || {};
    const getMoData = (rawId) => {
      if (!rawId) return null;
      const match = String(rawId).match(/\d+/);
      if (!match) return null;
      return moDataMap[match[0]] || null;
    };

    // Teams-friendly HTML: Use semantic tags with inline styles that work in dark mode
    // Avoid pure black (#000) - use slightly lighter for dark mode compatibility
    let html = `<!DOCTYPE html><html><body style="font-family: Calibri, Arial, sans-serif; color: #242424;">`;

    // Title with underline
    html += `<h2 style="margin: 0 0 8px 0; font-size: 18pt; font-weight: bold;"><b><u>${normalizedType === "weekend_report" ? "Weekend Shift Report" : "Shift Report"} - ${reportDate} - ${reportShift} - </u></b><b><u><font color="${teamColor}">${teamName}</font></u></b></h2>`;

    // Metadata table - Teams-friendly with simple styling and better colors
    html += `<table border="1" cellspacing="0" cellpadding="6" style="width: 100%; border-collapse: collapse; border-color: #999; margin-bottom: 12px; background-color: #f9f9f9;">`;
    html += `<tr>`;
    html += `<td style="text-align: center; font-weight: bold;">Attendance: <b><font color="${attVal / attTotal >= 0.8 ? "#107c10" : "#d13438"}">${sections.attendance}</font></b></td>`;
    html += `<td style="text-align: center; font-weight: bold;">EHS incidents: <b><font color="${ehsVal === 0 ? "#107c10" : "#d13438"}">${sections.ehs}</font></b></td>`;
    html += `<td style="text-align: center; font-weight: bold;">VIGEL: <b><font color="${vigelVal / vigelTotal >= 0.8 ? "#107c10" : "#d13438"}">${sections.vigel}</font></b></td>`;
    html += `<td style="text-align: center; font-weight: bold;">MDS: <b><font color="${mdsVal / mdsTotal >= 0.8 ? "#107c10" : "#d13438"}">${sections.mds}</font></b></td>`;
    html += `</tr></table>`;

    // Handover from previous shift
    html += `<h3 style="margin: 12px 0 6px 0; font-size: 14pt; font-weight: bold;"><b><u>Handover from previous Shift:</u></b></h3>`;
    if (sections.handoverFrom.length > 0) {
      sections.handoverFrom.forEach((item) => {
        html += `<p style="margin: 0; font-weight: bold;">${item.asset || "ASSET"} - <i>${item.title || ""}</i>:</p>`;
        html += `<div style="margin: 0 0 8px 16px; font-weight: normal;">${item.description || ""}</div>`;
      });
    } else {
      html += `<p style="margin: 0 0 8px 0;"><i>No notes from previous shift.</i></p>`;
    }

    if (normalizedType === "shift_report") {
      // Breakdowns section
      html += `<h3 style="margin: 12px 0 6px 0; font-size: 14pt; font-weight: bold;"><b><u>Breakdowns:</u></b></h3>`;
      if (sections.breakdowns.length > 0) {
        sections.breakdowns.forEach((bd) => {
          const asset = bd.equipment_line || bd.asset || "Line";
          let time = (bd.timestamp || bd.start_time || "")
            .toString()
            .replace(/start time:/i, "")
            .replace(/time:/i, "")
            .trim();
          if (time.includes(" ")) {
            const parts = time.split(" ");
            time = parts[parts.length - 1];
          }
          let header = `<b>${asset}</b>`;
          if (time) header += ` - ${time}`;
          if (bd.duration) {
            let dur = String(bd.duration)
              .toLowerCase()
              .replace(/duration:/i, "")
              .replace(/min/i, "")
              .trim();
            if (dur && dur !== "n/a" && !isNaN(dur)) dur = `${dur} min`;
            header += dur && dur !== "n/a" ? ` - ${dur}` : "";
          }
          html += `<p style="margin: 0;">${header}:</p>`;
          html += `<ul style="margin: 4px 0 8px 20px;">`;
          if (bd.description)
            html += `<li><b>Fault:</b> ${bd.description}</li>`;
          if (bd.root_cause)
            html += `<li><b>Root cause:</b> ${bd.root_cause}</li>`;
          if (bd.resolution_notes)
            html += `<li><b>Recovery:</b> ${bd.resolution_notes}</li>`;
          html += `</ul>`;
        });
      } else {
        html += `<p style="margin: 0 0 8px 0;"><i>No breakdowns recorded.</i></p>`;
      }

      // Engineering support / FLUX Tickets
      html += `<h3 style="margin: 12px 0 6px 0; font-size: 14pt; font-weight: bold;"><b><u>Engineering support / FLUX Tickets / Break Activities:</u></b></h3>`;
      const flux = (sections.activities || []).filter(
        (a) => a.type === "flux_ticket" || a.mo_id,
      );
      if (flux.length > 0) {
        html += `<p style="margin: 0 0 4px 0; font-weight: bold;"><b>FLUX Tickets/MOs:</b></p><ol style="margin: 0 0 8px 20px;">`;
        flux.forEach((a) => {
          const moData = getMoData(a.mo_id || a.id);
          const assetLabel = moData?.asset_code || a.asset || "ASSET";
          const description = moData?.description || a.description || "";
          const statusLabel = moData?.status || a.status || "";
          const statusSuffix = statusLabel ? ` - <i>${statusLabel}</i>` : "";
          const moIdLabel = a.mo_id || a.id || "N/A";

          html += `<li><b>${assetLabel}</b> - <i>${a.title || ""}</i> ${description} (MO/Ticket ID: <b>${moIdLabel}</b>)${statusSuffix}</li>`;
        });
        html += `</ol>`;
      }

      if (sections.engineeringSupport.length > 0) {
        html += `<p style="margin: 0 0 4px 0; font-weight: bold;"><b>Engineering Support:</b></p><ol style="margin: 0 0 8px 20px;">`;
        sections.engineeringSupport.forEach((supp) => {
          html += `<li><b>${supp.asset || "ASSET"}</b> - <i>${supp.title || "Title"}</i>:<br/>${supp.description || ""}</li>`;
        });
        html += `</ol>`;
      }
    }

    if (normalizedType === "weekend_report") {
      // PMs section
      html += `<h3 style="margin: 12px 0 6px 0; font-size: 14pt; font-weight: bold;"><b><u>PMs:</u></b></h3>`;
      if (sections.pms.length > 0) {
        html += `<ol style="margin: 0 0 8px 20px;">`;
        sections.pms.forEach((pm) => {
          const moData = getMoData(pm.id);
          const assetLabel = moData?.asset_code || pm.asset || "ASSET";
          const description = moData?.description || pm.description || "";
          const statusLabel = moData?.status || pm.status || "Completed";
          html += `<li><b>TASK: ${assetLabel}</b> + ${description} - <i>${statusLabel}</i></li>`;
        });
        html += `</ol>`;
      } else {
        html += `<p style="margin: 0 0 8px 0;"><i>No PMs recorded</i></p>`;
      }

      // MOs/Tickets section
      html += `<h3 style="margin: 12px 0 6px 0; font-size: 14pt; font-weight: bold;"><b><u>MOs/Tickets:</u></b></h3>`;
      if (sections.mos.length > 0) {
        html += `<ol style="margin: 0 0 8px 20px;">`;
        sections.mos.forEach((mo) => {
          const moData = getMoData(mo.mo_id || mo.id);
          const assetLabel = moData?.asset_code || mo.asset || "ASSET";
          const description = moData?.description || mo.description || "";
          const statusLabel = moData?.status || mo.status || "Pending";
          const moIdLabel = mo.mo_id || mo.id || "N/A";

          html += `<li><b>${assetLabel}</b> - ${description} (ID: <b>${moIdLabel}</b>) - <i>${statusLabel}</i></li>`;
        });
        html += `</ol>`;
      } else {
        html += `<p style="margin: 0 0 8px 0;"><i>No MOs/Tickets recorded</i></p>`;
      }

      // Additional Tickets section
      if (sections.additionalTickets.length > 0) {
        html += `<h3 style="margin: 12px 0 6px 0; font-size: 14pt; font-weight: bold;"><b><u>Additional Tickets:</u></b></h3>`;
        html += `<ol style="margin: 0 0 8px 20px;">`;
        sections.additionalTickets.forEach((t) => {
          const moData = getMoData(t.id);
          const assetLabel = moData?.asset_code || t.asset || "ASSET";
          const description = moData?.description || t.description || "";
          const statusLabel = moData?.status || t.status || "Pending";
          const ticketId = t.id || "N/A";

          html += `<li><b>${assetLabel}</b> - ${description} (ID: <b>${ticketId}</b>) - <i>${statusLabel}</i></li>`;
        });
        html += `</ol>`;
      }
    }

    // Handover to next shift
    html += `<h3 style="margin: 12px 0 6px 0; font-size: 14pt; font-weight: bold;"><b><u>Handover to next Shift:</u></b></h3>`;
    if (sections.handoverTo.length > 0) {
      sections.handoverTo.forEach((item) => {
        html += `<p style="margin: 0; font-weight: bold;">${item.asset || "ASSET"} - <i>${item.title || ""}</i>:</p>`;
        html += `<div style="margin: 0 0 8px 16px; font-weight: normal;">${item.description || ""}</div>`;
      });
    } else {
      html += `<p style="margin: 0 0 8px 0;"><i>No instructions provided.</i></p>`;
    }

    html += `<hr/><p style="font-weight: normal;">Have a good shift,<br/><br/><b>${data.generatedBy || "Technician"}</b></p>`;
    html += `</body></html>`;

    const plainText = buildPlainTextReport(
      data,
      normalizedType,
      reportDate,
      reportShift,
      teamName,
      sections,
    );

    copyToClipboard(html, plainText);
  }

  function copyToClipboard(htmlContent, plainTextContent) {
    // Modern ClipboardItem API - preferred for HTML + plain text
    if (navigator.clipboard && navigator.clipboard.write) {
      try {
        const blobHtml = new Blob([htmlContent], { type: "text/html" });
        const blobText = new Blob([plainTextContent], { type: "text/plain" });

        const item = new ClipboardItem({
          "text/html": blobHtml,
          "text/plain": blobText,
        });

        navigator.clipboard
          .write([item])
          .then(() => {
            if (window.ToastNotification)
              ToastNotification.success("Report copied for Teams!");
            else alert("Copied for Teams!");
          })
          .catch((err) => {
            console.warn("Modern clipboard API failed: ", err);
            fallbackCopy(htmlContent, plainTextContent);
          });
      } catch (err) {
        console.warn("Clipboard creation failed: ", err);
        fallbackCopy(htmlContent, plainTextContent);
      }
    } else {
      // Fallback for older browsers or HTTPS issues
      fallbackCopy(htmlContent, plainTextContent);
    }
  }

  /**
   * Fallback clipboard copy - creates contenteditable div and uses execCommand
   * This is more reliable for Teams/Office apps as they better support this method
   */
  function fallbackCopy(htmlContent, plainTextContent) {
    const tempDiv = document.createElement("div");
    tempDiv.contentEditable = "true";
    tempDiv.innerHTML = htmlContent;
    tempDiv.style.position = "fixed";
    tempDiv.style.left = "-9999px";
    tempDiv.style.top = "-9999px";
    tempDiv.style.opacity = "0";
    tempDiv.style.pointerEvents = "none";
    document.body.appendChild(tempDiv);

    try {
      const range = document.createRange();
      range.selectNodeContents(tempDiv);
      const sel = window.getSelection();
      sel.removeAllRanges();
      sel.addRange(range);

      // Copy command - will include both HTML and plain text
      const success = document.execCommand("copy");

      sel.removeAllRanges();
      document.body.removeChild(tempDiv);

      if (success) {
        if (window.ToastNotification)
          ToastNotification.success("Report copied for Teams!");
        else alert("Copied for Teams!");
      } else {
        throw new Error("execCommand copy returned false");
      }
    } catch (err) {
      console.error("Fallback copy failed: ", err);
      document.body.removeChild(tempDiv);
      if (window.ToastNotification)
        ToastNotification.error(
          "Copy failed. Please try selecting the report manually and copying.",
        );
      else alert("Copy failed. Try selecting manually.");
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
        currentContext.section === "handover_from" ||
        currentContext.section === "handover_from_previous"
      ) {
        data.section = "handover_from";
        data.asset = getVal(`${type}-handover-asset`);
        data.title = getVal(`${type}-handover-title`);
        data.description = getVal(`${type}-handover-desc`);
      } else if (
        currentContext.section === "handover_to" ||
        currentContext.section === "handover_to_next" ||
        currentContext.section === "handover"
      ) {
        data.section = "handover_to";
        data.asset = getVal(`${type}-handover-asset`);
        data.title = getVal(`${type}-handover-title`);
        data.description = getVal(`${type}-handover-desc`);
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
        } catch {
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
        data.section =
          currentContext.section === "handover_from"
            ? "handover_from"
            : "handover_to";
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
    // Robust report ID extraction from URL path
    const pathParts = window.location.pathname
      .split("/")
      .filter((p) => p !== "");
    const reportId = pathParts.includes("reporting")
      ? pathParts[pathParts.indexOf("reporting") + 1]
      : pathParts.pop();

    if (!reportId || isNaN(parseInt(reportId))) {
      console.error(
        "Could not determine report ID from URL:",
        window.location.pathname,
      );
      return;
    }

    const url = `/reporting/${reportId}/update`;

    // Get CSRF token from meta tag if available
    const csrfToken = document
      .querySelector('meta[name="csrf-token"]')
      ?.getAttribute("content");
    const headers = {
      "Content-Type": "application/json",
    };
    if (csrfToken) {
      headers["X-CSRFToken"] = csrfToken;
    }

    fetch(url, {
      method: "POST",
      headers: headers,
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

  function hideAllForms() {
    // Rely on class .modal-form-content
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
    if (modalId === "editModal") {
      const totalTextEl = document.getElementById("edit-metadata-total-text");
      if (totalTextEl) totalTextEl.textContent = "";
      const metadataInput = document.getElementById("edit-metadata-value");
      if (metadataInput) metadataInput.removeAttribute("data-max-total");
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

  // DOM dependent initializations
  document.addEventListener("DOMContentLoaded", function () {
    // jQuery Modal Focus management: Focus first input on show
    if (typeof $ !== "undefined") {
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
    }
  });

  // Export pure utility functions for unit testing (CommonJS)
  if (typeof module !== "undefined" && module.exports) {
    module.exports = {
      getTeamColor,
      normalizeReportType,
      itemToText,
      buildPlainTextReport,
      populateEditForm,
      populateAddForm,
      handleSaveEdit,
      handleSaveAdd,
      handleConfirmDelete,
      handleCopyMarkdown,
      copyToClipboard,
      fallbackCopy,
      getFormData,
      setVal,
      getVal,
      hideAllForms,
      showForm,
      clearAllInputs,
      toggleActivityFields,
      sendUpdate,
      setCurrentContext: (ctx) => {
        currentContext = { ...currentContext, ...ctx };
      },
      getCurrentContext: () => ({ ...currentContext }),
    };
  }
})();
