/**
 * Gantt Chart Implementation for Planning Module
 * Using Frappe Gantt library for simplicity and maintainability
 *
 * Features:
 * - Timeline visualization of task assignments
 * - Resource allocation view (technician utilization)
 * - Interactive hover and click
 * - Color-coded by task status and priority
 */

class PlanningGanttChart {
  constructor(containerId, options = {}) {
    this.containerId = containerId;
    this.container = document.getElementById(containerId);
    this.ganttInstance = null;
    this.tasks = [];
    this.viewMode = options.viewMode || "Day";
    this.scheduleId = options.scheduleId;
    this.onTaskClick = options.onTaskClick || null;

    if (!this.container) {
      console.error(`Gantt container #${containerId} not found`);
      return;
    }

    this.init();
  }

  async init() {
    console.log("[Gantt] Initializing Gantt chart...");
    await this.loadData();
    this.render();
  }

  async loadData() {
    try {
      const response = await fetch(
        `/planning/planning/schedules/${this.scheduleId}/gantt-data`,
      );
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      console.log("[Gantt] Loaded data:", data);

      // Transform data to Frappe Gantt format
      this.tasks = this.transformToGanttFormat(data);
    } catch (error) {
      console.error("[Gantt] Error loading data:", error);
      this.container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i>
                    Failed to load Gantt chart data: ${error.message}
                </div>
            `;
    }
  }

  transformToGanttFormat(data) {
    /**
     * Transform planning data to Frappe Gantt format
     * Frappe Gantt task format:
     * {
     *   id: 'Task 1',
     *   name: 'Redesign website',
     *   start: '2025-11-23',
     *   end: '2025-11-24',
     *   progress: 50,
     *   dependencies: 'Task 0, Task 2',
     *   custom_class: 'bar-milestone'
     * }
     */
    if (!data || !data.tasks || data.tasks.length === 0) {
      console.warn("[Gantt] No tasks to display");
      return [];
    }

    // Filter to only include tasks with planned times (Planned status)
    const plannedTasks = data.tasks.filter(
      (task) =>
        task.planned_start_time &&
        task.planned_end_time &&
        task.status === "Planned",
    );

    if (plannedTasks.length === 0) {
      console.warn("[Gantt] No planned tasks found with start/end times");
      return [];
    }

    return plannedTasks.map((task, index) => {
      // Parse start and end times
      const startTime = new Date(task.planned_start_time);
      const endTime = new Date(task.planned_end_time);

      // Format dates for Frappe Gantt (YYYY-MM-DD HH:mm)
      const startStr = this.formatDateTime(startTime);
      const endStr = this.formatDateTime(endTime);

      // Determine custom class based on status and priority
      let customClass = this.getTaskClass(task);

      // Build task name with technician info
      const techNames =
        task.assigned_technician_names &&
        task.assigned_technician_names.length > 0
          ? task.assigned_technician_names.join(", ")
          : "Unassigned";

      return {
        id: `task-${task.planning_task_id || index}`,
        name: `${task.task_description} [${techNames}]`,
        start: startStr,
        end: endStr,
        progress:
          task.status === "Completed"
            ? 100
            : task.status === "In Progress"
              ? 50
              : 0,
        custom_class: customClass,
        // Store original task data for click handling
        _originalData: task,
      };
    });
  }

  formatDateTime(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const hours = String(date.getHours()).padStart(2, "0");
    const minutes = String(date.getMinutes()).padStart(2, "0");
    return `${year}-${month}-${day} ${hours}:${minutes}`;
  }

  getTaskClass(task) {
    /**
     * Return CSS class based on task status and priority
     * Priority: Critical/High = red, Medium = yellow, Low = green
     * Status: Planned = blue, In Progress = purple, Completed = gray
     */
    const priorityClasses = {
      Critical: "bar-critical",
      High: "bar-high",
      Medium: "bar-medium",
      Low: "bar-low",
      Undefined: "bar-undefined",
    };

    const statusClasses = {
      Planned: "bar-planned",
      "In Progress": "bar-in-progress",
      Completed: "bar-completed",
      Unplanned: "bar-unplanned",
    };

    const priorityClass = priorityClasses[task.priority] || "bar-undefined";
    const statusClass = statusClasses[task.status] || "bar-unplanned";

    return `${priorityClass} ${statusClass}`;
  }

  render() {
    // Clear any existing content (including loading spinner)
    this.container.innerHTML = "";

    if (this.tasks.length === 0) {
      this.container.innerHTML = `
                <div class="gantt-empty-state">
                    <i class="fas fa-calendar-times"></i>
                    <h5>No Planned Tasks to Display</h5>
                    <p class="text-muted">
                        This schedule doesn't have any tasks with assigned times yet.<br>
                        Click <strong>"Run Planning"</strong> above to generate task assignments and view the Gantt chart.
                    </p>
                </div>
            `;
      return;
    }

    console.log("[Gantt] Rendering chart with tasks:", this.tasks);

    // Create Gantt instance
    try {
      this.ganttInstance = new Gantt(this.container, this.tasks, {
        view_mode: this.viewMode,
        date_format: "YYYY-MM-DD HH:mm",
        popup_trigger: "click",
        on_click: (task) => {
          console.log("[Gantt] Task clicked:", task);
          if (this.onTaskClick && task._originalData) {
            this.onTaskClick(task._originalData);
          }
        },
        on_date_change: (task, start, end) => {
          console.log("[Gantt] Task dates changed:", task, start, end);
          // TODO: Implement drag-and-drop reschedule (Supervisor/Planner only)
        },
        on_progress_change: (task, progress) => {
          console.log("[Gantt] Task progress changed:", task, progress);
          // TODO: Implement progress update
        },
        custom_popup_html: (task) => {
          const data = task._originalData;
          if (!data) return `<div class="gantt-popup">${task.name}</div>`;

          return `
                        <div class="gantt-popup">
                            <h5>${data.task_description}</h5>
                            <p><strong>Status:</strong> ${
                              data.status || "N/A"
                            }</p>
                            <p><strong>Priority:</strong> ${
                              data.priority || "N/A"
                            }</p>
                            <p><strong>Type:</strong> ${
                              data.task_type || "N/A"
                            }</p>
                            <p><strong>Assigned To:</strong> ${
                              data.assigned_technician_names
                                ? data.assigned_technician_names.join(", ")
                                : "Unassigned"
                            }</p>
                            <p><strong>Duration:</strong> ${
                              data.actual_duration_minutes ||
                              data.estimated_duration_minutes ||
                              "N/A"
                            } min</p>
                            ${
                              data.required_skills &&
                              data.required_skills.length > 0
                                ? `<p><strong>Skills:</strong> ${data.required_skills.join(
                                    ", ",
                                  )}</p>`
                                : ""
                            }
                        </div>
                    `;
        },
      });

      console.log("[Gantt] Chart rendered successfully");
    } catch (error) {
      console.error("[Gantt] Error rendering chart:", error);
      this.container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i>
                    Failed to render Gantt chart: ${error.message}
                </div>
            `;
    }
  }

