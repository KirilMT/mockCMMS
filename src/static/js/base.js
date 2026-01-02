/* global $ */
// Global delete confirmation handler
let deleteFormToSubmit = null;
let deleteCallback = null;

/**
 * Show delete confirmation modal
 * @param {HTMLFormElement} form - The form to submit on confirmation
 * @param {string} message - The message to display
 * @param {Function} callback - The callback function to execute on confirmation
 * @returns {boolean} - Always returns false to prevent default action
 */
function showDeleteConfirm(form, message, callback) {
  // If form is provided, use form submission (for delete forms)
  // If callback is provided, use callback (for JavaScript operations like view delete)
  deleteFormToSubmit = form;
  deleteCallback = callback;

  const msg = message || "Are you sure you want to delete this item?";

  // Check if jQuery and Bootstrap modal are available
  if (typeof $ !== 'undefined' && $.fn.modal) {
    document.getElementById("deleteConfirmModalMessage").textContent = msg;
    $("#deleteConfirmModal").modal("show");
  } else {
    // Fallback for when jQuery/Bootstrap is not loaded (e.g. some test environments)
    console.warn("jQuery or Bootstrap Modal not loaded. Using native confirm.");
    if (window.confirm(msg)) {
      if (deleteCallback) {
        deleteCallback();
        deleteCallback = null;
      } else if (deleteFormToSubmit) {
        deleteFormToSubmit.submit();
        deleteFormToSubmit = null;
      }
    }
  }
  return false; // Prevent form submission
}

// Global input modal handler
let inputCallback = null;

/**
 * Show input modal
 * @param {string} message - The message to display
 * @param {Function} callback - The callback function to execute on confirmation
 */
function showInputModal(message, callback) {
  inputCallback = callback;

  if (typeof $ !== 'undefined' && $.fn.modal) {
    document.getElementById("inputModalLabel").textContent = message;
    document.getElementById("inputModalValue").value = "";
    $("#inputModal").modal("show");
    // Focus on input after modal appears
    $("#inputModal").on("shown.bs.modal", function () {
      $("#inputModalValue").focus();
    });
  } else {
    // Fallback
    const value = window.prompt(message);
    if (value !== null && inputCallback) {
      inputCallback(value);
      inputCallback = null;
    }
  }
}

// Global generic confirmation handler
let confirmCallback = null;

/**
 * Show generic confirmation modal
 * @param {string} message - The message to display
 * @param {Function} callback - The callback function to execute on confirmation
 */
function showConfirmModal(message, callback) {
  confirmCallback = callback;
  const msg = message || "Are you sure you want to proceed?";

  if (typeof $ !== 'undefined' && $.fn.modal) {
    document.getElementById("confirmModalMessage").textContent = msg;
    $("#confirmModal").modal("show");
  } else {
    // Fallback
    if (window.confirm(msg)) {
      if (confirmCallback) {
        confirmCallback();
        confirmCallback = null;
      }
    }
  }
}

/**
 * Initialize base functionality
 */
function initBase() {
  // Initialize Select2 if present (Bootstrap 5 theme)
  if (typeof $ !== 'undefined' && $.fn.select2) {
    $('.select2').select2({
      theme: 'bootstrap-5'
    });
  }

  // Sidebar toggle functionality
  const sidebarToggle = document.getElementById("sidebarToggle");
  if (sidebarToggle) {
    sidebarToggle.addEventListener("click", function () {
      const sidebar = document.getElementById("sidebar-wrapper");
      const overlay = document.getElementById("overlay");

      sidebar.classList.toggle("toggled");

      if (sidebar.classList.contains("toggled")) {
        overlay.style.display = "block";
      } else {
        overlay.style.display = "none";
      }
    });
  }

  // Close sidebar when clicking overlay
  const overlay = document.getElementById("overlay");
  if (overlay) {
    overlay.addEventListener("click", function () {
      const sidebar = document.getElementById("sidebar-wrapper");

      sidebar.classList.remove("toggled");
      overlay.style.display = "none";
    });
  }

  // Handle confirm button click
  const confirmBtn = document.getElementById("confirmDeleteBtn");
  if (confirmBtn) {
    confirmBtn.addEventListener("click", function () {
      $("#deleteConfirmModal").modal("hide");

      if (deleteCallback) {
        // Use callback for JavaScript operations
        deleteCallback();
        deleteCallback = null;
      } else if (deleteFormToSubmit) {
        // Use form submission for delete forms
        deleteFormToSubmit.submit();
        deleteFormToSubmit = null;
      }
    });
  }

  // Handle input modal confirm
  const inputConfirmBtn = document.getElementById("inputModalConfirmBtn");
  if (inputConfirmBtn) {
    inputConfirmBtn.addEventListener("click", function () {
      const value = document.getElementById("inputModalValue").value;
      $("#inputModal").modal("hide");

      if (inputCallback) {
        inputCallback(value);
        inputCallback = null;
      }
    });
  }

  // Handle Enter key in input modal
  const inputField = document.getElementById("inputModalValue");
  if (inputField) {
    inputField.addEventListener("keypress", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        inputConfirmBtn.click();
      }
    });
  }

  // Handle confirm modal button
  const confirmModalBtn = document.getElementById("confirmModalBtn");
  if (confirmModalBtn) {
    confirmModalBtn.addEventListener("click", function () {
      $("#confirmModal").modal("hide");

      if (confirmCallback) {
        confirmCallback();
        confirmCallback = null;
      }
    });
  }

  // Handle global delete confirmation buttons
  document.querySelectorAll('.delete-confirm-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const form = btn.closest('form');
      const message = btn.dataset.confirmMessage;
      showDeleteConfirm(form, message);
    });
  });
}

// Initialize on DOM load
if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", initBase);
}

// Expose to window for browser usage
if (typeof window !== "undefined") {
  window.showDeleteConfirm = showDeleteConfirm;
  window.showInputModal = showInputModal;
  window.showConfirmModal = showConfirmModal;
  window.initBase = initBase;
}

// Update exports to include initBase
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    showDeleteConfirm,
    showInputModal,
    showConfirmModal,
    initBase
  };
}
