/**
 * Network Retry Utility for Advanced Table
 * Handles automatic retry with exponential backoff for failed network requests
 */

/**
 * Fetch with automatic retry and exponential backoff
 * @param {string} url - The URL to fetch
 * @param {Object} options - Fetch options
 * @param {number} [maxRetries=3] - Maximum number of retry attempts
 * @param {number} [baseDelay=1000] - Base delay in milliseconds for exponential backoff
 * @returns {Promise<Response>} Fetch response
 */
AdvancedTable.prototype.fetchWithRetry = async function (
  url,
  options = {},
  maxRetries = 3,
  baseDelay = 1000,
) {
  let lastError;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(url, options);

      // If response is OK, return it
      if (response.ok) {
        return response;
      }

      // For client errors (4xx), don't retry
      if (response.status >= 400 && response.status < 500) {
        return response;
      }

      // For server errors (5xx), retry
      if (response.status >= 500 && attempt < maxRetries) {
        const delay = baseDelay * Math.pow(2, attempt);

        await this.sleep(delay);
        continue;
      }

      return response;
    } catch (error) {
      lastError = error;

      // Check if it's a network error
      if (error instanceof TypeError && error.message.includes("fetch")) {
        if (attempt < maxRetries) {
          const delay = baseDelay * Math.pow(2, attempt);

          // Show user-friendly message on last retry
          if (attempt === maxRetries - 1) {
            ToastNotification.warning(
              "Connection issues detected. Retrying...",
            );
          }

          await this.sleep(delay);
          continue;
        }
      }

      // If not a network error or out of retries, throw
      throw error;
    }
  }

  // If we exhausted all retries, throw the last error
  throw lastError || new Error("Max retries exceeded");
};

/**
 * Sleep utility for retry delays
 * @param {number} ms - Milliseconds to sleep
 * @returns {Promise} Promise that resolves after delay
 */
AdvancedTable.prototype.sleep = function (ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
};

/**
 * Check if user is online
 * @returns {boolean} True if online
 */
AdvancedTable.prototype.isOnline = function () {
  return navigator.onLine;
};

/**
 * Execute a network operation with offline detection
 * @param {Function} operation - Async function that makes network requests
 * @param {string} [offlineMessage] - Custom message to show when offline
 * @returns {Promise} Result of the operation
 */
AdvancedTable.prototype.withNetworkCheck = async function (
  operation,
  offlineMessage = "You are offline. Please check your connection.",
) {
  if (!this.isOnline()) {
    ToastNotification.error(offlineMessage);
    throw new Error("OFFLINE");
  }

  return await operation();
};
