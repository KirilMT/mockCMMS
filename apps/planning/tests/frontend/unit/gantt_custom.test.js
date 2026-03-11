/**
 * @jest-environment jsdom
 */

// Mock data
const mockScheduleData = {
  schedule: {
    id: 1,
    start_date: "2025-11-23",
    end_date: "2025-11-24",
  },
  technicians: [
    { id: 101, name: "Tech A" },
    { id: 102, name: "Tech B" },
  ],
  tasks: [],
};

// Load the script
const {
  PlanningGanttChart,
} = require("../../../src/static/js/planning-gantt-custom.js");

describe("PlanningGanttChart (Custom)", () => {
  let container;
  let chart;

  beforeEach(() => {
    // Mock scrollIntoView
    Element.prototype.scrollIntoView = jest.fn();

    container = document.createElement("div");
    container.id = "gantt-chart";
    document.body.appendChild(container);

    // Mock fetch
    global.fetch = jest.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve(mockScheduleData),
        ok: true,
      }),
    );
    // Reset valid instance
    try {
      chart = new PlanningGanttChart("gantt-chart", 1);
    } catch {
      // Ignore constructor-initiated init error
    }
  });

  afterEach(() => {
    if (container && container.parentNode) {
      document.body.removeChild(container);
    }
    jest.clearAllMocks();
  });

  test("should initialize correctly", () => {
    expect(chart.container).toBe(container);
    expect(chart.scheduleId).toBe(1);
  });

  test("loadData should fetch schedule data", async () => {
    await chart.loadData();
    expect(global.fetch).toHaveBeenCalledWith(
      "/planning/schedules/1/gantt-data",
    );
    expect(chart.scheduleData).toEqual(mockScheduleData.schedule);
  });

  test("getPriorityColor should return correct color based on priority", () => {
    expect(chart.getPriorityColor("Critical")).toBe("#dc3545");
    expect(chart.getPriorityColor("High")).toBe("#fd7e14");
    expect(chart.getPriorityColor("Medium")).toBe("#ffc107");
    expect(chart.getPriorityColor("Low")).toBe("#28a745");
    expect(chart.getPriorityColor("Unknown")).toBe("#6c757d");
  });

  test("buildTimeGrid should calculate correct range", () => {
    chart.scheduleData = {
      start_date: "2025-11-23",
      end_date: "2025-11-24",
    };
    const grid = chart.buildTimeGrid();
    expect(grid.startTime).toBeInstanceOf(Date);
    expect(grid.endTime).toBeInstanceOf(Date);
    expect(grid.timeColumns.length).toBeGreaterThan(0);
  });

  test("render should handle empty state", () => {
    chart.tasks = [];
    chart.render();
    expect(container.innerHTML).toContain("No Planned Tasks to Display");
  });

  test("renderTaskBars should generate SVG or HTML bars", () => {
    const startTime = new Date("2025-11-23T00:00:00");
    const tasks = [
      {
        maintenance_order_id: 123,
        planned_start_time: "2025-11-23T08:00:00",
        planned_end_time: "2025-11-23T10:00:00",
        priority: "High",
        task_description: "Test Task",
      },
    ];
    const html = chart.renderTaskBars(tasks, startTime);
    expect(html).toContain('data-task-id="123"');
    expect(html).toContain("width: 200px"); // 2 hours * 100px/h
  });

  test("addInteractivity should attach event listeners", async () => {
    const testData = {
      schedule: { id: 1, start_date: "2025-11-23", end_date: "2025-11-24" },
      technicians: [{ id: 1, name: "Tech 1" }],
      tasks: [
        {
          maintenance_order_id: 123,
          planned_start_time: "2025-11-23T08:00:00",
          planned_end_time: "2025-11-23T10:00:00",
          status: "Planned",
          assigned_technician_ids: [1],
          task_description: "Test",
        },
      ],
    };
    global.fetch = jest.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve(testData),
        ok: true,
      }),
    );

    await chart.loadData();
    chart.render();

    const taskBar = container.querySelector(".gantt-task-bar");
    expect(taskBar).not.toBeNull();

    const spy = jest
      .spyOn(chart, "highlightTableRow")
      .mockImplementation(() => {});
    taskBar.click();
    expect(spy).toHaveBeenCalledWith("123");
  });

  test("groupTasksByTechnician should handle multiple techs and missing technician names", () => {
    chart.tasks = [
      {
        maintenance_order_id: 1,
        assigned_technician_ids: [101, 102],
        status: "Planned",
      },
    ];
    chart.technicians = [
      { id: 101, name: "Tech A" },
      { id: 102 }, // Missing name
    ];
    const grouped = chart.groupTasksByTechnician();
    expect(grouped[101]).toHaveLength(1);
    expect(grouped[102]).toHaveLength(1);
  });

  test("buildTimeGrid should handle shift_break mode", () => {
    chart.options.planningMode = "shift_break";
    chart.tasks = [
      {
        planned_start_time: "2025-11-23T10:00:00",
        planned_end_time: "2025-11-23T10:30:00",
        status: "Planned",
      },
    ];
    const grid = chart.buildTimeGrid();
    expect(grid.timeColumns.length).toBeGreaterThan(0);
    expect(grid.timeColumns[0].label).toContain("10:00");
  });

  test("buildTimeGrid should handle weekend mode", () => {
    chart.options.planningMode = "weekend";
    chart.scheduleData = { start_date: "2025-11-23" };
    chart.tasks = [];
    const grid = chart.buildTimeGrid();
    expect(grid.timeColumns.length).toBeGreaterThan(0);

    // With tasks
    chart.tasks = [
      {
        planned_start_time: "2025-11-23T09:00:00",
        planned_end_time: "2025-11-23T11:00:00",
      },
    ];
    const grid2 = chart.buildTimeGrid();
    expect(grid2.timeColumns.length).toBeGreaterThan(0);
  });

  test("buildTimeGrid should handle shift_break mode with no tasks", () => {
    chart.options.planningMode = "shift_break";
    chart.scheduleData = { start_date: "2025-11-23" };
    chart.tasks = [];
    const grid = chart.buildTimeGrid();
    // Just verify it returns something valid, avoid hard-coding hour if timezone differ
    expect(grid.startTime).toBeInstanceOf(Date);
    expect(grid.timeColumns.length).toBeGreaterThan(0);
  });

  test("getShiftInfo branches", () => {
    chart.options.planningMode = "weekend";
    chart.scheduleData = { start_date: "2025-11-23" };
    chart.shiftSchedule = [
      {
        date: "2025-11-23",
        early_shift: { team_name: "Team A" },
        late_shift: { team_name: "Team B" },
      },
      {
        date: "2025-11-22",
        early_shift: { team_name: "Team prev early" },
        late_shift: { team_name: "Team prev late" },
      },
    ];
    // Add a task to avoid early return in render
    chart.tasks = [
      {
        maintenance_order_id: 1,
        planned_start_time: "2025-11-23T09:00:00",
        planned_end_time: "2025-11-23T11:00:00",
        status: "Planned",
      },
    ];

    chart.render();
    expect(container.innerHTML).toContain("Team A (Early)");
    // Team B (Late) might not be in the current time grid if the grid ends at 20:00
    // But we just need some shift info labels
  });

  test("highlightTableRow should find and highlight row", () => {
    document.body.innerHTML += `
            <table id="planningTasksTable">
                <tbody>
                    <tr data-maintenance-order-id="123"><td>123</td></tr>
                    <tr data-maintenance-order-id="456"><td>456</td></tr>
                </tbody>
            </table>
        `;
    const row = document.querySelector(
      '#planningTasksTable tbody tr[data-maintenance-order-id="123"]',
    );
    chart.highlightTableRow(123);
    expect(row.style.backgroundColor).toBe("rgb(255, 243, 205)"); // #fff3cd
  });

  test("should handle missing container", () => {
    document.body.innerHTML = "";
    const gantt = new PlanningGanttChart("non-existent", 1);
    expect(gantt.container).toBeNull();
  });

  test("should handle fetch error", async () => {
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: false,
        status: 500,
      }),
    );

    // Mock init to prevent auto-run in constructor for this specific test
    const originalInit = PlanningGanttChart.prototype.init;
    PlanningGanttChart.prototype.init = jest.fn();

    const gantt = new PlanningGanttChart("gantt-chart", 1);
    PlanningGanttChart.prototype.init = originalInit;

    try {
      await gantt.loadData();
    } catch {
      // Error expected
    }
    expect(container.querySelector(".alert-danger")).not.toBeNull();
  });

  test("should handle fetch throwing error", async () => {
    global.fetch = jest.fn(() => Promise.reject(new Error("Network Error")));

    // Mock init to prevent auto-run in constructor
    const originalInit = PlanningGanttChart.prototype.init;
    PlanningGanttChart.prototype.init = jest.fn();

    const gantt = new PlanningGanttChart("gantt-chart", 1);
    PlanningGanttChart.prototype.init = originalInit;

    try {
      await gantt.loadData();
    } catch {
      // Error expected for branch coverage
    }
    expect(container.querySelector(".alert-danger")).not.toBeNull();
  });

  test("should trigger hover effects", () => {
    const testData = {
      schedule: { id: 1, start_date: "2025-11-23", end_date: "2025-11-24" },
      technicians: [{ id: 1, name: "Tech 1" }],
      tasks: [
        {
          maintenance_order_id: 123,
          planned_start_time: "2025-11-23T08:00:00",
          planned_end_time: "2025-11-23T10:00:00",
          status: "Planned",
          assigned_technician_ids: [1],
          task_description: "Test",
        },
      ],
    };
    chart.tasks = testData.tasks;
    chart.technicians = testData.technicians;
    chart.scheduleData = testData.schedule;
    chart.render();
    chart.addInteractivity();

    const row = container.querySelector(".gantt-row");
    row.dispatchEvent(new Event("mouseenter"));
    expect(row.style.background).toBe("rgb(240, 248, 255)"); // #f0f8ff
    row.dispatchEvent(new Event("mouseleave"));
    expect(row.style.background).toBe("");

    const cell = container.querySelector(".gantt-grid-cell");
    cell.setAttribute("data-col-index", "0");
    cell.dispatchEvent(new Event("mouseenter"));
    expect(cell.style.background).toBe("rgb(227, 242, 253)"); // #e3f2fd
    cell.dispatchEvent(new Event("mouseleave"));
    expect(cell.style.background).toBe("rgb(250, 250, 250)"); // #fafafa (since index 0 is even)
  });

  test("highlightTableRow should handle non-existent MO ID", () => {
    const logSpy = jest.spyOn(console, "warn").mockImplementation(() => {});
    document.body.innerHTML +=
      '<table id="planningTasksTable"><tbody><tr><td>123</td></tr></tbody></table>';
    chart.highlightTableRow(999);
    expect(logSpy).toHaveBeenCalledWith(
      "[Gantt] MO ID",
      999,
      "not visible in current table view (may be filtered)",
    );
    logSpy.mockRestore();
  });
});
