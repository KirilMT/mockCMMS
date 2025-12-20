// Configuration management methods

/**
 * Saves the current table configuration (columns, filters, sort) to the backend.
 * Prompts the user for a configuration name.
 */
AdvancedTable.prototype.saveConfiguration = function () {
  const name = prompt('Enter configuration name:');
  if (!name || !name.trim()) return;

  const duplicate = this.savedConfigs.find(
    (c) => c.config_name.toLowerCase() === name.trim().toLowerCase()
  );
  if (duplicate) {
    ToastNotification.error(
      `Configuration name "${name.trim()}" already exists. Please choose a different name.`
    );
    return;
  }

  const config = {
    config_name: name.trim(),
    column_order: JSON.stringify(this.columnOrder),
    hidden_columns: JSON.stringify(Array.from(this.hiddenColumns)),
    filters: JSON.stringify(this.filters),
    sort_config: JSON.stringify(this.currentSort),
    is_default: false,
  };

  const csrfToken = document
    .querySelector('meta[name=csrf-token]')
    ?.getAttribute('content');
  fetch('/api/table-config/' + this.pageName, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
    },
    body: JSON.stringify(config),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      if (data.success) {
        this.selectedConfigId = data.id;
        this.loadConfiguration();
      } else {
        ToastNotification.error(
          'Failed to save configuration: ' + (data.error || 'Unknown error')
        );
      }
    })
    .catch((error) => {
      console.error('Error saving configuration:', error);
      ToastNotification.error('Error saving configuration: ' + error.message);
    });
};

/**
 * Loads saved configurations from the backend.
 * Populates the sidebar and applies the default configuration if one exists.
 */
AdvancedTable.prototype.loadConfiguration = function () {
  // Show loading overlay for initial load
  this.showTableLoading('Loading saved views...');

  this.fetchWithRetry('/api/table-config/' + this.pageName)
    .then((response) => {
      if (!response.ok) {
        if (response.status === 404 || response.status === 401) {
          throw new Error('NO_CONFIGS');
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then((configs) => {
      this.savedConfigs = configs || [];

      // Populate sidebar saved views instead of dropdown
      if (this.sidebar) {
        this.sidebar.populateSavedViews();
      }

      // Auto-load default configuration if exists
      const defaultConfig = configs.find((c) => c.is_default);
      if (defaultConfig) {
        this.applyConfiguration(defaultConfig);
        this.selectedConfigId = defaultConfig.id;
        this.lastLoadedConfigId = defaultConfig.id; // Track for Update button

        // Refresh sidebar sections to reflect loaded state
        if (this.sidebar) {
          this.sidebar.loadExistingFilters();
          this.sidebar.populateColumns();
          this.sidebar.populateSavedViews();
        }
      }
    })
    .catch((error) => {
      if (error.message === 'NO_CONFIGS') {
        // No configurations found, this is expected for new users
      } else if (error.message === 'OFFLINE') {
        // Offline mode, silent fail
      } else if (error.message === 'Max retries exceeded') {
        console.error(
          'Failed to load configurations after multiple retries:',
          error
        );
        ToastNotification.error(
          'Unable to load saved views. Please try again later.'
        );
      } else {
        console.error('Error loading configurations:', error);
        ToastNotification.warning('Could not load saved configurations');
      }
      this.savedConfigs = [];

      // Still populate empty sidebar
      if (this.sidebar) {
        this.sidebar.populateSavedViews();
      }
    })
    .finally(() => {
      // Always hide loading overlay
      this.hideTableLoading();
    });
};

/**
 * Applies a given configuration to the table.
 * @param {Object} config - The configuration object to apply.
 * @param {string} config.column_order - JSON string of column order.
 * @param {string} config.hidden_columns - JSON string of hidden columns.
 * @param {string} config.filters - JSON string of filters.
 * @param {string} config.sort_config - JSON string of sort configuration.
 */
AdvancedTable.prototype.applyConfiguration = function (config) {
  if (config.column_order) this.columnOrder = JSON.parse(config.column_order);
  if (config.hidden_columns)
    this.hiddenColumns = new Set(JSON.parse(config.hidden_columns));
  if (config.filters) this.filters = JSON.parse(config.filters);
  if (config.sort_config) this.currentSort = JSON.parse(config.sort_config);

  this.render();
};

/**
 * Deletes a saved configuration by ID.
 * @param {number|string} configId - The ID of the configuration to delete.
 */
AdvancedTable.prototype.deleteConfiguration = function (configId) {
  if (!confirm('Are you sure you want to delete this view?')) return;

  const csrfToken = document
    .querySelector('meta[name=csrf-token]')
    ?.getAttribute('content');
  fetch(`/api/table-config/${this.pageName}/${configId}`, {
    method: 'DELETE',
    headers: {
      'X-CSRFToken': csrfToken,
    },
  })
    .then((response) => {
      if (!response.ok)
        throw new Error(`HTTP error! status: ${response.status}`);
      return response.json();
    })
    .then((data) => {
      if (data.success) {
        if (this.selectedConfigId === configId) {
          this.selectedConfigId = null;
        }
        this.loadConfiguration();
        ToastNotification.success('View deleted successfully');
      } else {
        ToastNotification.error('Failed to delete view');
      }
    })
    .catch((error) => {
      console.error('Error deleting configuration:', error);
      ToastNotification.error('Error deleting configuration');
    });
};

/**
 * Sets a configuration as the default view.
 * @param {number|string} configId - The ID of the configuration to set as default.
 */
AdvancedTable.prototype.setDefaultView = function (configId) {
  const csrfToken = document
    .querySelector('meta[name=csrf-token]')
    ?.getAttribute('content');
  fetch(`/api/table-config/${this.pageName}/${configId}/default`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrfToken,
    },
  })
    .then((response) => {
      if (!response.ok)
        throw new Error(`HTTP error! status: ${response.status}`);
      return response.json();
    })
    .then((data) => {
      if (data.success) {
        this.loadConfiguration();
        ToastNotification.success('Default view updated');
      } else {
        ToastNotification.error('Failed to update default view');
      }
    })
    .catch((error) => {
      console.error('Error setting default view:', error);
      ToastNotification.error('Error setting default view');
    });
};
