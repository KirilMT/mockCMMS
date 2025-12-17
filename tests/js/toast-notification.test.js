
// Setup environment
require('../../src/static/js/toast-notification.js');

describe('ToastNotification', () => {
    beforeEach(() => {
        document.body.innerHTML = '';
        jest.useFakeTimers();
    });

    afterEach(() => {
        jest.useRealTimers();
    });

    test('TN-1.1: test_show_creates_toast_element', () => {
        ToastNotification.show('Hello World');

        const container = document.getElementById('toastContainer');
        expect(container).not.toBeNull();
        expect(container.children.length).toBe(1);

        const toast = container.querySelector('.toast');
        expect(toast.querySelector('.toast-body').textContent).toBe('Hello World');
    });

    test('TN-1.2: test_show_with_different_types', () => {
        ToastNotification.success('Success Message');
        let toast = document.querySelector('.toast-header.toast-success');
        expect(toast).not.toBeNull();
        expect(toast.querySelector('.toast-title').textContent).toBe('Success');

        ToastNotification.error('Error Message');
        toast = document.querySelector('.toast-header.toast-error');
        expect(toast).not.toBeNull();
        expect(toast.querySelector('.toast-title').textContent).toBe('Error');

        ToastNotification.warning('Warning Message');
        toast = document.querySelector('.toast-header.toast-warning');
        expect(toast).not.toBeNull();

        ToastNotification.info('Info Message');
        toast = document.querySelector('.toast-header.toast-info');
        expect(toast).not.toBeNull();
    });

    test('TN-1.3: test_auto_dismiss_after_timeout', () => {
        ToastNotification.show('Auto Dismiss', 'info', 1000);

        expect(document.querySelector('.toast')).not.toBeNull();

        jest.advanceTimersByTime(1000);

        const toast = document.querySelector('.toast');
        expect(toast.classList.contains('hiding')).toBe(true);

        jest.advanceTimersByTime(300); // Wait for removal
        expect(document.querySelector('.toast')).toBeNull();
    });

    test('TN-1.4: test_manual_dismiss_on_click', () => {
        ToastNotification.show('Manual Dismiss');

        const closeBtn = document.querySelector('.toast-close');
        closeBtn.click();

        const toast = document.querySelector('.toast');
        expect(toast.classList.contains('hiding')).toBe(true);

        jest.advanceTimersByTime(300);
        expect(document.querySelector('.toast')).toBeNull();
    });

    test('TN-1.5: test_multiple_toasts_stack_correctly', () => {
        ToastNotification.show('Message 1');
        ToastNotification.show('Message 2');

        const container = document.getElementById('toastContainer');
        expect(container.children.length).toBe(2);

        // Check order (append means latest at bottom)
        expect(container.children[0].querySelector('.toast-body').textContent).toBe('Message 1');
        expect(container.children[1].querySelector('.toast-body').textContent).toBe('Message 2');
    });
});
