/**
 * Tests for pages/spare_part_detail.js
 */

describe('Spare Part Detail Page', () => {
    beforeEach(() => {
        jest.resetModules();
        document.body.innerHTML = '';
        global.showDeleteConfirm = jest.fn();
    });

    const loadScript = () => {
        require('../../../../src/static/js/pages/spare_part_detail');
        document.dispatchEvent(new Event('DOMContentLoaded'));
    };

    test('attaches click handler to delete buttons', () => {
        document.body.innerHTML = `
            <form>
                <button type="button" class="delete-confirm-btn" data-confirm-message="Delete part?">Delete</button>
            </form>
        `;
        loadScript();

        const btn = document.querySelector('.delete-confirm-btn');
        btn.click();

        expect(global.showDeleteConfirm).toHaveBeenCalled();
        const form = document.querySelector('form');
        expect(global.showDeleteConfirm).toHaveBeenCalledWith(form, "Delete part?");
    });
});
