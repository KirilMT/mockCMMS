/**
 * Unit tests for apps/reports/src/static/js/report-interactions.js
 * Tests pure utility functions: getTeamColor, normalizeReportType, itemToText,
 * getFormData helpers, DOM manipulation utilities.
 */

// Mock jQuery ($ global) to avoid errors during IIFE execution
const jqueryMockFactory = () => ({
  on: jest.fn().mockReturnThis(),
  off: jest.fn().mockReturnThis(),
  trigger: jest.fn().mockReturnThis(),
  modal: jest.fn().mockReturnThis(),
  val: jest.fn().mockReturnThis(),
  hasClass: jest.fn(() => false),
  select2: jest.fn().mockReturnThis(),
  attr: jest.fn(() => ""),
  find: jest.fn(() => ({
    length: 0,
    attr: jest.fn(() => ""),
    find: jest.fn().mockReturnThis(),
    not: jest.fn().mockReturnThis(),
    first: jest.fn(() => ({
      focus: jest.fn(),
      is: jest.fn(() => false),
      select: jest.fn(),
    })),
  })),
  not: jest.fn().mockReturnThis(),
  length: 0,
  closest: jest.fn(() => ({ attr: jest.fn(() => "editModal") })),
  first: jest.fn(() => ({
    focus: jest.fn(),
    is: jest.fn(() => false),
    select: jest.fn(),
  })),
});

global.$ = jest.fn(() => jqueryMockFactory());

let interactions;

