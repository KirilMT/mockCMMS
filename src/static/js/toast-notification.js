/**
 * Toast Notification Utility
 *
 * A lightweight, customizable toast notification system for displaying user feedback.
 * Supports multiple notification types with icons, auto-dismiss, and manual close.
 *
 * @class ToastNotification
 *
 * @description
 * Creates styled toast notifications with FontAwesome icons and Bootstrap-inspired styling.
 * Toasts appear at the top-center of the viewport and auto-dismiss after a configurable duration.
 *
 * @example
 * // Show a success message
 * ToastNotification.success('Data saved successfully!');
 *
 * // Show an error with custom duration
 * ToastNotification.error('Failed to connect', 10000);
 *
 * // Show a custom toast
 * ToastNotification.show('Custom message', 'warning', 5000);
 */
class ToastNotification {
  /**
   * Display a toast notification
   *
   * @param {string} message - The message to display
   * @param {string} [type='info'] - Toast type: 'success', 'error', 'warning', or 'info'
   * @param {number} [duration=5000] - Auto-dismiss duration in milliseconds (0 = no auto-dismiss)
   */
  static show(message, type = 'info', duration = 5000) {
    const container =
      document.getElementById('toastContainer') || this.createContainer();

    const icons = {
      success: 'fas fa-check-circle',
      error: 'fas fa-exclamation-circle',
      warning: 'fas fa-exclamation-triangle',
      info: 'fas fa-info-circle',
    };

    const titles = {
      success: 'Success',
      error: 'Error',
      warning: 'Warning',
      info: 'Info',
    };

    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.className = 'toast show';
    toast.id = toastId;
    toast.style.opacity = '1';
    toast.innerHTML = `
            <div class="toast-header toast-${type}">
                <i class="toast-icon ${icons[type]}"></i>
                <strong class="toast-title">${titles[type]}</strong>
                <button type="button" class="toast-close" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <div class="toast-body">${message}</div>
        `;

    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', () => {
      ToastNotification.hide(toastId);
    });

    container.appendChild(toast);

    if (duration > 0) {
      setTimeout(() => {
        ToastNotification.hide(toastId);
      }, duration);
    }
  }

  /**
   * Hide and remove a toast notification
   *
   * @param {string} toastId - The ID of the toast to hide
   */
  static hide(toastId) {
    const toast = document.getElementById(toastId);
    if (toast) {
      toast.classList.add('hiding');
      toast.classList.remove('show');
      setTimeout(() => {
        toast.remove();
      }, 300);
    }
  }

  /**
   * Create the toast container element
   *
   * @private
   * @returns {HTMLElement} The created container element
   */
  static createContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'position-fixed';
    container.style.cssText =
      'top: 70px; left: 50%; transform: translateX(-50%); z-index: 10000; min-width: 400px; max-width: 600px;';
    document.body.appendChild(container);
    return container;
  }

  /**
   * Show a success toast
   *
   * @param {string} message - Success message
   * @param {number} [duration=5000] - Auto-dismiss duration in milliseconds
   */
  static success(message, duration = 5000) {
    ToastNotification.show(message, 'success', duration);
  }

  /**
   * Show an error toast
   *
   * @param {string} message - Error message
   * @param {number} [duration=7000] - Auto-dismiss duration in milliseconds
   */
  static error(message, duration = 7000) {
    ToastNotification.show(message, 'error', duration);
  }

  /**
   * Show a warning toast
   *
   * @param {string} message - Warning message
   * @param {number} [duration=6000] - Auto-dismiss duration in milliseconds
   */
  static warning(message, duration = 6000) {
    ToastNotification.show(message, 'warning', duration);
  }

  /**
   * Show an info toast
   *
   * @param {string} message - Info message
   * @param {number} [duration=5000] - Auto-dismiss duration in milliseconds
   */
  static info(message, duration = 5000) {
    ToastNotification.show(message, 'info', duration);
  }
}

// Export to global scope
if (typeof window !== 'undefined') {
  window.ToastNotification = ToastNotification;
}

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ToastNotification;
}
