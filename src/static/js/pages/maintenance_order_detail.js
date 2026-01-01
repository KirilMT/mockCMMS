/* global showDeleteConfirm, $ */

// Enable/disable and require frequency field based on order type (Bug #16 & #26)
document.addEventListener('DOMContentLoaded', function () {
  const orderTypeField = document.getElementById('order_type');
  const frequencyField = document.getElementById('frequency');
  const frequencyLabel = document.querySelector('label[for="frequency"]');

  function updateFrequencyField() {
    const isPM = orderTypeField.value === 'PM';

    if (isPM) {
      // Enable and require the field for PM orders
      frequencyField.disabled = false;
      frequencyField.required = true;
      // Add required-field class to show red asterisk
      if (frequencyLabel && !frequencyLabel.classList.contains('required-field')) {
        frequencyLabel.classList.add('required-field');
      }
      // Don't touch the value - let the HTML 'selected' attribute handle it
    } else {
      // Disable, clear, and make optional for non-PM orders
      frequencyField.disabled = true;
      frequencyField.required = false;
      frequencyField.value = '';
      // Remove required-field class
      if (frequencyLabel) {
        frequencyLabel.classList.remove('required-field');
      }
    }
  }

  // Set initial state on page load
  if (orderTypeField && frequencyField) {
    updateFrequencyField();

    // Update when user changes the order type
    orderTypeField.addEventListener('change', function () {
      const isPM = orderTypeField.value === 'PM';

      if (!isPM) {
        // Only clear the value when user switches FROM PM to non-PM
        frequencyField.value = '';
      }
      // If switching TO PM, leave the value alone (it will be empty for new MOs,
      // or keep the existing value for edited MOs)

      updateFrequencyField();
    });
  }

  // Bug #5: Initialize Select2 for assignees dropdown
  const assigneesSelect = $('#assignees');
  if (assigneesSelect.length) {
    assigneesSelect.select2({
      theme: 'bootstrap-5',
      placeholder: 'Select assignees...',
      allowClear: true,
      closeOnSelect: false,
    });

    // Bug #28 refined: keep removal behavior intuitive and caret UX consistent.
    const containerEl = assigneesSelect.next('.select2-container');
    const selectionEl = containerEl.find('.select2-selection--multiple');
    const inlineInput = () => containerEl.find('.select2-search--inline input.select2-search__field');

    const setCaretVisible = (isVisible) => {
      const input = inlineInput();
      if (!input.length) {
        return;
      }
      if (isVisible) {
        input.prop('tabIndex', 0).css('width', '').focus();
      } else {
        input.val('').prop('tabIndex', -1).css('width', '0px');
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

    selectionEl.on('mousedown.select2Removal', '.select2-selection__choice__remove', () => {
      if (isOpen) {
        armPreventClose('removal');
        setTimeout(() => setCaretVisible(true), 0);
      }
      removalWhileClosed = !isOpen;
      if (removalWhileClosed) {
        setTimeout(() => setCaretVisible(false), 0);
      }
    });

    // Handle "Clear All" button: Let Select2 clear, but manage dropdown state
    // Listen for the clearing event which fires when allowClear 'x' is clicked
    assigneesSelect.on('select2:clearing', () => {
      // This fires BEFORE the clear happens
      // Capture current state
      const wasOpen = isOpen;

      // Prevent default opening behavior if it was closed
      if (!wasOpen) {
        removalWhileClosed = true;
      } else {
        // If open, keep it open
        armPreventClose('clear');
      }
    });

    // After clearing completes, ensure proper state
    assigneesSelect.on('select2:unselect', (e) => {
      // Check if this was a "clear all" (no data in event means clear button)
      if (!e.params || !e.params.data) {
        if (isOpen) {
          setTimeout(() => setCaretVisible(true), 0);
        } else {
          setTimeout(() => setCaretVisible(false), 0);
        }
      }
    });

    assigneesSelect.on('select2:opening', (e) => {
      if (removalWhileClosed && !isOpen) {
        removalWhileClosed = false;
        e.preventDefault();
      }
    });

    assigneesSelect.on('select2:select', () => {
      if (isOpen) {
        armPreventClose('select');
        setTimeout(() => setCaretVisible(true), 0);
      }
    });

    assigneesSelect.on('select2:open', () => {
      isOpen = true;
      removalWhileClosed = false;
      setCaretVisible(true);
    });

    assigneesSelect.on('select2:closing', (e) => {
      if (preventCloseReason) {
        preventCloseReason = null;
        clearTimeout(preventCloseTimer);
        e.preventDefault();
        setCaretVisible(true);
      }
    });

    const closeDropdown = () => {
      assigneesSelect.select2('close');
    };

    assigneesSelect.on('select2:close', () => {
      isOpen = false;
      preventCloseReason = null;
      clearTimeout(preventCloseTimer);
      setCaretVisible(false);
    });

    $(document).on('mousedown.select2Close', (event) => {
      if (!isOpen) {
        return;
      }
      const target = $(event.target);
      const dropdown = $('.select2-container--open');
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

  // Handle delete confirmation buttons
  document.querySelectorAll('.delete-confirm-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const form = btn.closest('form');
      const message = btn.dataset.confirmMessage;
      showDeleteConfirm(form, message);
    });
  });
});
