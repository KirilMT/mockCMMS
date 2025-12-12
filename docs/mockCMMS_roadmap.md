# mockCMMS Project Roadmap
_Updated December 12, 2025_

---

> [!IMPORTANT]
> **🚀 New to the project? Start here:** If you're unsure whether to work on code quality audit or GitHub best practices first, read the [Implementation Priority Guide](IMPLEMENTATION_PRIORITY_GUIDE.md) for a clear, step-by-step action plan.

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

##  LIVING DOCUMENT GUIDELINES

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

## 🔥 ACTIVE WORK

**Current Sprint:** Code Quality Analysis (Week 3)
**Status:** Ready to Begin - Prerequisites Met
**Started:** December 13, 2025 (planned)
**Target Completion:** December 20, 2025
**Goal:** Perform comprehensive code quality audit now that all 144 tests are passing.

**Prerequisites Met:** ✅ All 144 tests passing with 75.64% coverage

---

> [!IMPORTANT]
> **📋 Next Plan:** See [Core Code Quality Plan](core_code_quality_plan.md) for Phase 2 code audit specification.
> 
> **Related Documentation:**
> - **[Implementation Priority Guide](IMPLEMENTATION_PRIORITY_GUIDE.md)** - Week-by-week timeline
> - **[Comprehensive Testing Plan](comprehensive_testing_plan.md)** - Completed! All 144 tests passing
> - **[AI Agent Guide](AI_AGENT_GUIDE.md)** - Workflow guide for AI assistants
> 
> **Ready to Begin:**
> - ✅ All 144 tests passing (100%)
> - ✅ Code coverage: 75.64%
> - ✅ Test suite foundation complete
> - 🚀 Ready for Week 3: Code Quality Analysis
> 
> **Next Steps:**
> 1. Begin Phase 0 (Automated Analysis) from core_code_quality_plan.md
> 2. Run ruff, pylint, mypy, bandit
> 3. Document findings and create improvement tasks

---

## ✅ RECENTLY COMPLETED

### Test Suite Foundation (Week 2)
**Duration:** 12 days (December 11-12, 2025)  
**Status:** 100% Complete ✅

**Summary:** Implemented comprehensive test suite with 144 tests covering all core functionality, security, and performance.

**Key Outcomes:**
- ✅ Implemented all 144 automated tests (100% complete)
- ✅ Achieved 75.64% code coverage (exceeds 70% requirement)
- ✅ 100% test pass rate (144/144 passing)
- ✅ Phase 1: Foundation tests (96 tests) - Core functionality
- ��� Phase 2: Security & Robustness (48 tests) - Production quality
- ✅ Performance tests validate scalability
- ✅ Integration tests verify end-to-end workflows
- ✅ Security tests ensure authentication and validation

**Technical Details:**
- Test files: 11 test modules
- Coverage: 75.64% overall
  * app.py: 67.68%
  * api.py: 62.50%
  * main.py: 80.05%
  * db_utils.py: 85.66%
  * shift_utils.py: 100.00%
- All tests passing with pytest
- No critical failures

---### Advanced Table Column Resizing Polish
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

> **📋 Detailed Plan:** See [Core Code Quality Plan](core_code_quality_plan.md) for comprehensive audit and cleanup strategy

- **[x] Project Validation & Code Quality Audit** _(Priority: Critical)_
    - **Status:** ✅ Completed (November 29, 2025)
    - **Goal:** Comprehensive code quality audit and security review to ensure professional, production-ready codebase
    - **Outcome:** Audit report generated with prioritized findings.
    - **Note:** Initial audit completed. Comprehensive re-audit planned (see Core Code Quality Plan).

