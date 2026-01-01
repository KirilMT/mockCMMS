
// Setup environment
require('../../../src/static/js/toast-notification.js');

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

    test('TN-1.9: test_default_durations', () => {
        // Test success default duration (5000)
        ToastNotification.success('Success Defaults');
        jest.advanceTimersByTime(4999);
        expect(document.querySelector('.toast-success').closest('.toast')).not.toBeNull();
        jest.advanceTimersByTime(2); // > 5000
        jest.advanceTimersByTime(300); // removal
        expect(document.querySelector('.toast-success')).toBeNull();

        // Test error default duration (7000)
        ToastNotification.error('Error Defaults');
        jest.advanceTimersByTime(6999);
        expect(document.querySelector('.toast-error').closest('.toast')).not.toBeNull();
        jest.advanceTimersByTime(2);
        jest.advanceTimersByTime(300);
        expect(document.querySelector('.toast-error')).toBeNull();

        // Test warning default duration (6000)
        ToastNotification.warning('Warning Defaults');
        jest.advanceTimersByTime(5999);
        expect(document.querySelector('.toast-warning').closest('.toast')).not.toBeNull();
        jest.advanceTimersByTime(2);
        jest.advanceTimersByTime(300);
        expect(document.querySelector('.toast-warning')).toBeNull();
        
        // Test info default duration (5000)
        ToastNotification.info('Info Defaults');
        jest.advanceTimersByTime(4999);
        expect(document.querySelector('.toast-info').closest('.toast')).not.toBeNull();
        jest.advanceTimersByTime(2);
        jest.advanceTimersByTime(300);
        expect(document.querySelector('.toast-info')).toBeNull();
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

    test('TN-1.6: test_no_auto_dismiss_when_duration_is_zero', () => {
        // Duration = 0 should NOT auto-dismiss (covers the else branch)
        ToastNotification.show('No Auto Dismiss', 'info', 0);

        expect(document.querySelector('.toast')).not.toBeNull();

        // Advance time way past normal duration
        jest.advanceTimersByTime(10000);

        // Toast should still be there
        expect(document.querySelector('.toast')).not.toBeNull();
    });

    test('TN-1.7: test_hide_nonexistent_toast_does_nothing', () => {
        // Calling hide with a non-existent ID should not throw
        expect(() => {
            ToastNotification.hide('nonexistent-id');
        }).not.toThrow();
    });

    test('TN-1.8: test_hide_removes_toast_with_animation', () => {
        ToastNotification.show('To Hide', 'success', 0);
        const toast = document.querySelector('.toast');
        const toastId = toast.id;

        ToastNotification.hide(toastId);

        expect(toast.classList.contains('hiding')).toBe(true);
        expect(toast.classList.contains('show')).toBe(false);

        jest.advanceTimersByTime(300);
        expect(document.getElementById(toastId)).toBeNull();
    });
});