describe("report-interactions utilities", () => {
  beforeEach(() => {
    jest.resetModules();
    document.body.innerHTML = "";
    global.fetch = jest.fn(() =>
      Promise.resolve({ json: () => Promise.resolve({ success: true }) }),
    );
    window.fetch = global.fetch;
    global.alert = jest.fn();
    global.ToastNotification = {
      success: jest.fn(),
      error: jest.fn(),
    };
    Object.defineProperty(document, "execCommand", {
      value: jest.fn(() => true),
      configurable: true,
    });

    // Re-require to get fresh module
    interactions = require("../../../src/static/js/report-interactions");
  });

  describe("getTeamColor", () => {
    test("returns blue for Team A", () => {
      expect(interactions.getTeamColor("Team A")).toBe("#3498db");
    });

    test("returns yellow for Team B", () => {
      expect(interactions.getTeamColor("Team B")).toBe("#f1c40f");
    });

    test("returns green for Team C", () => {
      expect(interactions.getTeamColor("Team C")).toBe("#2ecc71");
    });

    test("returns red for Team D", () => {
      expect(interactions.getTeamColor("Team D")).toBe("#e74c3c");
    });

    test("returns default red for null/undefined", () => {
      expect(interactions.getTeamColor(null)).toBe("#e74c3c");
      expect(interactions.getTeamColor(undefined)).toBe("#e74c3c");
      expect(interactions.getTeamColor("")).toBe("#e74c3c");
    });

    test("returns grey for unknown team name", () => {
      expect(interactions.getTeamColor("Team X")).toBe("#95a5a6");
    });

    test("is case insensitive", () => {
      expect(interactions.getTeamColor("TEAM A")).toBe("#3498db");
      expect(interactions.getTeamColor("team b")).toBe("#f1c40f");
    });
  });

  describe("normalizeReportType", () => {
    test("returns weekend_report for weekend_report", () => {
      expect(interactions.normalizeReportType("weekend_report")).toBe(
        "weekend_report",
      );
    });

    test("returns shift_report for shift_report", () => {
      expect(interactions.normalizeReportType("shift_report")).toBe(
        "shift_report",
      );
    });

    test("defaults to shift_report for unknown types", () => {
      expect(interactions.normalizeReportType("unknown")).toBe("shift_report");
      expect(interactions.normalizeReportType(null)).toBe("shift_report");
      expect(interactions.normalizeReportType("")).toBe("shift_report");
    });
  });

  describe("itemToText", () => {
    test("returns trimmed string for string input", () => {
      expect(interactions.itemToText("  hello world  ")).toBe("hello world");
      expect(interactions.itemToText("simple")).toBe("simple");
    });

    test("formats object with asset, title, and description", () => {
      const item = {
        asset: "Pump A",
        title: "Check oil",
        description: "Verify oil level",
      };
      const result = interactions.itemToText(item);
      expect(result).toContain("Pump A");
      expect(result).toContain("Check oil");
      expect(result).toContain("Verify oil level");
    });

    test("uses defaults for missing fields", () => {
      const result = interactions.itemToText({});
      expect(result).toContain("ASSET");
      expect(result).toContain("Instruction");
    });

    test("handles partial object", () => {
      const result = interactions.itemToText({ asset: "Motor B" });
      expect(result).toContain("Motor B");
    });
  });

  describe("getVal and setVal", () => {
    test("getVal returns empty string for missing element", () => {
      expect(interactions.getVal("nonexistent-id")).toBe("");
    });

    test("setVal sets value on existing element", () => {
      document.body.innerHTML = '<input id="test-input" />';
      interactions.setVal("test-input", "hello");
      expect(document.getElementById("test-input").value).toBe("hello");
    });

    test("setVal does nothing for missing element", () => {
      expect(() => interactions.setVal("missing", "value")).not.toThrow();
    });

    test("getVal returns element value", () => {
      document.body.innerHTML = '<input id="my-input" value="world" />';
      expect(interactions.getVal("my-input")).toBe("world");
    });
  });

  describe("hideAllForms and showForm", () => {
    beforeEach(() => {
      document.body.innerHTML = `
        <div class="modal-form-content" id="form-a" style="display: block;"></div>
        <div class="modal-form-content" id="form-b" style="display: block;"></div>
      `;
    });

    test("hideAllForms hides all .modal-form-content elements", () => {
      interactions.hideAllForms();
      expect(document.getElementById("form-a").style.display).toBe("none");
      expect(document.getElementById("form-b").style.display).toBe("none");
    });

    test("showForm makes specific element visible", () => {
      interactions.hideAllForms();
      interactions.showForm("form-a");
      expect(document.getElementById("form-a").style.display).toBe("block");
      expect(document.getElementById("form-b").style.display).toBe("none");
    });

    test("showForm does nothing if element missing", () => {
      expect(() => interactions.showForm("missing-id")).not.toThrow();
    });
  });

  describe("clearAllInputs", () => {
    test("clears all inputs in a modal", () => {
      document.body.innerHTML = `
        <div id="editModal">
          <input id="edit-header-date" value="2026-01-01" />
          <textarea id="edit-desc">Some text</textarea>
          <select id="edit-shift"><option value="Early" selected>Early</option></select>
        </div>
      `;
      interactions.clearAllInputs("editModal");
      expect(document.getElementById("edit-header-date").value).toBe("");
      expect(document.getElementById("edit-desc").value).toBe("");
    });

    test("does nothing if modal missing", () => {
      expect(() => interactions.clearAllInputs("missing-modal")).not.toThrow();
    });

    test("clears metadata total text for editModal", () => {
      document.body.innerHTML = `
        <div id="editModal">
          <input id="edit-metadata-value" value="5" />
          <span id="edit-metadata-total-text">10</span>
        </div>
      `;
      interactions.clearAllInputs("editModal");
      expect(
        document.getElementById("edit-metadata-total-text").textContent,
      ).toBe("");
    });
  });

  describe("toggleActivityFields", () => {
    beforeEach(() => {
      document.body.innerHTML = `
        <input id="add-act-type" value="" />
        <div id="add-act-mo-group" style="display:none;"></div>
        <div id="add-act-title-group" style="display:none;"></div>
        <div id="add-act-status-group" style="display:none;"></div>
      `;
    });

    test("shows MO and status for flux_ticket type", () => {
      document.getElementById("add-act-type").value = "flux_ticket";
      interactions.toggleActivityFields("add");
      expect(document.getElementById("add-act-mo-group").style.display).toBe(
        "block",
      );
      expect(
        document.getElementById("add-act-status-group").style.display,
      ).toBe("block");
      expect(document.getElementById("add-act-title-group").style.display).toBe(
        "none",
      );
    });

    test("shows title and hides MO for engineering_support type", () => {
      document.getElementById("add-act-type").value = "engineering_support";
      interactions.toggleActivityFields("add");
      expect(document.getElementById("add-act-mo-group").style.display).toBe(
        "none",
      );
      expect(document.getElementById("add-act-title-group").style.display).toBe(
        "block",
      );
      expect(
        document.getElementById("add-act-status-group").style.display,
      ).toBe("none");
    });
  });

  describe("getFormData", () => {
    test("returns base context data with section/index/action", () => {
      // No DOM elements set up - returns minimal data for unknown section
      const data = interactions.getFormData("edit");
      expect(data).toHaveProperty("section");
      expect(data).toHaveProperty("index");
      expect(data).toHaveProperty("action");
    });
  });

  describe("buildPlainTextReport", () => {
    test("builds shift report plain text with key sections", () => {
      const reportText = interactions.buildPlainTextReport(
        { generatedBy: "admin" },
        "shift_report",
        "2026-01-21",
        "Early",
        "Team A",
        {
          attendance: "10/20",
          ehs: "0",
          vigel: "8/10",
          mds: "12/15",
          handoverFrom: [{ asset: "Line 1", title: "Pump", description: "OK" }],
          handoverTo: [
            { asset: "Line 2", title: "Valve", description: "Check" },
          ],
          breakdowns: [
            {
              equipment_line: "L1",
              timestamp: "08:00",
              duration: "30",
              description: "Leak",
              root_cause: "Seal",
              resolution_notes: "Replaced",
            },
          ],
          activities: [
            { type: "flux_ticket", mo_id: "123", description: "Fix" },
          ],
          engineeringSupport: [
            { asset: "L3", title: "Support", description: "Help" },
          ],
          pms: [],
          mos: [],
          additionalTickets: [],
        },
      );

      expect(reportText).toContain("Shift Report");
      expect(reportText).toContain("Attendance: 10/20");
      expect(reportText).toContain("Breakdowns:");
      expect(reportText).toContain("Have a good shift");
    });

    test("builds weekend report plain text with PM and MO sections", () => {
      const reportText = interactions.buildPlainTextReport(
        { generatedBy: "admin" },
        "weekend_report",
        "2026-01-24",
        "Night",
        "Team B",
        {
          attendance: "9/20",
          ehs: "1",
          vigel: "7/10",
          mds: "11/15",
          handoverFrom: [],
          handoverTo: [],
          breakdowns: [],
          activities: [],
          engineeringSupport: [],
          pms: [{ asset: "A1", description: "PM Task", status: "Done" }],
          mos: [{ asset: "A2", description: "MO Task", id: "77" }],
          additionalTickets: [{ asset: "A3", description: "Ticket", id: "88" }],
        },
      );

      expect(reportText).toContain("Weekend Shift Report");
      expect(reportText).toContain("PMs:");
      expect(reportText).toContain("MOs/Tickets:");
      expect(reportText).toContain("Additional Tickets:");
    });
  });

  describe("populateEditForm and populateAddForm", () => {
    beforeEach(() => {
      document.body.innerHTML = `
        <div id="edit-header-form" class="modal-form-content"></div>
        <div id="edit-metadata-form" class="modal-form-content"></div>
        <div id="edit-handover-form" class="modal-form-content"></div>
        <div id="edit-breakdown-form" class="modal-form-content"></div>
        <div id="edit-activity-form" class="modal-form-content"></div>
        <div id="edit-simple-task-form" class="modal-form-content"></div>
        <div id="edit-generic-form" class="modal-form-content"></div>

        <div id="add-handover-form" class="modal-form-content"></div>
        <div id="add-breakdown-form" class="modal-form-content"></div>
        <div id="add-activity-form" class="modal-form-content"></div>
        <div id="add-simple-task-form" class="modal-form-content"></div>
        <div id="add-generic-form" class="modal-form-content"></div>

        <input id="edit-header-date" />
        <input id="edit-header-shift" />
        <input id="edit-header-team" />
        <input id="edit-header-color" />

        <input id="edit-metadata-key" />
        <input id="edit-metadata-value" />
        <span id="edit-metadata-total-text"></span>

        <input id="edit-handover-title" />
        <textarea id="edit-handover-desc"></textarea>
        <select id="edit-handover-asset"></select>

        <input id="edit-bd-time" />
        <input id="edit-bd-duration" />
        <input id="edit-bd-fault" />
        <input id="edit-bd-root" />
        <input id="edit-bd-recovery" />
        <select id="edit-bd-asset"></select>

        <select id="edit-act-type"></select>
        <input id="edit-act-mo-id" />
        <input id="edit-act-title" />
        <input id="edit-act-desc" />
        <input id="edit-act-status" />
        <select id="edit-act-asset"></select>

        <input id="edit-task-desc" />
        <input id="edit-task-status" />
        <input id="edit-task-id" />
        <div id="edit-task-id-group"></div>
        <select id="edit-task-asset"></select>

        <textarea id="edit-generic-content"></textarea>

        <select id="add-handover-asset"></select>
        <select id="add-bd-asset"></select>
        <select id="add-act-asset"></select>
        <select id="add-task-asset"></select>

        <input id="add-bd-time" />
        <select id="add-act-type"></select>
        <div id="add-task-id-group"></div>

        <div id="add-act-mo-group"></div>
        <div id="add-act-title-group"></div>
        <div id="add-act-status-group"></div>
      `;
    });

    test("populateEditForm handles header section", () => {
      interactions.populateEditForm("header", {
        date: "2026-01-21",
        shift: "Early",
        team_name: "Team A",
        team_color: "#3498db",
      });
      expect(document.getElementById("edit-header-date").value).toBe(
        "2026-01-21",
      );
      expect(document.getElementById("edit-header-team").value).toBe("Team A");
    });

    test("populateEditForm handles metadata section with total", () => {
      interactions.populateEditForm("metadata", {
        key: "attendance",
        value: "5",
        total: 10,
      });
      expect(document.getElementById("edit-metadata-key").value).toBe(
        "attendance",
      );
      expect(document.getElementById("edit-metadata-value").value).toBe("5");
      expect(
        document.getElementById("edit-metadata-total-text").textContent,
      ).toContain("10");
    });

    test("populateEditForm handles generic fallback", () => {
      interactions.populateEditForm("unknown_section", { foo: "bar" });
      expect(document.getElementById("edit-generic-content").value).toContain(
        "foo",
      );
    });

    test("populateAddForm handles multiple sections", () => {
      interactions.populateAddForm("handover_from");
      interactions.populateAddForm("breakdown");
      interactions.populateAddForm("activities");
      interactions.populateAddForm("mos");
      interactions.populateAddForm("other");
      expect(document.getElementById("add-bd-time").value).not.toBe("");
    });
  });

  describe("getFormData branches", () => {
    beforeEach(() => {
      document.body.innerHTML = `
        <input id="edit-header-date" value="2026-01-21" />
        <input id="edit-header-shift" value="Early" />
        <input id="edit-header-team" value="Team A" />

        <input id="edit-metadata-key" value="attendance" />
        <input id="edit-metadata-value" value="7" />

        <input id="edit-handover-asset" value="L1" />
        <input id="edit-handover-title" value="Title" />
        <input id="edit-handover-desc" value="Desc" />

        <input id="edit-bd-asset" value="L2" />
        <input id="edit-bd-time" value="08:00" />
        <input id="edit-bd-duration" value="20" />
        <input id="edit-bd-fault" value="Fault" />
        <input id="edit-bd-root" value="Root" />
        <input id="edit-bd-recovery" value="Recovery" />

        <input id="edit-act-type" value="flux_ticket" />
        <input id="edit-act-asset" value="L3" />
        <input id="edit-act-mo-id" value="123" />
        <input id="edit-act-title" value="Act" />
        <input id="edit-act-desc" value="Desc" />
        <input id="edit-act-status" value="Open" />

        <input id="edit-task-asset" value="L4" />
        <input id="edit-task-desc" value="Task" />
        <input id="edit-task-status" value="Done" />
        <input id="edit-task-id" value="99" />

        <textarea id="edit-generic-content">{"k":"v"}</textarea>

        <input id="add-handover-asset" value="L5" />
        <input id="add-handover-title" value="T" />
        <input id="add-handover-desc" value="D" />

        <input id="add-bd-asset" value="L6" />
        <input id="add-bd-time" value="09:00" />
        <input id="add-bd-duration" value="30" />
        <input id="add-bd-fault" value="F" />
        <input id="add-bd-root" value="R" />
        <input id="add-bd-recovery" value="Rec" />

        <input id="add-act-type" value="engineering_support" />
        <input id="add-act-asset" value="L7" />
        <input id="add-act-mo-id" value="124" />
        <input id="add-act-title" value="AT" />
        <input id="add-act-desc" value="AD" />
        <input id="add-act-status" value="Closed" />

        <input id="add-task-asset" value="L8" />
        <input id="add-task-desc" value="TD" />
        <input id="add-task-status" value="TS" />
        <input id="add-task-id" value="88" />
      `;
    });

    test("getFormData edit covers header and metadata", () => {
      interactions.setCurrentContext({
        section: "header",
        index: 0,
        action: "edit",
      });
      const headerData = interactions.getFormData("edit");
      expect(headerData.team_color).toBe("#3498db");

      interactions.setCurrentContext({
        section: "metadata",
        index: 1,
        action: "edit",
      });
      const metaData = interactions.getFormData("edit");
      expect(metaData.key).toBe("attendance");
    });

    test("getFormData edit covers handover, breakdown, activity, task, generic", () => {
      interactions.setCurrentContext({
        section: "handover_from_previous",
        action: "edit",
        index: 1,
      });
      expect(interactions.getFormData("edit").section).toBe("handover_from");

      interactions.setCurrentContext({
        section: "breakdown",
        action: "edit",
        index: 1,
      });
      expect(interactions.getFormData("edit").root_cause).toBe("Root");

      interactions.setCurrentContext({
        section: "activities",
        action: "edit",
        index: 1,
      });
      expect(interactions.getFormData("edit").mo_id).toBe("123");

      interactions.setCurrentContext({
        section: "mos",
        action: "edit",
        index: 1,
      });
      expect(interactions.getFormData("edit").id).toBe("99");

      interactions.setCurrentContext({
        section: "other",
        action: "edit",
        index: 1,
      });
      expect(interactions.getFormData("edit").content).toEqual({ k: "v" });
    });

    test("getFormData add covers handover, breakdown, activities, tasks", () => {
      interactions.setCurrentContext({
        section: "handover_from",
        action: "add",
        index: null,
      });
      expect(interactions.getFormData("add").section).toBe("handover_from");

      interactions.setCurrentContext({
        section: "breakdown",
        action: "add",
        index: null,
      });
      expect(interactions.getFormData("add").duration).toBe("30");

      interactions.setCurrentContext({
        section: "activities",
        action: "add",
        index: null,
      });
      expect(interactions.getFormData("add").type).toBe("engineering_support");

      interactions.setCurrentContext({
        section: "additional",
        action: "add",
        index: null,
      });
      expect(interactions.getFormData("add").id).toBe("88");
    });
  });

  describe("copy and update helpers", () => {
    test("fallbackCopy uses execCommand and success toast", () => {
      interactions.fallbackCopy("<b>hello</b>", "hello");
      expect(document.execCommand).toHaveBeenCalledWith("copy");
      expect(global.ToastNotification.success).toHaveBeenCalled();
    });

    test("sendUpdate posts to report endpoint and handles success", async () => {
      window.history.pushState({}, "", "/reports/15");
      document.body.innerHTML = '<meta name="csrf-token" content="abc" />';

      interactions.sendUpdate({ section: "metadata", action: "edit" });
      await Promise.resolve();
      await Promise.resolve();

      expect(global.fetch).toHaveBeenCalled();
      const [url] = global.fetch.mock.calls[0];
      expect(url).toBe("/reports/15/update");
    });

    test("sendUpdate returns early for invalid URL", () => {
      window.history.pushState({}, "", "/reports/not-a-number");
      const spy = jest.spyOn(console, "error").mockImplementation(() => {});
      interactions.sendUpdate({ section: "metadata" });
      expect(global.fetch).not.toHaveBeenCalled();
      spy.mockRestore();
    });
  });
});
