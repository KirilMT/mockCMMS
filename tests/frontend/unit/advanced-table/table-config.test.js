
// Mock dependencies
global.TableSidebar = class {
    constructor(table) {
        this.table = table;
    }
    populateSavedViews() { }
    loadExistingFilters() { }
    populateColumns() { }
};

global.ToastNotification = {
    error: jest.fn(),
    warning: jest.fn(),
    success: jest.fn(),
    info: jest.fn()
};

global.fetch = jest.fn();
global.prompt = jest.fn();

// Setup environment
const AdvancedTable = require('../../../../src/static/js/advanced-table/table-core.js');
global.AdvancedTable = AdvancedTable;
require('../../../../src/static/js/advanced-table/table-config.js');

// Helper to mock fetch response
const mockFetchResponse = (ok, data) => {
    return Promise.resolve({
        ok,
        status: ok ? 200 : 400,
        json: () => Promise.resolve(data)
    });
};

describe('TableConfig Module', () => {
    let table;

    beforeEach(() => {
        document.body.innerHTML = `
            <div id="table-container"></div>
            <meta name="csrf-token" content="mock-token">
        `;

        // Mock init methods to avoid full render
        AdvancedTable.prototype.render = jest.fn();
        // Overwrite loadConfiguration mock from beforeEach if it exists or use original
        // But since we are testing loadConfiguration, we want the real one.
        // The real one is added by require(...) above.

        // Mock fetchWithRetry (used in loadConfiguration)
        AdvancedTable.prototype.fetchWithRetry = jest.fn().mockResolvedValue({
            ok: true,
            json: () => Promise.resolve([])
        });
        AdvancedTable.prototype.showTableLoading = jest.fn();
        AdvancedTable.prototype.hideTableLoading = jest.fn();

        table = new AdvancedTable('table-container');
        table.pageName = 'test-page';
        table.savedConfigs = [];

        jest.clearAllMocks();
    });

    test('TG-1.1: test_saveView_creates_named_configuration', async () => {
        global.prompt.mockReturnValue('My Config');

        // Setup table state
        table.columnOrder = ['id', 'name'];
        table.hiddenColumns = new Set(['age']);
        table.filters = [{ col: 'name', val: 'a' }];
        table.currentSort = { col: 'name', dir: 'asc' };

        // Mock fetch success
        global.fetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve({ success: true, id: 123 })
        });

        // Spy on loadConfiguration to verify it's called
        const loadConfigSpy = jest.spyOn(table, 'loadConfiguration').mockImplementation(() => { });

        await table.saveConfiguration();

        expect(global.fetch).toHaveBeenCalledWith('/api/table-config/test-page', expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('"config_name":"My Config"')
        }));

        // Check body content
        const callArgs = global.fetch.mock.calls[0];
        const body = JSON.parse(callArgs[1].body);
        expect(body.config_name).toBe('My Config');
        expect(JSON.parse(body.hidden_columns)).toEqual(['age']);

        // Should reload configs on success
        // Since loadConfiguration is async and called in a promise chain, we need to wait?
        // saveConfiguration returns a promise? No, it doesn't return the promise chain.
        // It's "void". This makes testing async difficult.

        // We can wait for all promises to resolve
        await new Promise(resolve => setTimeout(resolve, 0));

        expect(table.selectedConfigId).toBe(123);
        expect(loadConfigSpy).toHaveBeenCalled();
    });

    test('TG-1.2: test_loadView_restores_configuration', async () => {
        const mockConfigs = [{
            id: 1,
            config_name: 'Default',
            is_default: true,
            column_order: '["name", "id"]',
            hidden_columns: '["role"]',
            filters: '[{"col":"name"}]',
            sort_config: '{"col":"id","dir":"desc"}'
        }];

        table.fetchWithRetry.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve(mockConfigs)
        });

        // Spy on applyConfiguration
        const applySpy = jest.spyOn(table, 'applyConfiguration');

        // We need to verify side effects on sidebar
        table.sidebar.populateSavedViews = jest.fn();
        table.sidebar.loadExistingFilters = jest.fn();
        table.sidebar.populateColumns = jest.fn();

        // wait for loadConfiguration promise
        const loadPromise = table.loadConfiguration();
        await new Promise(resolve => setTimeout(resolve, 0));
        await loadPromise;

        expect(table.savedConfigs).toEqual(mockConfigs);
        expect(applySpy).toHaveBeenCalledWith(mockConfigs[0]);
        expect(table.selectedConfigId).toBe(1);
        expect(table.sidebar.populateSavedViews).toHaveBeenCalled();
    });

    test('TG-1.3: test_deleteView_removes_configuration', async () => {
        global.confirm = jest.fn(() => true);
        global.fetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve({ success: true })
        });
        const loadConfigSpy = jest.spyOn(table, 'loadConfiguration');

        table.selectedConfigId = 5;
        await table.deleteConfiguration(5);

        // Wait for promises to resolve
        await new Promise(resolve => setTimeout(resolve, 0));

        expect(global.confirm).toHaveBeenCalled();
        expect(global.fetch).toHaveBeenCalledWith('/api/table-config/test-page/5', expect.objectContaining({
            method: 'DELETE'
        }));
        expect(table.selectedConfigId).toBeNull(); // Should reset if deleted current
        expect(loadConfigSpy).toHaveBeenCalled();
    });

    test('TG-1.4: test_setDefaultView_persists_preference', async () => {
        global.fetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve({ success: true })
        });
        const loadConfigSpy = jest.spyOn(table, 'loadConfiguration');

        await table.setDefaultView(10);

        // Wait for promises to resolve
        await new Promise(resolve => setTimeout(resolve, 0));

        expect(global.fetch).toHaveBeenCalledWith('/api/table-config/test-page/10/default', expect.objectContaining({
            method: 'POST'
        }));
        expect(loadConfigSpy).toHaveBeenCalled();
    });


    test('TG-1.5: test_getViews_returns_all_saved_views', async () => {
        // This functionality is implicitly covered by loadConfiguration which populates this.savedConfigs
        // Let's verify that property access works as expected
        const mockConfigs = [{ id: 1, name: 'View 1' }, { id: 2, name: 'View 2' }];
        table.fetchWithRetry.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve(mockConfigs)
        });

        const loadPromise = table.loadConfiguration();
        await new Promise(resolve => setTimeout(resolve, 0));
        await loadPromise;
        expect(table.savedConfigs).toEqual(mockConfigs);
    });

    test('TG-2.1: test_saveConfiguration_cancelled_by_user', async () => {
        global.prompt.mockReturnValue(null);

        await table.saveConfiguration();

        expect(global.fetch).not.toHaveBeenCalled();
    });

    test('TG-2.2: test_saveConfiguration_empty_name', async () => {
        global.prompt.mockReturnValue('   '); // whitespace only

        await table.saveConfiguration();

        expect(global.fetch).not.toHaveBeenCalled();
    });

    test('TG-2.3: test_saveConfiguration_duplicate_name', async () => {
        global.prompt.mockReturnValue('Existing View');
        table.savedConfigs = [{ id: 1, config_name: 'Existing View' }];

        await table.saveConfiguration();

        expect(global.fetch).not.toHaveBeenCalled();
        expect(ToastNotification.error).toHaveBeenCalled();
    });

    test('TG-2.4: test_applyConfiguration_parses_all_fields', () => {
        const config = {
            column_order: '["name", "age"]',
            hidden_columns: '["id"]',
            filters: '[{"column":"name","operator":"contains","value":"test"}]',
            sort_config: '{"column":"name","direction":"asc"}'
        };

        table.applyConfiguration(config);

        expect(table.columnOrder).toEqual(['name', 'age']);
        expect(table.hiddenColumns).toEqual(new Set(['id']));
        expect(table.filters).toEqual([{ "column": "name", "operator": "contains", "value": "test" }]);
        expect(table.currentSort).toEqual({ "column": "name", "direction": "asc" });
        expect(table.render).toHaveBeenCalled();
    });

    test('TG-2.5: test_loadConfiguration_handles_404', async () => {
        table.fetchWithRetry.mockResolvedValue({
            ok: false,
            status: 404
        });

        await table.loadConfiguration();
        await new Promise(resolve => setTimeout(resolve, 0));

        expect(table.savedConfigs).toEqual([]);
    });

    test('TG-2.6: test_loadConfiguration_handles_network_error', async () => {
        table.fetchWithRetry.mockRejectedValue(new Error('Network error'));
        console.error = jest.fn();

        await table.loadConfiguration();
        await new Promise(resolve => setTimeout(resolve, 0));

        expect(table.savedConfigs).toEqual([]);
    });

    test('TG-2.7: test_deleteConfiguration_cancelled_by_user', async () => {
        global.confirm = jest.fn(() => false);

        await table.deleteConfiguration(5);

        expect(global.fetch).not.toHaveBeenCalled();
    });

    test('TG-2.8: test_deleteConfiguration_handles_error', async () => {
        global.confirm = jest.fn(() => true);
        global.fetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve({ success: false })
        });

        await table.deleteConfiguration(5);
        await new Promise(resolve => setTimeout(resolve, 0));

        expect(ToastNotification.error).toHaveBeenCalledWith('Failed to delete view');
    });

    test('TG-2.9: test_setDefaultView_handles_error', async () => {
        global.fetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve({ success: false })
        });

        await table.setDefaultView(10);
        await new Promise(resolve => setTimeout(resolve, 0));

        expect(ToastNotification.error).toHaveBeenCalledWith('Failed to update default view');
    });

    test('TG-2.10: test_saveConfiguration_handles_fetch_error', async () => {
        global.prompt.mockReturnValue('New View');
        table.savedConfigs = [];
        global.fetch.mockRejectedValue(new Error('Network error'));
        console.error = jest.fn();

        await table.saveConfiguration();
        await new Promise(resolve => setTimeout(resolve, 0));

        expect(ToastNotification.error).toHaveBeenCalled();
    });

    // Additional branch coverage tests
    test('TG-3.1: test_applyConfiguration_parses_filters', async () => {
        const config = {
            id: 1,
            column_order: '["id", "name"]',
            hidden_columns: '["age"]',
            filters: '[{"column":"name","operator":"contains","value":"test"}]',
            sort_config: '{"column":"name","direction":"asc"}'
        };
        table.updateTable = jest.fn();
        table.saveTableState = jest.fn();

        table.applyConfiguration(config);

        expect(table.filters).toEqual([{ column: 'name', operator: 'contains', value: 'test' }]);
    });

    test('TG-3.2: test_applyConfiguration_parses_sort_config', async () => {
        const config = {
            id: 1,
            column_order: '["id", "name"]',
            hidden_columns: '[]',
            filters: '[]',
            sort_config: '{"column":"name","direction":"desc"}'
        };
        table.updateTable = jest.fn();
        table.saveTableState = jest.fn();

        table.applyConfiguration(config);

        expect(table.currentSort).toEqual({ column: 'name', direction: 'desc' });
    });

    test('TG-3.3: test_applyConfiguration_is_callable', () => {
        const config = {
            id: 42,
            column_order: '["id"]',
            hidden_columns: '[]',
            filters: '[]',
            sort_config: '{}'
        };
        table.updateTable = jest.fn();
        table.saveTableState = jest.fn();
        table.sidebar = { loadExistingFilters: jest.fn(), populateColumns: jest.fn(), populateSavedViews: jest.fn() };

        expect(() => table.applyConfiguration(config)).not.toThrow();
    });

    test('TG-3.4: test_loadConfiguration_404_response', async () => {
        table.fetchWithRetry = jest.fn().mockResolvedValue({
            ok: false,
            status: 404
        });

        await table.loadConfiguration();
        await new Promise(resolve => setTimeout(resolve, 0));

        expect(table.savedConfigs).toEqual([]);
    });

    test('TG-3.5: test_loadConfiguration_network_error', async () => {
        console.error = jest.fn();
        table.fetchWithRetry = jest.fn().mockRejectedValue(new Error('Network error'));

        await table.loadConfiguration();
        await new Promise(resolve => setTimeout(resolve, 0));

        expect(console.error).toHaveBeenCalled();
    });

    test('TG-3.6: test_deleteConfiguration_network_error', async () => {
        global.confirm = jest.fn(() => true);
        global.fetch.mockRejectedValue(new Error('Network error'));
        console.error = jest.fn();

        await table.deleteConfiguration(5);
        await new Promise(resolve => setTimeout(resolve, 0));

        expect(ToastNotification.error).toHaveBeenCalled();
    });

    test('TG-3.7: test_setDefaultView_network_error', async () => {
        global.fetch.mockRejectedValue(new Error('Network error'));
        console.error = jest.fn();

        await table.setDefaultView(10);
        await new Promise(resolve => setTimeout(resolve, 0));

        expect(ToastNotification.error).toHaveBeenCalled();
    });

    test('TG-3.8: test_loadConfiguration_applies_default', async () => {
        table.fetchWithRetry = jest.fn().mockResolvedValue({
            ok: true,
            json: () => Promise.resolve([
                { id: 1, is_default: true, column_order: '[]', hidden_columns: '[]', filters: '[]', sort_config: '{}' }
            ])
        });
        table.applyConfiguration = jest.fn();

        await table.loadConfiguration();
        await new Promise(resolve => setTimeout(resolve, 0));

        expect(table.applyConfiguration).toHaveBeenCalled();
    });

    test('TG-3.9: test_saveConfiguration_http_error', async () => {
        global.prompt.mockReturnValue('Test View');
        table.savedConfigs = [];
        global.fetch.mockResolvedValue({
            ok: false,
            status: 500
        });

        await table.saveConfiguration();
        await new Promise(resolve => setTimeout(resolve, 0));

        expect(ToastNotification.error).toHaveBeenCalled();
    });

    test('TG-3.10: test_deleteConfiguration_http_error', async () => {
        global.confirm = jest.fn(() => true);
        global.fetch.mockResolvedValue({
            ok: false,
            status: 500
        });

        await table.deleteConfiguration(5);
        await new Promise(resolve => setTimeout(resolve, 0));

        expect(ToastNotification.error).toHaveBeenCalled();
    });
});

