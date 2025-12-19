# mockCMMS Project Roadmap
_Updated December 19, 2025_

---

> [!IMPORTANT]
> **🚀 New to the project? Start here:** If you're unsure whether to work on the code quality audit or GitHub best practices first, read the [Implementation Priority Guide](IMPLEMENTATION_PRIORITY_GUIDE.md) for a clear, step-by-step action plan.

---

> [!TIP]
> **Document Relationship:** This roadmap tracks new features and strategic improvements. For bugs in existing functionality, see `bug_tracking.md`.

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

##  LIVING DOCUMENT GUIDELINES

**This roadmap is a living document that evolves with the project.**

### Maintenance Rules

1. **Mark Completed Items**
   - When a feature is completed, change `[ ]` to `[x]` in the checkbox
   - Move completed items to the "Recently Completed" section with a completion date and summary
   - Add key outcomes and technical details to help future reference

2. **Add New Ideas**
   - New features should be added to the appropriate application section (`planning`, `reports`, `core mockCMMS`, etc.)
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

**Current Sprint:** Code Quality Audit - Phase 3 (JavaScript)
**Status:** ✅ Ready to Start
**Started:** December 19, 2025

> [!NOTE]
> The Frontend Test Suite Foundation is **COMPLETE** (293 Jest + 71 Playwright tests passing).
> The code quality audit can now proceed with Phase 3 (JavaScript files).

---

> [!IMPORTANT]
> **📋 Active Plan:** [Core Code Quality Plan](core_code_quality_plan.md) - Phase 3 Ready
> **🧪 Frontend Tests:** 293 Jest + 71 Playwright tests ✅
> **📊 Backend Tests:** 223 pytest tests ✅

---

## ✅ RECENTLY COMPLETED

### Phase 2 Verified: Critical Backend Fixes (December 17, 2025)
- ✅ **Critical Bug Fix:** Fixed `UnboundExecutionError` during app startup by ensuring modular app models are only registered when enabled.
- ✅ **Critical Test Fix:** Resolved dangerous test cleanup bug that was deleting production database (`mockcmms.db`).
- ✅ **Infrastructure:** Implemented proper SQLAlchemy connection scoping in test fixtures to eliminate resource leaks.
- ✅ **Audit Verified:** Confirmed `src/` directory meets strict quality standards (0 Ruff errors, 9.29/10 Pylint score, 100% test pass rate).

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

## 🚀 FUTURE FEATURES (Strategic Planning)

> **Note:** This section outlines unimplemented, high-value features for future development. These features are adapted to the project's modular architecture and serve as a guide for future sprints. Use this as a guide for *adding new features*, not for re-implementing existing functionality.

---

## Application-Specific Feature Roadmap

### Core `mockCMMS` Application Enhancements
The core application can be improved with the following features to support the satellite apps.

#### Code Quality & Architecture

> **📋 Detailed Plan:** See [Core Code Quality Plan](core_code_quality_plan.md) for the comprehensive audit and cleanup strategy.

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

- **[ ] Core mockCMMS Code Quality Comprehensive Audit & Cleanup** _(Priority: Critical)_
    - **Status:** 🔄 **Phase 3 In Progress** (Phase 2 Complete)
    - **Goal:** A systematic, comprehensive audit and cleanup of all core mockCMMS code files.
    - **Detailed Plan:** [core_code_quality_plan.md](core_code_quality_plan.md)
    - **Scope:**
        - **Phase 1:** Automated Code Quality Analysis
        - **Phase 2:** Python Backend Analysis (app.py, routes, services)
        - **Phase 3:** JavaScript Frontend Analysis (Advanced Table, utilities)
        - **Phase 4:** CSS Styling Analysis (main.css, advanced-table.css)
        - **Phase 5:** HTML Templates Analysis (all templates in src/templates/)
        - **Phase 6:** Root-Level & Configuration Files
        - **Phase 7:** Cross-Cutting Concerns (naming, configuration, documentation)
    - **Approach:**
        - Analyze every single code file in the core mockCMMS.
        - Identify issues: duplicates, bad practices, violations of standards.
        - Propose solutions and wait for user approval.
        - Implement approved fixes with comprehensive testing.
        - Commit after user confirmation.
    - **Testing:** Manual testing following the `table_features_test_plan.md` methodology.
    - **Dependencies:** None (can start immediately).

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

