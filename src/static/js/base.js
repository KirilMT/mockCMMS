// Sidebar toggle functionality
if (typeof module !== 'undefined' && module.exports) {
    // Jest environment - no-op or mock
} else {
    // Browser environment
    document.addEventListener('DOMContentLoaded', function () {
        // Sidebar Toggle
        const sidebarToggle = document.getElementById('sidebarToggle');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', function () {
                const sidebar = document.getElementById('sidebar-wrapper');
                const overlay = document.getElementById('overlay');

                if (sidebar) sidebar.classList.toggle('toggled');

                if (overlay) {
                    if (sidebar && sidebar.classList.contains('toggled')) {
                        overlay.style.display = 'block';
                    } else {
                        overlay.style.display = 'none';
                    }
                }
            });
        }

        // Overlay Click
        const overlay = document.getElementById('overlay');
        if (overlay) {
            overlay.addEventListener('click', function () {
                const sidebar = document.getElementById('sidebar-wrapper');
                const overlay = document.getElementById('overlay');

                if (sidebar) sidebar.classList.remove('toggled');
                if (overlay) overlay.style.display = 'none';
            });
        }

        // Confirmation Modal Handlers
        const confirmBtn = document.getElementById('confirmDeleteBtn');
        if (confirmBtn) {
            confirmBtn.addEventListener('click', function () {
                $('#deleteConfirmModal').modal('hide');

                if (window.deleteCallback) {
                    // Use callback for JavaScript operations
                    window.deleteCallback();
                    window.deleteCallback = null;
                } else if (window.deleteFormToSubmit) {
                    // Use form submission for delete forms
                    window.deleteFormToSubmit.submit();
                    window.deleteFormToSubmit = null;
                }
            });
        }

        // Handle input modal confirm
        const inputConfirmBtn = document.getElementById('inputModalConfirmBtn');
        if (inputConfirmBtn) {
            inputConfirmBtn.addEventListener('click', function () {
                const valueInput = document.getElementById('inputModalValue');
                const value = valueInput ? valueInput.value : '';
                $('#inputModal').modal('hide');

                if (window.inputCallback) {
                    window.inputCallback(value);
                    window.inputCallback = null;
                }
            });
        }

        // Handle Enter key in input modal
        const inputField = document.getElementById('inputModalValue');
        if (inputField && inputConfirmBtn) {
            inputField.addEventListener('keypress', function (e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    inputConfirmBtn.click();
                }
            });
        }

        // Handle confirm modal button
        const confirmModalBtn = document.getElementById('confirmModalBtn');
        if (confirmModalBtn) {
            confirmModalBtn.addEventListener('click', function () {
                $('#confirmModal').modal('hide');

                if (window.confirmCallback) {
                    window.confirmCallback();
                    window.confirmCallback = null;
                }
            });
        }
    });
}

// Global variables for callbacks
window.deleteFormToSubmit = null;
window.deleteCallback = null;
window.inputCallback = null;
window.confirmCallback = null;

/**
 * Show delete confirmation modal
 * @param {HTMLFormElement} form - Form to submit on confirmation (optional)
 * @param {string} message - Message to display
 * @param {Function} callback - Callback to execute on confirmation (optional)
 * @returns {boolean} - Always returns false to prevent default action
 */
function showDeleteConfirm(form, message, callback) {
    window.deleteFormToSubmit = form;
    window.deleteCallback = callback;
    const msgEl = document.getElementById('deleteConfirmMessage');
    if (msgEl) {
        msgEl.textContent = message || 'Are you sure you want to delete this item?';
    }
    $('#deleteConfirmModal').modal('show');
    return false;
}

/**
 * Show input modal
 * @param {string} message - Message/Label to display
 * @param {Function} callback - Callback that receives the input value
 */
function showInputModal(message, callback) {
    window.inputCallback = callback;
    const labelEl = document.getElementById('inputModalLabel');
    if (labelEl) labelEl.textContent = message;

    const inputEl = document.getElementById('inputModalValue');
    if (inputEl) inputEl.value = '';

    $('#inputModal').modal('show');
    // Focus on input after modal appears
    $('#inputModal').on('shown.bs.modal', function () {
        if (inputEl) inputEl.focus();
    });
}

/**
 * Show generic confirmation modal
 * @param {string} message - Message to display
 * @param {Function} callback - Callback to execute on confirmation
 */
function showConfirmModal(message, callback) {
    window.confirmCallback = callback;
    const msgEl = document.getElementById('confirmModalMessage');
    if (msgEl) {
        msgEl.textContent = message || 'Are you sure you want to proceed?';
    }
    $('#confirmModal').modal('show');
}

// Export functions for potential module usage (though mostly global)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        showDeleteConfirm,
        showInputModal,
        showConfirmModal
    };
}