  changeViewMode(mode) {
    /**
     * Change Gantt view mode
     * Options: Quarter Day, Half Day, Day, Week, Month
     */
    if (this.ganttInstance) {
      this.ganttInstance.change_view_mode(mode);
      this.viewMode = mode;
      console.log("[Gantt] View mode changed to:", mode);
    }
  }

  refresh() {
    /**
     * Refresh Gantt chart with latest data
     */
    console.log("[Gantt] Refreshing chart...");
    this.loadData().then(() => this.render());
  }
}

// Initialize Gantt chart helper function
function initPlanningGantt(containerId, scheduleId, options = {}) {
  console.log("[Gantt] initPlanningGantt called:", containerId, scheduleId);

  // Check if Frappe Gantt library is loaded
  if (typeof Gantt === "undefined") {
    console.error("[Gantt] Frappe Gantt library not loaded!");
    const container = document.getElementById(containerId);
    if (container) {
      container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i>
                    Gantt chart library failed to load. Please refresh the page.
                </div>
            `;
    }
    return null;
  }

  return new PlanningGanttChart(containerId, {
    ...options,
    scheduleId: scheduleId,
  });
}

// Make globally available
window.PlanningGanttChart = PlanningGanttChart;
window.initPlanningGantt = initPlanningGantt;
