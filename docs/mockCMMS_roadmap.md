# mockCMMS Project Roadmap
_Updated November 29, 2025 - 8:58 PM_

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

## � LIVING DOCUMENT GUIDELINES

**This roadmap is a living document that evolves with the project.**

### Maintenance Rules

1. **Mark Completed Items**
   - When a feature is completed, change `[ ]` to `[x]` in the checkbox
   - Move completed items to the "Recently Completed" section with completion date and summary
   - Add key outcomes and technical details to help future reference

2. **Add New Ideas**
   - New features should be added to the appropriate application section (`planning`, `reports`, `core mockCMMS`, etc.)
   - Follow the existing structure: Goal → Features → Priority → Reference (if applicable)
   - Assign priority level: Critical, High, Medium, or Low
   - Maintain alphabetical or logical ordering within priority groups

3. **Update Progress**
   - Add status updates to in-progress items (e.g., "Status: 60% complete - Phase 2")
   - Update the "ACTIVE WORK" section when starting new sprints
   - Keep the "Last Updated" timestamp current

4. **Preserve History**
   - **Do not delete completed items** - move them to "Recently Completed"
   - Archive old completed items (30+ days) to bottom or separate archive file
   - Keep historical context for future reference and learning

5. **Update Summary Section**
   - Keep "Summary of Key Unimplemented Features" synchronized with the detailed sections
   - Ensure priority groupings remain accurate

### Document Philosophy

- **Strategic Planning Focus:** This roadmap guides long-term development, not day-to-day tasks
- **Modular Architecture:** Features are organized by application/component area
- **Priority-Driven:** Critical and high-priority items should be addressed first
- **Traceable:** Link to GitHub issues, ADRs, or other documentation where applicable

---

## �🔥 ACTIVE WORK

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

### Core `mockCMMS` Application Enhancements
The core application can be improved with the following features to support the satellite apps.

#### Code Quality & Architecture

