// Configuration management methods
AdvancedTable.prototype.saveConfiguration = function() {
    const name = prompt('Enter configuration name:');
    if (!name || !name.trim()) return;

    const duplicate = this.savedConfigs.find(c => c.config_name.toLowerCase() === name.trim().toLowerCase());
    if (duplicate) {
        ToastNotification.error(`Configuration name "${name.trim()}" already exists. Please choose a different name.`);
        return;
    }

    const config = {
        config_name: name.trim(),
        column_order: JSON.stringify(this.columnOrder),
        hidden_columns: JSON.stringify(Array.from(this.hiddenColumns)),
        filters: JSON.stringify(this.filters),
        sort_config: JSON.stringify(this.currentSort),
        is_default: false
    };

    const csrfToken = document.querySelector('meta[name=csrf-token]')?.getAttribute('content');
    fetch('/api/table-config/' + this.pageName, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(config)
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                this.selectedConfigId = data.id;
                this.loadConfiguration();
            } else {
                ToastNotification.error('Failed to save configuration: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error saving configuration:', error);
            ToastNotification.error('Error saving configuration: ' + error.message);
        });
};

AdvancedTable.prototype.loadConfiguration = function() {
    fetch('/api/table-config/' + this.pageName)
        .then(response => {
            if (!response.ok) {
                if (response.status === 404 || response.status === 401) {
                    throw new Error('NO_CONFIGS');
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(configs => {
            this.savedConfigs = configs || [];

            // Populate sidebar saved views instead of dropdown
            if (this.sidebar) {
                this.sidebar.populateSavedViews();
            }

            // Auto-load default configuration if exists
            const defaultConfig = configs.find(c => c.is_default);
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
        .catch(error => {
            if (error.message === 'NO_CONFIGS') {
                console.log('No saved configurations available');
            } else {
                console.error('Error loading configurations:', error);
                ToastNotification.warning('Could not load saved configurations');
            }
            this.savedConfigs = [];

            // Still populate empty sidebar
            if (this.sidebar) {
                this.sidebar.populateSavedViews();
            }
        });
};

AdvancedTable.prototype.applyConfiguration = function(config) {
    if (config.column_order) this.columnOrder = JSON.parse(config.column_order);
    if (config.hidden_columns) this.hiddenColumns = new Set(JSON.parse(config.hidden_columns));
    if (config.filters) this.filters = JSON.parse(config.filters);
    if (config.sort_config) this.currentSort = JSON.parse(config.sort_config);

    this.render();
};