- **[ ] Standardize Naming Conventions** _(Priority: High)_
    - **Goal:** Establish and enforce consistent naming conventions across the codebase.
    - **Issue:** Inconsistent naming (e.g., `advanced-table` vs `table-` prefixes) leads to confusion and maintenance overhead.
    - **Scope:**
        - Files and directories (kebab-case vs snake_case)
        - Variables and functions (camelCase vs snake_case)
        - CSS classes and IDs
        - Database tables and columns
    - **Action:** Define standards in `CONTRIBUTING.md` and refactor existing inconsistencies.

- **[ ] Code Comments Cleanup & Standards** _(Priority: High)_
    - **Goal:** Ensure all code comments are professional, descriptive, and follow coding standards.
    - **Issues:**
        - Bug reference comments (e.g., `<!-- Select2 CSS for Bug #5 -->`, `// Bug #5: Initialize Select2`)
        - Duplicate or redundant comments
        - Non-descriptive or unclear comments
        - Inconsistent comment styles across files
    - **Standards:**
        - Comments should explain WHY, not WHAT (the code should be self-explanatory).
        - No bug/issue references in production code.
        - Use proper grammar and punctuation.
        - Keep comments concise and relevant.
        - Remove commented-out code blocks.
    - **Scope:**
        - HTML/Jinja2 templates: `<!-- Comment -->`
        - JavaScript: `// Single line` or `/* Multi-line */`
        - Python: `# Comment` or `"""Docstring"""`
        - CSS: `/* Comment */`
    - **Action:** Audit all files and refactor comments to meet standards.

- **[ ] Separation of Concerns - Code Organization** _(Priority: High)_
    - **Goal:** Ensure proper separation of HTML, CSS, and JavaScript code.
    - **Issues:**
        - Inline JavaScript in HTML templates
        - Inline CSS styles in HTML templates
        - Mixed code types in single files
    - **Standards:**
        - JavaScript code belongs in `.js` files only.
        - CSS code belongs in `.css` files only.
        - HTML code belongs in `.html` templates only.
        - Inline styles/scripts should only be used when strictly necessary (e.g., for dynamic values from the backend).
    - **Scope:**
        - Extract inline `<script>` blocks to separate `.js` files.
        - Extract inline `<style>` blocks to separate `.css` files.
        - Move inline `style="..."` attributes to CSS classes.
        - Move inline `onclick="..."` attributes to event listeners in JS files.
    - **Action:** Audit all templates and refactor to ensure proper file separation.

- **[x] Structured Logging & Performance Monitoring** _(Priority: High)_
    - **Goal:** Implement enterprise-grade logging similar to `apps/planning`.
    - **Features:**
        - **Structured JSON Logging:** For production environments (for easier parsing).
        - **Request Context:** Include method, path, and user agent in logs.
        - **Performance Metrics:** Track request duration and database operation times.
        - **Slow Operation Warnings:** Automatically log warnings for slow requests (>2s) or DB queries (>1s).
        - **Separated Log Files:** Use distinct files for application, error, and performance logs.
    - **Reference:** `apps/planning/src/services/logging_config.py`

#### Asset & Data Management

- **[ ] Advanced Asset & Spares Management** _(Priority: Medium)_
    - **Goal:** Move beyond basic CRUD to more intelligent management.
    - **Features:**
        - **Asset Hierarchy:** Implement a full 5-level hierarchy: `Department -> Location -> Line -> Station -> Equipment` (tooling, robot, etc.). Ensure this hierarchy is enforced and visible across all application pages where assets are referenced.
        - **Automated Spares Ordering:** Create a system that automatically flags spare parts for reorder when inventory drops below a certain threshold during task planning.

