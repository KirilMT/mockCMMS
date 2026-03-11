/**
 * @jest-environment jsdom
 */

// Mock Frappe Gantt class if it's referenced
window.Gantt = class {
  constructor() {}
  change_view_mode() {}
};

const {
  PlanningGanttChart,
  initPlanningGantt,
} = require("../../../src/static/js/planning-gantt.js");

describe("PlanningGanttChart", () => {
  let ganttChart;
  let container;

  beforeEach(() => {
    container = document.createElement("div");
    container.id = "gantt-chart";
    document.body.appendChild(container);

    global.fetch = jest.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve({ success: true, tasks: [] }),
        ok: true,
      }),
    );
    // Reset valid instance
    ganttChart = new PlanningGanttChart("gantt-chart", { scheduleId: 1 });
  });

  afterEach(() => {
    if (container && container.parentNode) {
      document.body.removeChild(container);
    }
    jest.clearAllMocks();
  });

  test("should initialize correctly", () => {
    expect(ganttChart.containerId).toBe("gantt-chart");
    expect(ganttChart.scheduleId).toBe(1);
  });

  test("loadData should fetch and transform tasks", async () => {
    const mockData = {
      success: true,
      tasks: [
        {
          planning_task_id: 1,
          task_description: "Test Task",
          planned_start_time: "2025-11-23T08:00:00",
          planned_end_time: "2025-11-23T10:00:00",
          status: "Planned",
          priority: "High",
        },
      ],
    };
    global.fetch = jest.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve(mockData),
        ok: true,
      }),
    );

    await ganttChart.loadData();
    expect(ganttChart.tasks.length).toBe(1);
    expect(ganttChart.tasks[0].name).toContain("Test Task");
  });

  test("transformToGanttFormat should handle empty data", () => {
    expect(ganttChart.transformToGanttFormat(null)).toEqual([]);
    expect(ganttChart.transformToGanttFormat({})).toEqual([]);
    expect(ganttChart.transformToGanttFormat({ tasks: [] })).toEqual([]);
  });

  test("getTaskClass should return correct classes", () => {
    const task = { status: "Planned", priority: "Critical" };
    expect(ganttChart.getTaskClass(task)).toContain("bar-critical");

    const unknownTask = { status: "Unknown", priority: "Unknown" };
    const unknownClasses = ganttChart.getTaskClass(unknownTask);
    expect(unknownClasses).toContain("bar-undefined");
    expect(unknownClasses).toContain("bar-unplanned");
  });

  test("transformToGanttFormat should handle no planned tasks", () => {
    const data = {
      tasks: [
        {
          status: "Completed",
          planned_start_time: "2025-01-01",
          planned_end_time: "2025-01-02",
        },
      ],
    };
    expect(ganttChart.transformToGanttFormat(data)).toEqual([]);
  });

  describe("View Modes and Refresh", () => {
    test("changeViewMode should update viewMode", () => {
      ganttChart.ganttInstance = { change_view_mode: jest.fn() };
      ganttChart.changeViewMode("Week");
      expect(ganttChart.viewMode).toBe("Week");
    });

    test("should handle missing container", () => {
      document.body.innerHTML = "";
      const gc = new PlanningGanttChart("non-existent");
      expect(gc.container).toBeNull();
    });

    test("should handle fetch error", async () => {
      global.fetch = jest.fn(() =>
        Promise.resolve({
          ok: false,
          status: 500,
        }),
      );

      await ganttChart.loadData();
      expect(container.querySelector(".alert-danger")).not.toBeNull();
    });

    test("should handle fetch throwing error", async () => {
      global.fetch = jest.fn(() => Promise.reject(new Error("Network Error")));

      await ganttChart.loadData();
      expect(container.querySelector(".alert-danger")).not.toBeNull();
    });

    test("should handle tasks with unassigned technicians", () => {
      const data = {
        success: true,
        tasks: [
          {
            planning_task_id: 101,
            task_description: "Task 1",
            planned_start_time: "2025-11-23T08:00:00",
            planned_end_time: "2025-11-23T10:00:00",
            status: "Planned",
            priority: "High",
            assigned_technician_names: null,
          },
        ],
      };

      const tasks = ganttChart.transformToGanttFormat(data);
      expect(tasks[0].name).toContain("[Unassigned]");
    });

    test("should handle render error", () => {
      const originalGantt = global.Gantt;
      global.Gantt = jest.fn(() => {
        throw new Error("Render Error");
      });

      ganttChart.tasks = [
        { id: "1", name: "Task 1", start: "2025-01-01", end: "2025-01-02" },
      ];
      ganttChart.render();
      expect(container.querySelector(".alert-danger")).not.toBeNull();
      global.Gantt = originalGantt;
    });

    test("should trigger on_date_change, on_progress_change and test custom_popup_html", () => {
      let onDateChange, onProgressChange, onClick, customPopup;
      const originalGantt = global.Gantt;
      const onClickSpy = jest.fn();
      const gc = new PlanningGanttChart("gantt-chart", {
        scheduleId: 1,
        onTaskClick: onClickSpy,
      });

      global.Gantt = jest.fn((cont, tasks, options) => {
        onDateChange = options.on_date_change;
        onProgressChange = options.on_progress_change;
        onClick = options.on_click;
        customPopup = options.custom_popup_html;
        return {};
      });

      gc.tasks = [
        { id: "1", name: "Task 1", start: "2025-01-01", end: "2025-01-02" },
      ];
      gc.render();

      const logSpy = jest.spyOn(console, "warn").mockImplementation();
      onDateChange({ id: 1 }, "start", "end");
      onProgressChange({ id: 1 }, 50);
      onClick({ _originalData: { id: 123 } });

      // Test customPopup branches
      const fullHtml = customPopup({
        _originalData: {
          task_description: "Test",
          status: "Planned",
          priority: "High",
          task_type: "Repair",
          assigned_technician_names: ["A", "B"],
          estimated_duration_minutes: 60,
          required_skills: ["Mech"],
        },
      });
      expect(fullHtml).toContain("Mech");

      const minimalHtml = customPopup({
        _originalData: {
          task_description: "Test",
        },
      });
      expect(minimalHtml).toContain("N/A");
      expect(minimalHtml).toContain("Unassigned");

      expect(logSpy).toHaveBeenCalledTimes(3);
      expect(onClickSpy).toHaveBeenCalledWith({ id: 123 });

      logSpy.mockRestore();
      global.Gantt = originalGantt;
    });

    test("should generate custom popup HTML", () => {
      let customPopupHtml;
      const originalGantt = global.Gantt;
      global.Gantt = jest.fn((cont, tasks, options) => {
        customPopupHtml = options.custom_popup_html;
        return {};
      });

      ganttChart.tasks = [
        { id: "1", name: "Task 1", start: "2025-01-01", end: "2025-01-02" },
      ];
      ganttChart.render();

      const taskData = {
        name: "Task 1",
        _originalData: {
          task_description: "Description",
          status: "Planned",
          priority: "High",
          task_type: "Work",
          assigned_technician_names: ["Tech A"],
          actual_duration_minutes: 60,
          required_skills: ["Skill 1"],
        },
      };

      const html = customPopupHtml(taskData);
      expect(html).toContain("Description");
      expect(html).toContain("Planned");
      expect(html).toContain("High");
      expect(html).toContain("Skill 1");

      const missingData = { name: "Task 2", _originalData: null };
      const html2 = customPopupHtml(missingData);
      expect(html2).toContain("Task 2");
      global.Gantt = originalGantt;
    });

    test("refresh should reload data and re-render", async () => {
      const loadDataSpy = jest
        .spyOn(ganttChart, "loadData")
        .mockResolvedValue();
      const renderSpy = jest.spyOn(ganttChart, "render").mockImplementation();

      await ganttChart.refresh();

      expect(loadDataSpy).toHaveBeenCalled();
      expect(renderSpy).toHaveBeenCalled();
    });
  });

  describe("initPlanningGantt", () => {
    test("should return null if Gantt library is missing", () => {
      const originalGantt = window.Gantt;
      delete window.Gantt;
      const result = initPlanningGantt("gantt-chart", 1);
      expect(result).toBeNull();
      window.Gantt = originalGantt;
    });

    test("should create new PlanningGanttChart if library exists", () => {
      const result = initPlanningGantt("gantt-chart", 1);
      expect(result).toBeInstanceOf(PlanningGanttChart);
    });
  });
});
