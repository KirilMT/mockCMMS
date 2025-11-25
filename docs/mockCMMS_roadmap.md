# mockCMMS Project Roadmap
_Updated November 25, 2025 - 11:30 AM_

---

## ⚠️ INSTRUCTIONS FOR AI ASSISTANTS

**When working on this project:**

1. **Update "ACTIVE WORK" section** when sprint phases change or complete
2. **Update status** as work progresses (e.g., "Phase 1" → "Phase 2" → "Completed")
3. **Move completed sprints** to a "Recently Completed" section (don't delete immediately)
4. **Keep synchronized** with detailed plan files (e.g., `advanced-table-fixes-plan.md`)
5. **Add new active work** when starting new sprints/features
6. **Update "Last Updated" date** at the top when making changes
7. **Archive old sprints** after 30 days by moving to bottom or separate archive file

**Quick Update Template:**
```markdown
## 🔥 ACTIVE WORK

**Current Sprint:** [Sprint Name] ([X] days, [Y]% complete)
**Status:** [Phase Name] - [Brief status]
**Link:** [Detailed Plan](./link-to-detailed-plan.md)
**Started:** [Date]
**Target Completion:** [Date]
```

---

## 🔥 ACTIVE WORK

**Current Sprint:** Advanced Table Component Fixes & Enhancements (17 days)

See detailed plan here: **[Advanced Table Fixes Plan](./advanced-table-fixes-plan.md)**

**Quick Summary:**
- Fix AND/OR filter logic (currently only AND works)
- Fix Save/Load view configuration (dropdown breaks after filters)
- Fix global search (breaks on typing)
- Add filter persistence (localStorage)
- Add Team column to Users table
- Add filter validation
- Add real-time table updates

**Status:** In Progress - Phase 1 (Critical Fixes)  
**Started:** November 23, 2025  
**Target Completion:** December 10, 2025

---

## ✅ RECENTLY COMPLETED

_No completed sprints yet. When a sprint completes, move it here from "ACTIVE WORK" section._

**Template for completed sprints:**
```markdown
**Sprint:** [Name] ([X] days)
**Completed:** [Date]
**Summary:** [Brief description of what was accomplished]
**Key Outcomes:**
- [Outcome 1]
- [Outcome 2]
```

---

## 🚀 FUTURE FEATURES (Strategic Planning)

> **Note for AI Assistants:** This roadmap was created by analyzing a previous, deprecated project (`planning`). It captures the strategic vision and high-value, unimplemented features from that project, adapted for the modern, modular architecture of `mockCMMS`. Its purpose is to guide future development on the **existing** `mockCMMS` project, not to suggest overwriting or replacing its current functionality. Please use this file as a guide for *adding new features*, not for re-implementing what is already in place.

### Purpose
This section outlines a strategic roadmap for the `mockCMMS` project, focusing on unimplemented, high-value features identified from previous planning documents. It is adapted to the project's current modular architecture and serves as a guide for future development sprints.

---

## Application-Specific Feature Roadmap

### `planning` App Enhancements
This application already handles skill-based task assignment. The next logical steps involve deeper integration and more advanced planning management features.

- **[ ] Advanced Technician Management:**
    - **Goal:** Track detailed technician status beyond basic skills.
    - **Features:**
        - Implement models and UI to manage shifts, availability, and status (e.g., on-call, sick leave, training).
        - Track and visualize individual technician workload over time.

- **[ ] Advanced Planning Algorithms:**
    - **Goal:** Evolve beyond simple task assignment to holistic planning planning.
    - **Features:**
        - Develop logic for complex scheduling scenarios like multi-day shutdowns or holidays, factoring in technician availability.
        - Create a "planning" feature that can simulate and optimize schedules before finalizing them.

### `reports` App Enhancements
This application is intended for reporting and analytics. The following features would provide significant value.

- **[ ] Automated & Specialized Reporting:**
    - **Goal:** Generate key operational reports automatically.
    - **Features:**
        - **Weekend Task Report:** A report summarizing all tasks planned and completed over a weekend.
        - **Shift Production Report:** A summary of maintenance activities during a specific shift.
        - **Technician-Submitted Reports:** A system for technicians to log ad-hoc issues like breakdowns or PLC alarms, which can then be aggregated into reports.

- **[ ] Advanced Statistical Analysis:**
    - **Goal:** Provide deeper insights into maintenance operations.
    - **Features:**
        - Develop statistical dashboards for asset performance (e.g., Mean Time Between Failures).
        - Analyze technician performance and skill gaps.
        - Generate reports on spare part consumption trends.

### Core `mockCMMS` Application Enhancements
The core application can be improved with the following features to support the satellite apps.

- **[ ] Advanced Asset & Spares Management:**
    - **Goal:** Move beyond basic CRUD to more intelligent management.
    - **Features:**
        - **Asset Hierarchy:** Implement full parent-child relationships for assets (e.g., Line > Station > Asset > Sub-asset) and allow metadata (e.g., manuals, diagrams) to be attached.
        - **Automated Spares Ordering:** Create a system that automatically flags spare parts for reorder when inventory drops below a certain threshold during task planning.

- **[ ] Realistic Data Simulation & Testing Tools:**
    - **Goal:** Improve the robustness and testability of the entire platform.
    - **Features:**
        - Build a service that can generate realistic mock data (PMs, MOs, technician logs) for stress-testing and demonstration purposes.
        - Create a UI for simulating user inputs, such as manually triggering a breakdown alarm or reporting a technician as absent, to test the system's dynamic response.

- **[ ] UI Regression Automation:**
    - **Goal:** Ensure critical UI workflows (advanced tables, filters, dropdown persistence, toast handling) are validated automatically.
    - **Plan:** Introduce a lightweight Playwright (or Selenium/Cypress) suite that exercises the advanced-table component end-to-end, complementing existing backend pytest coverage.

---

## Summary of Key Unimplemented Features

- **Advanced Technician Tracking:** Availability, workload, and dynamic status.
- **Automated, Specialized Reports:** Shift, weekend, and technician-submitted reports.
- **Hierarchical Assets & Automated Spares:** Deeper, more intelligent asset and inventory management.
- **Data Simulation Engine:** For robust testing and development.

