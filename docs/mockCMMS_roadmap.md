# mockCMMS Project Roadmap

_Updated March 17, 2026_ (Targeted CI Validation & Pre-Commit Refinement)

---

> [!TIP] > **Document Relationship:** This roadmap tracks new features and strategic improvements. For bugs in existing functionality, see `bug_tracking.md`.

---

## ⚠️ INSTRUCTIONS FOR AI ASSISTANTS

**When working on this project:**

1. **Update "ACTIVE WORK" section** when sprint phases change or complete
2. **Update status** as work progresses (e.g., "Phase 1" → "Phase 2" → "Completed")
3. **Move completed sprints** to "Recently Completed" section (don't delete immediately)
4. **Add new active work** when starting new sprints/features
5. **Update "Last Updated" date** at the top when making changes
6. **Archive old sprints** after 30 days by moving to the bottom or a separate archive file

**Quick Update Template:**

```markdown
## 🔥 ACTIVE WORK

**Current Sprint:** [Sprint Name]
**Status:** [Phase Name] - [Brief status]
**Started:** [Date]
**Target Completion:** [Date]
```

---

## LIVING DOCUMENT GUIDELINES

**This roadmap is a living document that evolves with the project.**

### Maintenance Rules

1. **Mark Completed Items**
   - When a feature is completed, change `[ ]` to `[x]` in the checkbox
   - Move completed items to the "Recently Completed" section with a completion date and summary
   - Add key outcomes and technical details to help future reference

2. **Add New Ideas**
   - New features should be new features should be added to the appropriate application section (`planning`, `reporting`, `core mockCMMS`, etc.) mockCMMS`, etc.)
   - Follow the existing structure: Goal → Features → Priority → Reference (if applicable)
   - Assign a priority level: Critical, High, Medium, or Low
   - Maintain alphabetical or logical ordering within priority groups

3. **Update Progress**
   - Add status updates to in-progress items (e.g., "Status: 60% complete - Phase 2")
   - Update the "ACTIVE WORK" section when starting new sprints
   - Keep the "Last Updated" timestamp current

4. **Preserve History**
   - **Do not delete completed items** - move them to "Recently Completed"
   - Archive old completed items (30+ days) to the bottom or a separate archive file
   - Keep historical context for future reference and learning

5. **Update Summary Section**
   - Keep the "Summary of Key Unimplemented Features" synchronized with the detailed sections
   - Ensure priority groupings remain accurate

### Document Philosophy

- **Strategic Planning Focus:** This roadmap guides long-term development, not day-to-day tasks
- **Modular Architecture:** Features are organized by application/component area
- **Priority-Driven:** Critical and high-priority items should be addressed first
- **Traceable:** Link to GitHub issues, ADRs, or other documentation where applicable

---

## 🔥 ACTIVE WORK

**Current Sprint:** Code Quality Audit Complete ✅
**Status:** ✅ All 9 Phases Complete
**Started:** December 13, 2025
**Completed:** January 5, 2026

> [!NOTE]
> The Code Quality Audit (Phases 1-9) is **COMPLETE**.
> All test files and frontend tests have been audited.

---

> [!IMPORTANT] > **📋 Active Plan:** [Core Code Quality Plan](deprecated/core_code_quality_plan.md) - All 9 Phases Complete ✅
> **🧪 Frontend Tests:** 437 Jest + 82 Playwright tests ✅ (80%+ branch coverage)
> **📊 Backend Tests:** 261 pytest tests ✅ (88%+ coverage)

---

## 📋 PLANNED WORK

- **[ ] Troubleshooting App Creation (New Modular App)** _(Priority: High)_
  - **Goal:** Build a new fully modular `Troubleshooting` app inspired by the `Troubleshooting-Wizard` concept and integrate it into the mockCMMS monorepo without coupling it to core app internals.
  - **Concept Scope (from Troubleshooting-Wizard):**
    - Technology-based troubleshooting entry point (select system/technology first)
    - Error code lookup workflows (PDF/manual references + structured database lookup)
    - Configuration-driven resource mapping (manuals, guides, and troubleshooting paths)
  - **Monorepo Standards (non-negotiable):**
    - App lives in `apps/troubleshooting/` with isolated `src/`, `tests/`, `docs/`, and `config/`
    - App enablement via environment flag (planned: `TROUBLESHOOTING_ENABLED=True|False`)
    - Conditional registration in core app factory (no unconditional module-level imports from `apps/*` in `src/`)
    - Dedicated roadmap/bug tracking in app docs (no task duplication in core roadmap)
  - **Planning Docs:**
    - [Troubleshooting App Roadmap](./Troubleshooting app/troubleshooting_roadmap.md)
    - [Troubleshooting App Concept & Modular Architecture](./Troubleshooting app/troubleshooting_concept_and_modular_architecture.md)
  - **Status:** Discovery + architecture definition

- **[ ] Monitoring App Creation (New Modular App)** _(Priority: High)_
  - **Goal:** Build a real-time **Production Re-Start Status Monitoring** application that provides visual oversight of plant floor readiness after Break Activities periods or weekend maintenance tasks.
  - **Core Features:**
    - **Plant Layout Visualization:** Spatial representation of production floor matching physical arrangement
    - **Real-Time Status Tracking:** Live status indicators (green/yellow/red/blue) for each station and task type
    - **MO-Asset Integration:** Automatic status updates based on Maintenance Order completion
    - **Interactive Drill-Down:** Click stations to view detailed task lists and linked MOs/Assets
    - **Production Readiness Dashboard:** At-a-glance view of which lines are ready for production restart
  - **Use Cases:**
    - Post-weekend readiness verification (operations managers check line status before production restart)
    - Break period status monitoring (track maintenance progress during shutdowns)
    - Cross-team coordination (shared visual reference for maintenance, operations, production teams)
  - **Monorepo Standards (non-negotiable):**
    - App lives in `apps/monitoring/` with isolated `src/`, `tests/`, `docs/`, and `config/`
    - App enablement via environment flag (planned: `MONITORING_ENABLED=True|False`)
    - Conditional registration in core app factory (no unconditional module-level imports from `apps/*` in `src/`)
    - Dedicated roadmap/bug tracking in app docs (no task duplication in core roadmap)
  - **Planning Docs:**
    - [Monitoring App Roadmap](./Monitoring app/monitoring_roadmap.md)
    - [Monitoring App Concept & Modular Architecture](./Monitoring app/monitoring_concept_and_modular_architecture.md)
  - **Status:** Discovery + architecture definition

- **[x] Collaborative Development: Live Synchronization & File Locking** _(Priority: High)_ — **Delivered via installed `collab-runtime`** (not an in-repo Flask lock service).
  - **Goal:** Synchronized development with real-time visibility and conflict prevention across contributors.
  - **Solution:** External **`collab-runtime`** Python package (default pin `0.2.9`), VS Code extension from [KirilMT/collab](https://github.com/KirilMT/collab) releases, git hooks under `scripts/hooks/`, and CI smoke (`.github/workflows/lock-service-smoke-test.yml`). Legacy planning docs under `docs/COLLABORATIVE_DEVELOPMENT/` were removed; use current onboarding below.
  - **Onboarding (developers and agents):**
    - [README.md](../README.md) — **Collab runtime (file locking)** (install, env overrides, verification commands)
    - [AGENTS.md](../AGENTS.md) — file-locking protocol; use `.\.venv\Scripts\collab.exe` when the venv is not activated (Windows)
    - Skill: `.agents/skills/file-locking/SKILL.md`
  - **Setup:** `.\scripts\setup-dev.ps1` provisions `collab-runtime`, hooks, and optional extension `.vsix`.
  - **Status:** Complete on `main` (integration PRs #136, #138, #142, #143). Ongoing work (version bumps, runtime hardening) happens in the **collab** repository.

- **[ ] Bootstrap 5 Migration** _(Priority: Medium)_
  - **Goal:** Upgrade from Bootstrap 4.5.2 to Bootstrap 5.3.x to modernize the UI framework and improve accessibility.
  - **Detailed Plan:** [docs/bootstrap5_upgrade_analysis.md](bootstrap5_upgrade_analysis.md)
  - **Key Benefits:**
    - Improved accessibility features
    - Better responsive utilities
    - Enhanced form controls
    - Modern CSS architecture
    - Better performance
  - **Estimated Effort:** 2-3 weeks
  - **Status:** Pending - Planning phase

---

## ✅ RECENTLY COMPLETED

### CI Validation & Pre-Commit Refinement (March 17, 2026)

- ✅ **Targeted Pre-Commit:** Updated `.pre-commit-config.yaml` and `scripts/validate_code.py` to only validate staged files during commits, drastically reducing false positives from unstaged debt.
- ✅ **Conditional Sectioning:** Refined `validate_code.py` output to only show relevant tool headers (Bandit, DjLint) when applicable files are staged.
- ✅ **Windows DB Locking Solved:** Migrated modular app tests (Planning) to strict in-memory SQLite to eliminate `PermissionError` (WinError 32) during parallel test execution.

### AI Instruction Consolidation (March 14, 2026)

- ✅ **Master Instruction File:** Created `AGENTS.md` as the single source of truth for all AI agents, reducing total line count across instruction files by >70%.
- ✅ **Tool-Specific Overlays:** Implemented thin overlays for `CLAUDE.md` and `.github/copilot-instructions.md` to handle tool-specific behaviors without duplicating context.
- ✅ **Skills Architecture:** Modularized complex workflows (testing, committing, bug tracking, feature creation) into `.agents/skills/` following the AGENTS.md + SKILL.md open standard.
- ✅ **Knowledge Preservation:** Audited `docs/deprecated/` and preserved all essential project knowledge, patterns, and philosophies in the new Skills and master document.
- ✅ **Validation Verified:** Full codebase validation (`validate_code.py`) passing with new instruction set.

### Portable Windows Distribution Package (March 13, 2026)

- ✅ **Zero-Installation App:** Created a portable distribution of mockCMMS for non-technical users to access the application via a simple `.zip` file.
- ✅ **Automated Build:** Implemented `scripts/build_portable.py` to seamlessly bundle embedded Python 3.12, dependencies, databases, and code.
- ✅ **Refined UX/UI:** Built `START_mockCMMS.bat` which launches an immersive console spinner and seamlessly directs the user to their local browser once the background server goes fully alive.

### Pre-Commit Hooks Automation (March 12, 2026)

- ✅ **Permanent Solution:** Added automatic pre-commit hook installation to `scripts/setup-dev.ps1`.
- ✅ **Developer Experience:** New developers now automatically get pre-commit and pre-push hooks installed when running setup-dev.ps1.
- ✅ **Safe Amend Workflow:** Added `scripts/safe-amend.ps1` to prevent pre-commit stash rollback conflicts during `git commit --amend`.
- ✅ **Git Alias:** `git safe-amend` configured automatically via setup-dev.ps1.

### Phase 6: Root-Level & Configuration Files (January 2, 2026)

- ✅ Audited and improved all root-level files (`run.py`, `requirements.txt`, `.env.example`, etc.).
- ✅ Verified documentation and GitHub configuration.
- ✅ Improved test infrastructure and setup scripts.

### Phase 5: HTML Templates Analysis (January 2, 2026)

- ✅ Audited and improved all 16 HTML templates.
- ✅ Ensured proper separation of concerns (no inline JS/CSS).
- ✅ Verified HTML validity and accessibility.

### Phase 4: CSS Styling Analysis (January 1, 2026)

- ✅ Audited and improved all CSS files.
- ✅ Verified responsive design and visual consistency.

### Phase 3: JavaScript Frontend Analysis (January 1, 2026)

- ✅ Audited and improved all 13 JavaScript files.
- ✅ Verified functionality with browser tests.

### Jest Branch Coverage Improvement (January 1, 2026)

- ✅ **Global Coverage:** Achieved **80.8%** branch coverage (up from 75%).
- ✅ **New Tests:** Added comprehensive tests for `AdvancedTable` sidebar complexity, filtering logic, and delete confirmations.
- ✅ **Validation:** Verified via `scripts/validate_code.py` passing all checks.

### Phase 2 Verified: Critical Backend Fixes (December 17, 2025)

- ✅ **Critical Bug Fix:** Fixed `UnboundExecutionError` during app startup by ensuring modular app models are only registered when enabled.
- ✅ **Critical Test Fix:** Resolved dangerous test cleanup bug that was deleting production database (`mockcmms.db`).
- ✅ **Infrastructure:** Implemented proper SQLAlchemy connection scoping in test fixtures to eliminate resource leaks.
- ✅ **Audit Verified:** Confirmed `src/` directory meets strict quality standards (0 Ruff errors, 9.29/10 Pylint score, 100% test pass rate).

### Phase 2 Verified: Simulation & Testing Tools (December 18, 2025)

- ✅ **Bulk Data Generator:** Implemented `DataSimulationService` to generate thousands of assets, techs, and orders.
- ✅ **Simulation Dashboard:** Created a new "Sim Tools" UI for developers and QA.
- ✅ **Dynamic Events:** Implemented manual triggers for Breakdown Simulation and Technician Availability.
- ✅ **Verified:** 100% test coverage for simulation service and functional UI tests.

### Phase 2: Python Backend Audit (December 15, 2025)

- ✅ Audited and improved all Python files in `src/`, including routes, services, and the main application factory.
- ✅ Refactored `main.py` to improve separation of concerns by moving calendar logic to `shift_utils.py`.
- ✅ Standardized data models and removed deprecated columns in `db_utils.py`.
- ✅ Improved the idempotency and robustness of the database seeding logic in `db_seeding.py`.

### Phase 1: Automated Code Quality Analysis (December 13, 2025)

- ✅ Ruff: 0 issues, Pylint: 9.15/10, Radon: A(2.0), Bandit: 0
- ✅ Refactored `populate_dummy_data()` from E(33) to A(2) complexity
- ✅ Created `db_seeding.py` module with 9 helper functions

### Test Suite Foundation (December 11-13, 2025)

- ✅ 210 automated tests, 82.99% coverage, 100% pass rate

### Advanced Table Component (November 22-29, 2025)

- ✅ Excel-like column resizing, sidebar UI, error handling, retry mechanisms
- ✅ **Local Development Scripts:** `validate_code.py`, `format_code.py`, `release_manager.py` all implemented and verified.

## 🚀 FUTURE FEATURES (Strategic Planning)

> **Note:** This section outlines unimplemented, high-value features for future development. These features are adapted to the project's modular architecture and serve as a guide for future sprints. Use this as a guide for _adding new features_, not for re-implementing existing functionality.

---

## Application-Specific Feature Roadmap

### Core `mockCMMS` Application Enhancements

The core application can be improved with the following features to support the satellite apps.

#### Code Quality & Architecture

> **📋 Detailed Plan:** See [Core Code Quality Plan](deprecated/core_code_quality_plan.md) for the comprehensive audit and cleanup strategy.

- **[x] Project Validation & Code Quality Audit** _(Priority: Critical)_
  - **Status:** ✅ Completed (November 29, 2025)
  - **Goal:** Comprehensive code quality audit and security review to ensure a professional, production-ready codebase.
  - **Outcome:** An audit report was generated with prioritized findings.
  - **Note:** The initial audit is completed. A comprehensive re-audit is planned (see Core Code Quality Plan).

- **[x] Implement Code Quality & Security Fixes** _(Priority: Critical)_
  - **Status:** ✅ Completed (November 29, 2025)
  - **Goal:** Address critical and high-priority issues identified in the audit.
  - **Outcome:** Secured SECRET_KEY, improved logging, and cleaned up frontend code.
  - **Scope:**
    - Move `SECRET_KEY` to environment variables
    - Replace `print()` with `app.logger`
    - Remove `console.log()` from production JS
    - Fix inline styles and other maintenance issues
  - **Dependencies:** Follows the Project Validation Audit.
  - **Note:** Initial fixes are completed. A comprehensive cleanup is planned (see Core Code Quality Plan).

- **[x] Core mockCMMS Code Quality Comprehensive Audit & Cleanup** _(Priority: Critical)_
  - **Status:** ✅ **All 9 Phases Complete** (January 5, 2026)
  - **Goal:** A systematic, comprehensive audit and cleanup of all core mockCMMS code files.
  - **Detailed Plan:** [deprecated/core_code_quality_plan.md](deprecated/core_code_quality_plan.md)
  - **Scope:**
    - **Phase 1:** Automated Code Quality Analysis ✅
    - **Phase 2:** Python Backend Analysis (app.py, routes, services) ✅
    - **Phase 3:** JavaScript Frontend Analysis (Advanced Table, utilities) ✅
    - **Phase 4:** CSS Styling Analysis (main.css, advanced-table.css) ✅
    - **Phase 5:** HTML Templates Analysis (all templates in src/templates/) ✅
    - **Phase 6:** Root-Level & Configuration Files ✅
    - **Phase 7:** Cross-Cutting Concerns (naming, configuration, documentation) ✅
    - **Phase 8:** Test Files Quality Audit ✅
    - **Phase 9:** Frontend Test Audit ✅
  - **Approach:**
    - Analyze every single code file in the core mockCMMS.
    - Identify issues: duplicates, bad practices, violations of standards.
    - Propose solutions and wait for user approval.
    - Implement approved fixes with comprehensive testing.
    - Commit after user confirmation.
  - **Testing:** Manual testing following the `table_features_test_plan.md` methodology.
  - **Dependencies:** None (completed).

- **[ ] Docker-Based Visual Regression Testing** _(Priority: High)_
  - **Goal:** Implement containerized visual testing to eliminate cross-platform rendering inconsistencies (Windows vs. Linux).
  - **Detailed Plan:** [docs/visual_testing_strategy.md](visual_testing_strategy.md)
  - **Scope:**
    - Add `npm run test:visual:docker` script
    - Use official Playwright Docker image
    - Remove current 5% tolerance workaround

- **[ ] Infrastructure & Quality Refinement** _(Priority: Medium)_
  - **Goal:** Consolidate and expand the robustness of the CI/CD and testing infrastructure.
  - **Features:**
    - **Ruff Rule Expansion:** Enable `B` (Bugbear), `I` (Isort), and `UP` (Pyupgrade) rules to catch more logic bugs and consolidate `isort` and `flake8` checks.
    - **Coverage Threshold Alignment:** Standardize coverage requirements consistently across `pyproject.toml`, `validate_code.py`, `package.json`, and documentation to 83-85% for both backend and frontend.
    - **Security Tool Consolidation:** Integrate `bandit` configuration directly into `pyproject.toml` to reduce configuration file sprawl.
    - **ESLint Plugin Expansion:** Add `eslint-plugin-security` or `eslint-plugin-sonarjs` to catch frontend logic bugs and security issues.
    - **Stylelint Standard Rule Enforcement:** Re-enable standard CSS rules (e.g., class pattern enforcement) to improve frontend architecture consistency.
  - **Reference:** Consultation Reporting (January 24, 2026)

- **[ ] Frontend Architecture Decision** _(Priority: High)_
  - **Goal:** Evaluate and decide on a frontend technology stack migration strategy.
  - **Current Stack:**
    - Flask environment with Jinja2 templates (`.html`)
    - Vanilla CSS and JavaScript
    - Custom-built Gantt Chart component (a previous attempt to migrate to the Frappe library was reverted)
  - **Decision Required:**
    - Should the project migrate from vanilla HTML/CSS/JS to Angular or React?
    - Explore hybrid options for a gradual migration.
    - Consider the impact on highly customized components (Gantt Chart).
    - Code Quality: [code-quality.yml](https://github.com/KirilMT/Troubleshooting-Wizard/blob/main/.github/workflows/code-quality.yml)
    - Release: [release.yml](https://github.com/KirilMT/Troubleshooting-Wizard/blob/main/.github/workflows/release.yml)
  - **Dependencies:** Blocked by Project Validation (#7)
  - **Reference:** [GitHub Issue #3](https://github.com/KirilMT/mockCMMS/issues/3)

- **[x] Standardize Naming Conventions** _(Priority: High)_
  - **Status:** ✅ Completed (January 2, 2026)
  - **Goal:** Establish and enforce consistent naming conventions across the codebase.
  - **Outcome:** Audited all files in Phase 7.1 of Core Code Quality Plan.
  - **Reference:** [deprecated/core_code_quality_plan.md](deprecated/core_code_quality_plan.md)

- **[x] Code Comments Cleanup & Standards** _(Priority: High)_
  - **Status:** ✅ Completed (January 2, 2026)
  - **Goal:** Ensure all code comments are professional, descriptive, and follow coding standards.
  - **Outcome:** Removed bug references and standardized comments in Phase 7.1 and Manual Audits.
  - **Reference:** [deprecated/core_code_quality_plan.md](deprecated/core_code_quality_plan.md)

- **[x] Separation of Concerns - Code Organization** _(Priority: High)_
  - **Status:** ✅ Completed (January 2, 2026)
  - **Goal:** Ensure proper separation of HTML, CSS, and JavaScript code.
  - **Outcome:** Extracted inline JS/CSS in Phase 5 (Templates) and Phase 3 (Frontend).
  - **Reference:** [deprecated/core_code_quality_plan.md](deprecated/core_code_quality_plan.md)

- **[x] Structured Logging & Performance Monitoring** _(Priority: High)_
  - **Goal:** Implement enterprise-grade logging similar to `apps/planning`.
  - **Features:**
    - **Structured JSON Logging:** For production environments (for easier parsing).
    - **Request Context:** Include method, path, and user agent in logs.
    - **Performance Metrics:** Track request duration and database operation times.
    - **Slow Operation Warnings:** Automatically log warnings for slow requests (>2s) or DB queries (>1s).
    - **Separated Log Files:** Use distinct files for application, error, and performance logs.
  - **Reference:** `apps/planning/src/services/logging_config.py`

- **[ ] Global Settings Integration** _(Priority: High)_
  - **Goal:** Implement a consistent "Settings" interface across all major modules (Assets, MOs, Users, Spare Parts) to manage configuration data.
  - **Concept:** A dedicated settings page or modal for each module where administrators can configure dropdown options and reference data.
  - **Scope:**
    - **Configurable Topics:** Asset Types, Cost Centers, Asset Status, Maintenance Order Types, Priorities, Frequencies, Manufacturers, User Roles, Shift Teams, Satellite Points, etc.
    - **Implementation:** Replace hardcoded options or JSON configuration files with database-driven settings manageable via the UI.
    - **Location:** Access settings from the main list/dashboard pages of each module (not detail pages).

- **[ ] Integration & Cleanup (Maintenance Grid & Tickets)** _(Priority: Medium)_
  - **Goal:** Review and properly implement or deprecate the integration stub pages (`maintenance_grid.html`, `ticket.html`).
  - **Scope:**
    - Review usage in `apps/planning` and `dummy_data.json`.
    - Refactor `maintenance_grid` to use the actual Maintenance Orders list view with filtering.
    - Refactor `tickets` to redirect to the actual Maintenance Order detail page.
    - Update `apps/planning` configuration to point to the new real URLs.
    - Remove the placeholder templates and routes once replaced.

#### Asset & Data Management

- **[ ] Advanced Asset & Spares Management** _(Priority: Medium)_
  - **Goal:** Move beyond basic CRUD to more intelligent management.
  - **Features:**
    - **Asset Hierarchy:** Implement a full 5-level hierarchy: `Department -> Location -> Line -> Station -> Equipment` (tooling, robot, etc.). Ensure this hierarchy is enforced and visible across all application pages where assets are referenced.
    - **Automated Spares Ordering:** Create a system that automatically flags spare parts for reorder when inventory drops below a certain threshold during task planning.

- **[x] Realistic Data Simulation & Testing Tools** _(Priority: Medium)_
  - **Goal:** Improve the robustness and testability of the entire platform.
  - **Features:**
    - **High-Volume Random Data Generation:** Generate large datasets (thousands of items per table) with realistic, randomized values to mimic production environments.
    - **Data Simulation Service:** Build a service that can generate realistic mock data (PMs, MOs, technician logs) for stress-testing and demonstration purposes.
    - **User Input Simulation:** Create a UI for simulating user inputs, such as manually triggering a breakdown alarm or reporting a technician as absent, to test the system's dynamic response.
  - **Follow-up Enhancement Pending:** Add team-aware labor scaling for bulk-generated MOs so generated staffing better reflects assigned team headcount.

- **[ ] Bulk Data Generator Team-Based Labor Scaling** _(Priority: Medium)_
  - **Goal:** Keep generated maintenance order labor demand aligned with real team capacity.
  - **Acceptance Criteria:**
    - **Team Headcount Batching:** In bulk generation flows, each block of 100 generated MOs should represent one complete team profile (example: team headcount = 10 technicians, configurable by team).
    - **Adaptive MO Labor Count Option:** When assigning a generated MO to a team, provide an option to auto-set MO `labour_count` to the assigned team's headcount.

#### User & Calendar Management

- **[ ] Advanced User & Technician Management** _(Priority: Medium)_
  - **Goal:** Comprehensive user management with roles, skills, training, and external manpower integration.
  - **Features:**
    - **Roles & Permissions:** Implement role-based access control (RBAC) for different user types.
    - **Skills Management:** Track and manage technician skills and certifications.
    - **Training Tracking:** Record and monitor training completion and requirements.
    - **Manpower API Integration:** Connect to an external manpower management system via an API to track:
      - Onsite presence
      - Sick leave status
      - Vacation schedules
      - Real-time availability
    - **Availability Dashboard:** Visualize technician availability, shifts, and status (on-call, sick leave, training).
    - **Workload Tracking:** Track and visualize individual technician workload over time.

- **[X] Shift Calendar Redesign** _(Priority: Medium)_
  - **Goal:** Improve the usability of the Shift Calendar page.
  - **Status:** ✅ Completed
  - **Features:**
    - **Calendar Grid View:** Redesign the interface to resemble a standard calendar (month/week view) instead of a list.
    - **No-Scroll Layout:** Optimize the layout to fit within the viewport without requiring vertical scrolling.
    - **Interactive Elements:** Allow clicking on days/shifts for more details without leaving the calendar view.

#### Testing & Quality Assurance

- **[x] Comprehensive Testing & CI/CD Pipeline** _(Priority: High)_
  - **Status:** ✅ Completed (January 5, 2026)
    - ✅ Pre-commit hooks enabled and configured (`.pre-commit-config.yaml`)
    - ✅ Local validation script (`scripts/validate_code.py`)
    - ✅ Local formatting script (`scripts/format_code.py`)
    - ✅ Test suite expanded to 287 tests (88%+ coverage)
    - ✅ GitHub Actions CI pipeline (`ci.yml`) with Python, Jest, and Playwright tests
    - ✅ Coverage thresholds enforced (82% total, 90% diff)
    - ✅ Pytest configuration in `pyproject.toml`
  - **Objective:** Implement a strict "Local -> Commit -> Push -> CI" workflow to ensure code quality and stability.
  - **Philosophy:** "Verify locally before committing, verify globally on push."
  - **Outcome:** A robust pipeline where passing local tests is a prerequisite for committing, and passing CI is a prerequisite for merging.

- **[ ] UI Regression Automation** _(Priority: Medium)_
  - **Goal:** Ensure critical UI workflows (advanced tables, filters, dropdown persistence, toast handling) are validated automatically.
  - **Plan:** Introduce a lightweight Playwright (or Selenium/Cypress) suite that exercises the advanced-table component end-to-end, complementing the existing backend pytest coverage.

#### Advanced Table Component Enhancements

The Advanced Table component was recently completed with core functionality. The following features were identified but deferred for future development.

- **[x] Sidebar Toggle Implementation Improvement** _(Priority: Medium)_
  - **Status:** ✅ Completed → Verified (December 1, 2025)
  - **Goal:** Improve the sidebar toggle to use a CSS class instead of DOM removal for better performance and state preservation.
  - **Current Issue:** The sidebar toggle removes/adds the element from the DOM, which:
    - Loses internal state (scroll position, expanded sections).
    - Prevents smooth CSS animations.
    - Causes performance overhead from DOM manipulation.
    - Makes Test 2.1.3 (Sidebar State Persistence) fail.
  - **Proposed Solution:**
    - Replace DOM removal with a `collapsed` class toggle.
    - Add CSS: `.table-sidebar.collapsed { display: none; }` or use `transform` for animations.
    - Preserve sidebar state when toggling.
    - Enable smooth collapse/expand animations.
  - **Files to Modify:**
    - `src/static/js/advanced-table/table-sidebar.js` - Update the `toggleSidebar()` method.
    - `src/static/css/advanced-table.css` - Add `.collapsed` class styles.
  - **Reference:** Identified during Test 2.1.1 execution (November 30, 2025).

- **[ ] Improved Form Input Controls & Table Filtering** _(Priority: Medium)_
  - **Goal:** Implement proper input controls for predefined values and date-specific filtering.
  - **Phase 1 - Form Dropdowns (Critical):**
    - Replace text inputs with dropdowns for fields with predefined options (Priority, Status, Order Type, Frequency).
    - Distinguish between single-select and multi-select fields (use Select2 for multi-select).
    - Add backend validation for predefined values.
    - Update database models with ENUM or foreign key constraints.
  - **Phase 2 - Date Filter Operators (Critical):**
    - Replace text-based operators ("contains", "equals") with date-specific operators for date columns.
    - Implement: Exact Date, Before, After, Between, Is Empty, Is Not Empty.
    - Use HTML5 `<input type="date">` for date inputs.
    - Auto-detect date columns in the Advanced Table.
  - **Phase 3 - Numeric Column Filtering (High Value):**
    - Auto-detect columns that contain numeric data (e.g., ID, Quantity, Duration, Count fields).
    - Replace text-based operators ("contains", "equals") with numeric-specific comparators:
      - **Equals** (`= N`)
      - **Not Equals** (`≠ N`)
      - **Greater Than** (`> N`)
      - **Greater Than or Equal** (`≥ N`)
      - **Less Than** (`< N`)
      - **Less Than or Equal** (`≤ N`)
      - **Between** (`N₁ ≤ x ≤ N₂`) — renders two number inputs
    - Column type detection strategy: inspect the first non-empty values in the column at runtime
      (e.g., if all non-null values parse as numbers, treat as numeric).
    - Ensure filter inputs use `<input type="number">` for numeric columns.
    - Validate on the frontend that the entered value is a valid number before applying.
    - Backend filtering logic must handle all comparators safely (no raw string injection).
  - **Phase 4 - Conflicting Filter Detection (High Complexity):**
    - Develop an algorithm to detect conflicting filter combinations (e.g., "Status = Open" AND "Status = Closed").
    - Implement a dynamic UI to prevent conflicts:
      - Option A: Disable conflicting filter options in real-time.
      - Option B: Show a warning when a conflict is detected with an option to resolve it.
      - Option C: Auto-suggest compatible filters based on the current selection.
    - Handle conflicts across AND/OR logic groups.
    - Provide clear user feedback when filters would return no results.
  - **Phase 5 - Advanced Filtering (Optional Enhancement):**
    - Calendar date pickers with visual widgets.
    - Relative date filters ("Today", "This Week", "Last 7 Days").
    - Multi-select filters for status/team fields.
    - Saved filter presets and templates.
  - **Affected Files:**
    - `src/templates/*_detail.html` (form dropdowns)
    - `src/static/js/advanced-table/table-sidebar.js` (date operators, conflict detection)
    - `src/static/js/advanced-table/table-data.js` (filter logic)
    - `src/routes/main.py` (validation)
    - `src/services/db_utils.py` (model constraints)

- **[ ] Pagination** _(Priority: Low)_
  - **Goal:** Enable efficient navigation through large datasets.
  - **Features:**
    - **Page Controls:** Next/Previous buttons with page numbers.
    - **Page Size Selector:** Allow users to choose the number of rows per page (10, 25, 50, 100).
    - **Jump to Page:** An input field to jump directly to a specific page.
    - **Page Info Display:** Show "Page X of Y" and "Showing 1-25 of 1000 rows."
    - **Persist Page Settings:** Remember the page size preference in saved views.

- **[ ] Bulk Operations & Selection Improvements** _(Priority: Low)_
  - **Goal:** Enable efficient multi-row operations and improve selection behavior.
  - **Features:**
    - **Enhanced Select All:** Fix the current page-only limitation. Options:
      - Select all rows across ALL pages (with a warning).
      - Show a "Selected X of Y rows on this page" indicator.
      - Add a dropdown: "Select all on page" vs "Select all X items."
    - **Multi-Row Selection:** Track selection state across pagination.
    - **Bulk Edit:** Edit common fields across multiple selected rows simultaneously.
    - **Bulk Delete:** Delete multiple rows in a single operation with confirmation.
    - **Export Selected Rows Only:** Export only the currently selected rows to CSV/Excel.
  - **Affected Files:**
    - `src/static/js/advanced-table/table-events.js` (checkbox logic)
    - `src/static/js/advanced-table/table-render.js` (selection state)
    - `src/static/css/advanced-table.css` (selection indicator styling)

- **[ ] Collaboration Features** _(Priority: Low)_
  - **Goal:** Enable team collaboration around table views and data.
  - **Features:**
    - **Share Views with Team Members:** Send saved views to other users or teams.
    - **View Usage Analytics:** Track which views are most popular, who's using them, and how often.
    - **Collaborative Filtering:** Real-time filter sharing where team members can see each other's active filters.
    - **View Comments/Notes:** Add notes or comments to saved views to explain their purpose.

- **[ ] Automation Features** _(Priority: Low)_
  - **Goal:** Automate repetitive tasks and reporting.
  - **Features:**
    - **Scheduled Exports:** Configure automatic CSV exports on a schedule (daily, weekly, monthly).
    - **Email Reporting:** Automatically email filtered data or reporting to stakeholders.
    - **Integration with External Tools:** Connect table data to external systems (Slack notifications, webhook triggers).
    - **Data Change Notifications:** Alert users when filtered data changes or meets certain conditions.

**Note:** Low priority - The current implementation meets all immediate needs. These enhancements should be considered after the core application features are complete.

#### Project Infrastructure & Documentation

Cross-cutting concerns that improve overall project quality, team collaboration, and maintainability.

> **📚 Best Practices Reference:** This project follows industry-standard best practices for GitHub workflows, repository organization, security, and team collaboration. See the detailed best practices sections below.

##### GitHub Best Practices Implementation

- **[ ] Implement GitHub Organization Best Practices** _(Priority: High)_
  - **Goal:** Structure the GitHub organization, teams, and repositories following enterprise best practices.
  - **Organization Structure:**
    - Use minimal organizations (one or a few) with teams for access segmentation.
    - Teams should be visible and use cascading permissions.
    - Limit organization owners to 2+ people for redundancy.
    - Use the security manager role for security-focused teams.
  - **Repository Permissions:**
    - Set base permissions to "None" at the org level.
    - Grant access via teams or individual users at the repo level.
    - Repository creation should be limited to organization owners.
    - Outside collaborator access should be managed by owners only.
  - **Repository Visibility:**
    - **Public:** For open-source contributions (current mockCMMS status).
    - **Internal:** For enterprise-wide visibility (future consideration).
    - **Private:** For sensitive or proprietary code.
  - **Reference:** [GitHub Guide to Organizations (PDF)](https://resources.github.com/downloads/github-guide-to-organizations.pdf)

- **[ ] Implement Security & Access Control Standards** _(Priority: Critical)_
  - **Goal:** Enforce security best practices for authentication, tokens, and repository access.
  - **Personal Access Tokens (PAT):**
    - Always set a token expiration (avoid "No Expiry").
    - Limit token scopes to the minimum required permissions.
    - Use the `repo` scope for repository access from the command line.
    - Rotate tokens regularly and revoke unused tokens.
  - **Two-Factor Authentication (2FA):**
    - Require 2FA for all organization members.
    - Organization owners can view members' 2FA status.
    - Enforce the 2FA requirement at the organization level.
  - **Security Features:**
    - Enable the dependency graph for all repositories.
    - Enable Dependabot alerts for security vulnerabilities.
    - Consider code scanning and secret scanning for critical repos.
  - **CODEOWNERS File:**
    - Define code ownership for critical areas.
    - Require reviews from specific teams/individuals.
    - Use for automated review assignment.

- **[x] Implement Git Workflow Standards** _(Priority: High)_
  - **Status:** ✅ Completed (January 5, 2026)
  - **Goal:** Establish and enforce a consistent Git workflow across all contributors.
  - **Implemented:**
    - ✅ **Documentation:** Comprehensive `.github/GIT_WORKFLOW.md` with step-by-step instructions
    - ✅ **Feature Branch Workflow:** Documented in GIT_WORKFLOW.md
      - Branch naming conventions: `feature/<name>`, `bugfix/<name>`, `hotfix/<name>`
      - Branch creation and management
      - Sync strategies and conflict resolution
    - ✅ **PR Standards:** `.github/pull_request_template.md` with checklist
      - Type of change selection
      - Testing requirements
      - Code review checklist
    - ✅ **Commit Message Conventions:** Documented in CONTRIBUTING.md
      - Conventional commits format: `type(scope): subject`
      - Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
      - Issue linking with closing keywords
    - ✅ **Automated Release:** CI/CD pipeline via `workflow_dispatch`
  - **Pending (GitHub Settings):**
    - ⚠️ **Branch Protection Rules:** Must be configured in GitHub repository settings
      - Protect `main` branch from direct pushes
      - Require PR reviews before merging
      - Require status checks to pass (CI/CD)
      - Enforce linear history (squash and merge)
  - **Note:** Branch protection rules require repository admin access to configure in GitHub Settings > Branches.

- **[x] Implement GitHub Actions CI/CD Workflow** _(Priority: High)_
  - **Status:** ✅ Completed (January 5, 2026)
  - **Goal:** Automate testing, code quality checks, and deployment.
  - **Implemented:**
    - ✅ **CI Workflow (`ci.yml`):** Runs on push/PR to main/develop
      - Python backend tests (pytest with 82% coverage threshold)
      - Jest unit tests with coverage
      - Playwright E2E tests
      - Linting (isort, black, docformatter, ruff, flake8)
      - Type checking (mypy)
      - Security scanning (bandit)
      - Diff coverage (90% threshold for new code)
      - Codecov integration
    - ✅ **Release Workflow (`release.yml`):** Automatically runs Google Release Please
      - Assumes control of versioning based on Conventional Commits
      - Automatically opens "Release PRs" and updates CHANGELOG.md
      - Creates GitHub release natively upon merging Release PR
    - ✅ **Local Scripts:** `format_code.py`, `validate_code.py`
    - ✅ **Pre-commit Hooks:** Automated formatting and validation checks
  - **Note:** A separate `code-quality.yml` is not needed since `ci.yml` already includes all quality checks (linting, type checking, security scanning).

- **[x] Implement Local Development Scripts** _(Priority: High)_
  - **Status:** ✅ Completed (January 5, 2026)
    - ✅ `validate_code.py` - Comprehensive pre-commit validation script (simulates CI locally)
    - ✅ `format_code.py` - Actively formats code (Black, isort, Prettier)
    - ✅ `test_workflow.py` - Deprecated (CI pipeline `ci.yml` is the source of truth)
  - **Goal:** Create utility scripts for local development workflow, adapted from Troubleshooting-Wizard.
  - **Reference:** [Troubleshooting-Wizard scripts/](https://github.com/KirilMT/Troubleshooting-Wizard/tree/main/scripts)
  - **Scripts to Implement:**
    - **`validate_code.py`:** ✅ COMPLETED - Comprehensive validation script that runs all checks (linting, formatting, tests, coverage, security) before committing. Simulates CI pipeline locally.
    - **`format_code.py`:** ✅ COMPLETED - Actively formats Python code (not just check). Applies Black, isort, and other formatters.
    - **`test_workflow.py`:** 🚫 DEPRECATED - CI/CD pipeline handles full validation.
    - **`setup_environment.py`:** Not required for current scope.
  - **Key Requirements:**
    - Scripts must be modular and reusable across the mockCMMS ecosystem.
    - `format_code.py` should perform actual formatting, not just linting/checking.
  - **Location:** Create a `scripts/` directory at the repository root.

- **[ ] Implement Repository Standards & Configuration** _(Priority: Medium)_
  - **Goal:** Standardize repository structure, naming, and configuration.
  - **Naming Conventions:**
    - Use lowercase for repository names.
    - Use dashes for word separation (kebab-case).
    - Format: `<area>-<product>-<project>` (e.g., `cmms-planning-scheduler`).
    - Be descriptive and consistent across the organization.
  - **Repository Structure:**
    - Maintain permissions at the team level (not individual).
    - Use `.gitignore` to exclude system files, IDE configs, and dependencies.
    - Include standard files: `README.md`, `LICENSE`, `CONTRIBUTING.md`, `CHANGELOG.md`.
    - Organize code with a clear directory structure.
  - **Documentation Standards:**
    - Use a README.md template with standard sections.
    - Keep README.md updated as the project evolves.
    - Provide links between related repositories.
    - Use docstrings and inline comments.
    - Document public APIs and complex functions.
    - Keep comments relevant as the code evolves.
  - **Dependency Management:**
    - Track dependencies in version control (`requirements.txt`, `package.json`).
    - Check download statistics before adding new dependencies.
    - Verify the maturity, maintenance, and security of dependencies.
    - Keep dependencies updated (automated Dependabot PRs).
    - Remove unused dependencies regularly.
    - Test with the latest versions before updating.
  - **Code Quality Standards:**
    - Use a consistent code style (PEP 8 for Python, style guides for other languages).
    - Use docstrings for all public functions/classes.
    - Comment on complex logic and non-obvious decisions.
    - Include links to discussions/Stack Overflow in comments when relevant.
    - Keep the code clean and remove commented-out code blocks.
    - Avoid irrelevant or unprofessional comments.
    - Use descriptive, searchable names (avoid abbreviations).
    - Organize functions top-down (high-level to low-level).

- **[ ] Project Team Collaboration & Documentation** _(Priority: High)_
  - **Goal:** Create comprehensive team collaboration documentation and tools, and implement GitHub team structure best practices.
  - **Documentation & Tools:**
    - **GitHub Tutorial:** Document all GitHub features for team collaboration (issues, projects, repository rules, settings).
    - **CONTRIBUTING.md Update:** Adapt from a public contributor focus to a private organization team focus.
      - Add media/video tutorials for visual learning.
      - Include a note: if mockCMMS components in `src/` become too complex, migrate them to individual apps.
    - **Setup Automation:** Create a batch script for automatic project setup (to replace the step-by-step instructions in README.md).
    - **Demo Creation:** Build a non-technical demo for stakeholders (management, other teams).
    - **README.md Cleanup:** Move development instructions to CONTRIBUTING.md.
  - **Team Structure Implementation:**
    - Create teams based on product areas or responsibilities.
    - Use a parent/child team hierarchy for organization.
    - Set teams as "Visible" for transparency.
    - Assign team maintainers for each team.
    - Grant repository access at the team level (not individual).
    - Use appropriate permission levels: `read`, `write`, `admin`.
    - Teams can be designated as code owners via CODEOWNERS.
    - Use team mentions (`@org/team-name`) for notifications.
  - **Communication & Workflows:**
    - Use GitHub Discussions for team conversations.
    - Tag teams for review requests on PRs.
    - Use GitHub Projects for tracking work across repos.
    - Document decisions in ADRs (Architecture Decision Records).
  - **Onboarding:**
    - Maintain a team member list with roles.
    - Document team responsibilities and ownership areas.
    - Create an onboarding guide for new team members.
    - Provide training on the Git workflow and GitHub features.
  - **Reference:** [GitHub Issue #4](https://github.com/KirilMT/mockCMMS/issues/4)

- **[x] Fix GitHub Issue Templates** _(Priority: Medium)_
  - **Status:** ✅ Completed (December 18, 2025)
  - **Goal:** Resolve the issue where GitHub issue templates are not working properly.
  - **Tasks:**
    - Investigate why the templates in `.github/ISSUE_TEMPLATE/` are not functioning.
    - Test and validate all issue templates (bug_report.md, feature_request.md, custom.md).
    - Ensure proper YAML frontmatter and template configuration.
  - **Reference:** [GitHub Issue #2](https://github.com/KirilMT/mockCMMS/issues/2)

- **[ ] Update CODEOWNERS File** _(Priority: Low)_
  - **Goal:** Update the CODEOWNERS file with new team members and sections.
  - **Tasks:**
    - Add new users to CODEOWNERS.
    - Define ownership for new sections/modules.
    - Ensure proper GitHub team integration.
  - **Reference:** [GitHub Issue #5](https://github.com/KirilMT/mockCMMS/issues/5)

### Reporting Application Enhancements

> **📋 Detailed Roadmap:** See [Reporting App Roadmap](../apps/reporting/docs/reporting_roadmap.md) for complete task breakdown and implementation details.

- **[ ] Team-Scoped Shift Report Filtering** _(Priority: High)_
  - Filter handovers, breakdowns, and break activities to MOs assigned to the report team
  - Future: support department/team categories for non-maintenance report types

- **[ ] Link Reporting to Core CMMS Data** _(Priority: High)_
  - Link Shift Report sections (Breakdowns, Engineering Support, Handover) to live MO database
  - Detailed tasks in `apps/reporting/docs/reporting_roadmap.md`

- **[ ] Asset Dropdown Population (Select2 AJAX)** _(Priority: Medium)_
  - Replace free-text asset entries with DB-backed API selection
  - Larger enhancement beyond current scope

- **[x] Restructure GEMINI.md Documentation** _(Priority: Low)_
  - **Status:** ✅ Completed → Verified (December 1, 2025)
  - **Goal:** Improve the documentation structure for better clarity.
  - **Changes Required:**
    - Move "Detailed Directory Structure" outside of section 3.1 (apps/workforceManager).
    - Create a new structure:
      - 3.1 Detailed Directory Structure
      - 3.2 apps/workforceManager
      - 3.3 apps/reporting
    - Verify README.md for consistency.
  - **Reference:** [GitHub Issue #1](https://github.com/KirilMT/mockCMMS/issues/1)

- **[x] Improve README Badges** _(Priority: Medium)_
  - **Goal:** Enhance project visibility and demonstrate code quality, security, and modular coverage.
  - **Strategy:**

    > Your current set of badges is a strong start and follows professional standards. Since your project is a **modular Flask monorepo**, you can add a few high-value badges to further demonstrate code quality and security.

    **1. Code Quality & Linting**
    Adding badges for your linting and formatting tools signals that the project follows strict coding standards.
    - **Ruff/Black Formatter:** Shows you use modern, automated formatting.
    - **Static Analysis:** Display `pylint` or `flake8` results using **Shields.io**.

    ```markdown
    [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
    [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
    ```

    **2. Dependency & Security Status**
    - **Dependabot:** Show that Dependabot is active.
    - **Security (Safety/Bandit):** Create a custom "Security: Passing" badge.

    ```markdown
    [![Security: Bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
    ```

    **3. Monorepo-Specific: Component Coverage**
    Use **Codecov Flags** to show coverage of individual applications (e.g., `planning`, `reporting`) to reveal gaps hidden by overall coverage.
    - **Planning Module Coverage:** `[![coverage: planning](https://codecov.io/gh/KirilMT/mockCMMS/branch/main/graph/badge.svg?token=YOUR_TOKEN&flag=planning)](https://codecov.io/gh/KirilMT/mockCMMS)`
    - **Reporting Module Coverage:** `[![coverage: reporting](https://codecov.io/gh/KirilMT/mockCMMS/branch/main/graph/badge.svg?token=YOUR_TOKEN&flag=reporting)](https://codecov.io/gh/KirilMT/mockCMMS)`

    **Recommended Layout:**
    Group badges by category at the top of `README.md`:

    ```markdown
    # mockCMMS

    [![CI Pipeline](...)](...)
    [![codecov](...)](...)
    [![Ruff](...)](...)

    [![Python 3.12+](...)](...)
    [![License: MIT](...)](...)

    [![Planning Coverage](...)](...)
    [![Reporting Coverage](...)](...)
    ```

### `planning` App Enhancements

> **See:** [Planning App Roadmap](../apps/planning/docs/planning_roadmap.md) for detailed feature plans and legacy code analysis tasks.

**Currently Implementing:**

- **[ ] Line Conditions for Planning** _(Priority: High)_
  - **Goal:** Standardize the line conditions needed for task planning to ensure proper execution prerequisites.
  - **Features:**
    - Define and track line conditions (line full/empty, part in fixture, robot position).
    - Add a dedicated column to the planning table showing the necessary line conditions for each task.
    - Make conditions visible to users with operations roles.
    - Integrate condition validation into the task assignment workflow.
  - **Reference:** [GitHub Issue #6](https://github.com/KirilMT/mockCMMS/issues/6)

### `reporting` App Enhancements

> **See:** [Reporting App Roadmap](../apps/reporting/docs/reporting_roadmap.md) for future reporting features.

    - **Availability Dashboard:** Visualize technician availability, shifts, and status (on-call, sick leave, training).
    - **Workload Tracking:** Track and visualize individual technician workload over time.

- **[ ] Shift Calendar Redesign** _(Priority: Medium)_
  - **Goal:** Improve the usability of the Shift Calendar page.
  - **Features:**
    - **Calendar Grid View:** Redesign the interface to resemble a standard calendar (month/week view) instead of a list.
    - **No-Scroll Layout:** Optimize the layout to fit within the viewport without requiring vertical scrolling.
    - **Interactive Elements:** Allow clicking on days/shifts for more details without leaving the calendar view.

- **[ ] Advanced Planning Algorithms** _(Priority: Medium)_
  - **Goal:** Evolve beyond simple task assignment to holistic planning.
  - **Features:**
    - Develop logic for complex scheduling scenarios like multi-day shutdowns or holidays, factoring in technician availability.
    - Create a simulation feature that can optimize schedules before finalizing them.

### `reporting` App Enhancements

This application is intended for reporting and analytics. The following features would provide significant value.

- **[ ] HMI → Reactive MO Integration for Breakdowns** _(Priority: Medium)_
  - **Goal:** When operations press the MNTC (Maintenance) button on the HMI, automatically open a
    Reactive Maintenance Order in the system — eliminating the manual creation gap between the
    physical breakdown event and the digital record.
  - **Core MO Workflow Impact:** This feature requires changes to the MO creation flow in
    the core mockCMMS app (auto-populate asset, shift, timestamp, status = "Open").
  - **Features:**
    - Define an HMI → CMMS integration API contract (webhook or polling endpoint).
    - Auto-create a generic Reactive MO with pre-filled context from the HMI signal.
    - Allow operators/technicians to edit the MO after the fact (fault, root cause, recovery time).
    - Ensure auto-created MOs are correctly picked up by the Reporting Breakdowns section.
  - **Note:** The Reporting-side tracking (ensuring these MOs appear in Shift Reporting) is in
    `apps/reporting/docs/reporting_roadmap.md`.

- **[ ] Automated & Specialized Reporting**
  - **Goal:** Generate key operational reporting automatically.
  - **Features:**
    - **Weekend Task Report:** A report summarizing all tasks planned and completed over a weekend.
    - **Shift Production Report:** A summary of maintenance activities during a specific shift.
    - **Technician-Submitted Reporting:** A system for technicians to log ad-hoc issues like breakdowns or PLC alarms, which can then be aggregated into reporting.

- **[ ] Advanced Statistical Analysis**
  - **Goal:** Provide deeper insights into maintenance operations.
  - **Features:**
    - Develop statistical dashboards for asset performance (e.g., Mean Time Between Failures).
    - Analyze technician performance and skill gaps.
    - Generate reporting on spare part consumption trends.

### `troubleshooting` App (Planned New Module)

> **See:** [Troubleshooting App Roadmap](./Troubleshooting app/troubleshooting_roadmap.md) for phased implementation tasks.

- **[ ] Build Troubleshooting Module Foundation** _(Priority: High)_
  - Scaffold `apps/troubleshooting` as an isolated Flask module with blueprint registration, config, and test suite.
  - Keep strict boundary from core app and other apps; integrate only through controlled app registration and shared APIs.

- **[ ] Implement Troubleshooting Knowledge Workflows** _(Priority: High)_
  - Add technology selector and troubleshooting decision flow.
  - Support error-code-centric diagnosis with configurable references to manuals/knowledge entries.

- **[ ] Add Config-Driven Data and Resource Management** _(Priority: Medium)_
  - Store troubleshooting mappings in app-specific config and/or dedicated app tables.
  - Ensure secure handling of local/manual resource paths and separation from repository-sensitive data.

---

## Summary of Key Unimplemented Features

**Critical Priority:**

- ✅ **Core mockCMMS Code Quality Comprehensive Audit & Cleanup:** COMPLETE ([Detailed Plan](deprecated/core_code_quality_plan.md))
- 🔴 **Legacy Code Analysis & Cleanup Decision (Planning App):** SUPER CRITICAL - [See Planning Roadmap](../apps/planning/docs/planning_roadmap.md)

**High Priority:**

- **Line Conditions for Planning:** [See Planning Roadmap](../apps/planning/docs/planning_roadmap.md)
- **Troubleshooting App Creation (New Modular App):** [See Troubleshooting Roadmap](./Troubleshooting app/troubleshooting_roadmap.md)
- **Monitoring App Creation (New Modular App):** [See Monitoring Roadmap](./Monitoring app/monitoring_roadmap.md)
- **Frontend Architecture Decision:** Evaluate migration to a modern framework (Angular/React).
- **Docker-Based Visual Regression Testing:** Standardize visual testing with containerized runner.
- **CI/CD Pipeline:** ✅ COMPLETE.
- **Team Collaboration Documentation:** GitHub workflows and setup automation.
- ✅ **Standardize Naming Conventions:** COMPLETE.
- ✅ **Code Comments Cleanup:** COMPLETE.
- ✅ **Code Separation:** COMPLETE.
- ✅ **Structured Logging:** COMPLETE.
- ✅ **Local Development Scripts:** COMPLETE.

**Medium Priority:**

- **Advanced User & Technician Management:** Comprehensive user management with roles, skills, training, and manpower API integration (availability, workload, dynamic status).
- **Shift Calendar Redesign:** Improve calendar UI with grid view and interactive elements.
- **Automated, Specialized Reporting:** [See Reporting Roadmap](../apps/reporting/docs/reporting_roadmap.md)
- **HMI → Reactive MO Integration:** Auto-create breakdown MOs from HMI MNTC button signal.
- **Hierarchical Assets & Automated Spares:** Deeper, more intelligent asset and inventory management.
- **Bulk Data Generator Team-Based Labor Scaling:** Add team headcount batching (100 MOs per complete team profile) and optional MO `labour_count` auto-alignment to assigned team size.
- **Form Input Controls & Table Filtering:** Dropdowns for predefined values, date-specific operators, **numeric comparators (between / greater-than / less-than)** for numeric columns.
- **Infrastructure & Quality Refinement:** Ruff expansion, ESLint/Stylelint enforcement, and global coverage alignment (85%).
- **UI Regression Automation:** End-to-end UI testing.
- ✅ **Data Simulation Engine:** COMPLETE.
- ✅ **Fix GitHub Issue Templates:** COMPLETE.

**Low Priority:**

- **Advanced Table Enhancements:** Pagination, bulk operations, collaboration, automation.
- **CODEOWNERS Update:** Add new team members.
- ✅ **GEMINI.md Restructure:** COMPLETE.