- **[ ] Realistic Data Simulation & Testing Tools** _(Priority: Medium)_
    - **Goal:** Improve the robustness and testability of the entire platform.
    - **Features:**
        - **High-Volume Random Data Generation:** Generate large datasets (thousands of items per table) with realistic, randomized values to mimic production environments.
        - **Data Simulation Service:** Build a service that can generate realistic mock data (PMs, MOs, technician logs) for stress-testing and demonstration purposes.
        - **User Input Simulation:** Create a UI for simulating user inputs, such as manually triggering a breakdown alarm or reporting a technician as absent, to test the system's dynamic response.

#### Testing & Quality Assurance

- **[ ] Comprehensive Testing & CI/CD Pipeline** _(Priority: High)_
    - **Objective:** Implement a strict "Local -> Commit -> Push -> CI" workflow to ensure code quality and stability.
    - **Philosophy:** "Verify locally before committing, verify globally on push."
    - **Scope:**
        - **Pre-Commit Hooks:** Implement `.pre-commit-config.yaml` to run linters (flake8, black), formatters, and basic checks before every commit.
        - **Local Test Runner:** Configure `pytest.ini` and `pyproject.toml` for easy local execution of core tests.
        - **Expanded Test Suite:** Increase the core app test coverage from ~2 tests to comprehensive unit/integration tests.
        - **GitHub Actions:**
            - `ci.yml`: Run tests and linting on push/PR.
            - `code-quality.yml`: Perform advanced static analysis.
            - `release.yml`: Automate the release process.
    - **Reference:** [Troubleshooting-Wizard Tests](https://github.com/KirilMT/Troubleshooting-Wizard/tree/main/tests)
    - **Key Deliverable:** A robust pipeline where passing local tests is a prerequisite for committing, and passing CI is a prerequisite for merging.

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
    - **Phase 3 - Conflicting Filter Detection (High Complexity):**
        - Develop an algorithm to detect conflicting filter combinations (e.g., "Status = Open" AND "Status = Closed").
        - Implement a dynamic UI to prevent conflicts:
            - Option A: Disable conflicting filter options in real-time.
            - Option B: Show a warning when a conflict is detected with an option to resolve it.
            - Option C: Auto-suggest compatible filters based on the current selection.
        - Handle conflicts across AND/OR logic groups.
        - Provide clear user feedback when filters would return no results.
    - **Phase 4 - Advanced Filtering (Optional Enhancement):**
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
        - **Email Reports:** Automatically email filtered data or reports to stakeholders.
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

- **[ ] Implement Git Workflow Standards** _(Priority: High)_
    - **Goal:** Establish and enforce a consistent Git workflow across all contributors.
    - **Branch Protection Rules:**
        - Protect `main` and `develop` branches from direct pushes.
        - Require pull requests for all changes.
        - Require status checks to pass before merging.
        - Enforce a linear history (rebase or squash).
    - **Feature Branch Workflow:**
        - Always work in feature branches (never push directly to `main`/`develop`).
        - Branch naming: `feature/<name>`, `bugfix/<name>`, `hotfix/<name>`.
        - Branch out from `develop` (or `main` for hotfixes).
        - Keep feature branches short-lived (days, not weeks).
    - **Pull Request Standards:**
        - PRs should notify team members and enable code review.
        - All changes must go through the PR process (no direct commits).
        - The PR title should be descriptive and follow conventional commits.
        - Include a detailed description, testing steps, and screenshots.
    - **Rebase Strategy:**
        - Update the feature branch with an interactive rebase before creating a PR.
        - Resolve conflicts locally before creating the PR.
        - Use `git rebase -i --autosquash develop` to clean up commits.
        - Use `git push --force-with-lease` if others are on the branch.
    - **Commit Standards:**
        - Follow the conventional commits format: `type(scope): subject`.
        - Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`.
        - Subject: imperative mood, 50 chars max, no period.
        - Body: explain what and why (not how), wrap at 72 chars.
        - Separate the subject and body with a blank line.
    - **Branch Cleanup:**
        - Delete feature branches after merging (both local and remote).
        - Use `git fetch -p` to prune deleted remote branches.
        - Keep `main`/`develop` clean and up-to-date.

- [ ] Implement GitHub Actions CI/CD Workflow** _(Priority: High)_
    - **Status:** ✅ In Progress (December 11, 2025)
    - **Goal:** Automate testing, code quality checks, and deployment.
    - **Workflow Structure:**
        - **CI Workflow:** Run on push/PR to any branch.
            - Checkout code.
            - Set up the Python environment.
            - Install dependencies.
            - Run linters (flake8, black, pylint).
            - Run the test suite (pytest).
            - Generate a coverage report.
        - **Code Quality Workflow:** Perform advanced static analysis.
            - Security scanning (Bandit, Safety).
            - Dependency auditing.
            - Code complexity analysis.
            - Documentation coverage.
        - **Release Workflow:** Automated versioning and changelog.
            - Trigger on tag creation.
            - Generate release notes from commits.
            - Create a GitHub release.
            - Deploy to staging/production (future).
    - **Workflow Best Practices:**
        - Use `self-hosted` runners when available (or GitHub-hosted).
        - Cache dependencies to speed up builds.
        - Use workflow templates for consistency.
        - Store secrets in GitHub Secrets (never in code).
        - Use environment-specific secrets for staging/production.
    - **Container Support:**
        - Use Docker containers for consistent environments.
        - Mount the workspace to the container for workflow steps.
        - Clean up workspace ownership issues after the container runs.
        - Authenticate to private registries using secrets.
    - **Reference Examples:**
        - CI: [Troubleshooting-Wizard ci.yml](https://github.com/KirilMT/Troubleshooting-Wizard/blob/main/.github/workflows/ci.yml)
        - Code Quality: [code-quality.yml](https://github.com/KirilMT/Troubleshooting-Wizard/blob/main/.github/workflows/code-quality.yml)
        - Release: [release.yml](https://github.com/KirilMT/Troubleshooting-Wizard/blob/main/.github/workflows/release.yml)

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

- **[x] Restructure GEMINI.md Documentation** _(Priority: Low)_
    - **Status:** ✅ Completed → Verified (December 1, 2025)
    - **Goal:** Improve the documentation structure for better clarity.
    - **Changes Required:**
        - Move "Detailed Directory Structure" outside of section 3.1 (apps/workforceManager).
        - Create a new structure:
            - 3.1 Detailed Directory Structure
            - 3.2 apps/workforceManager
            - 3.3 apps/reports
        - Verify README.md for consistency.
    - **Reference:** [GitHub Issue #1](https://github.com/KirilMT/mockCMMS/issues/1)

- **[x] Improve README Badges** _(Priority: Medium)_
    - **Goal:** Enhance project visibility and demonstrate code quality, security, and modular coverage.
    - **Strategy:**
        > Your current set of badges is a strong start and follows professional standards. Since your project is a **modular Flask monorepo**, you can add a few high-value badges to further demonstrate code quality and security.

        **1. Code Quality & Linting**
        Adding badges for your linting and formatting tools signals that the project follows strict coding standards.
        * **Ruff/Black Formatter:** Shows you use modern, automated formatting.
        * **Static Analysis:** Display `pylint` or `flake8` results using **Shields.io**.
        ```markdown
        [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
        [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
        ```

        **2. Dependency & Security Status**
        * **Dependabot:** Show that Dependabot is active.
        * **Security (Safety/Bandit):** Create a custom "Security: Passing" badge.
        ```markdown
        [![Security: Bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
        ```

        **3. Monorepo-Specific: Component Coverage**
        Use **Codecov Flags** to show coverage of individual applications (e.g., `planning`, `reports`) to reveal gaps hidden by overall coverage.
        * **Planning Module Coverage:** `[![coverage: planning](https://codecov.io/gh/KirilMT/mockCMMS/branch/main/graph/badge.svg?token=YOUR_TOKEN&flag=planning)](https://codecov.io/gh/KirilMT/mockCMMS)`
        * **Reports Module Coverage:** `[![coverage: reports](https://codecov.io/gh/KirilMT/mockCMMS/branch/main/graph/badge.svg?token=YOUR_TOKEN&flag=reports)](https://codecov.io/gh/KirilMT/mockCMMS)`

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
        [![Reports Coverage](...)](...)
        ```

### `planning` App Enhancements
This application already handles skill-based task assignment. The next logical steps involve deeper integration and more advanced planning management features.

- **[ ] Line Conditions for Planning** _(Priority: High)_
    - **Goal:** Standardize the line conditions needed for task planning to ensure proper execution prerequisites.
    - **Features:**
        - Define and track line conditions (line full/empty, part in fixture, robot position).
        - Add a dedicated column to the planning table showing the necessary line conditions for each task.
        - Make conditions visible to users with operations roles.
        - Integrate condition validation into the task assignment workflow.
    - **Reference:** [GitHub Issue #6](https://github.com/KirilMT/mockCMMS/issues/6)

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

### `reports` App Enhancements
This application is intended for reporting and analytics. The following features would provide significant value.

- **[ ] Automated & Specialized Reporting**
    - **Goal:** Generate key operational reports automatically.
    - **Features:**
        - **Weekend Task Report:** A report summarizing all tasks planned and completed over a weekend.
        - **Shift Production Report:** A summary of maintenance activities during a specific shift.
        - **Technician-Submitted Reports:** A system for technicians to log ad-hoc issues like breakdowns or PLC alarms, which can then be aggregated into reports.

- **[ ] Advanced Statistical Analysis**
    - **Goal:** Provide deeper insights into maintenance operations.
    - **Features:**
        - Develop statistical dashboards for asset performance (e.g., Mean Time Between Failures).
        - Analyze technician performance and skill gaps.
        - Generate reports on spare part consumption trends.

---

## Summary of Key Unimplemented Features

**Critical Priority:**
- **Core mockCMMS Code Quality Comprehensive Audit & Cleanup:** A systematic audit of all core code files ([Detailed Plan](core_code_quality_plan.md)).

**High Priority:**
- **Line Conditions for Planning:** Standardize prerequisites for task execution.
- **Frontend Architecture Decision:** Evaluate migration to a modern framework (Angular/React).
- **CI/CD Pipeline:** Automated testing, code quality, and deployment.
- **Team Collaboration Documentation:** GitHub workflows and setup automation.
- **Code Comments Cleanup:** Remove bug references and ensure professional, descriptive comments.
- **Code Separation:** Proper separation of HTML, CSS, and JavaScript.

**Medium Priority:**
- **Advanced Technician Tracking:** Availability, workload, and dynamic status.
- **Automated, Specialized Reports:** Shift, weekend, and technician-submitted reports.
- **Hierarchical Assets & Automated Spares:** Deeper, more intelligent asset and inventory management.
- **Data Simulation Engine:** For robust testing and development.
- **Core Test Suite Enhancement:** Comprehensive testing infrastructure.
- **UI Regression Automation:** End-to-end UI testing.
- **Fix GitHub Issue Templates:** Resolve template functionality issues.

**Medium Priority:**
- **Form Input Controls & Table Filtering:** Dropdowns for predefined values, date-specific filter operators.

**Low Priority:**
- **Advanced Table Enhancements:** Bulk operations, collaboration, automation.
- **CODEOWNERS Update:** Add new team members.
- **GEMINI.md Restructure:** Improve documentation organization.
