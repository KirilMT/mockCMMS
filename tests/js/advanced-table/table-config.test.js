
// Mock dependencies
global.TableSidebar = class {
    constructor(table) {
        this.table = table;
    }
    populateSavedViews() {}
    loadExistingFilters() {}
    populateColumns() {}
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
const AdvancedTable = require('../../../src/static/js/advanced-table/table-core.js');
global.AdvancedTable = AdvancedTable;
require('../../../src/static/js/advanced-table/table-config.js');

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
        table.filters = [{col: 'name', val: 'a'}];
        table.currentSort = {col: 'name', dir: 'asc'};

        // Mock fetch success
        global.fetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve({ success: true, id: 123 })
        });

        // Spy on loadConfiguration to verify it's called
        const loadConfigSpy = jest.spyOn(table, 'loadConfiguration').mockImplementation(() => {});

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
        const mockConfigs = [{id: 1, name: 'View 1'}, {id: 2, name: 'View 2'}];
         table.fetchWithRetry.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve(mockConfigs)
        });

        const loadPromise = table.loadConfiguration();
        await new Promise(resolve => setTimeout(resolve, 0));
        await loadPromise;
        expect(table.savedConfigs).toEqual(mockConfigs);
    });

});
