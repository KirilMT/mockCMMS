/**
 * Tests for table-retry.js
 * Covers: fetchWithRetry, sleep, isOnline, withNetworkCheck
 */

// Mock dependencies
global.TableSidebar = class {
    constructor(table) { this.table = table; }
    generateHTML() { return '<div class="sidebar"></div>'; }
    attachEventListeners() { }
    populateColumns() { }
    populateSavedViews() { }
    restoreFilterUI() { }
};

global.ToastNotification = {
    warning: jest.fn(),
    error: jest.fn()
};

// Load AdvancedTable and make it global
const AdvancedTable = require('../../../src/static/js/advanced-table/table-core');
global.AdvancedTable = AdvancedTable;

// Load ALL modules
require('../../../src/static/js/advanced-table/table-data');
require('../../../src/static/js/advanced-table/table-render');
require('../../../src/static/js/advanced-table/table-events');
require('../../../src/static/js/advanced-table/table-retry');

describe('AdvancedTable Retry Methods', () => {
    let table;
    let localStorageMock;

    beforeEach(() => {
        document.body.innerHTML = '<div id="test-container"></div>';

        localStorageMock = {
            store: {},
            getItem: jest.fn((key) => localStorageMock.store[key] || null),
            setItem: jest.fn((key, value) => { localStorageMock.store[key] = value; }),
            removeItem: jest.fn(),
            clear: jest.fn()
        };
        Object.defineProperty(window, 'localStorage', { value: localStorageMock, writable: true });

        AdvancedTable.prototype.loadConfiguration = jest.fn();

        table = new AdvancedTable('test-container', {
            columns: [{ key: 'id', label: 'ID' }],
            data: [{ id: 1 }],
            pageName: 'testRetry'
        });

        jest.clearAllMocks();
        global.fetch = jest.fn();
    });

    afterEach(() => {
        document.body.innerHTML = '';
    });

    describe('sleep', () => {
        test('should return a promise', () => {
            const result = table.sleep(10);
            expect(result).toBeInstanceOf(Promise);
        });
    });

    describe('isOnline', () => {
        test('should return true when navigator.onLine is true', () => {
            Object.defineProperty(navigator, 'onLine', { value: true, configurable: true });
            expect(table.isOnline()).toBe(true);
        });

        test('should return false when navigator.onLine is false', () => {
            Object.defineProperty(navigator, 'onLine', { value: false, configurable: true });
            expect(table.isOnline()).toBe(false);
        });
    });

    describe('fetchWithRetry', () => {
        beforeEach(() => {
            table.sleep = jest.fn().mockResolvedValue();
        });

        test('should return response on success', async () => {
            const mockResponse = { ok: true, status: 200 };
            global.fetch.mockResolvedValue(mockResponse);

            const result = await table.fetchWithRetry('/api/data');

            expect(result).toBe(mockResponse);
            expect(global.fetch).toHaveBeenCalledTimes(1);
        });

        test('should not retry on 4xx errors', async () => {
            const mockResponse = { ok: false, status: 404 };
            global.fetch.mockResolvedValue(mockResponse);

            const result = await table.fetchWithRetry('/api/data');

            expect(result).toBe(mockResponse);
            expect(global.fetch).toHaveBeenCalledTimes(1);
        });

        test('should retry on 5xx errors', async () => {
            const failResponse = { ok: false, status: 500 };
            const successResponse = { ok: true, status: 200 };

            global.fetch
                .mockResolvedValueOnce(failResponse)
                .mockResolvedValueOnce(successResponse);

            const result = await table.fetchWithRetry('/api/data', {}, 3, 100);

            expect(result).toBe(successResponse);
            expect(global.fetch).toHaveBeenCalledTimes(2);
        });
    });

    describe('withNetworkCheck', () => {
        test('should execute operation when online', async () => {
            Object.defineProperty(navigator, 'onLine', { value: true, configurable: true });

            const operation = jest.fn().mockResolvedValue('result');
            const result = await table.withNetworkCheck(operation);

            expect(result).toBe('result');
            expect(operation).toHaveBeenCalled();
        });

        test('should throw error when offline', async () => {
            Object.defineProperty(navigator, 'onLine', { value: false, configurable: true });

            const operation = jest.fn();

            await expect(table.withNetworkCheck(operation)).rejects.toThrow('OFFLINE');
            expect(operation).not.toHaveBeenCalled();
        });
        test('TR-1.5: fetchWithRetry handles network errors (TypeError)', async () => {
            const error = new TypeError('Network request failed: fetch');
            const successResponse = { ok: true, status: 200 };

            global.fetch
                .mockRejectedValueOnce(error)
                .mockResolvedValueOnce(successResponse);

            const result = await table.fetchWithRetry('/api/data', {}, 3, 10);

            expect(result).toBe(successResponse);
            expect(global.fetch).toHaveBeenCalledTimes(2);
        });

        test('TR-1.6: fetchWithRetry shows warning on last retry', async () => {
            const error = new TypeError('Network request failed: fetch');

            global.fetch.mockRejectedValue(error);

            try {
                await table.fetchWithRetry('/api/data', {}, 2, 10);
            } catch (e) {
                // Expected failure
            }

            expect(ToastNotification.warning).toHaveBeenCalledWith(expect.stringContaining('Connection issues'));
        });

        test('TR-1.7: fetchWithRetry throws max retries limit', async () => {
            const error = new TypeError('Network request failed: fetch');
            global.fetch.mockRejectedValue(error);

            await expect(table.fetchWithRetry('/api/data', {}, 1, 10))
                .rejects.toThrow('Network request failed'); // Or the last error
        });

        test('TR-1.8: fetchWithRetry throws non-network errors immediately', async () => {
            const error = new Error('Some other error');
            global.fetch.mockRejectedValue(error);

            await expect(table.fetchWithRetry('/api/data'))
                .rejects.toThrow('Some other error');

            expect(global.fetch).toHaveBeenCalledTimes(1);
        });
    });
});
