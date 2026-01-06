/**
 * Tests for pages/users.js render functions
 */

// Mock global initAdvancedTable to prevent ReferenceError if DOMContentLoaded fires
global.initAdvancedTable = jest.fn();

const userModule = require("../../../../src/static/js/pages/users");

const {
  renderUserId,
  renderUsername,
  renderTeam,
  renderAvailability,
  getUsersColumns,
  initUsersTable,
} = userModule;

describe("Users Page - Render Functions", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Initialization", () => {
    test("initializes table with data", () => {
      document.body.innerHTML =
        '<div id="users-data">[{"id":1, "username":"test"}]</div>';
      initUsersTable();
      expect(global.initAdvancedTable).toHaveBeenCalledWith(
        "usersTable",
        [{ id: 1, username: "test" }],
        expect.any(Array),
        25,
      );
    });

    test("does not initialize if data element missing", () => {
      document.body.innerHTML = "";
      initUsersTable();
      expect(global.initAdvancedTable).not.toHaveBeenCalledWith(
        "usersTable",
        expect.any(Array),
        expect.any(Array),
        expect.any(Number),
      );
    });
  });

  describe("renderUserId", () => {
    test("renders ID as link to user detail page", () => {
      const result = renderUserId(42, { id: 42 });
      expect(result).toBe('<a href="/users/42">42</a>');
    });

    test("handles string ID value", () => {
      const result = renderUserId("100", { id: 100 });
      expect(result).toContain("/users/100");
      expect(result).toContain(">100<");
    });
  });

  describe("renderUsername", () => {
    test("returns username without warning for non-technician", () => {
      const result = renderUsername("john_doe", {
        is_technician: false,
        team_id: null,
      });
      expect(result).toBe("john_doe");
    });

    test("returns username without warning for technician with team", () => {
      const result = renderUsername("jane_doe", {
        is_technician: true,
        team_id: 1,
      });
      expect(result).toBe("jane_doe");
    });

    test("returns username with warning for technician without team", () => {
      const result = renderUsername("bob_tech", {
        is_technician: true,
        team_id: null,
      });
      expect(result).toContain("bob_tech");
      expect(result).toContain("⚠️");
      expect(result).toContain("text-warning-custom");
    });

    test("returns username with warning when team_id is 0 (falsy)", () => {
      const result = renderUsername("tech_user", {
        is_technician: true,
        team_id: 0,
      });
      expect(result).toContain("⚠️");
    });

    test("returns username without warning when is_technician is false and team_id is null", () => {
      const result = renderUsername("regular_user", {
        is_technician: false,
        team_id: null,
      });
      expect(result).toBe("regular_user");
      expect(result).not.toContain("⚠️");
    });
  });

  describe("renderTeam", () => {
    test("returns team name when present", () => {
      const result = renderTeam("Alpha Team");
      expect(result).toBe("Alpha Team");
    });

    test("returns Unassigned span when team is null", () => {
      const result = renderTeam(null);
      expect(result).toContain("Unassigned");
      expect(result).toContain("text-muted");
    });

    test("returns Unassigned span when team is empty string", () => {
      const result = renderTeam("");
      expect(result).toContain("Unassigned");
    });

    test("returns Unassigned span when team is undefined", () => {
      const result = renderTeam(undefined);
      expect(result).toContain("Unassigned");
    });
  });

  describe("renderAvailability", () => {
    test("returns dash for non-technician", () => {
      expect(renderAvailability("Available", { is_technician: false })).toBe(
        "-",
      );
    });

    test("returns success badge for Available status", () => {
      const result = renderAvailability("Available", { is_technician: true });
      expect(result).toContain("badge-success");
      expect(result).toContain("Available");
    });

    test("returns warning badge for On Leave status", () => {
      const result = renderAvailability("On Leave", { is_technician: true });
      expect(result).toContain("badge-warning");
      expect(result).toContain("On Leave");
    });

    test("returns danger badge for Sick status", () => {
      const result = renderAvailability("Sick", { is_technician: true });
      expect(result).toContain("badge-danger");
      expect(result).toContain("Sick");
    });

    test("returns raw value for unknown status", () => {
      const result = renderAvailability("Custom Status", {
        is_technician: true,
      });
      expect(result).toBe("Custom Status");
    });

    test("returns dash when status is null for technician", () => {
      const result = renderAvailability(null, { is_technician: true });
      expect(result).toBe("-");
    });

    test("returns dash when status is empty string for technician", () => {
      const result = renderAvailability("", { is_technician: true });
      expect(result).toBe("-");
    });
  });

  describe("getUsersColumns", () => {
    test("returns correct number of columns", () => {
      const columns = getUsersColumns();
      expect(columns).toHaveLength(8);
    });

    test("includes all required column keys", () => {
      const columns = getUsersColumns();
      const keys = columns.map((col) => col.key);
      expect(keys).toContain("id");
      expect(keys).toContain("username");
      expect(keys).toContain("email");
      expect(keys).toContain("team_name");
      expect(keys).toContain("availability_status");
    });

    test("id column has render function", () => {
      const columns = getUsersColumns();
      const idCol = columns.find((col) => col.key === "id");
      expect(typeof idCol.render).toBe("function");
    });
  });
});
