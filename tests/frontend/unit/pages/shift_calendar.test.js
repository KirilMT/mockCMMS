
const { JSDOM } = require('jsdom');

describe('Shift Calendar Page Scripts', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <script type="application/json" id="shift-data">
                [{"title": "Shift 1", "start": "2023-01-01"}]
            </script>
            <div id="calendar"></div>
        `;

        // Mock FullCalendar
        global.FullCalendar = {
            Calendar: jest.fn().mockImplementation(() => ({
                render: jest.fn()
            }))
        };
        window.FullCalendar = global.FullCalendar;

        jest.resetModules();
    });

    afterEach(() => {
        document.body.innerHTML = '';
        jest.restoreAllMocks();
    });

    test('should initialize FullCalendar', () => {
        require('../../../../src/static/js/pages/shift_calendar.js');
        document.dispatchEvent(new Event('DOMContentLoaded', { bubbles: true, cancelable: true }));

        expect(global.FullCalendar.Calendar).toHaveBeenCalledWith(
            expect.any(HTMLElement),
            expect.objectContaining({
                initialView: 'dayGridMonth',
                events: [{ title: "Shift 1", start: "2023-01-01" }]
            })
        );
    });

    test('should handle missing data gracefully', () => {
        document.getElementById('shift-data').remove();
        require('../../../../src/static/js/pages/shift_calendar.js');
        document.dispatchEvent(new Event('DOMContentLoaded', { bubbles: true, cancelable: true }));

        expect(global.FullCalendar.Calendar).not.toHaveBeenCalled();
    });
});
