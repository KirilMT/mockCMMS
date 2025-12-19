
// Setup environment
require('../../../src/static/js/toast-notification.js');

// Mock console.error
console.error = jest.fn();

describe('FlashMessages', () => {
    let processFlashMessages;

    beforeEach(() => {
        document.body.innerHTML = '';
        ToastNotification.show = jest.fn();

        // We need to load or reload the module to trigger execution or access the function.
        // But flash-messages.js executes immediately or on DOMContentLoaded.
        // And it defines processFlashMessages locally (not exported).

        // Since it is not exported, we can't call it directly unless we modify the file or use eval/require trick.
        // However, the file executes immediately. So `require` will execute it.
        // But functions are local.
        // If I modify `flash-messages.js` to assign to window, I can test it.

        jest.resetModules();
    });

    test('FM-1.1: test_converts_flask_flash_to_toast', () => {
        const messages = [['success', 'Operation successful!']];
        document.body.innerHTML = `<div id="flash-messages" data-messages='${JSON.stringify(messages)}'></div>`;

        require('../../../src/static/js/flash-messages.js');

        // Since we are requiring, it might run immediately if readyState != loading.
        // In JSDOM, readyState is usually 'complete' initially or requires config.

        expect(ToastNotification.show).toHaveBeenCalledWith('Operation successful!', 'success');
    });

    test('FM-1.2: test_handles_multiple_flash_messages', () => {
        const messages = [
            ['success', 'Success 1'],
            ['info', 'Info 2']
        ];
        document.body.innerHTML = `<div id="flash-messages" data-messages='${JSON.stringify(messages)}'></div>`;

        require('../../../src/static/js/flash-messages.js');

        expect(ToastNotification.show).toHaveBeenCalledTimes(2);
        expect(ToastNotification.show).toHaveBeenCalledWith('Success 1', 'success');
        expect(ToastNotification.show).toHaveBeenCalledWith('Info 2', 'info');
    });

    test('FM-1.3: test_maps_flask_categories_correctly', () => {
        const messages = [
            ['danger', 'Danger maps to error']
        ];
        document.body.innerHTML = `<div id="flash-messages" data-messages='${JSON.stringify(messages)}'></div>`;

        require('../../../src/static/js/flash-messages.js');

        expect(ToastNotification.show).toHaveBeenCalledWith('Danger maps to error', 'error');
    });

    test('FM-1.4: handles JSON parse error gracefully', () => {
        // Invalid JSON to trigger catch block (line 58)
        document.body.innerHTML = `<div id="flash-messages" data-messages='invalid json here'></div>`;

        require('../../../src/static/js/flash-messages.js');

        expect(console.error).toHaveBeenCalled();
    });

    test('FM-1.5: handles empty flash container', () => {
        // No data-messages attribute
        document.body.innerHTML = `<div id="flash-messages"></div>`;

        require('../../../src/static/js/flash-messages.js');

        expect(ToastNotification.show).not.toHaveBeenCalled();
    });

    test('FM-1.6: handles missing flash container', () => {
        document.body.innerHTML = '';

        require('../../../src/static/js/flash-messages.js');

        expect(ToastNotification.show).not.toHaveBeenCalled();
    });

    test('FM-1.7: handles invalid message format (not array)', () => {
        // Messages that are not arrays
        const messages = [{ bad: 'format' }, 'just a string'];
        document.body.innerHTML = `<div id="flash-messages" data-messages='${JSON.stringify(messages)}'></div>`;

        require('../../../src/static/js/flash-messages.js');

        expect(ToastNotification.show).not.toHaveBeenCalled();
    });

    test('FM-1.8: handles array with only one element', () => {
        // Array with only one element (msg.length < 2)
        const messages = [['onlyCategory']];
        document.body.innerHTML = `<div id="flash-messages" data-messages='${JSON.stringify(messages)}'></div>`;

        require('../../../src/static/js/flash-messages.js');

        expect(ToastNotification.show).not.toHaveBeenCalled();
    });
});
