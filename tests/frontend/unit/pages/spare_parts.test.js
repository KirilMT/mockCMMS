
const { JSDOM } = require('jsdom');

describe('Spare Parts Page Scripts', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <script type="application/json" id="spare-parts-data">
                [{"id": 1, "description": "Part 1"}]
            </script>
            <div id="sparePartsTable"></div>
        `;

        global.initAdvancedTable = jest.fn();
        window.initAdvancedTable = global.initAdvancedTable;
        jest.resetModules();
    });

    afterEach(() => {
        document.body.innerHTML = '';
        jest.restoreAllMocks();
    });

    test('should initialize table', () => {
        require('../../../../src/static/js/pages/spare_parts.js');
        document.dispatchEvent(new Event('DOMContentLoaded', { bubbles: true, cancelable: true }));

        expect(global.initAdvancedTable).toHaveBeenCalledWith(
            'sparePartsTable',
            [{ id: 1, description: "Part 1" }],
            expect.any(Array),
            25
        );
    });
});
