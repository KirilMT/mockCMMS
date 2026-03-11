/* global $ */

// Enable/disable and require frequency field based on order type
document.addEventListener("DOMContentLoaded", function () {
  const orderTypeField = document.getElementById("order_type");
  const frequencyField = document.getElementById("frequency");
  const scheduleNameField = document.getElementById("schedule_name");
  const frequencyLabel = document.querySelector('label[for="frequency"]');
  const estimatedTimeField = document.getElementById(
    "estimated_completion_time",
  );
  const estimatedTimeLabel = document.getElementById("label_estimated_time");
  const breakdownFields = document.querySelectorAll(".breakdown-fields");
  const pmFields = document.querySelectorAll(".pm-fields");

  // Reactive field elements
  const downtimeField = document.getElementById("downtime_duration");
  const rootCauseField = document.getElementById("root_cause");
  const recoveryField = document.getElementById("recovery");

  function updateFieldsBasedOnType() {
    const isPM = orderTypeField.value === "PM";
    const isReactive = orderTypeField.value === "Reactive";
    const label =
      (estimatedTimeField && estimatedTimeField.previousElementSibling) ||
      estimatedTimeLabel;

    if (isPM) {
      // Show and require PM-specific fields
      pmFields.forEach((field) => {
        field.style.display = "block";
      });

      // Make PM fields required
      if (scheduleNameField) scheduleNameField.required = true;
      if (frequencyField) frequencyField.required = true;
      if (estimatedTimeField) estimatedTimeField.required = true;

      // Hide breakdown fields for PM
      breakdownFields.forEach((field) => {
        field.style.display = "none";
      });

      // Make Reactive fields optional
      if (downtimeField) downtimeField.required = false;
      if (rootCauseField) rootCauseField.required = false;
      if (recoveryField) recoveryField.required = false;
    } else if (isReactive) {
      // Hide PM fields for Reactive
      pmFields.forEach((field) => {
        field.style.display = "none";
      });

      // Make PM fields optional
      if (scheduleNameField) {
        scheduleNameField.required = false;
        scheduleNameField.value = "";
      }
      if (frequencyField) {
        frequencyField.required = false;
        frequencyField.value = "";
      }
      if (estimatedTimeField) estimatedTimeField.required = false;

      // Show and require breakdown fields for Reactive
      breakdownFields.forEach((field) => {
        field.style.display = "block";
      });

      // Make Reactive fields required
      if (downtimeField) downtimeField.required = true;
      if (rootCauseField) rootCauseField.required = true;
      if (recoveryField) recoveryField.required = true;
    } else {
      // Corrective or other types
      // Hide both PM and breakdown fields
      pmFields.forEach((field) => {
        field.style.display = "none";
      });
      breakdownFields.forEach((field) => {
        field.style.display = "none";
      });

      // Make all conditional fields optional
      if (scheduleNameField) {
        scheduleNameField.required = false;
        scheduleNameField.value = "";
      }
      if (frequencyField) {
        frequencyField.required = false;
        frequencyField.value = "";
      }
      if (estimatedTimeField) estimatedTimeField.required = false;
      if (downtimeField) downtimeField.required = false;
      if (rootCauseField) rootCauseField.required = false;
      if (recoveryField) recoveryField.required = false;
    }
  }

  // Set initial state on page load
  if (orderTypeField && frequencyField) {
    updateFieldsBasedOnType();

    // Update when user changes the order type
    orderTypeField.addEventListener("change", function () {
      updateFieldsBasedOnType();
    });
  }

  // Initialize Select2 for assignees dropdown with multi-select support
  const assigneesSelect = $("#assignees");
  if (assigneesSelect.length) {
    assigneesSelect.select2({
      theme: "bootstrap-5",
      placeholder: "Select assignees...",
      allowClear: true,
      closeOnSelect: false,
    });

    // Keep removal behavior intuitive and caret UX consistent
    const containerEl = assigneesSelect.next(".select2-container");
    const selectionEl = containerEl.find(".select2-selection--multiple");
    const inlineInput = () =>
      containerEl.find(".select2-search--inline input.select2-search__field");

    const setCaretVisible = (isVisible) => {
      const input = inlineInput();
      if (!input.length) {
        return;
      }
      if (isVisible) {
        input.prop("tabIndex", 0).css("width", "").focus();
      } else {
        input.val("").prop("tabIndex", -1).css("width", "0px");
        if (document.activeElement === input[0]) {
          input.blur();
        }
      }
    };

    let isOpen = false;
    let removalWhileClosed = false;
    let preventCloseReason = null;
    let preventCloseTimer = null;

    const armPreventClose = (reason) => {
      preventCloseReason = reason;
      clearTimeout(preventCloseTimer);
      preventCloseTimer = setTimeout(() => {
        preventCloseReason = null;
      }, 200);
    };

    setCaretVisible(false);

    selectionEl.on(
      "mousedown.select2Removal",
      ".select2-selection__choice__remove",
      () => {
        if (isOpen) {
          armPreventClose("removal");
          setTimeout(() => setCaretVisible(true), 0);
        }
        removalWhileClosed = !isOpen;
        if (removalWhileClosed) {
          setTimeout(() => setCaretVisible(false), 0);
        }
      },
    );

    // Handle "Clear All" button: Let Select2 clear, but manage dropdown state
    // Listen for the clearing event which fires when allowClear 'x' is clicked
    assigneesSelect.on("select2:clearing", () => {
      // This fires BEFORE the clear happens
      // Capture current state
      const wasOpen = isOpen;

      // Prevent default opening behavior if it was closed
      if (!wasOpen) {
        removalWhileClosed = true;
      } else {
        // If open, keep it open
        armPreventClose("clear");
      }
    });

    // After clearing completes, ensure proper state
    assigneesSelect.on("select2:unselect", (e) => {
      // Check if this was a "clear all" (no data in event means clear button)
      if (!e.params || !e.params.data) {
        if (isOpen) {
          setTimeout(() => setCaretVisible(true), 0);
        } else {
          setTimeout(() => setCaretVisible(false), 0);
        }
      }
    });

    assigneesSelect.on("select2:opening", (e) => {
      if (removalWhileClosed && !isOpen) {
        removalWhileClosed = false;
        e.preventDefault();
      }
    });

    assigneesSelect.on("select2:select", () => {
      if (isOpen) {
        armPreventClose("select");
        setTimeout(() => setCaretVisible(true), 0);
      }
    });

    assigneesSelect.on("select2:open", () => {
      isOpen = true;
      removalWhileClosed = false;
      setCaretVisible(true);
    });

    assigneesSelect.on("select2:closing", (e) => {
      if (preventCloseReason) {
        preventCloseReason = null;
        clearTimeout(preventCloseTimer);
        e.preventDefault();
        setCaretVisible(true);
      }
    });

    const closeDropdown = () => {
      assigneesSelect.select2("close");
    };

    assigneesSelect.on("select2:close", () => {
      isOpen = false;
      preventCloseReason = null;
      clearTimeout(preventCloseTimer);
      setCaretVisible(false);
    });

    $(document).on("mousedown.select2Close", (event) => {
      if (!isOpen) {
        return;
      }
      const target = $(event.target);
      const dropdown = $(".select2-container--open");
      if (
        !selectionEl.is(target) &&
        selectionEl.has(target).length === 0 &&
        !dropdown.is(target) &&
        dropdown.has(target).length === 0
      ) {
        closeDropdown();
      }
    });
  }
});
