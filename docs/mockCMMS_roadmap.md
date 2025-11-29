# mockCMMS Project Roadmap
_Updated November 29, 2025 - 7:50 PM_

---

## ⚠️ INSTRUCTIONS FOR AI ASSISTANTS

**When working on this project:**

1. **Update "ACTIVE WORK" section** when sprint phases change or complete
2. **Update status** as work progresses (e.g., "Phase 1" → "Phase 2" → "Completed")
3. **Move completed sprints** to "Recently Completed" section (don't delete immediately)
4. **Add new active work** when starting new sprints/features
5. **Update "Last Updated" date** at the top when making changes
6. **Archive old sprints** after 30 days by moving to bottom or separate archive file

**Quick Update Template:**
```markdown
## 🔥 ACTIVE WORK

**Current Sprint:** [Sprint Name] ([X] days, [Y]% complete)
**Status:** [Phase Name] - [Brief status]
**Started:** [Date]
**Target Completion:** [Date]
```

---

## 🔥 ACTIVE WORK

_No active sprints at this time. All recent work has been completed._

**Next Steps:**
- Run comprehensive testing guide for Advanced Table component
- Plan next sprint from Future Features section below

---

## ✅ RECENTLY COMPLETED

### Advanced Table Column Resizing Polish
**Duration:** 1 day (November 29, 2025)  
**Status:** 100% Complete

**Summary:** Polished column resizing functionality to achieve Excel-like behavior with sub-pixel precision and reduced auto-fit padding.

**Key Outcomes:**
- ✅ Implemented Excel-like column resizing (columns to left stay fixed, columns to right shift without changing width)
- ✅ Added sub-pixel precision using `getBoundingClientRect()` to eliminate jitter
- ✅ Reduced auto-fit padding from 24px to 5px for tighter content fit
- ✅ Implemented `requestAnimationFrame` for smooth 60fps resizing
- ✅ Added click suppression to prevent unintended sorting after resize

**Technical Details:**
- Modified `src/static/js/advanced-table/table-resize.js`
- Table width now adjusts dynamically: `New Width = Start Width + (Column Change)`
- All width calculations use float precision to prevent rounding errors
- Verified with browser automation testing

---

### Advanced Table Component Fixes & Enhancements
**Duration:** 7 days (November 22-29, 2025)  
**Status:** 100% Complete

**Summary:** Successfully transformed the basic Advanced Table component into a production-ready, enterprise-grade component with comprehensive features, robust error handling, and polished user experience.

**Key Outcomes:**
- ✅ Fixed all critical bugs (AND/OR filter logic, save/load persistence, global search)
- ✅ Implemented modern sidebar UI with collapsible sections (Filters, Columns, Saved Views)
- ✅ Added robust error handling with loading states and automatic retry mechanisms
- ✅ Created comprehensive testing guide with 200+ test cases
- ✅ All 13 tasks completed across 3 phases (Core Fixes, Sidebar Implementation, Polish & Testing)

**Technical Achievements:**
- Created 3 new utility files (`table-loading.js`, `table-retry.js`, testing guide)
- Modified 15+ JavaScript, CSS, and HTML files
- Implemented exponential backoff retry with offline detection
- Added professional loading spinners for all async operations
- Built mobile-responsive design for all screen sizes

---

## 🚀 FUTURE FEATURES (Strategic Planning)

> **Note:** This section outlines unimplemented, high-value features for future development. These features are adapted to the project's modular architecture and serve as a guide for future sprints. Use this as a guide for *adding new features*, not for re-implementing existing functionality.

---

## Application-Specific Feature Roadmap

### `planning` App Enhancements
This application already handles skill-based task assignment. The next logical steps involve deeper integration and more advanced planning management features.

- **[ ] Advanced Technician Management**
    - **Goal:** Track detailed technician status beyond basic skills
    - **Features:**
        - Implement models and UI to manage shifts, availability, and status (e.g., on-call, sick leave, training)
        - Track and visualize individual technician workload over time

- **[ ] Advanced Planning Algorithms**
    - **Goal:** Evolve beyond simple task assignment to holistic planning
    - **Features:**
        - Develop logic for complex scheduling scenarios like multi-day shutdowns or holidays, factoring in technician availability
        - Create a simulation feature that can optimize schedules before finalizing them

### `reports` App Enhancements
This application is intended for reporting and analytics. The following features would provide significant value.

- **[ ] Automated & Specialized Reporting**
    - **Goal:** Generate key operational reports automatically
    - **Features:**
        - **Weekend Task Report:** A report summarizing all tasks planned and completed over a weekend
        - **Shift Production Report:** A summary of maintenance activities during a specific shift
        - **Technician-Submitted Reports:** A system for technicians to log ad-hoc issues like breakdowns or PLC alarms, which can then be aggregated into reports

- **[ ] Advanced Statistical Analysis**
    - **Goal:** Provide deeper insights into maintenance operations
    - **Features:**
        - Develop statistical dashboards for asset performance (e.g., Mean Time Between Failures)
        - Analyze technician performance and skill gaps
        - Generate reports on spare part consumption trends

### Core `mockCMMS` Application Enhancements
The core application can be improved with the following features to support the satellite apps.

- **[ ] Advanced Asset & Spares Management**
    - **Goal:** Move beyond basic CRUD to more intelligent management
    - **Features:**
        - **Asset Hierarchy:** Implement full parent-child relationships for assets (e.g., Line > Station > Asset > Sub-asset) and allow metadata (e.g., manuals, diagrams) to be attached
        - **Automated Spares Ordering:** Create a system that automatically flags spare parts for reorder when inventory drops below a certain threshold during task planning

- **[ ] Realistic Data Simulation & Testing Tools**
    - **Goal:** Improve the robustness and testability of the entire platform
    - **Features:**
        - Build a service that can generate realistic mock data (PMs, MOs, technician logs) for stress-testing and demonstration purposes
        - Create a UI for simulating user inputs, such as manually triggering a breakdown alarm or reporting a technician as absent, to test the system's dynamic response

- **[ ] Core Application Test Suite Enhancement**
    - **Objective:** Build a comprehensive, isolated test suite for the main mockCMMS application, separate from the modular app tests
    - **Details:**
        - Create a dedicated test runner and configuration for the main application
        - Develop unit and integration tests for core services (`db_utils`, `shift_utils`, etc.)
        - Write robust tests for all main API endpoints (`/api/v1/...`)
        - Implement tests for user authentication and authorization logic
        - Defer fixing the extensive test failures in the `apps/planning` test suite to focus on core application stability first
        - **Key Deliverable:** A reliable CI pipeline that runs core application tests on every commit, ensuring the main application remains stable and bug-free

- **[ ] UI Regression Automation**
    - **Goal:** Ensure critical UI workflows (advanced tables, filters, dropdown persistence, toast handling) are validated automatically
    - **Plan:** Introduce a lightweight Playwright (or Selenium/Cypress) suite that exercises the advanced-table component end-to-end, complementing existing backend pytest coverage

### Advanced Table Component Enhancements
The Advanced Table component was recently completed with core functionality. The following features were identified but deferred for future development.

- **[ ] Advanced Filtering**
    - **Goal:** Provide more sophisticated filtering capabilities
    - **Features:**
        - **Date Range Pickers:** Add calendar-based date range selection for date columns
        - **Multi-Select Filters:** Allow filtering by multiple values simultaneously (e.g., select multiple teams or statuses)
        - **Saved Filter Presets:** Create and save commonly-used filter combinations as reusable presets
        - **Filter Templates:** Share filter patterns across users or teams

- **[ ] Pagination**
    - **Goal:** Enable efficient navigation through large datasets
    - **Features:**
        - **Page Controls:** Next/Previous buttons with page numbers
        - **Page Size Selector:** Allow users to choose rows per page (10, 25, 50, 100)
        - **Jump to Page:** Input field to jump directly to a specific page
        - **Page Info Display:** Show "Page X of Y" and "Showing 1-25 of 1000 rows"
        - **Persist Page Settings:** Remember page size preference in saved views

- **[ ] Bulk Operations**
    - **Goal:** Enable efficient multi-row operations
    - **Features:**
        - **Multi-Row Selection:** Checkbox selection for multiple rows with select-all functionality
        - **Bulk Edit:** Edit common fields across multiple selected rows simultaneously
        - **Bulk Delete:** Delete multiple rows in a single operation with confirmation
        - **Export Selected Rows Only:** Export only the currently selected rows to CSV/Excel

- **[ ] Collaboration Features**
    - **Goal:** Enable team collaboration around table views and data
    - **Features:**
        - **Share Views with Team Members:** Send saved views to other users or teams
        - **View Usage Analytics:** Track which views are most popular, who's using them, and how often
        - **Collaborative Filtering:** Real-time filter sharing where team members can see each other's active filters
        - **View Comments/Notes:** Add notes or comments to saved views explaining their purpose

- **[ ] Automation Features**
    - **Goal:** Automate repetitive tasks and reporting
    - **Features:**
        - **Scheduled Exports:** Configure automatic CSV exports on a schedule (daily, weekly, monthly)
        - **Email Reports:** Automatically email filtered data or reports to stakeholders
        - **Integration with External Tools:** Connect table data to external systems (Slack notifications, webhook triggers)
        - **Data Change Notifications:** Alert users when filtered data changes or meets certain conditions

**Priority:** Low - Current implementation meets all immediate needs. These enhancements should be considered after core application features are complete.

**Estimated Effort:** 2-4 weeks per feature category (8-16 weeks total for all features)

---

## Summary of Key Unimplemented Features

- **Advanced Technician Tracking:** Availability, workload, and dynamic status
- **Automated, Specialized Reports:** Shift, weekend, and technician-submitted reports
- **Hierarchical Assets & Automated Spares:** Deeper, more intelligent asset and inventory management
- **Data Simulation Engine:** For robust testing and development
- **Advanced Table Enhancements:** Date pickers, multi-select, bulk operations, collaboration, automation