- **[x] Implement Code Quality & Security Fixes** _(Priority: Critical)_
    - **Status:** ✅ Completed (November 29, 2025)
    - **Goal:** Address critical and high-priority issues identified in the audit
    - **Outcome:** Secured SECRET_KEY, improved logging, and cleaned up frontend code.
    - **Scope:**
        - Move `SECRET_KEY` to environment variables
        - Replace `print()` with `app.logger`
        - Remove `console.log()` from production JS
        - Fix inline styles and other maintenance issues
    - **Dependencies:** Follows Project Validation Audit
    - **Note:** Initial fixes completed. Comprehensive cleanup planned (see Core Code Quality Plan).

- **[ ] Core mockCMMS Code Quality Comprehensive Audit & Cleanup** _(Priority: Critical)_
    - **Status:** 📋 Planning Phase
    - **Goal:** Systematic, comprehensive audit and cleanup of all core mockCMMS code files
    - **Detailed Plan:** [core_code_quality_plan.md](core_code_quality_plan.md)
    - **Scope:**
        - **Phase 1:** Python Backend Analysis (app.py, routes, services)
        - **Phase 2:** JavaScript Frontend Analysis (Advanced Table, utilities)
        - **Phase 3:** CSS Styling Analysis (main.css, advanced-table.css)
        - **Phase 4:** HTML Templates Analysis (all templates in src/templates/)
        - **Phase 5:** Cross-Cutting Concerns (naming, configuration, documentation)
    - **Approach:**
        - Analyze every single code file in core mockCMMS
        - Identify issues: duplicates, bad practices, violations of standards
        - Propose solutions and wait for user approval
        - Implement approved fixes with comprehensive testing
        - Commit after user confirmation
    - **Testing:** Manual testing following `table_features_test_plan.md` methodology
    - **Estimated Duration:** 2-3 weeks (9-14 days)
    - **Dependencies:** None (can start immediately)

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

- **[ ] Standardize Naming Conventions** _(Priority: High)_
    - **Goal:** Establish and enforce consistent naming conventions across the codebase
    - **Issue:** Inconsistent naming (e.g., `advanced-table` vs `table-` prefixes) leads to confusion and maintenance overhead
    - **Scope:**
        - Files and directories (kebab-case vs snake_case)
        - Variables and functions (camelCase vs snake_case)
        - CSS classes and IDs
        - Database tables and columns
    - **Action:** Define standards in `CONTRIBUTING.md` and refactor existing inconsistencies

- **[ ] Code Comments Cleanup & Standards** _(Priority: High)_
    - **Goal:** Ensure all code comments are professional, descriptive, and follow coding standards
    - **Issues:**
        - Bug reference comments (e.g., `<!-- Select2 CSS for Bug #5 -->`, `// Bug #5: Initialize Select2`)
        - Duplicate or redundant comments
        - Non-descriptive or unclear comments
        - Inconsistent comment styles across files
    - **Standards:**
        - Comments explain WHY, not WHAT (code should be self-explanatory)
        - No bug/issue references in production code
        - Use proper grammar and punctuation
        - Keep comments concise and relevant
        - Remove commented-out code blocks
    - **Scope:**
        - HTML/Jinja2 templates: `<!-- Comment -->`
        - JavaScript: `// Single line` or `/* Multi-line */`
        - Python: `# Comment` or `"""Docstring"""`
        - CSS: `/* Comment */`
    - **Action:** Audit all files and refactor comments to meet standards

- **[ ] Separation of Concerns - Code Organization** _(Priority: High)_
    - **Goal:** Ensure proper separation of HTML, CSS, and JavaScript code
    - **Issues:**
        - Inline JavaScript in HTML templates
        - Inline CSS styles in HTML templates
        - Mixed code types in single files
    - **Standards:**
        - JavaScript code belongs in `.js` files only
        - CSS code belongs in `.css` files only
        - HTML code belongs in `.html` templates only
        - Inline styles/scripts only when strictly necessary (e.g., dynamic values from backend)
    - **Scope:**
        - Extract inline `<script>` blocks to separate `.js` files
        - Extract inline `<style>` blocks to separate `.css` files
        - Move inline `style="..."` attributes to CSS classes
        - Move inline `onclick="..."` to event listeners in JS files
    - **Action:** Audit all templates and refactor to proper file separation

