
const { JSDOM } = require('jsdom');

describe('Assets Page Scripts', () => {
    beforeEach(() => {
        // 1. Reset DOM (using standard Jest JSDOM environment)
        document.body.innerHTML = `
            <script type="application/json" id="assets-data">
                [{"id": 1, "name": "Asset 1", "asset_code": "A1"}]
            </script>
            <div id="assetsTable"></div>
        `;

        // 2. Mock initAdvancedTable
        global.initAdvancedTable = jest.fn();
        window.initAdvancedTable = global.initAdvancedTable;

        // 3. Reset modules
        jest.resetModules();
    });

    afterEach(() => {
        jest.restoreAllMocks();
        document.body.innerHTML = '';
    });

    test('should initialize assets table on DOMContentLoaded', () => {
        // 4. Require the script
        // Jest's require will execute it in the current context (which has the global document)
        require('../../../../src/static/js/pages/assets.js');

        // 5. Trigger DOMContentLoaded
        const event = new Event('DOMContentLoaded', {
            bubbles: true,
            cancelable: true
        });
        document.dispatchEvent(event);

        // 6. Assertions
        expect(global.initAdvancedTable).toHaveBeenCalled();
        const callArgs = global.initAdvancedTable.mock.calls[0];
        expect(callArgs[0]).toBe('assetsTable');
        expect(callArgs[1]).toEqual([{id: 1, name: "Asset 1", asset_code: "A1"}]);
    });

     test('should handle missing data element', () => {
        const el = document.getElementById('assets-data');
        if (el) el.remove();

        require('../../../../src/static/js/pages/assets.js');

        const event = new Event('DOMContentLoaded', {
            bubbles: true,
            cancelable: true
        });
        document.dispatchEvent(event);

        expect(global.initAdvancedTable).not.toHaveBeenCalled();
    });

    test('should handle JSON parse error', () => {
        const el = document.getElementById('assets-data');
        if (el) el.textContent = 'invalid json';

        const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

        require('../../../../src/static/js/pages/assets.js');

        const event = new Event('DOMContentLoaded', {
            bubbles: true,
            cancelable: true
        });
        document.dispatchEvent(event);

        expect(consoleSpy).toHaveBeenCalledWith(
            expect.stringContaining('Error'),
            expect.any(Error)
        );
    });
});
