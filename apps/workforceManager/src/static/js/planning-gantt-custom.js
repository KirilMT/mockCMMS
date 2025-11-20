/**
 * Planning Gantt Chart - Custom Implementation
 * Based on original technician_dashboard Gantt chart
 * Shows technicians on left, tasks as horizontal bars on timeline
 */

class PlanningGanttChart {
    constructor(containerId, scheduleId, options = {}) {
        console.log('[Gantt] Initializing Planning Gantt Chart...');

        this.scheduleId = scheduleId;
        this.container = document.getElementById(containerId);
        this.options = options;
        this.tasks = [];
        this.technicians = [];
        this.scheduleData = null;

        if (!this.container) {
            console.error(`Gantt container #${containerId} not found`);
            return;
        }

        this.init();
    }

    async init() {
        console.log('[Gantt] Loading data...');
        await this.loadData();
        this.render();
    }

    async loadData() {
        try {
            const response = await fetch(`/workforce-manager/planning/schedules/${this.scheduleId}/gantt-data`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            console.log('[Gantt] Loaded data:', data);

            this.scheduleData = data.schedule;
            this.technicians = data.technicians;

            // Filter only planned tasks with valid times
            this.tasks = data.tasks.filter(task =>
                task.planned_start_time &&
                task.planned_end_time &&
                task.status === 'Planned'
            );

            console.log(`[Gantt] Filtered ${this.tasks.length} planned tasks from ${data.tasks.length} total`);
        } catch (error) {
            console.error('[Gantt] Error loading data:', error);
            this.container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i>
                    Failed to load Gantt data: ${error.message}
                </div>
            `;
            throw error;
        }
    }

    render() {
        // Clear container
        this.container.innerHTML = '';

        if (this.tasks.length === 0) {
            this.renderEmptyState();
            return;
        }

        console.log('[Gantt] Rendering custom Gantt chart...');

        // Build time grid
        const { startTime, endTime, timeColumns } = this.buildTimeGrid();
        this.timeColumns = timeColumns; // Store for column hover functionality

        // Group tasks by technician
        const tasksByTech = this.groupTasksByTechnician();

        // Render Gantt structure
        this.renderGanttStructure(startTime, endTime, timeColumns, tasksByTech);
    }

    renderEmptyState() {
        this.container.innerHTML = `
            <div class="gantt-empty-state">
                <i class="fas fa-calendar-times"></i>
                <h5>No Planned Tasks to Display</h5>
                <p class="text-muted">
                    This schedule doesn't have any tasks with assigned times yet.<br>
                    Click <strong>"Run Planning"</strong> above to generate task assignments.
                </p>
            </div>
        `;
    }

    buildTimeGrid() {
        // Determine time range based on planning mode
        const planningMode = this.options.planningMode || 'weekend';

        // Get configuration from options (can be passed from backend)
        const shiftConfig = this.options.shiftConfig || {};

        let earliestTime, latestTime;

        if (planningMode === 'shift_break') {
            // Shift-break mode: Configurable duration (default 30 minutes from config)
            const shiftDuration = shiftConfig.duration_minutes || 30; // CONFIGURABLE: Change in config.json
            const defaultStart = shiftConfig.default_start_time || "10:00"; // CONFIGURABLE

            // Use task times if available, otherwise default from config
            if (this.tasks.length > 0) {
                earliestTime = new Date(Math.min(...this.tasks.map(t => new Date(t.planned_start_time))));
                latestTime = new Date(earliestTime);
                latestTime.setMinutes(latestTime.getMinutes() + shiftDuration);
            } else {
                // Default from config
                earliestTime = new Date(this.scheduleData.start_date);
                const [hours, minutes] = defaultStart.split(':');
                earliestTime.setHours(parseInt(hours), parseInt(minutes), 0, 0);
                latestTime = new Date(earliestTime);
                latestTime.setMinutes(latestTime.getMinutes() + shiftDuration);
            }

            // Round to nearest 30 minutes
            earliestTime.setMinutes(Math.floor(earliestTime.getMinutes() / 30) * 30, 0, 0);
            latestTime.setMinutes(Math.ceil(latestTime.getMinutes() / 30) * 30, 0, 0);

            // Build 30-minute columns for shift break
            const timeColumns = [];
            let currentTime = new Date(earliestTime);

            while (currentTime <= latestTime) {
                timeColumns.push({
                    time: new Date(currentTime),
                    label: this.formatHour(currentTime)
                });
                currentTime.setMinutes(currentTime.getMinutes() + 30);
            }

            return { startTime: earliestTime, endTime: latestTime, timeColumns };

        } else {
            // Weekend mode: 12-hour window (e.g., 08:00 - 20:00)
            if (this.tasks.length > 0) {
                earliestTime = new Date(Math.min(...this.tasks.map(t => new Date(t.planned_start_time))));
                latestTime = new Date(Math.max(...this.tasks.map(t => new Date(t.planned_end_time))));
            } else {
                // Default to 08:00 - 20:00 for weekend
                earliestTime = new Date(this.scheduleData.start_date);
                earliestTime.setHours(8, 0, 0, 0);
                latestTime = new Date(earliestTime);
                latestTime.setHours(20, 0, 0, 0);
            }

            // Round to nearest hour
            earliestTime.setMinutes(0, 0, 0);
            latestTime.setHours(latestTime.getHours() + 1, 0, 0, 0);

            // Build hourly columns for weekend
            const timeColumns = [];
            let currentTime = new Date(earliestTime);

            while (currentTime < latestTime) {
                timeColumns.push({
                    time: new Date(currentTime),
                    label: this.formatHour(currentTime)
                });
                currentTime.setHours(currentTime.getHours() + 1);
            }

            return { startTime: earliestTime, endTime: latestTime, timeColumns };
        }
    }

    groupTasksByTechnician() {
        const tasksByTech = {};

        this.tasks.forEach(task => {
            // Handle multi-technician assignments
            const techIds = task.assigned_technician_ids || [];
            techIds.forEach(techId => {
                if (!tasksByTech[techId]) {
                    tasksByTech[techId] = [];
                }
                tasksByTech[techId].push(task);
            });
        });

        return tasksByTech;
    }

    renderGanttStructure(startTime, endTime, timeColumns, tasksByTech) {
        const techsWithTasks = this.technicians.filter(tech => tasksByTech[tech.id]);
        const techsToShow = techsWithTasks.length > 0 ? techsWithTasks : this.technicians;

        // Calculate dynamic height: header (55px) + rows (40px each) + padding (20px)
        const ganttHeight = 55 + (techsToShow.length * 40) + 20;

        const html = `
            <div class="custom-gantt-chart" style="height: ${ganttHeight}px;">
                <div class="gantt-fixed-left-pane">
                    <div class="gantt-header-spacer" style="height: 55px; background: #f9f9f9; border-bottom: 1px solid #ccc;">
                        <div style="padding: 10px; font-weight: 600;">Technician</div>
                    </div>
                    <div class="gantt-technician-labels">
                        ${this.renderTechnicianLabels(tasksByTech)}
                    </div>
                </div>
                <div class="gantt-scrollable-right-pane">
                    <div class="gantt-time-header" style="height: 55px; position: sticky; top: 0; z-index: 10; background: #fff;">
                        <div class="gantt-time-axis" style="display: grid; grid-template-columns: repeat(${timeColumns.length}, 100px); border-bottom: 1px solid #ccc;">
                            ${this.renderTimeAxis(timeColumns)}
                        </div>
                    </div>
                    <div class="gantt-rows-container">
                        ${this.renderGanttRows(startTime, endTime, timeColumns, tasksByTech)}
                    </div>
                </div>
            </div>
        `;

        this.container.innerHTML = html;

        // Add event listeners
        this.addInteractivity();
    }

    renderTechnicianLabels(tasksByTech) {
        let html = '';

        // Show only technicians with tasks
        const techsWithTasks = this.technicians.filter(tech => tasksByTech[tech.id]);

        if (techsWithTasks.length === 0) {
            // If no specific assignments, show all available technicians
            this.technicians.forEach(tech => {
                html += `
                    <div class="gantt-tech-label" data-tech-id="${tech.id}" style="height: 40px; padding: 0 10px; display: flex; align-items: center; border-bottom: 1px solid #eee; background: #f9f9f9;">
                        <span style="font-weight: 500;">${tech.name}</span>
                        <span style="margin-left: auto; font-size: 0.85em; color: #666;">No tasks</span>
                    </div>
                `;
            });
        } else {
            techsWithTasks.forEach(tech => {
                const taskCount = tasksByTech[tech.id].length;
                html += `
                    <div class="gantt-tech-label" data-tech-id="${tech.id}" style="height: 40px; padding: 0 10px; display: flex; align-items: center; border-bottom: 1px solid #eee; background: #f9f9f9;">
                        <span style="font-weight: 500;">${tech.name}</span>
                        <span style="margin-left: auto; font-size: 0.85em; color: #666;">${taskCount} task${taskCount > 1 ? 's' : ''}</span>
                    </div>
                `;
            });
        }

        return html;
    }

    renderTimeAxis(timeColumns) {
        return timeColumns.map(col => `
            <div class="gantt-time-tick" style="text-align: center; padding: 18px 0; border-right: 1px solid #eee; font-size: 0.9em; color: #666;">
                ${col.label}
            </div>
        `).join('');
    }

    renderGanttRows(startTime, endTime, timeColumns, tasksByTech) {
        let html = '';
        const techsWithTasks = this.technicians.filter(tech => tasksByTech[tech.id]);
        const techsToShow = techsWithTasks.length > 0 ? techsWithTasks : this.technicians;

        techsToShow.forEach(tech => {
            const techTasks = tasksByTech[tech.id] || [];
            html += `
                <div class="gantt-row" data-tech-id="${tech.id}" style="position: relative; height: 40px; border-bottom: 1px solid #eee;">
                    <div class="gantt-time-grid" style="position: absolute; top: 0; left: 0; right: 0; height: 100%; display: grid; grid-template-columns: repeat(${timeColumns.length}, 100px);">
                        ${this.renderTimeGrid(timeColumns)}
                    </div>
                    <div class="gantt-task-bars" style="position: absolute; top: 0; left: 0; right: 0; height: 100%;">
                        ${this.renderTaskBars(techTasks, startTime, endTime)}
                    </div>
                </div>
            `;
        });

        return html;
    }

    renderTimeGrid(timeColumns) {
        return timeColumns.map((col, index) => `
            <div class="gantt-grid-cell"
                 data-col-index="${index}"
                 style="border-right: 1px solid #f0f0f0; ${index % 2 === 0 ? 'background: #fafafa;' : ''}">
            </div>
        `).join('');
    }

    renderTaskBars(tasks, startTime, endTime) {
        const totalDuration = endTime - startTime;

        return tasks.map(task => {
            const taskStart = new Date(task.planned_start_time);
            const taskEnd = new Date(task.planned_end_time);

            // Calculate position and width as percentages
            const left = ((taskStart - startTime) / totalDuration) * 100;
            const width = ((taskEnd - taskStart) / totalDuration) * 100;

            const priorityColor = this.getPriorityColor(task.priority);
            const taskId = task.maintenance_order_id; // Use actual MO ID

            return `
                <div class="gantt-task-bar"
                     data-task-id="${taskId}"
                     style="
                         position: absolute;
                         left: ${left}%;
                         width: ${width}%;
                         top: 8px;
                         height: 24px;
                         background: ${priorityColor};
                         border-radius: 4px;
                         padding: 0 8px;
                         display: flex;
                         align-items: center;
                         justify-content: center;
                         color: white;
                         font-size: 0.9em;
                         font-weight: 600;
                         box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                         cursor: pointer;
                     "
                     title="MO #${taskId}: ${task.task_description}">
                    ${taskId}
                </div>
            `;
        }).join('');
    }

    getPriorityColor(priority) {
        const colors = {
            'Critical': '#dc3545',
            'High': '#fd7e14',
            'Medium': '#ffc107',
            'Low': '#28a745',
            'Undefined': '#6c757d'
        };
        return colors[priority] || colors['Undefined'];
    }

    formatHour(date) {
        return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
    }

    addInteractivity() {
        // Add hover effects for rows
        const rows = this.container.querySelectorAll('.gantt-row');
        rows.forEach(row => {
            row.addEventListener('mouseenter', () => {
                row.style.background = '#f0f8ff';
            });
            row.addEventListener('mouseleave', () => {
                row.style.background = '';
            });
        });

        // Add column hover highlighting using data-col-index
        const gridCells = this.container.querySelectorAll('.gantt-grid-cell');
        gridCells.forEach(cell => {
            cell.addEventListener('mouseenter', () => {
                const colIndex = cell.getAttribute('data-col-index');
                // Highlight all cells with the same column index
                const allCells = this.container.querySelectorAll(`[data-col-index="${colIndex}"]`);
                allCells.forEach(c => {
                    c.style.background = '#e3f2fd';
                });
            });
            cell.addEventListener('mouseleave', () => {
                const colIndex = cell.getAttribute('data-col-index');
                // Restore original background for all cells in this column
                const allCells = this.container.querySelectorAll(`[data-col-index="${colIndex}"]`);
                allCells.forEach(c => {
                    const idx = parseInt(colIndex);
                    if (idx % 2 === 0) {
                        c.style.background = '#fafafa';
                    } else {
                        c.style.background = '';
                    }
                });
            });
        });

        // Add click handlers for task bars with table navigation
        const taskBars = this.container.querySelectorAll('.gantt-task-bar');
        taskBars.forEach(bar => {
            bar.addEventListener('click', (e) => {
                const taskId = bar.getAttribute('data-task-id');
                const task = this.tasks.find(t => t.maintenance_order_id == taskId);

                console.log('[Gantt] Task clicked:', task);

                if (this.options.onTaskClick) {
                    this.options.onTaskClick(task);
                }

                // Navigate to and highlight corresponding table row by MO ID
                this.highlightTableRow(taskId);
            });
        });
    }

    highlightTableRow(moId) {
        // Find the table and scroll to the row with matching MO ID
        const table = document.getElementById('planningTasksTable');
        if (!table) {
            console.warn('[Gantt] Planning tasks table not found');
            return;
        }

        // Find all table rows
        const rows = table.querySelectorAll('tbody tr');

        // Find the row with matching maintenance order ID in first column
        let targetRow = null;
        rows.forEach(row => {
            const firstCell = row.querySelector('td:first-child');
            if (firstCell) {
                // Extract text content and clean it (remove badge HTML)
                const cellText = firstCell.textContent.trim();
                if (cellText === moId.toString()) {
                    targetRow = row;
                }
            }
        });

        if (targetRow) {
            // Scroll to the row
            targetRow.scrollIntoView({ behavior: 'smooth', block: 'center' });

            // Add highlight animation with dim in/out effect
            targetRow.style.transition = 'background-color 0.3s ease';
            targetRow.style.backgroundColor = '#fff3cd'; // Yellow highlight

            // Dim out after 2 seconds
            setTimeout(() => {
                targetRow.style.backgroundColor = '';
            }, 2000);
        } else {
            // Don't spam console - just silently fail (task might be filtered out)
            console.log('[Gantt] MO ID', moId, 'not visible in current table view (may be filtered)');
        }
    }

    // View mode controls (for compatibility with buttons)
    changeViewMode(mode) {
        console.log('[Gantt] View mode change requested:', mode);
        // For now, these don't change the view since we show hourly by default
        // In the future, you can implement:
        // - "Quarter Day" = 15-min columns
        // - "Half Day" = 30-min columns
        // - "Day" = hourly columns (current)
        alert(`View mode "${mode}" will be implemented in a future update. Currently showing hourly view.`);
    }

    refresh() {
        console.log('[Gantt] Refreshing chart...');
        this.init();
    }
}

// Helper function to initialize Gantt
function initPlanningGantt(containerId, scheduleId, options = {}) {
    return new PlanningGanttChart(containerId, scheduleId, options);
}

// Export for use in templates
if (typeof window !== 'undefined') {
    window.PlanningGanttChart = PlanningGanttChart;
    window.initPlanningGantt = initPlanningGantt;
}