- **[ ] Structured Logging & Performance Monitoring** _(Priority: High)_
    - **Goal:** Implement enterprise-grade logging similar to `apps/planning`
    - **Features:**
        - **Structured JSON Logging:** For production environments (easier parsing)
        - **Request Context:** Include method, path, user agent in logs
        - **Performance Metrics:** Track request duration and database operation times
        - **Slow Operation Warnings:** Auto-log warnings for slow requests (>2s) or DB queries (>1s)
        - **Separated Log Files:** Distinct files for application, error, and performance logs
    - **Reference:** `apps/planning/src/services/logging_config.py`

#### Asset & Data Management

- **[ ] Advanced Asset & Spares Management** _(Priority: Medium)_
    - **Goal:** Move beyond basic CRUD to more intelligent management
    - **Features:**
        - **Asset Hierarchy:** Implement full 5-level hierarchy: `Department -> Location -> Line -> Station -> Equipment` (tooling, robot, etc). Ensure this hierarchy is enforced and visible across all application pages where assets are referenced.
        - **Automated Spares Ordering:** Create a system that automatically flags spare parts for reorder when inventory drops below a certain threshold during task planning

- **[ ] Realistic Data Simulation & Testing Tools** _(Priority: Medium)_
    - **Goal:** Improve the robustness and testability of the entire platform
    - **Features:**
        - **High Volume Random Data Generation:** Generate large datasets (thousands of items per table) with realistic, randomized values to mimic production environments.
        - **Data Simulation Service:** Build a service that can generate realistic mock data (PMs, MOs, technician logs) for stress-testing and demonstration purposes.
        - **User Input Simulation:** Create a UI for simulating user inputs, such as manually triggering a breakdown alarm or reporting a technician as absent, to test the system's dynamic response.

#### Testing & Quality Assurance

