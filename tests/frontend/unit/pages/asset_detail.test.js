/**
 * Tests for pages/asset_detail.js
 */

describe('Asset Detail Page', () => {
    beforeEach(() => {
        jest.resetModules();
        document.body.innerHTML = '';
        global.showDeleteConfirm = jest.fn();
    });

    const loadScript = () => {
        require('../../../../src/static/js/pages/asset-detail');
        document.dispatchEvent(new Event('DOMContentLoaded'));
    };

    test('attaches click handler to delete buttons', () => {
        document.body.innerHTML = `
            <form>
                <button type="button" class="delete-confirm-btn" data-confirm-message="Delete asset?">Delete</button>
            </form>
        `;
        loadScript();

        const btn = document.querySelector('.delete-confirm-btn');
        btn.click();

        expect(global.showDeleteConfirm).toHaveBeenCalled();
        const form = document.querySelector('form');
        expect(global.showDeleteConfirm).toHaveBeenCalledWith(form, "Delete asset?");
    });
});
