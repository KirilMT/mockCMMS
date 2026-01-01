/**
 * Tests for base.js global functions and event handling
 */

const {
    showDeleteConfirm,
    showInputModal,
    showConfirmModal,
    initBase,
} = require("../../../src/static/js/base");

// Mock jQuery
global.$ = jest.fn((selector) => ({
    modal: jest.fn(),
    on: jest.fn(),
    select2: jest.fn(),
}));
global.$.fn = { select2: jest.fn() };

describe("Base JS", () => {
    beforeEach(() => {
        // Reset mocks
        jest.clearAllMocks();
        document.body.innerHTML = `
      <div id="deleteConfirmMessage"></div>
      <div id="deleteConfirmModal"></div>
      <div id="inputModalLabel"></div>
      <div id="inputModalValue"></div>
      <div id="inputModal"></div>
      <div id="confirmModalMessage"></div>
      <div id="confirmModal"></div>
      <div id="sidebarToggle"></div>
      <div id="sidebar-wrapper"></div>
      <div id="overlay"></div>
      <button id="confirmDeleteBtn"></button>
      <button id="inputModalConfirmBtn"></button>
      <button id="confirmModalBtn"></button>
    `;
    });

    describe("showDeleteConfirm", () => {
        test("sets message and shows modal", () => {
            const result = showDeleteConfirm(null, "Delete this?", null);

            expect(document.getElementById("deleteConfirmMessage").textContent).toBe("Delete this?");
            expect(global.$).toHaveBeenCalledWith("#deleteConfirmModal");
            expect(result).toBe(false);
        });

        test("uses default message if not provided", () => {
            showDeleteConfirm(null, null, null);
            expect(document.getElementById("deleteConfirmMessage").textContent).toContain("Are you sure");
        });

        test("handles form submission", () => {
            // Need to simulate confirm click which uses closure variables
            // But we can't easily test side effects of closure variables without triggering the listener
            // defined in initBase.

            // Let's set up the listener first
            initBase();

            const mockForm = { submit: jest.fn() };
            showDeleteConfirm(mockForm, "Msg", null);

            const confirmBtn = document.getElementById("confirmDeleteBtn");
            confirmBtn.click();

            expect(mockForm.submit).toHaveBeenCalled();
        });
    });

    describe("showInputModal", () => {
        test("sets message and clears value", () => {
            document.getElementById("inputModalValue").value = "old";
            showInputModal("Enter something", jest.fn());

            expect(document.getElementById("inputModalLabel").textContent).toBe("Enter something");
            expect(document.getElementById("inputModalValue").value).toBe("");
            expect(global.$).toHaveBeenCalledWith("#inputModal");
        });

        test("focuses input after modal shown", () => {
            // Capture the shown.bs.modal callback
            let shownCallback = null;
            global.$ = jest.fn((selector) => ({
                modal: jest.fn(),
                on: jest.fn((event, cb) => {
                    if (event === 'shown.bs.modal') {
                        shownCallback = cb;
                    }
                }),
                focus: jest.fn(),
                select2: jest.fn(),
            }));
            global.$.fn = { select2: jest.fn() };

            showInputModal("Focus test", jest.fn());

            // Trigger the captured callback
            expect(shownCallback).not.toBeNull();
            if (shownCallback) {
                shownCallback();
            }
            
            // Verify focus was called on inputModalValue
            expect(global.$).toHaveBeenCalledWith("#inputModalValue");
        });
    });

    describe("showConfirmModal", () => {
        test("sets message and shows modal", () => {
            showConfirmModal("Confirm?", jest.fn());
            expect(document.getElementById("confirmModalMessage").textContent).toBe("Confirm?");
            expect(global.$).toHaveBeenCalledWith("#confirmModal");
        });
    });

    describe("initBase (Event Listeners)", () => {
        test("initializes Select2", () => {
            initBase();
            expect(global.$).toHaveBeenCalledWith(".select2");
        });

        test("toggles sidebar on click", () => {
            initBase();
            const toggle = document.getElementById("sidebarToggle");
            const sidebar = document.getElementById("sidebar-wrapper");
            const overlay = document.getElementById("overlay");

            toggle.click();
            expect(sidebar.classList.contains("toggled")).toBe(true);
            expect(overlay.style.display).toBe("block");

            toggle.click();
            expect(sidebar.classList.contains("toggled")).toBe(false);
            expect(overlay.style.display).toBe("none");
        });

        test("closes sidebar on overlay click", () => {
            initBase();
            const sidebar = document.getElementById("sidebar-wrapper");
            const overlay = document.getElementById("overlay");
            sidebar.classList.add("toggled");

            overlay.click();
            expect(sidebar.classList.contains("toggled")).toBe(false);
            expect(overlay.style.display).toBe("none");
        });

        test("executes delete callback on confirm", () => {
            initBase();
            const callback = jest.fn();
            showDeleteConfirm(null, "msg", callback);

            const confirmBtn = document.getElementById("confirmDeleteBtn");
            confirmBtn.click();

            expect(callback).toHaveBeenCalled();
            expect(global.$).toHaveBeenCalledWith("#deleteConfirmModal");
        });

        test("executes input callback on confirm", () => {
            initBase();
            const callback = jest.fn();
            showInputModal("msg", callback);

            document.getElementById("inputModalValue").value = "test val";
            const confirmBtn = document.getElementById("inputModalConfirmBtn");
            confirmBtn.click();

            expect(callback).toHaveBeenCalledWith("test val");
            expect(global.$).toHaveBeenCalledWith("#inputModal");
        });

        test("executes input confirm on Enter key", () => {
            initBase();
            const callback = jest.fn();
            showInputModal("msg", callback);

            const input = document.getElementById("inputModalValue");
            const event = new KeyboardEvent("keypress", { key: "Enter" });
            const spy = jest.spyOn(event, "preventDefault");

            const confirmBtn = document.getElementById("inputModalConfirmBtn");
            const clickSpy = jest.spyOn(confirmBtn, 'click');

            input.dispatchEvent(event);

            expect(clickSpy).toHaveBeenCalled();
            expect(spy).toHaveBeenCalled();
        });

        test("executes confirm callback on generic confirm modal", () => {
            initBase();
            const callback = jest.fn();
            showConfirmModal("msg", callback);

            const confirmBtn = document.getElementById("confirmModalBtn");
            confirmBtn.click();

            expect(callback).toHaveBeenCalled();
            expect(global.$).toHaveBeenCalledWith("#confirmModal");
        });
        test("handles missing elements gracefully", () => {
            document.body.innerHTML = "";
            // Should not throw
            expect(() => initBase()).not.toThrow();
        });
    });
});