- **[ ] Comprehensive Testing & CI/CD Pipeline** _(Priority: High)_
    - **Objective:** Implement a strict "Local -> Commit -> Push -> CI" workflow to ensure code quality and stability
    - **Philosophy:** "Verify locally before commit, verify globally on push"
    - **Scope:**
        - **Pre-Commit Hooks:** Implement `.pre-commit-config.yaml` to run linters (flake8, black), formatters, and basic checks before every commit
        - **Local Test Runner:** Configure `pytest.ini` and `pyproject.toml` for easy local execution of core tests
        - **Expanded Test Suite:** Increase core app test coverage from ~2 tests to comprehensive unit/integration tests
        - **GitHub Actions:**
            - `ci.yml`: Run tests and linting on push/PR
            - `code-quality.yml`: Advanced static analysis
            - `release.yml`: Automated release process
    - **Reference:** [Troubleshooting-Wizard Tests](https://github.com/KirilMT/Troubleshooting-Wizard/tree/main/tests)
    - **Key Deliverable:** A robust pipeline where passing local tests is a prerequisite for committing, and passing CI is a prerequisite for merging

- **[ ] UI Regression Automation** _(Priority: Medium)_
    - **Goal:** Ensure critical UI workflows (advanced tables, filters, dropdown persistence, toast handling) are validated automatically
    - **Plan:** Introduce a lightweight Playwright (or Selenium/Cypress) suite that exercises the advanced-table component end-to-end, complementing existing backend pytest coverage

#### Advanced Table Component Enhancements
The Advanced Table component was recently completed with core functionality. The following features were identified but deferred for future development.

- **[x] Sidebar Toggle Implementation Improvement** _(Priority: Medium)_
    - **Status:** ✅ Completed → Verified (December 1, 2025)
    - **Goal:** Improve sidebar toggle to use CSS class instead of DOM removal for better performance and state preservation
    - **Current Issue:** Sidebar toggle removes/adds element from DOM, which:
        - Loses internal state (scroll position, expanded sections)
        - Prevents smooth CSS animations
        - Causes performance overhead from DOM manipulation
        - Makes Test 2.1.3 (Sidebar State Persistence) fail
    - **Proposed Solution:**
        - Replace DOM removal with `collapsed` class toggle
        - Add CSS: `.table-sidebar.collapsed { display: none; }` or use `transform` for animations
        - Preserve sidebar state when toggling
        - Enable smooth collapse/expand animations
    - **Files to Modify:**
        - `src/static/js/advanced-table/table-sidebar.js` - Update `toggleSidebar()` method
        - `src/static/css/advanced-table.css` - Add `.collapsed` class styles
    - **Reference:** Identified during Test 2.1.1 execution (November 30, 2025)

- **[ ] Improved Form Input Controls & Table Filtering** _(Priority: Medium)_
    - **Goal:** Implement proper input controls for predefined values and date-specific filtering
    - **Phase 1 - Form Dropdowns (Critical):**
        - Replace text inputs with dropdowns for fields with predefined options (Priority, Status, Order Type, Frequency)
        - Distinguish single-select vs multi-select fields (use Select2 for multi-select)
        - Add backend validation for predefined values
        - Update database models with ENUM or foreign key constraints
    - **Phase 2 - Date Filter Operators (Critical):**
        - Replace text-based operators ("contains", "equals") with date-specific operators for date columns
        - Implement: Exact Date, Before, After, Between, Is Empty, Is Not Empty
        - Use HTML5 `<input type="date">` for date inputs
        - Auto-detect date columns in Advanced Table
    - **Phase 3 - Conflicting Filter Detection (High Complexity):**
        - Develop algorithm to detect conflicting filter combinations (e.g., "Status = Open" AND "Status = Closed")
        - Implement dynamic UI to prevent conflicts:
            - Option A: Disable conflicting filter options in real-time
            - Option B: Show warning when conflict detected with option to resolve
            - Option C: Auto-suggest compatible filters based on current selection
        - Handle conflicts across AND/OR logic groups
        - Provide clear user feedback when filters would return no results
    - **Phase 4 - Advanced Filtering (Optional Enhancement):**
        - Calendar date pickers with visual widgets
        - Relative date filters ("Today", "This Week", "Last 7 Days")
        - Multi-select filters for status/team fields
        - Saved filter presets and templates
    - **Affected Files:**
        - `src/templates/*_detail.html` (form dropdowns)
        - `src/static/js/advanced-table/table-sidebar.js` (date operators, conflict detection)
        - `src/static/js/advanced-table/table-data.js` (filter logic)
        - `src/routes/main.py` (validation)
        - `src/services/db_utils.py` (model constraints)

- **[ ] Pagination** _(Priority: Low)_
    - **Goal:** Enable efficient navigation through large datasets
    - **Features:**
        - **Page Controls:** Next/Previous buttons with page numbers
        - **Page Size Selector:** Allow users to choose rows per page (10, 25, 50, 100)
        - **Jump to Page:** Input field to jump directly to a specific page
        - **Page Info Display:** Show "Page X of Y" and "Showing 1-25 of 1000 rows"
        - **Persist Page Settings:** Remember page size preference in saved views

- **[ ] Bulk Operations & Selection Improvements** _(Priority: Low)_
    - **Goal:** Enable efficient multi-row operations and improve selection behavior
    - **Features:**
        - **Enhanced Select All:** Fix current page-only limitation. Options:
            - Select all rows across ALL pages (with warning)
            - Show "Selected X of Y rows on this page" indicator
            - Add dropdown: "Select all on page" vs "Select all X items"
        - **Multi-Row Selection:** Track selection state across pagination
        - **Bulk Edit:** Edit common fields across multiple selected rows simultaneously
        - **Bulk Delete:** Delete multiple rows in a single operation with confirmation
        - **Export Selected Rows Only:** Export only the currently selected rows to CSV/Excel
    - **Affected Files:**
        - `src/static/js/advanced-table/table-events.js` (checkbox logic)
        - `src/static/js/advanced-table/table-render.js` (selection state)
        - `src/static/css/advanced-table.css` (selection indicator styling)

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

> **📚 Best Practices Reference:** This project follows industry-standard best practices for GitHub workflows, repository organization, security, and team collaboration. See the detailed best practices sections below.

##### GitHub Best Practices Implementation

- **[ ] Implement GitHub Organization Best Practices** _(Priority: High)_
    - **Goal:** Structure GitHub organization, teams, and repositories following enterprise best practices
    - **Organization Structure:**
        - Use minimal organizations (one or few) with teams for access segmentation
        - Teams should be visible and use cascading permissions
        - Limit organization owners to 2+ people for redundancy
        - Use security manager role for security-focused teams
    - **Repository Permissions:**
        - Set base permissions to "None" at org level
        - Grant access via teams or individual users at repo level
        - Repository creation limited to organization owners
        - Outside collaborator access managed by owners only
    - **Repository Visibility:**
        - **Public:** For open-source contributions (current mockCMMS status)
        - **Internal:** For enterprise-wide visibility (future consideration)
        - **Private:** For sensitive or proprietary code
    - **Reference:** [GitHub Guide to Organizations (PDF)](https://resources.github.com/downloads/github-guide-to-organizations.pdf)

- **[ ] Implement Security & Access Control Standards** _(Priority: Critical)_
    - **Goal:** Enforce security best practices for authentication, tokens, and repository access
    - **Personal Access Tokens (PAT):**
        - Always set token expiration (avoid "No Expiry")
        - Limit token scopes to minimum required permissions
        - Use `repo` scope for repository access from command line
        - Rotate tokens regularly and revoke unused tokens
    - **Two-Factor Authentication (2FA):**
        - Require 2FA for all organization members
        - Organization owners can view members' 2FA status
        - Enforce 2FA requirement at organization level
    - **Security Features:**
        - Enable dependency graph for all repositories
        - Enable Dependabot alerts for security vulnerabilities
        - Consider code scanning and secret scanning for critical repos
    - **CODEOWNERS File:**
        - Define code ownership for critical areas
        - Require reviews from specific teams/individuals
        - Use for automated review assignment

- **[ ] Implement Git Workflow Standards** _(Priority: High)_
    - **Goal:** Establish and enforce consistent Git workflow across all contributors
    - **Branch Protection Rules:**
        - Protect `main` and `develop` branches from direct pushes
        - Require pull requests for all changes
        - Require status checks to pass before merging
        - Enforce linear history (rebase or squash)
    - **Feature Branch Workflow:**
        - Always work in feature branches (never push directly to `main`/`develop`)
        - Branch naming: `feature/<name>`, `bugfix/<name>`, `hotfix/<name>`
        - Branch out from `develop` (or `main` for hotfixes)
        - Keep feature branches short-lived (days, not weeks)
    - **Pull Request Standards:**
        - PRs notify team members and enable code review
        - All changes must go through PR process (no direct commits)
        - PR title should be descriptive and follow conventional commits
        - Include detailed description, testing steps, and screenshots
    - **Rebase Strategy:**
        - Update feature branch with interactive rebase before PR
        - Resolve conflicts locally before creating PR
        - Use `git rebase -i --autosquash develop` to clean up commits
        - Force push with `--force-with-lease` if others are on the branch
    - **Commit Standards:**
        - Follow conventional commits format: `type(scope): subject`
        - Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
        - Subject: imperative mood, 50 chars max, no period
        - Body: explain what and why (not how), wrap at 72 chars
        - Separate subject and body with blank line
    - **Branch Cleanup:**
        - Delete feature branches after merging (both local and remote)
        - Use `git fetch -p` to prune deleted remote branches
        - Keep `main`/`develop` clean and up-to-date

- [ ] Implement GitHub Actions CI/CD Workflow** _(Priority: High)_
    - **Status:** ✅ In Progress (December 11, 2025)
    - **Goal:** Automate testing, code quality checks, and deployment
    - **Workflow Structure:**
        - **CI Workflow:** Run on push/PR to any branch
            - Checkout code
            - Set up Python environment
            - Install dependencies
            - Run linters (flake8, black, pylint)
            - Run test suite (pytest)
            - Generate coverage report
        - **Code Quality Workflow:** Advanced static analysis
            - Security scanning (Bandit, Safety)
            - Dependency auditing
            - Code complexity analysis
            - Documentation coverage
        - **Release Workflow:** Automated versioning and changelog
            - Trigger on tag creation
            - Generate release notes from commits
            - Create GitHub release
            - Deploy to staging/production (future)
    - **Workflow Best Practices:**
        - Use `self-hosted` runners when available (or GitHub-hosted)
        - Cache dependencies to speed up builds
        - Use workflow templates for consistency
        - Store secrets in GitHub Secrets (never in code)
        - Use environment-specific secrets for staging/production
    - **Container Support:**
        - Use Docker containers for consistent environments
        - Mount workspace to container for workflow steps
        - Clean up workspace ownership issues after container runs
        - Authenticate to private registries using secrets
    - **Reference Examples:**
        - CI: [Troubleshooting-Wizard ci.yml](https://github.com/KirilMT/Troubleshooting-Wizard/blob/main/.github/workflows/ci.yml)
        - Code Quality: [code-quality.yml](https://github.com/KirilMT/Troubleshooting-Wizard/blob/main/.github/workflows/code-quality.yml)
        - Release: [release.yml](https://github.com/KirilMT/Troubleshooting-Wizard/blob/main/.github/workflows/release.yml)

- **[ ] Implement Repository Standards & Configuration** _(Priority: Medium)_
    - **Goal:** Standardize repository structure, naming, and configuration
    - **Naming Conventions:**
        - Use lowercase for repository names
        - Use dashes for word separation (kebab-case)
        - Format: `<area>-<product>-<project>` (e.g., `cmms-planning-scheduler`)
        - Be descriptive and consistent across organization
    - **Repository Structure:**
        - Maintain permissions at team level (not individual)
        - Use `.gitignore` to exclude system files, IDE configs, dependencies
        - Include standard files: `README.md`, `LICENSE`, `CONTRIBUTING.md`, `CHANGELOG.md`
        - Organize code with clear directory structure
    - **Documentation Standards:**
        - Use README.md template with standard sections
        - Keep README.md updated as project evolves
        - Provide links between related repositories
        - Use docstrings and inline comments
        - Document public APIs and complex functions
        - Keep comments relevant as code evolves
    - **Dependency Management:**
        - Track dependencies in version control (`requirements.txt`, `package.json`)
        - Check download statistics before adding new dependencies
        - Verify maturity, maintenance, and security of dependencies
        - Keep dependencies updated (automated Dependabot PRs)
        - Remove unused dependencies regularly
        - Test with latest versions before updating
    - **Code Quality Standards:**
        - Use consistent code style (PEP 8 for Python, style guides for other languages)
        - Use docstrings for all public functions/classes
        - Comment complex logic and non-obvious decisions
        - Include links to discussions/Stack Overflow in comments when relevant
        - Keep code clean and remove commented-out blocks
        - Avoid irrelevant or unprofessional comments
        - Use descriptive, searchable names (avoid abbreviations)
        - Organize functions top-down (high-level to low-level)

- **[ ] Project Team Collaboration & Documentation** _(Priority: High)_
    - **Goal:** Create comprehensive team collaboration documentation, tools, and implement GitHub team structure best practices
    - **Documentation & Tools:**
        - **GitHub Tutorial:** Document all GitHub features for team collaboration (issues, projects, repository rules, settings)
        - **CONTRIBUTING.md Update:** Adapt from public contributor focus to private organization team focus
            - Add media/video tutorials for visual learning
            - Include note: if mockCMMS components in `src/` become too complex, migrate to individual apps
        - **Setup Automation:** Create batch script for automatic project setup (replace step-by-step instructions in README.md)
        - **Demo Creation:** Build non-technical demo for stakeholders (management, other teams)
        - **README.md Cleanup:** Move development instructions to CONTRIBUTING.md
    - **Team Structure Implementation:**
        - Create teams based on product areas or responsibilities
        - Use parent/child team hierarchy for organization
        - Set teams as "Visible" for transparency
        - Assign team maintainers for each team
        - Grant repository access at team level (not individual)
        - Use appropriate permission levels: `read`, `write`, `admin`
        - Teams can be designated as code owners via CODEOWNERS
        - Use team mentions (`@org/team-name`) for notifications
    - **Communication & Workflows:**
        - Use GitHub Discussions for team conversations
        - Tag teams for review requests on PRs
        - Use GitHub Projects for tracking work across repos
        - Document decisions in ADRs (Architecture Decision Records)
    - **Onboarding:**
        - Maintain team member list with roles
        - Document team responsibilities and ownership areas
        - Create onboarding guide for new team members
        - Provide training on Git workflow and GitHub features
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

- **[x] Restructure GEMINI.md Documentation** _(Priority: Low)_
    - **Status:** ✅ Completed → Verified (December 1, 2025)
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

- **[ ] Advanced User & Technician Management** _(Priority: Medium)_
    - **Goal:** Comprehensive user management with roles, skills, training, and external manpower integration
    - **Features:**
        - **Roles & Permissions:** Implement role-based access control (RBAC) for different user types
        - **Skills Management:** Track and manage technician skills and certifications
        - **Training Tracking:** Record and monitor training completion and requirements
        - **Manpower API Integration:** Connect to external manpower management system via API to track:
            - Onsite presence
            - Sick leave status
            - Vacation schedules
            - Real-time availability
        - **Availability Dashboard:** Visualize technician availability, shifts, and status (on-call, sick leave, training)
        - **Workload Tracking:** Track and visualize individual technician workload over time

- **[ ] Shift Calendar Redesign** _(Priority: Medium)_
    - **Goal:** Improve the usability of the Shift Calendar page
    - **Features:**
        - **Calendar Grid View:** Redesign the interface to resemble a standard calendar (month/week view) instead of a list
        - **No-Scroll Layout:** Optimize the layout to fit within the viewport without requiring vertical scrolling
        - **Interactive Elements:** Allow clicking on days/shifts for more details without leaving the calendar view

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
- **Core mockCMMS Code Quality Comprehensive Audit & Cleanup:** Systematic audit of all core code files ([Detailed Plan](core_code_quality_plan.md))

**High Priority:**
- **Line Conditions for Planning:** Standardize prerequisites for task execution
- **Frontend Architecture Decision:** Evaluate migration to modern framework (Angular/React)
- **CI/CD Pipeline:** Automated testing, code quality, and deployment
- **Team Collaboration Documentation:** GitHub workflows and setup automation
- **Code Comments Cleanup:** Remove bug references, ensure professional descriptive comments
- **Code Separation:** Proper separation of HTML, CSS, and JavaScript

**Medium Priority:**
- **Advanced Technician Tracking:** Availability, workload, and dynamic status
- **Automated, Specialized Reports:** Shift, weekend, and technician-submitted reports
- **Hierarchical Assets & Automated Spares:** Deeper, more intelligent asset and inventory management
- **Data Simulation Engine:** For robust testing and development
- **Core Test Suite Enhancement:** Comprehensive testing infrastructure
- **UI Regression Automation:** End-to-end UI testing
- **Fix GitHub Issue Templates:** Resolve template functionality issues

**Medium Priority:**
- **Form Input Controls & Table Filtering:** Dropdowns for predefined values, date-specific filter operators

**Low Priority:**
- **Advanced Table Enhancements:** Bulk operations, collaboration, automation
- **CODEOWNERS Update:** Add new team members
- **GEMINI.md Restructure:** Improve documentation organization
