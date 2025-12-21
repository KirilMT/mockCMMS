
const { JSDOM } = require('jsdom');

describe('Users Page Scripts', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <script type="application/json" id="users-data">
                [{"id": 1, "username": "admin"}]
            </script>
            <div id="usersTable"></div>
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
        require('../../../../src/static/js/pages/users.js');
        document.dispatchEvent(new Event('DOMContentLoaded', { bubbles: true, cancelable: true }));

        expect(global.initAdvancedTable).toHaveBeenCalledWith(
            'usersTable',
            [{ id: 1, username: "admin" }],
            expect.any(Array),
            25
        );
    });

    test('should test custom renderers via calling them directly', () => {
        require('../../../../src/static/js/pages/users.js');
        document.dispatchEvent(new Event('DOMContentLoaded', { bubbles: true, cancelable: true }));

        const columns = global.initAdvancedTable.mock.calls[0][2];
        const usernameCol = columns.find(c => c.key === 'username');
        const teamCol = columns.find(c => c.key === 'team_name');
        const availabilityCol = columns.find(c => c.key === 'availability_status');

        // Test Username Renderer
        expect(usernameCol.render('User1', { is_technician: false })).toBe('User1');
        expect(usernameCol.render('Tech1', { is_technician: true, team_id: 1 })).toBe('Tech1');
        expect(usernameCol.render('Tech1', { is_technician: true, team_id: null })).toContain('⚠️');

        // Test Team Renderer
        expect(teamCol.render('Team A', {})).toBe('Team A');
        expect(teamCol.render(null, {})).toContain('Unassigned');
        expect(teamCol.render('', {})).toContain('Unassigned');

        // Test Availability Renderer
        expect(availabilityCol.render('Available', { is_technician: false })).toBe('-');
        expect(availabilityCol.render(null, { is_technician: true })).toBe('-');
        expect(availabilityCol.render('Available', { is_technician: true })).toContain('badge-success');
        expect(availabilityCol.render('On Leave', { is_technician: true })).toContain('badge-warning');
        expect(availabilityCol.render('Sick', { is_technician: true })).toContain('badge-danger');
        expect(availabilityCol.render('Other', { is_technician: true })).toBe('Other');
    });
});
