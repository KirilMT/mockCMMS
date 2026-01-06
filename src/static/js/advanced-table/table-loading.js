/**
 * Loading State Management for Advanced Table
 * Handles loading spinners and disabled states during async operations
 */

/**
 * Show a loading spinner overlay on a button
 * @param {HTMLElement} button - The button element to show loading state
 * @param {string} [loadingText='Loading...'] - Optional loading text
 * @returns {Object} Object with restore function to revert button state
 */
AdvancedTable.prototype.showButtonLoading = function (
  button,
  loadingText = "Loading...",
) {
  if (!button) return { restore: () => {} };

  // Store original state
  const originalHTML = button.innerHTML;
  const originalDisabled = button.disabled;

  // Set loading state
  button.disabled = true;
  button.innerHTML = `
        <span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
        ${loadingText}
    `;

  // Return restore function
  return {
    restore: () => {
      button.innerHTML = originalHTML;
      button.disabled = originalDisabled;
    },
  };
};

/**
 * Show a loading overlay on the table content area only
 * @param {string} [message='Loading...'] - Loading message to display
 */
AdvancedTable.prototype.showTableLoading = function (message = "Loading...") {
  // Remove existing overlay if present
  this.hideTableLoading();

  const overlay = document.createElement("div");
  overlay.className = "table-loading-overlay";
  overlay.innerHTML = `
        <div class="table-loading">
            <div class="spinner-border text-primary" role="status"></div>
            <div class="loading-text">${message}</div>
        </div>
    `;

  // Append to table-responsive div, not the entire container
  const tableResponsive = this.container.querySelector(".table-responsive");
  if (tableResponsive) {
    tableResponsive.appendChild(overlay);
  } else {
    // Fallback: if table-responsive doesn't exist yet, append to container
    this.container.appendChild(overlay);
  }
};

/**
 * Hide the table loading overlay
 */
AdvancedTable.prototype.hideTableLoading = function () {
  // Check in table-responsive first
  const tableResponsive = this.container.querySelector(".table-responsive");
  const overlay = tableResponsive
    ? tableResponsive.querySelector(".table-loading-overlay")
    : this.container.querySelector(".table-loading-overlay");

  if (overlay) {
    overlay.remove();
  }
};

/**
 * Execute an async operation with loading state
 * @param {Function} operation - Async function to execute
 * @param {Object} options - Configuration options
 * @param {HTMLElement} [options.button] - Button to show loading state on
 * @param {string} [options.loadingText] - Button loading text
 * @param {boolean} [options.showTableOverlay] - Show full table overlay
 * @param {string} [options.overlayMessage] - Table overlay message
 * @returns {Promise} Promise that resolves when operation completes
 */
AdvancedTable.prototype.withLoading = async function (operation, options = {}) {
  let buttonState = null;

  try {
    // Show loading state
    if (options.button) {
      buttonState = this.showButtonLoading(options.button, options.loadingText);
    }
    if (options.showTableOverlay) {
      this.showTableLoading(options.overlayMessage);
    }

    // Execute operation
    const result = await operation();

    return result;
  } finally {
    // Always restore state
    if (buttonState) {
      buttonState.restore();
    }
    if (options.showTableOverlay) {
      this.hideTableLoading();
    }
  }
};
