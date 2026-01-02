/**
 * Tests for pages/user_detail.js
 */

describe('User Detail Page', () => {
    beforeEach(() => {
        jest.resetModules();
        document.body.innerHTML = '';
        global.showDeleteConfirm = jest.fn();
    });

    const loadScript = () => {
        require('../../../../src/static/js/pages/user-detail');
        document.dispatchEvent(new Event('DOMContentLoaded'));
    };

    test('attaches click handler to delete buttons', () => {
        document.body.innerHTML = `
            <form>
                <button type="button" class="delete-confirm-btn" data-confirm-message="Delete user?">Delete</button>
            </form>
        `;
        loadScript();

        const btn = document.querySelector('.delete-confirm-btn');
        btn.click();

        expect(global.showDeleteConfirm).toHaveBeenCalled();
        const form = document.querySelector('form');
        expect(global.showDeleteConfirm).toHaveBeenCalledWith(form, "Delete user?");
    });
});
