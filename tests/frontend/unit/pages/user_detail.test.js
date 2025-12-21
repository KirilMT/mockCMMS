
const { JSDOM } = require('jsdom');

describe('User Detail Page Scripts', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <select id="roles" multiple>
                <option value="Admin">Admin</option>
                <option value="Technician">Technician</option>
            </select>
            <div id="team-group" style="display: none;"></div>
        `;
        jest.resetModules();
    });

    afterEach(() => {
        document.body.innerHTML = '';
        jest.restoreAllMocks();
    });

    test('should show team group when Technician role is selected', () => {
        require('../../../../src/static/js/pages/user_detail.js');

        // Trigger DOMContentLoaded
        const loadEvent = new Event('DOMContentLoaded', { bubbles: true, cancelable: true });
        document.dispatchEvent(loadEvent);

        const rolesSelect = document.getElementById('roles');
        const teamGroup = document.getElementById('team-group');

        // Initial check (none selected)
        expect(teamGroup.style.display).toBe('none');

        // Select Technician
        rolesSelect.options[1].selected = true;
        const changeEvent = new Event('change');
        rolesSelect.dispatchEvent(changeEvent);

        expect(teamGroup.style.display).toBe('block');

        // Deselect Technician
        rolesSelect.options[1].selected = false;
        rolesSelect.dispatchEvent(changeEvent);

        expect(teamGroup.style.display).toBe('none');
    });

    test('should handle missing elements gracefully', () => {
        document.body.innerHTML = ''; // No elements
        require('../../../../src/static/js/pages/user_detail.js');
        const loadEvent = new Event('DOMContentLoaded', { bubbles: true, cancelable: true });
        document.dispatchEvent(loadEvent);
        // Should not throw error
    });
});
