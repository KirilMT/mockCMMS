/**
 * Flash Messages Handler
 *
 * Processes server-side Flask flash messages and displays them as toast notifications.
 * This module bridges Flask's flash() function with the ToastNotification UI component.
 *
 * @module flash-messages
 * @requires ToastNotification
 *
 * @description
 * Flask flash messages are rendered into a hidden div with a data-messages attribute.
 * This script reads that data on DOMContentLoaded and displays each message as a toast.
 *
 * Category Mapping:
 * - Flask 'danger' → ToastNotification 'error'
 * - Flask 'success' → ToastNotification 'success'
 * - Flask 'warning' → ToastNotification 'warning'
 * - Flask 'info' → ToastNotification 'info'
 *
 * @example
 * // In Flask:
 * flash('Operation successful!', 'success')
 * flash('Invalid input', 'danger')
 *
 * // In template (base.html):
 * <div id="flash-messages" data-messages="{{ messages | tojson | safe }}"></div>
 *
 * // This script automatically processes and displays them
 */

/**
 * Process and display flash messages
 */
function processFlashMessages() {
  const flashContainer = document.getElementById('flash-messages');

  if (flashContainer && flashContainer.dataset.messages) {
    try {
      const flashMessages = JSON.parse(flashContainer.dataset.messages);

      // Map Flask flash categories to ToastNotification types
      const categoryMap = {
        danger: 'error', // Flask uses 'danger', ToastNotification uses 'error'
        success: 'success',
        warning: 'warning',
        info: 'info',
      };

      flashMessages.forEach((msg) => {
        if (window.ToastNotification && Array.isArray(msg) && msg.length >= 2) {
          // msg[0] is the category (success, danger/error, warning, info)
          // msg[1] is the message text
          const category = categoryMap[msg[0]] || msg[0];
          window.ToastNotification.show(msg[1], category);
        }
      });
    } catch (error) {
      console.error('Error parsing flash messages:', error);
    }
  }
}

// Try to process immediately if DOM is already loaded
if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') {
    // DOM is still loading, wait for DOMContentLoaded
    document.addEventListener('DOMContentLoaded', processFlashMessages);
  } else {
    // DOM is already loaded, process immediately
    processFlashMessages();
  }
}

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { processFlashMessages };
}