- **[x] Project Validation & Code Quality Audit** _(Priority: Critical)_
    - **Status:** ✅ Completed (November 29, 2025)
    - **Goal:** Comprehensive code quality audit and security review to ensure professional, production-ready codebase
    - **Outcome:** Audit report generated with prioritized findings.
    - **Reference:** [Audit Report](file:///C:/Users/kiril/.gemini/antigravity/brain/c76ad166-8bb1-40b2-9de6-ef2a962b4a0d/audit_report.md)

- **[x] Implement Code Quality & Security Fixes** _(Priority: Critical)_
    - **Status:** ✅ Completed (November 29, 2025)
    - **Goal:** Address critical and high-priority issues identified in the audit
    - **Outcome:** Secured SECRET_KEY, improved logging, and cleaned up frontend code.
    - **Reference:** [Walkthrough](file:///C:/Users/kiril/.gemini/antigravity/brain/c76ad166-8bb1-40b2-9de6-ef2a962b4a0d/walkthrough.md)
    - **Scope:**
        - Move `SECRET_KEY` to environment variables
        - Replace `print()` with `app.logger`
        - Remove `console.log()` from production JS
        - Fix inline styles and other maintenance issues
    - **Dependencies:** Follows Project Validation Audit

- **[ ] Frontend Architecture Decision** _(Priority: High)_
    - **Goal:** Evaluate and decide on frontend technology stack migration strategy
    - **Current Stack:**
        - Flask environment with Jinja2 templates (`.html`)
        - Vanilla CSS and JavaScript
        - Custom-built Gantt Chart component (previously attempted Frappe library migration but reverted)
    - **Decision Required:**
        - Should project migrate from vanilla HTML/CSS/JS to Angular or React?
        - Explore hybrid options for gradual migration
        - Consider impact on highly customized components (Gantt Chart)
        - Code Quality: [code-quality.yml](https://github.com/KirilMT/Troubleshooting-Wizard/blob/main/.github/workflows/code-quality.yml)
        - Release: [release.yml](https://github.com/KirilMT/Troubleshooting-Wizard/blob/main/.github/workflows/release.yml)
    - **Dependencies:** Blocked by Project Validation (#7)
    - **Reference:** [GitHub Issue #3](https://github.com/KirilMT/mockCMMS/issues/3)

#### Asset & Data Management

- **[ ] Advanced Asset & Spares Management** _(Priority: Medium)_
    - **Goal:** Move beyond basic CRUD to more intelligent management
    - **Features:**
        - **Asset Hierarchy:** Implement full parent-child relationships for assets (e.g., Line > Station > Asset > Sub-asset) and allow metadata (e.g., manuals, diagrams) to be attached
        - **Automated Spares Ordering:** Create a system that automatically flags spare parts for reorder when inventory drops below a certain threshold during task planning

- **[ ] Realistic Data Simulation & Testing Tools** _(Priority: Medium)_
    - **Goal:** Improve the robustness and testability of the entire platform
    - **Features:**
        - Build a service that can generate realistic mock data (PMs, MOs, technician logs) for stress-testing and demonstration purposes
        - Create a UI for simulating user inputs, such as manually triggering a breakdown alarm or reporting a technician as absent, to test the system's dynamic response

#### Testing & Quality Assurance

- **[ ] Core Application Test Suite Enhancement** _(Priority: Medium)_
    - **Objective:** Build a comprehensive, isolated test suite for the main mockCMMS application, separate from the modular app tests
    - **Details:**
        - Create a dedicated test runner and configuration for the main application
        - Develop unit and integration tests for core services (`db_utils`, `shift_utils`, etc.)
        - Write robust tests for all main API endpoints (`/api/v1/...`)
        - Implement tests for user authentication and authorization logic
        - Defer fixing the extensive test failures in the `apps/planning` test suite to focus on core application stability first
        - **Key Deliverable:** A reliable CI pipeline that runs core application tests on every commit, ensuring the main application remains stable and bug-free

- **[ ] UI Regression Automation** _(Priority: Medium)_
    - **Goal:** Ensure critical UI workflows (advanced tables, filters, dropdown persistence, toast handling) are validated automatically
    - **Plan:** Introduce a lightweight Playwright (or Selenium/Cypress) suite that exercises the advanced-table component end-to-end, complementing existing backend pytest coverage

#### Advanced Table Component Enhancements
The Advanced Table component was recently completed with core functionality. The following features were identified but deferred for future development.

- **[ ] Advanced Filtering** _(Priority: Low)_
    - **Goal:** Provide more sophisticated filtering capabilities
    - **Features:**
        - **Date Range Pickers:** Add calendar-based date range selection for date columns
        - **Multi-Select Filters:** Allow filtering by multiple values simultaneously (e.g., select multiple teams or statuses)
        - **Saved Filter Presets:** Create and save commonly-used filter combinations as reusable presets
        - **Filter Templates:** Share filter patterns across users or teams

- **[ ] Pagination** _(Priority: Low)_
    - **Goal:** Enable efficient navigation through large datasets
    - **Features:**
        - **Page Controls:** Next/Previous buttons with page numbers
        - **Page Size Selector:** Allow users to choose rows per page (10, 25, 50, 100)
        - **Jump to Page:** Input field to jump directly to a specific page
        - **Page Info Display:** Show "Page X of Y" and "Showing 1-25 of 1000 rows"
        - **Persist Page Settings:** Remember page size preference in saved views

- **[ ] Bulk Operations** _(Priority: Low)_
    - **Goal:** Enable efficient multi-row operations
    - **Features:**
        - **Multi-Row Selection:** Checkbox selection for multiple rows with select-all functionality
        - **Bulk Edit:** Edit common fields across multiple selected rows simultaneously
        - **Bulk Delete:** Delete multiple rows in a single operation with confirmation
        - **Export Selected Rows Only:** Export only the currently selected rows to CSV/Excel

- **[ ] Collaboration Features** _(Priority: Low)_
    - **Goal:** Enable team collaboration around table views and data
    - **Features:**
        - **Share Views with Team Members:** Send saved views to other users or teams
        - **View Usage Analytics:** Track which views are most popular, who's using them, and how often
        - **Collaborative Filtering:** Real-time filter sharing where team members can see each other's active filters
        - **View Comments/Notes:** Add notes or comments to saved views explaining their purpose

- **[ ] Automation Features** _(Priority: Low)_
    - **Goal:** Automate repetitive tasks and reporting
    - **Features:**
        - **Scheduled Exports:** Configure automatic CSV exports on a schedule (daily, weekly, monthly)
        - **Email Reports:** Automatically email filtered data or reports to stakeholders
        - **Integration with External Tools:** Connect table data to external systems (Slack notifications, webhook triggers)
        - **Data Change Notifications:** Alert users when filtered data changes or meets certain conditions

**Note:** Low priority - Current implementation meets all immediate needs. These enhancements should be considered after core application features are complete.

**Estimated Effort:** 2-4 weeks per feature category (8-16 weeks total for all features)

#### Project Infrastructure & Documentation
Cross-cutting concerns that improve the overall project quality, team collaboration, and maintainability.

- **[ ] Project Team Collaboration & Documentation** _(Priority: High)_
    - **Goal:** Create comprehensive team collaboration documentation and tools
    - **Features:**
        - **GitHub Tutorial:** Document all GitHub features for team collaboration (issues, projects, repository rules, settings)
        - **CONTRIBUTING.md Update:** Adapt from public contributor focus to private organization team focus
            - Add media/video tutorials for visual learning
            - Include note: if mockCMMS components in `src/` become too complex, migrate to individual apps
        - **Setup Automation:** Create batch script for automatic project setup (replace step-by-step instructions in README.md)
        - **Demo Creation:** Build non-technical demo for stakeholders (management, other teams)
        - **README.md Cleanup:** Move development instructions to CONTRIBUTING.md
    - **Reference:** [GitHub Issue #4](https://github.com/KirilMT/mockCMMS/issues/4)

- **[ ] Fix GitHub Issue Templates** _(Priority: Medium)_
    - **Goal:** Resolve issue where GitHub issue templates are not working properly
    - **Tasks:**
        - Investigate why templates in `.github/ISSUE_TEMPLATE/` are not functioning
        - Test and validate all issue templates (bug_report.md, feature_request.md, custom.md)
        - Ensure proper YAML frontmatter and template configuration
    - **Reference:** [GitHub Issue #2](https://github.com/KirilMT/mockCMMS/issues/2)

- **[ ] Update CODEOWNERS File** _(Priority: Low)_
    - **Goal:** Update CODEOWNERS file with new team members and sections
    - **Tasks:**
        - Add new users to CODEOWNERS
        - Define ownership for new sections/modules
        - Ensure proper GitHub team integration
    - **Reference:** [GitHub Issue #5](https://github.com/KirilMT/mockCMMS/issues/5)

- **[ ] Restructure GEMINI.md Documentation** _(Priority: Low)_
    - **Goal:** Improve documentation structure for better clarity
    - **Changes Required:**
        - Move "Detailed Directory Structure" outside of section 3.1 (apps/workforceManager)
        - Create new structure:
            - 3.1 Detailed Directory Structure
            - 3.2 apps/workforceManager
            - 3.3 apps/reports
        - Verify README.md for consistency
    - **Reference:** [GitHub Issue #1](https://github.com/KirilMT/mockCMMS/issues/1)

### `planning` App Enhancements
This application already handles skill-based task assignment. The next logical steps involve deeper integration and more advanced planning management features.

- **[ ] Line Conditions for Planning** _(Priority: High)_
    - **Goal:** Standardize line conditions needed for task planning to ensure proper execution prerequisites
    - **Features:**
        - Define and track line conditions (line full/empty, part in fixture, robot position)
        - Add dedicated column to planning table showing necessary line conditions for each task
        - Make conditions visible to users with operations roles
        - Integrate condition validation into task assignment workflow
    - **Reference:** [GitHub Issue #6](https://github.com/KirilMT/mockCMMS/issues/6)

- **[ ] Advanced Technician Management** _(Priority: Medium)_
    - **Goal:** Track detailed technician status beyond basic skills
    - **Features:**
        - Implement models and UI to manage shifts, availability, and status (e.g., on-call, sick leave, training)
        - Track and visualize individual technician workload over time

- **[ ] Advanced Planning Algorithms** _(Priority: Medium)_
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

---

## Summary of Key Unimplemented Features

**Critical Priority:**
- **Project Validation & Code Quality Audit:** Comprehensive security and quality review

**High Priority:**
- **Line Conditions for Planning:** Standardize prerequisites for task execution
- **Frontend Architecture Decision:** Evaluate migration to modern framework (Angular/React)
- **CI/CD Pipeline:** Automated testing, code quality, and deployment
- **Team Collaboration Documentation:** GitHub workflows and setup automation

**Medium Priority:**
- **Advanced Technician Tracking:** Availability, workload, and dynamic status
- **Automated, Specialized Reports:** Shift, weekend, and technician-submitted reports
- **Hierarchical Assets & Automated Spares:** Deeper, more intelligent asset and inventory management
- **Data Simulation Engine:** For robust testing and development
- **Core Test Suite Enhancement:** Comprehensive testing infrastructure
- **UI Regression Automation:** End-to-end UI testing
- **Fix GitHub Issue Templates:** Resolve template functionality issues

**Low Priority:**
- **Advanced Table Enhancements:** Date pickers, multi-select, bulk operations, collaboration, automation
- **CODEOWNERS Update:** Add new team members
- **GEMINI.md Restructure:** Improve documentation organization
