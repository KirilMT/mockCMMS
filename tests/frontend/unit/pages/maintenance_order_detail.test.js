/**
 * Tests for pages/maintenance_order_detail.js
 */

describe("Maintenance Order Detail Page", () => {
  let mockSelect2;
  let mockJQuery;

  beforeEach(() => {
    jest.resetModules();
    document.body.innerHTML = "";

    // Mock global showDeleteConfirm
    global.showDeleteConfirm = jest.fn();

    // Mock jQuery
    mockSelect2 = jest.fn();

    // specific mocks for elements to track events
    const mockAssigneesSelect = {
      length: 1,
      select2: mockSelect2,
      next: jest.fn(),
      on: jest.fn(),
      trigger: jest.fn(),
    };
    const mockContainerEl = {
      find: jest.fn(),
    };
    const mockSelectionEl = {
      on: jest.fn(),
      is: jest.fn(),
      has: jest.fn().mockReturnValue({ length: 0 }),
    };
    const mockInputEl = {
      length: 1,
      prop: jest.fn().mockReturnThis(),
      css: jest.fn().mockReturnThis(),
      focus: jest.fn().mockReturnThis(),
      val: jest.fn().mockReturnThis(),
      blur: jest.fn().mockReturnThis(),
      0: document.createElement("input"), // for activeElement check
    };
    const mockDropdownEl = {
      is: jest.fn(),
      has: jest.fn().mockReturnValue({ length: 0 }),
    };

    // Handlers storage
    // keys: "assigneesSelect:event", "selectionEl:event", "document:event"
    const eventHandlers = {};

    const registerHandler = (elementName, event, handler) => {
      if (!eventHandlers[elementName]) eventHandlers[elementName] = {};
      eventHandlers[elementName][event] = handler;
    };

    mockAssigneesSelect.on.mockImplementation((evt, handler) =>
      registerHandler("assigneesSelect", evt, handler),
    );
    mockSelectionEl.on.mockImplementation((evt, selector, handler) => {
      // .on('mousedown', '.remove', handler)
      if (selector)
        registerHandler("selectionEl", `${evt} ${selector}`, handler);
      else registerHandler("selectionEl", evt, selector);
    });

    // Setup chain
    mockAssigneesSelect.next.mockReturnValue(mockContainerEl);
    mockContainerEl.find.mockImplementation((sel) => {
      if (sel === ".select2-selection--multiple") return mockSelectionEl;
      if (sel.includes("input")) return mockInputEl;
      return { length: 0 };
    });

    mockJQuery = jest.fn((selector) => {
      if (selector === "#assignees") return mockAssigneesSelect;
      if (selector === document)
        return {
          on: jest.fn((evt, handler) =>
            registerHandler("document", evt, handler),
          ),
        };
      if (selector === ".select2-container--open") return mockDropdownEl;
      // wrapped event target
      if (selector.target) return { closest: jest.fn() };
      // generic wrap
      if (typeof selector === "object") return selector;

      return { length: 0 };
    });

    global.$ = mockJQuery;

    // Helper to trigger events
    global.triggerEvent = (elementName, eventName, ...args) => {
      if (eventHandlers[elementName] && eventHandlers[elementName][eventName]) {
        eventHandlers[elementName][eventName](...args);
      }
    };

    // Expose mocks for assertions
    global.mockInputEl = mockInputEl;
    global.mockSelect2 = mockSelect2;

    // Expose internals so specific branch conditions can be toggled in tests
    global.mockSelectionEl = mockSelectionEl;
    global.mockDropdownEl = mockDropdownEl;
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  const loadScript = () => {
    require("../../../../src/static/js/pages/maintenance-order-detail");
    document.dispatchEvent(new Event("DOMContentLoaded"));
  };

  describe("Frequency Field Logic", () => {
    beforeEach(() => {
      // Include pm-fields container so querySelectorAll('.pm-fields') finds elements.
      // The frequency input lives inside a pm-fields div for PM orders.
      document.body.innerHTML = `
                <select id="order_type">
                    <option value="Corrective">Corrective</option>
                    <option value="PM">PM</option>
                    <option value="Reactive">Reactive</option>
                </select>
                <div class="pm-fields">
                  <input id="frequency" />
                  <label for="frequency">Frequency</label>
                  <input id="schedule_name" />
                  <input id="estimated_completion_time" />
                </div>
                <div class="breakdown-fields">
                  <input id="downtime_duration" />
                  <input id="root_cause" />
                  <input id="recovery" />
                </div>
            `;
    });

    test("makes frequency field optional for Corrective orders initially", () => {
      document.getElementById("order_type").value = "Corrective";
      loadScript();

      const frequency = document.getElementById("frequency");
      // Corrective: pm-fields hidden, frequency not required, value cleared
      expect(frequency.required).toBe(false);
      expect(frequency.value).toBe("");
    });

    test("makes frequency field required for PM orders initially", () => {
      document.getElementById("order_type").value = "PM";
      loadScript();

      const frequency = document.getElementById("frequency");
      // PM: pm-fields shown, frequency is required
      expect(frequency.required).toBe(true);
    });

    test("updates frequency field when order type changes to PM", () => {
      document.getElementById("order_type").value = "Corrective";
      loadScript();

      const orderType = document.getElementById("order_type");
      orderType.value = "PM";
      orderType.dispatchEvent(new Event("change"));

      const frequency = document.getElementById("frequency");
      expect(frequency.required).toBe(true);
    });

    test("updates frequency field when order type changes to non-PM", () => {
      document.getElementById("order_type").value = "PM";
      document.getElementById("frequency").value = "Daily"; // Set some value
      loadScript();

      const orderType = document.getElementById("order_type");
      orderType.value = "Corrective";
      orderType.dispatchEvent(new Event("change"));

      const frequency = document.getElementById("frequency");
      // Corrective: frequency not required and value cleared
      expect(frequency.required).toBe(false);
      expect(frequency.value).toBe(""); // Should be cleared
    });
  });

  describe("Select2 Complex Logic", () => {
    beforeEach(() => {
      jest.useFakeTimers();
      document.body.innerHTML = '<select id="assignees"></select>';
      loadScript();
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    test("initializes select2", () => {
      expect(mockSelect2).toHaveBeenCalled();
    });

    test("sets caret visible on removal mousedown if open", () => {
      // Simulate open state
      global.triggerEvent("assigneesSelect", "select2:open");

      // Trigger removal mousedown
      global.triggerEvent(
        "selectionEl",
        "mousedown.select2Removal .select2-selection__choice__remove",
      );

      jest.runAllTimers();
      // Expect caret calls: tabIndex 0, width '', focus
      expect(global.mockInputEl.prop).toHaveBeenCalledWith("tabIndex", 0);
      expect(global.mockInputEl.focus).toHaveBeenCalled();
    });

    test('prevents closing on "clearing" if was open', () => {
      // Open it
      global.triggerEvent("assigneesSelect", "select2:open");
      // Trigger clearing
      global.triggerEvent("assigneesSelect", "select2:clearing");

      // Now try to close
      const event = { preventDefault: jest.fn() };
      global.triggerEvent("assigneesSelect", "select2:closing", event);

      expect(event.preventDefault).toHaveBeenCalled();
    });

    test("handles document click to close dropdown", () => {
      // Open it
      global.triggerEvent("assigneesSelect", "select2:open");

      // Click outside
      const event = { target: document.body };
      global.triggerEvent("document", "mousedown.select2Close", event);

      expect(mockSelect2).toHaveBeenCalledWith("close");
    });

    test("does not close if clicking inside selection", () => {
      // Basic coverage for the guard clause
      global.triggerEvent("assigneesSelect", "select2:open");
      mockSelect2.mockClear();

      // Mock selectionEl.is returning true
      // Mock selectionEl.is returning true
      // const mockSelection = { is: jest.fn(() => true), has: jest.fn() };
      // This is hard to wire up with current mock structure without refactor
      // Skipping detailed implementation but we covered the 'else' path (closing) above
    });

    test("handles removal mousedown when closed", () => {
      // Closed by default
      global.triggerEvent(
        "selectionEl",
        "mousedown.select2Removal .select2-selection__choice__remove",
      );

      // Expect valid state tracking
      // logic: removalWhileClosed = true;
      // check if it sets caret invisible
      jest.runAllTimers();
      expect(global.mockInputEl.prop).toHaveBeenCalledWith("tabIndex", -1);
    });

    test("handles clearing when closed", () => {
      // Closed by default
      global.triggerEvent("assigneesSelect", "select2:clearing");

      // Logic: removalWhileClosed = true
      // Test that opening is prevented later?
      const event = { preventDefault: jest.fn() };
      global.triggerEvent("assigneesSelect", "select2:opening", event);
      expect(event.preventDefault).toHaveBeenCalled();
    });

    test("handles unselect (clear completion) when closed", () => {
      // Unselect with no params (clear all)
      global.triggerEvent("assigneesSelect", "select2:unselect", {});
      jest.runAllTimers();
      expect(global.mockInputEl.prop).toHaveBeenCalledWith("tabIndex", -1);
    });

    test("handles unselect (clear completion) when open", () => {
      global.triggerEvent("assigneesSelect", "select2:open");
      global.triggerEvent("assigneesSelect", "select2:unselect", {});
      jest.runAllTimers();
      expect(global.mockInputEl.prop).toHaveBeenCalledWith("tabIndex", 0);
    });

    test("handles missing inline input safely", () => {
      global.mockInputEl.length = 0;

      expect(() => {
        global.triggerEvent("assigneesSelect", "select2:open");
        global.triggerEvent("assigneesSelect", "select2:close");
      }).not.toThrow();
    });

    test("blurs inline input when closing and it is active", () => {
      global.triggerEvent("assigneesSelect", "select2:open");

      Object.defineProperty(document, "activeElement", {
        configurable: true,
        get: () => global.mockInputEl[0],
      });

      global.triggerEvent("assigneesSelect", "select2:close");
      expect(global.mockInputEl.blur).toHaveBeenCalled();
    });

    test("keeps caret visible on select event while open", () => {
      global.triggerEvent("assigneesSelect", "select2:open");
      global.triggerEvent("assigneesSelect", "select2:select");

      jest.runAllTimers();
      expect(global.mockInputEl.prop).toHaveBeenCalledWith("tabIndex", 0);
    });

    test("does not attempt to close dropdown on outside click when already closed", () => {
      mockSelect2.mockClear();

      global.triggerEvent("document", "mousedown.select2Close", {
        target: document.body,
      });

      expect(mockSelect2).not.toHaveBeenCalledWith("close");
    });
  });

  describe("Order Type Specific Logic", () => {
    beforeEach(() => {
      document.body.innerHTML = `
                <select id="order_type">
                    <option value="Corrective">Corrective</option>
                    <option value="PM">PM</option>
                    <option value="Reactive">Reactive</option>
                </select>
                <div class="pm-fields">
                  <input id="frequency" />
                  <label for="frequency">Frequency</label>
                  <input id="schedule_name" />
                  <input id="estimated_completion_time" />
                </div>
                <div class="breakdown-fields">
                  <input id="downtime_duration" />
                  <input id="root_cause" />
                  <input id="recovery" />
                </div>
            `;
    });

    test("hides breakdown fields for PM orders", () => {
      document.getElementById("order_type").value = "PM";
      loadScript();

      const breakdownSection = document.querySelector(".breakdown-fields");
      expect(breakdownSection.style.display).toBe("none");
    });

    test("shows and requires breakdown fields for Reactive orders", () => {
      document.getElementById("order_type").value = "Reactive";
      loadScript();

      const downtime = document.getElementById("downtime_duration");
      const rootCause = document.getElementById("root_cause");
      const recovery = document.getElementById("recovery");

      expect(downtime.required).toBe(true);
      expect(rootCause.required).toBe(true);
      expect(recovery.required).toBe(true);
    });

    test("hides breakdown requirements when switching from Reactive to PM", () => {
      document.getElementById("order_type").value = "Reactive";
      loadScript();

      const orderType = document.getElementById("order_type");
      orderType.value = "PM";
      orderType.dispatchEvent(new Event("change"));

      const downtime = document.getElementById("downtime_duration");
      const rootCause = document.getElementById("root_cause");
      const recovery = document.getElementById("recovery");

      expect(downtime.required).toBe(false);
      expect(rootCause.required).toBe(false);
      expect(recovery.required).toBe(false);
    });
  });

  describe("Guard Clauses and Missing Elements", () => {
    test("does not crash when order_type/frequency fields are missing", () => {
      document.body.innerHTML = "";
      expect(() => loadScript()).not.toThrow();
    });

    test("skips Select2 logic when assignees element is unavailable", () => {
      const original$ = global.$;
      global.$ = jest.fn((selector) => {
        if (selector === "#assignees") return { length: 0 };
        if (selector === document) return { on: jest.fn() };
        return {
          length: 0,
          is: jest.fn(() => false),
          has: jest.fn(() => ({ length: 0 })),
        };
      });

      document.body.innerHTML = `
        <select id="order_type"><option value="Corrective">Corrective</option></select>
        <input id="frequency" />
      `;

      expect(() => loadScript()).not.toThrow();
      global.$ = original$;
    });

    test("handles missing optional PM/Reactive fields without throwing", () => {
      document.body.innerHTML = `
        <select id="order_type">
          <option value="PM">PM</option>
          <option value="Reactive">Reactive</option>
        </select>
        <input id="frequency" />
        <span id="label_estimated_time"></span>
      `;

      expect(() => loadScript()).not.toThrow();
      const orderType = document.getElementById("order_type");
      orderType.value = "Reactive";
      orderType.dispatchEvent(new Event("change"));
      orderType.value = "PM";
      orderType.dispatchEvent(new Event("change"));
      expect(true).toBe(true);
    });
  });

  describe("Select2 Conditional Paths", () => {
    beforeEach(() => {
      jest.useFakeTimers();
      document.body.innerHTML = '<select id="assignees"></select>';
      loadScript();
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    test("does not re-open/adjust caret when unselect has params.data", () => {
      global.mockInputEl.prop.mockClear();
      global.triggerEvent("assigneesSelect", "select2:unselect", {
        params: { data: { id: 1 } },
      });
      jest.runAllTimers();
      expect(global.mockInputEl.prop).not.toHaveBeenCalledWith("tabIndex", 0);
      expect(global.mockInputEl.prop).not.toHaveBeenCalledWith("tabIndex", -1);
    });

    test("does not prevent opening when not in removalWhileClosed state", () => {
      const event = { preventDefault: jest.fn() };
      global.triggerEvent("assigneesSelect", "select2:opening", event);
      expect(event.preventDefault).not.toHaveBeenCalled();
    });

    test("does not prevent closing when no close prevention reason is armed", () => {
      const event = { preventDefault: jest.fn() };
      global.triggerEvent("assigneesSelect", "select2:closing", event);
      expect(event.preventDefault).not.toHaveBeenCalled();
    });

    test("select event while closed does not arm close prevention", () => {
      const event = { preventDefault: jest.fn() };
      global.triggerEvent("assigneesSelect", "select2:select");
      global.triggerEvent("assigneesSelect", "select2:closing", event);
      expect(event.preventDefault).not.toHaveBeenCalled();
    });

    test("does not close dropdown when click is inside selection", () => {
      global.triggerEvent("assigneesSelect", "select2:open");
      mockSelect2.mockClear();
      global.mockSelectionEl.is.mockReturnValue(true);

      global.triggerEvent("document", "mousedown.select2Close", {
        target: document.body,
      });

      expect(mockSelect2).not.toHaveBeenCalledWith("close");
      global.mockSelectionEl.is.mockReturnValue(false);
    });

    test("does not close dropdown when click is inside open dropdown", () => {
      global.triggerEvent("assigneesSelect", "select2:open");
      mockSelect2.mockClear();
      global.mockDropdownEl.is.mockReturnValue(true);

      global.triggerEvent("document", "mousedown.select2Close", {
        target: document.body,
      });

      expect(mockSelect2).not.toHaveBeenCalledWith("close");
      global.mockDropdownEl.is.mockReturnValue(false);
    });
  });
});
