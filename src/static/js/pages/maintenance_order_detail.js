// Maintenance Order Detail Page Scripts

document.addEventListener("DOMContentLoaded", function () {
  // -------------------------------------------------------------------------
  // Frequency Field Handling (Bug #16 & #26)
  // -------------------------------------------------------------------------
  const orderTypeField = document.getElementById("order_type");
  const frequencyField = document.getElementById("frequency");
  const frequencyLabel = document.querySelector('label[for="frequency"]');

  function updateFrequencyField() {
    if (!orderTypeField || !frequencyField) return;

    const isPM = orderTypeField.value === "PM";

    if (isPM) {
      // Enable and require the field for PM orders
      frequencyField.disabled = false;
      frequencyField.required = true;
      // Add required-field class to show red asterisk
      if (
        frequencyLabel &&
        !frequencyLabel.classList.contains("required-field")
      ) {
        frequencyLabel.classList.add("required-field");
      }
    } else {
      // Disable, clear, and make optional for non-PM orders
      frequencyField.disabled = true;
      frequencyField.required = false;
      frequencyField.value = "";
      // Remove required-field class
      if (frequencyLabel) {
        frequencyLabel.classList.remove("required-field");
      }
    }
  }

  // Set initial state on page load
  updateFrequencyField();

  // Update when user changes the order type
  if (orderTypeField) {
    orderTypeField.addEventListener("change", function () {
      const isPM = orderTypeField.value === "PM";

      if (!isPM && frequencyField) {
        // Only clear the value when user switches FROM PM to non-PM
        frequencyField.value = "";
      }
      updateFrequencyField();
    });
  }

  // -------------------------------------------------------------------------
  // Assignees Select2 Initialization (Bug #5 & #28)
  // -------------------------------------------------------------------------
  if (window.$ && $.fn.select2) {
    const assigneesSelect = $("#assignees");
    if (assigneesSelect.length) {
      assigneesSelect.select2({
        theme: "bootstrap-5",
        placeholder: "Select assignees...",
        allowClear: true,
        closeOnSelect: false,
      });

      // Bug #28 refined: keep removal behavior intuitive and caret UX consistent.
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
      assigneesSelect.on("select2:clearing", (e) => {
        const wasOpen = isOpen;
        if (!wasOpen) {
          removalWhileClosed = true;
        } else {
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
  }
});
