# Core mockCMMS Code Quality & Architecture Audit Plan

**Created:** December 1, 2025  
**Last Updated:** December 17, 2025
**Status:** ⏸️ **On Hold** (Waiting for Frontend Test Suite Foundation)
**Prerequisites Met:** All 210 tests complete with 82.99% coverage. Phase 1 & 2 (Automated Analysis & Python Backend) complete.

---

> [!IMPORTANT]
> **📋 Workflow Context:** This plan details the 7 phases of the Code Quality Audit.
> 
> **Related Documentation:**
> - **[Comprehensive Testing Plan](comprehensive_testing_plan.md)** - Testing Foundation (Completed)
> - **[Implementation Priority Guide](IMPLEMENTATION_PRIORITY_GUIDE.md)** - Overall timeline
> - **[mockCMMS Roadmap](mockCMMS_roadmap.md)** - Strategic context
> 
> **Prerequisites Before Starting This Plan:**
> 1. ✅ All 210 tests from `comprehensive_testing_plan.md` must be implemented (210/210 complete - 100%)
> 2. ✅ All tests must pass (100% pass rate) (210/210 passing)
> 3. ✅ Code coverage must reach 80-85% overall (Current: 82.99%, Target: 80-85%) ✅
> 4. ✅ Critical coverage gaps closed (api.py: 78.78%, app.py: 88.89%, main.py: 81.42%)
> 5. ✅ CI configured with pytest + coverage in .github/workflows/ci.yml
> 
> **Status:** ✅ **READY TO START** (210/210 tests, 82.99% coverage)
> **Current Progress:** Phase 2 Complete. Phase 3 In Progress.

---  
**Scope:** Entire mockCMMS repository (excluding `apps/` directory)

---

> [!IMPORTANT]
> **🎯 Implementation Strategy:** This audit should be performed alongside GitHub best practices setup. See [Implementation Priority Guide](IMPLEMENTATION_PRIORITY_GUIDE.md) for a complete action plan showing how to integrate code quality work with infrastructure setup.

---

## 📋 Overview

This document outlines a comprehensive, systematic approach to auditing and improving the code quality of the core mockCMMS application. The focus is on ensuring the codebase is clean, organized, optimized, follows coding conventions, and contains no duplicates or technical debt.

**Philosophy:** Analyze first, propose solutions, get approval, implement, test, commit.

## 🔄 Standard Workflow: 5-Step Iterative Loop

For all audit tasks, we follow a strict 5-step iterative process to ensure quality:

1.  **Lint**: Run `ruff`, `pylint`, `mypy`, `radon`, `bandit`, `jscpd`. **Fix all errors.**
2.  **Format**: Run `flake8` and `black`. **Fix all issues.**
3.  **Test**: Run `pytest` with coverage. **Ensure references pass and coverage is maintained (target 85%+).**
4.  **Audit Report**: Generate/Update an audit report (e.g., `docs/AUDIT_REPORT_SRC.md`) documenting findings and fixes. **Loop back to Step 1 if code changes.**
5.  **Final Verification**: Confirm all metrics are met before marking task complete.

---

## 📄 LIVING DOCUMENT GUIDELINES

**This is a living document that must be updated continuously throughout the audit process.**

### Maintenance Rules

1. **Update Progress Continuously**
   - Mark checkboxes `[x]` when items are completed
   - Add completion dates and notes to completed items
   - Update "Last Updated" timestamp at the top
   - Update "Status" field as work progresses

2. **Avoid Duplicates**
   - Before adding new issues, search the document to ensure it doesn't already exist
   - Consolidate related issues into single entries
   - Cross-reference related issues when necessary

3. **Do Not Delete - Mark as Complete**
   - Never delete completed items
   - Mark items as complete with `[x]` and add resolution notes
   - Keep historical context for future reference

4. **Add Details as Discovered**
   - When new issues are found, add them to the appropriate phase
   - Include file paths, line numbers, and severity
   - Link to issue reports when created

5. **Update Metrics**
   - Keep "Progress Tracking" section current
   - Update issue counts as work progresses
   - Track commits and files modified

6. **Synchronize with Roadmap**
   - Update `mockCMMS_roadmap.md` when major phases complete
   - Keep both documents aligned

---

## 🎯 Objectives

> **📚 Best Practices Foundation:** All audit work must follow the comprehensive GitHub and coding best practices outlined in the [mockCMMS Roadmap - Project Infrastructure & Documentation](mockCMMS_roadmap.md#project-infrastructure--documentation) section. This includes Git workflow standards, security practices, code quality standards, and team collaboration guidelines.

1. **Code Organization:** Ensure proper separation of concerns (HTML, CSS, JavaScript)
2. **Code Quality:** Remove duplicates, optimize logic, improve readability
3. **Standards Compliance:** Follow Python PEP 8, JavaScript best practices, CSS conventions, and GitHub workflow standards
4. **Comment Quality:** Professional, descriptive comments (no bug references)
5. **Naming Consistency:** Standardized naming across files, variables, functions, classes
6. **Performance:** Identify and fix performance bottlenecks
7. **Security:** Ensure no security vulnerabilities or bad practices (PAT tokens, 2FA, input validation)
8. **Git Workflow:** Follow feature branch workflow, PR standards, commit message conventions
9. **Repository Standards:** Adhere to naming conventions, documentation standards, dependency management

---

## 📁 Scope: Files to Audit

> **Note:** This audit covers the entire mockCMMS repository EXCEPT the `apps/` directory (planning, reports modules are excluded).
>
> **Future Phases:** At a later stage, we will perform auditing of **ALL** python files, including `run.py` and the `tests/` directory. For now, focus on `src/`.

### Root-Level Files
- [x] `run.py` - Application entry point ✅ Phase 6
- [x] `requirements.txt` - Python dependencies ✅ Phase 6
- [x] `.env.example` - Environment configuration template ✅ Phase 6
- [x] `CHANGELOG.md` - Version history ✅ Phase 6
- [x] `README.md` - Project documentation ✅ Phase 6
- [x] `GEMINI.md` - AI assistant instructions ✅ Phase 6
- [x] `.gitignore` - Git ignore rules ✅ Phase 6

### Configuration Files (`.github/`)
- [x] `.github/copilot-instructions.md` - GitHub Copilot instructions ✅ Phase 6
- [x] `.github/CONTRIBUTING.md` - Contribution guidelines ✅ Phase 6
- [x] `.github/GIT_WORKFLOW.md` - Git workflow documentation ✅ Phase 6
- [x] `.github/CODEOWNERS` - Code ownership definitions ✅ Phase 6
- [x] `.github/PULL_REQUEST_TEMPLATE.md` - PR template ✅ Phase 6
- [x] `.github/ISSUE_TEMPLATE/bug_report.md` - Bug report template ✅ Phase 6
- [x] `.github/ISSUE_TEMPLATE/feature_request.md` - Feature request template ✅ Phase 6
- [x] `.github/ISSUE_TEMPLATE/custom.md` - Custom issue template ✅ Phase 6
- [x] `.github/ISSUE_TEMPLATE/config.yml` - Issue template configuration ✅ Phase 6

### Documentation Files (`docs/`)
- [ ] `docs/mockCMMS_roadmap.md` - Project roadmap
- [ ] `docs/bug_tracking.md` - Bug tracking document
- [ ] `docs/table_features_test_plan.md` - Advanced Table test plan
- [ ] `docs/HOW_TO_UPDATE_ROADMAPS.md` - Roadmap update guide
- [ ] `docs/core_code_quality_plan.md` - This document (self-audit)

### Test Files (`tests/`)
- [x] `tests/conftest.py` - Pytest configuration ✅ Black formatted (Dec 17, 2025)
- [ ] `tests/unit/test_app.py` - App unit tests
- [ ] `tests/unit/test_db_utils.py` - Database utilities tests
- [ ] `tests/unit/test_shift_utils.py` - Shift utilities tests
- [ ] `tests/functional/test_api_routes.py` - API endpoint tests
- [ ] `tests/functional/test_main_routes.py` - Main route tests
- [ ] `tests/integration/test_integration.py` - Integration tests
- [ ] `tests/security/test_auth.py` - Authentication tests
- [ ] `tests/security/test_validation.py` - Validation tests
- [ ] `tests/security/test_advanced_validation.py` - Advanced validation tests
- [ ] `tests/performance/test_performance.py` - Performance tests
- [ ] `tests/reliability/test_errors.py` - Error handling tests

### Test Data (`test_data/`)
- [x] `test_data/dummy_data.json` - Test fixtures ✅ Phase 6

### Scripts (`scripts/`)
- [x] `scripts/setup.ps1` - Setup automation script ✅ Phase 6

### Python Files (`src/`)
- [x] `src/__init__.py` - Package initialization ✅ Phase 1
- [x] `src/app.py` - Flask application factory ✅ Phase 2
- [x] `src/routes/api.py` - REST API endpoints ✅ Phase 2
- [x] `src/routes/main.py` - Web interface routes ✅ Phase 2
- [x] `src/services/__init__.py` - Services package initialization ✅ Phase 1
- [x] `src/services/db_utils.py` - Database utilities ✅ Phase 2
- [x] `src/services/db_seeding.py` - Database seeding helpers ✅ Phase 2
- [x] `src/services/shift_utils.py` - Shift management utilities ✅ Phase 2

### JavaScript Files (`src/static/js/`)
- [ ] `src/static/js/advanced-table/table-core.js`
- [ ] `src/static/js/advanced-table/table-render.js`
- [ ] `src/static/js/advanced-table/table-data.js`
- [ ] `src/static/js/advanced-table/table-config.js`
- [ ] `src/static/js/advanced-table/table-events.js`
- [ ] `src/static/js/advanced-table/table-export.js`
- [ ] `src/static/js/advanced-table/table-init.js`
- [ ] `src/static/js/advanced-table/table-sidebar.js`
- [ ] `src/static/js/advanced-table/table-resize.js`
- [ ] `src/static/js/advanced-table/table-loading.js`
- [ ] `src/static/js/advanced-table/table-retry.js`
- [ ] `src/static/js/toast-notification.js`
- [ ] `src/static/js/flash-messages.js`

### CSS Files (`src/static/css/`)
- [ ] `src/static/css/main.css` - Main application styles
- [ ] `src/static/css/advanced-table.css` - Advanced Table component styles
- [ ] `src/static/css/advanced-table-sidebar.css` - Advanced Table sidebar styles

### HTML Templates (`src/templates/`)
- [ ] `src/templates/base.html` - Base template with common layout
- [ ] `src/templates/index.html` - Dashboard/home page
- [ ] `src/templates/login.html` - Login page
- [ ] `src/templates/assets.html` - Assets list page
- [ ] `src/templates/asset_detail.html` - Asset detail/edit page
- [ ] `src/templates/maintenance_orders.html` - Maintenance orders list
- [ ] `src/templates/maintenance_order_detail.html` - MO detail/edit page
- [ ] `src/templates/maintenance_grid.html` - Maintenance grid view
- [ ] `src/templates/spare_parts.html` - Spare parts list
- [ ] `src/templates/spare_part_detail.html` - Spare part detail/edit page
- [ ] `src/templates/technician_detail.html` - Technician detail/edit page
- [ ] `src/templates/users.html` - Users list page
- [ ] `src/templates/user_detail.html` - User detail/edit page
- [ ] `src/templates/shift_calendar.html` - Shift calendar view
- [ ] `src/templates/planning.html` - Planning page
- [ ] `src/templates/planning_embed.html` - Embedded planning view
- [ ] `src/templates/ticket.html` - Ticket view
- [ ] `src/templates/components/advanced_table.html` - Advanced Table component template

---

## 🤖 Phase 1: Automated Code Quality Analysis (PREREQUISITE)

> [!IMPORTANT]
> **Run BEFORE Manual Audit:** Before starting the detailed manual phase-by-phase audit, run all automated tools to identify issues quickly. This provides a baseline and guides where to focus manual review efforts.

### Why Automated Analysis First?

1. **Faster Issue Detection** - Tools find problems in seconds vs. hours of manual review
2. **Comprehensive Coverage** - Tools analyze entire codebase systematically
3. **Objective Metrics** - Provides quantifiable measurements (complexity scores, coverage %)
4. **Guided Manual Review** - Directs human attention to problem areas
5. **Repeatable** - Can be run continuously in CI/CD

### Automated Tools & What They Verify

| Tool | Purpose | What It Catches | Command |
|------|---------|----------------|---------|
| **ruff** | Fast Python linter | Style violations, unused imports, syntax issues | `ruff check src/` |
| **pylint** | Comprehensive linter | Code smells, complexity, naming issues | `pylint src/` |
| **mypy** | Static type checker | Type errors, logic flow issues | `mypy src/` |
| **radon** | Complexity analyzer | High complexity functions, maintainability index | `radon cc src/ -a` |
| **bandit** | Security scanner | Security vulnerabilities, unsafe patterns | `bandit -r src/` |
| **jscpd** | Duplicate detector | Copy-paste code, similar blocks | `jscpd src/` |
| **pytest --cov** | Coverage analyzer | Untested code paths | `pytest --cov=src tests/` |

### Phase 1 Execution Steps

#### Step 1: Install All Tools

```bash
# Python tools
pip install ruff pylint mypy radon bandit pytest-cov

# JavaScript tools (Node.js required)
npm install -g jscpd eslint
```

#### Step 2: Run Each Tool and Collect Results

```bash
# Create results directory
mkdir -p audit_results

# 1. Ruff - Fast linting
ruff check src/ --output-format=concise > audit_results/ruff_report.txt

# 2. Pylint - Comprehensive linting  
pylint src/ --output-format=text > audit_results/pylint_report.txt

# 3. Mypy - Type checking
mypy src/ --follow-imports=silent --exclude "apps/" > audit_results/mypy_report.txt

# 4. Radon - Complexity analysis
radon cc src/ -a -s > audit_results/radon_complexity.txt
radon mi src/ -s > audit_results/radon_maintainability.txt

# 5. Bandit - Security scanning
bandit -r src/ -f txt -o audit_results/bandit_security.txt

# 6. JSCPD - Duplicate detection
jscpd src/ --reporters json --output audit_results

# 7. Coverage - Test coverage
pytest --cov=src --cov-report=term --cov-report=html:audit_results/coverage_html tests/ > audit_results/coverage_report.txt
```

#### Step 3: Analyze and Prioritize Issues

**Create an issues summary:**

```bash
# Combine all results into summary
cat audit_results/*.txt > audit_results/audit_results_full.txt
```

**Categorize by severity:**

1. **Critical (Fix Immediately)**
   - Security vulnerabilities (bandit)
   - Type errors (mypy)
   - High complexity (radon CC > 15)

2. **High Priority (Fix Soon)**
   - Code duplicates >10 lines (jscpd)
   - Low test coverage (<70%) (pytest-cov)
   - Major pylint violations (scoring < 7.0)

3. **Medium Priority (Fix This Sprint)**
   - Style violations (ruff, pylint)
   - Medium complexity (radon CC 10-15)
   - Maintainability index < 20

4. **Low Priority (Technical Debt)**
   - Minor style issues
   - Missing docstrings
   - Low complexity improvements

#### Step 4: Document Baseline Metrics

**Create `audit_results/baseline_metrics.md`:**

```markdown
# Baseline Code Quality Metrics
**Date:** [Current Date]
**Commit:** [Git SHA]

## Python Code Quality
- **Ruff Issues:** [Count]
- **Pylint Score:** [Score/10]
- **Mypy Errors:** [Count]
- **Average Complexity:** [Score]
- **Maintainability Index:** [Score]
- **Security Issues:** [Count]

## Test Coverage
- **Overall Coverage:** [%]
- **Critical Paths Coverage:** [%]
- **Untested Files:** [Count]

## Code Duplicates
- **Duplicate Blocks:** [Count]
- **Duplicate Lines:** [Count]
- **Duplicate Percentage:** [%]

## Goals (After Audit)
- Ruff: 0 issues
- Pylint: 9.0+/10
- Mypy: 0 errors
- Complexity: <10 average
- Security: 0 issues
- Coverage: >80%
- Duplicates: <2%
```

### Phase 1 Deliverables (Completed Dec 13, 2025)

- [x] **`audit_results/` directory** - All tool outputs ✅
- [x] **`audit_results_full.txt`** - Combined results ✅
- [x] **`baseline_metrics.md`** - Initial measurements ✅
- [x] **`priority_issues.md`** - Categorized issue list ✅
- [x] **All critical/high priority issues fixed** ✅

### Phase 1 Results Summary

**Completion Date:** December 13, 2025

**Final Scores:**
- ✅ **Ruff**: 0 issues (perfect)
- ✅ **Pylint**: 9.15/10 (excellent, improved from 7.10)
- ✅ **Radon**: Average complexity A (2.0)
- ✅ **Bandit**: 0 security issues
- ✅ **Coverage**: 82.99% (target achieved)
- ✅ **Tests**: 210/210 passing (100%)

**Major Refactoring:**
- Refactored `populate_dummy_data()` from E (33) complexity to A (2)
- Created new `db_seeding.py` module with 9 helper functions
- Fixed all style violations and import order issues
- Added comprehensive docstrings to all modules

**Development Tools:**
- Created `requirements-dev.txt` for development dependencies
- Created `docs/DEVELOPMENT_TOOLS.md` usage guide
- Configured `mypy.ini` for type checking
- Disabled pre-commit hooks for Phase 2

### Integration with Manual Phases

**After Phase 1 completion:**

- **Phase 2 (Python Backend)** - Focus on areas flagged by ruff, pylint, mypy, radon, bandit
- **Phase 3 (JavaScript Frontend)** - Focus on areas flagged by eslint, jscpd
- **Phase 4 (CSS)** - Focus on duplicate selectors and unused styles
- **Phase 5 (Templates)** - Focus on areas flagged by duplicate detection
- **Phase 6 (Root Files)** - Focus on configuration and documentation
- **Phase 7 (Cross-Cutting)** - Use metrics to verify improvements

> [!NOTE]
> **Continuous Monitoring:** After initial analysis, add these tools to CI/CD to prevent regression. See Phase 6 for CI integration details.

---

## 🔍 Audit Phases

### Phase 2: Python Backend Analysis ✅ **COMPLETE (December 15, 2025)**
**Focus:** Iterative quality loop per file with one commit per task.
**Strategy:** Each task below represents one file or logical group. Follow the 5-step iterative loop for each task until perfect, then commit before moving to the next task.

---

#### Task 2.1: API Routes (`src/routes/api.py`) ✅ **COMPLETE (December 14, 2025)**

**Step 1: Flake8 Linting**
- [x] Run `flake8 src/routes/api.py` to identify style issues
- [x] Fix any problems found
- [x] Proceed to Step 2

**Step 2: Black Formatting**
- [x] Run `black src/routes/api.py` to auto-format code
- [x] Review changes
- [x] Proceed to Step 3

**Step 3: Test Verification**
- [x] Run `pytest tests/` (verify all 210 tests pass)
- [x] Fix any broken tests
- [x] ✅ **Checkpoint:** After this step, flake8/black/tests should all pass

**Step 4: Manual Audit**
Focus on logic, architecture, and patterns that tools can't catch:
- [x] Verify RESTful conventions (proper HTTP methods, status codes)
- [x] Check input validation and sanitization
- [x] Review error responses and status codes
- [x] Ensure proper authentication/authorization
- [x] Check for duplicate code across endpoints
- [x] Verify proper use of Flask patterns
- [x] Review database query efficiency
- [x] Check for SQL injection vulnerabilities

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [x] Document what was changed and why
- [x] Update any affected tests
- [x] 🔄 **Loop back to Step 1** and repeat until file is perfect

If Step 4 resulted in NO modifications:
- [x] Mark task as COMPLETE ✅
- [x] Commit changes with message: `refactor(api): audit and improve api.py [Phase 2.1]`
- [x] Move to Task 2.2

---

#### Task 2.2: Web Routes (`src/routes/main.py`) ✅ **COMPLETE (December 15, 2025)**

**Step 1: Flake8 Linting**
- [x] Run `flake8 src/routes/main.py` to identify style issues
- [x] Fix any problems found
- [x] Proceed to Step 2

**Step 2: Black Formatting**
- [x] Run `black src/routes/main.py` to auto-format code
- [x] Review changes
- [x] Proceed to Step 3

**Step 3: Test Verification**
- [x] Run `pytest tests/` (verify all 210 tests pass)
- [x] Fix any broken tests
- [x] ✅ **Checkpoint:** After this step, flake8/black/tests should all pass

**Step 4: Manual Audit**
Focus on logic, architecture, and patterns that tools can't catch:
- [x] Review route organization and naming
- [x] Check for duplicate logic between routes
- [x] Verify proper template rendering
- [x] Review form handling and validation
- [x] Check flash message usage
- [x] Verify proper error handling

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [x] Document what was changed and why
- [x] Update any affected tests
- [x] 🔄 **Loop back to Step 1** and repeat until file is perfect

If Step 4 resulted in NO modifications:
- [x] Mark task as COMPLETE ✅
- [x] Commit changes with message: `refactor(routes): audit and improve main.py [Phase 2.2]`
- [x] Move to Task 2.3

---

#### Task 2.3: Database Layer (`src/services/db_utils.py`) ✅ **COMPLETE (December 15, 2025)**

**Step 1: Flake8 Linting**
- [x] Run `flake8 src/services/db_utils.py` to identify style issues
- [x] Fix any problems found
- [x] Proceed to Step 2

**Step 2: Black Formatting**
- [x] Run `black src/services/db_utils.py` to auto-format code
- [x] Review changes
- [x] Proceed to Step 3

**Step 3: Test Verification**
- [x] Run `pytest tests/` (verify all 210 tests pass)
- [x] Fix any broken tests
- [x] ✅ **Checkpoint:** After this step, flake8/black/tests should all pass

**Step 4: Manual Audit**
Focus on logic, architecture, and patterns that tools can't catch:
- [x] Check for SQL injection vulnerabilities
- [x] Review query optimization opportunities
- [x] Verify proper use of SQLAlchemy ORM
- [x] Check for N+1 query problems
- [x] Ensure proper transaction handling
- [x] Review model relationships and constraints

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [x] Document what was changed and why
- [x] Update any affected tests
- [x] 🔄 **Loop back to Step 1** and repeat until file is perfect

If Step 4 resulted in NO modifications:
- [x] Mark task as COMPLETE ✅
- [x] Commit changes with message: `refactor(db): audit and improve db_utils.py [Phase 2.3]`
- [x] Move to Task 2.4

---

#### Task 2.4: Application Core (`src/app.py`) ✅ **COMPLETE (December 15, 2025)**

**Step 1: Flake8 Linting**
- [x] Run `flake8 src/app.py` to identify style issues
- [x] Fix any problems found
- [x] Proceed to Step 2

**Step 2: Black Formatting**
- [x] Run `black src/app.py` to auto-format code
- [x] Review changes
- [x] Proceed to Step 3

**Step 3: Test Verification**
- [x] Run `pytest tests/` (verify all 210 tests pass)
- [x] Fix any broken tests
- [x] ✅ **Checkpoint:** After this step, flake8/black/tests should all pass

**Step 4: Manual Audit**
Focus on logic, architecture, and patterns that tools can't catch:
- [x] Verify Flask factory pattern implementation
- [x] Check blueprint registration
- [x] Review configuration handling
- [x] Verify error handler setup
- [x] Check security settings (SECRET_KEY, etc.)

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [x] Document what was changed and why
- [x] Update any affected tests
- [x] 🔄 **Loop back to Step 1** and repeat until file is perfect

If Step 4 resulted in NO modifications:
- [x] Mark task as COMPLETE ✅
- [x] Commit changes with message: `refactor(app): audit and improve app.py [Phase 2.4]`
- [x] Move to Task 2.5

---

#### Task 2.5: Shift Utilities (`src/services/shift_utils.py`) ✅ **COMPLETE (December 15, 2025)**

**Step 1: Flake8 Linting**
- [x] Run `flake8 src/services/shift_utils.py` to identify style issues
- [x] Fix any problems found
- [x] Proceed to Step 2

**Step 2: Black Formatting**
- [x] Run `black src/services/shift_utils.py` to auto-format code
- [x] Review changes
- [x] Proceed to Step 3

**Step 3: Test Verification**
- [x] Run `pytest tests/` (verify all 210 tests pass)
- [x] Fix any broken tests
- [x] ✅ **Checkpoint:** After this step, flake8/black/tests should all pass

**Step 4: Manual Audit**
Focus on logic, architecture, and patterns that tools can't catch:
- [x] Review business logic correctness
- [x] Check for edge cases
- [x] Verify proper error handling

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [x] Document what was changed and why
- [x] Update any affected tests
- [x] 🔄 **Loop back to Step 1** and repeat until file is perfect

If Step 4 resulted in NO modifications:
- [x] Mark task as COMPLETE ✅
- [x] Commit changes with message: `refactor(services): audit and improve shift_utils.py [Phase 2.5]`
- [x] Move to Task 2.6

---

#### Task 2.6: Database Seeding (`src/services/db_seeding.py`) ✅ **COMPLETE (December 15, 2025)**

**Step 1: Flake8 Linting**
- [x] Run `flake8 src/services/db_seeding.py` to identify style issues
- [x] Fix any problems found
- [x] Proceed to Step 2

**Step 2: Black Formatting**
- [x] Run `black src/services/db_seeding.py` to auto-format code
- [x] Review changes
- [x] Proceed to Step 3

**Step 3: Test Verification**
- [x] Run `pytest tests/` (verify all 210 tests pass)
- [x] Fix any broken tests
- [x] ✅ **Checkpoint:** After this step, flake8/black/tests should all pass

**Step 4: Manual Audit**
Focus on logic, architecture, and patterns that tools can't catch:
- [x] Review business logic correctness
- [x] Check for edge cases
- [x] Verify proper error handling

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [x] Document what was changed and why
- [x] Update any affected tests
- [x] 🔄 **Loop back to Step 1** and repeat until file is perfect

If Step 4 resulted in NO modifications:
- [x] Mark task as COMPLETE ✅
- [x] Commit changes with message: `refactor(services): audit and improve db_seeding.py [Phase 2.6]`
- [x] Move to Phase 2 Final Verification

---

#### Phase 2 Final Verification (After All Tasks Complete)
- [x] Run `ruff check src/` (verify 0 issues)
- [x] Run `pylint src/` (verify 9.0+ score)
- [x] Run `pytest --cov=src tests/` (verify 82.99%+ coverage)
- [x] Update `audit_results/baseline_metrics.md` with final scores
- [x] Document all findings in audit report
- [x] Mark Phase 2 COMPLETE ✅

**Deliverable:** Formatted, audited Python codebase with documented findings (6 commits total)

---

### Phase 3: JavaScript Frontend Analysis
**Focus:** Iterative quality loop per file with one commit per task.
**Strategy:** Each task below represents one file or logical group. Follow the 5-step iterative loop for each task until perfect, then commit before moving to the next task.

---

#### Task 3.1: Advanced Table Core (`src/static/js/advanced-table/table-core.js`)

**Step 1: ESLint Linting**
- [ ] Run `eslint src/static/js/advanced-table/table-core.js` to identify code quality issues
- [ ] Fix any problems found (style, unused vars, etc.)
- [ ] Proceed to Step 2

**Step 2: Prettier Formatting**
- [ ] Run `prettier --write src/static/js/advanced-table/table-core.js` to auto-format code
- [ ] Review changes for consistency
- [ ] Proceed to Step 3

**Step 3: Browser Testing**
- [ ] Load application in browser
- [ ] Test Advanced Table functionality
- [ ] Check browser console for errors
- [ ] Verify no JavaScript exceptions
- [ ] ✅ **Checkpoint:** After this step, ESLint/Prettier/browser tests should all pass

**Step 4: Manual Audit**
Focus on architecture, logic, and patterns that tools can't catch:
- [ ] Review module organization and dependencies
- [ ] Check for circular dependencies
- [ ] Verify proper encapsulation and class structure
- [ ] Review initialization patterns
- [ ] Check for memory leaks (event listener cleanup)
- [ ] Consistent naming conventions (camelCase)
- [ ] Proper use of `const`, `let` (no `var`)
- [ ] Arrow functions vs regular functions consistency
- [ ] Remove `console.log()` statements
- [ ] Remove bug reference comments (e.g., `// Bug #5`)
- [ ] Add JSDoc comments for public methods
- [ ] Remove commented-out code blocks

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [ ] Document what was changed and why
- [ ] Update any affected browser tests
- [ ] 🔄 **Loop back to Step 1** and repeat until file is perfect

If Step 4 resulted in NO modifications:
- [ ] Mark task as COMPLETE ✅
- [ ] Commit changes with message: `refactor(table): audit and improve table-core.js [Phase 3.1]`
- [ ] Move to Task 3.2

---

#### Task 3.2: Advanced Table Init (`src/static/js/advanced-table/table-init.js`)

**Step 1: ESLint Linting**
- [ ] Run `eslint src/static/js/advanced-table/table-init.js` to identify code quality issues
- [ ] Fix any problems found (style, unused vars, etc.)
- [ ] Proceed to Step 2

**Step 2: Prettier Formatting**
- [ ] Run `prettier --write src/static/js/advanced-table/table-init.js` to auto-format code
- [ ] Review changes for consistency
- [ ] Proceed to Step 3

**Step 3: Browser Testing**
- [ ] Load application in browser
- [ ] Test Advanced Table initialization
- [ ] Check browser console for errors
- [ ] Verify no JavaScript exceptions
- [ ] ✅ **Checkpoint:** After this step, ESLint/Prettier/browser tests should all pass

**Step 4: Manual Audit**
Focus on architecture, logic, and patterns that tools can't catch:
- [ ] Review module organization and dependencies
- [ ] Check for circular dependencies
- [ ] Verify proper encapsulation and class structure
- [ ] Review initialization patterns
- [ ] Check for memory leaks (event listener cleanup)
- [ ] Consistent naming conventions (camelCase)
- [ ] Proper use of `const`, `let` (no `var`)
- [ ] Arrow functions vs regular functions consistency
- [ ] Remove `console.log()` statements
- [ ] Remove bug reference comments (e.g., `// Bug #5`)
- [ ] Add JSDoc comments for public methods
- [ ] Remove commented-out code blocks

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [ ] Document what was changed and why
- [ ] Update any affected browser tests
- [ ] 🔄 **Loop back to Step 1** and repeat until file is perfect

If Step 4 resulted in NO modifications:
- [ ] Mark task as COMPLETE ✅
- [ ] Commit changes with message: `refactor(table): audit and improve table-init.js [Phase 3.2]`
- [ ] Move to Task 3.3

---

#### Task 3.3: Table Rendering (`src/static/js/advanced-table/table-render.js`)

**Step 1: ESLint Linting**
- [ ] Run `eslint src/static/js/advanced-table/table-render.js` to identify code quality issues
- [ ] Fix any problems found (style, unused vars, etc.)
- [ ] Proceed to Step 2

**Step 2: Prettier Formatting**
- [ ] Run `prettier --write src/static/js/advanced-table/table-render.js` to auto-format code
- [ ] Review changes for consistency
- [ ] Proceed to Step 3

**Step 3: Browser Testing**
- [ ] Load application in browser
- [ ] Test table rendering functionality
- [ ] Check browser console for errors
- [ ] Verify no JavaScript exceptions
- [ ] ✅ **Checkpoint:** After this step, ESLint/Prettier/browser tests should all pass

**Step 4: Manual Audit**
Focus on architecture, logic, and patterns that tools can't catch:
- [ ] Review DOM manipulation efficiency
- [ ] Check for unnecessary re-renders
- [ ] Verify proper use of event delegation
- [ ] Review template string usage
- [ ] Check for duplicate rendering logic
- [ ] Consistent naming conventions (camelCase)
- [ ] Proper use of `const`, `let` (no `var`)
- [ ] Arrow functions vs regular functions consistency
- [ ] Remove `console.log()` statements
- [ ] Remove bug reference comments (e.g., `// Bug #5`)
- [ ] Add JSDoc comments for public methods
- [ ] Remove commented-out code blocks

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [ ] Document what was changed and why
- [ ] Update any affected browser tests
- [ ] 🔄 **Loop back to Step 1** and repeat until file is perfect

If Step 4 resulted in NO modifications:
- [ ] Mark task as COMPLETE ✅
- [ ] Commit changes with message: `refactor(table): audit and improve table-render.js [Phase 3.3]`
- [ ] Move to Task 3.4

---

#### Task 3.4: Table Sidebar (`src/static/js/advanced-table/table-sidebar.js`)

**Step 1: ESLint Linting**
- [ ] Run `eslint src/static/js/advanced-table/table-sidebar.js` to identify code quality issues
- [ ] Fix any problems found (style, unused vars, etc.)
- [ ] Proceed to Step 2

**Step 2: Prettier Formatting**
- [ ] Run `prettier --write src/static/js/advanced-table/table-sidebar.js` to auto-format code
- [ ] Review changes for consistency
- [ ] Proceed to Step 3

**Step 3: Browser Testing**
- [ ] Load application in browser
- [ ] Test table sidebar functionality
- [ ] Check browser console for errors
- [ ] Verify no JavaScript exceptions
- [ ] ✅ **Checkpoint:** After this step, ESLint/Prettier/browser tests should all pass

**Step 4: Manual Audit**
Focus on architecture, logic, and patterns that tools can't catch:
- [ ] Review DOM manipulation efficiency
- [ ] Check for unnecessary re-renders
- [ ] Verify proper use of event delegation
- [ ] Review template string usage
- [ ] Check for duplicate rendering logic
- [ ] Consistent naming conventions (camelCase)
- [ ] Proper use of `const`, `let` (no `var`)
- [ ] Arrow functions vs regular functions consistency
- [ ] Remove `console.log()` statements
- [ ] Remove bug reference comments (e.g., `// Bug #5`)
- [ ] Add JSDoc comments for public methods
- [ ] Remove commented-out code blocks

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [ ] Document what was changed and why
- [ ] Update any affected browser tests
- [ ] 🔄 **Loop back to Step 1** and repeat until file is perfect

If Step 4 resulted in NO modifications:
- [ ] Mark task as COMPLETE ✅
- [ ] Commit changes with message: `refactor(table): audit and improve table-sidebar.js [Phase 3.4]`
- [ ] Move to Task 3.5

---

#### Task 3.5: Table Resize (`src/static/js/advanced-table/table-resize.js`)

**Step 1: ESLint Linting**
- [ ] Run `eslint src/static/js/advanced-table/table-resize.js` to identify code quality issues
- [ ] Fix any problems found (style, unused vars, etc.)
- [ ] Proceed to Step 2

**Step 2: Prettier Formatting**
- [ ] Run `prettier --write src/static/js/advanced-table/table-resize.js` to auto-format code
- [ ] Review changes for consistency
- [ ] Proceed to Step 3

**Step 3: Browser Testing**
- [ ] Load application in browser
- [ ] Test table column resizing functionality
- [ ] Check browser console for errors
- [ ] Verify no JavaScript exceptions
- [ ] ✅ **Checkpoint:** After this step, ESLint/Prettier/browser tests should all pass

**Step 4: Manual Audit**
Focus on architecture, logic, and patterns that tools can't catch:
- [ ] Review DOM manipulation efficiency
- [ ] Check for unnecessary re-renders
- [ ] Verify proper use of event delegation
- [ ] Review template string usage
- [ ] Check for duplicate rendering logic
- [ ] Consistent naming conventions (camelCase)
- [ ] Proper use of `const`, `let` (no `var`)
- [ ] Arrow functions vs regular functions consistency
- [ ] Remove `console.log()` statements
- [ ] Remove bug reference comments (e.g., `// Bug #5`)
- [ ] Add JSDoc comments for public methods
- [ ] Remove commented-out code blocks

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [ ] Document what was changed and why
- [ ] Update any affected browser tests
- [ ] 🔄 **Loop back to Step 1** and repeat until file is perfect

If Step 4 resulted in NO modifications:
- [ ] Mark task as COMPLETE ✅
- [ ] Commit changes with message: `refactor(table): audit and improve table-resize.js [Phase 3.5]`
- [ ] Move to Task 3.6

---

#### Task 3.6: Table Data Management (`src/static/js/advanced-table/table-data.js`)

**Step 1: ESLint Linting**
- [ ] Run `eslint src/static/js/advanced-table/table-data.js` to identify code quality issues
- [ ] Fix any problems found (style, unused vars, etc.)
- [ ] Proceed to Step 2

**Step 2: Prettier Formatting**
- [ ] Run `prettier --write src/static/js/advanced-table/table-data.js` to auto-format code
- [ ] Review changes for consistency
- [ ] Proceed to Step 3

**Step 3: Browser Testing**
- [ ] Load application in browser
- [ ] Test table data filtering and sorting
- [ ] Check browser console for errors
- [ ] Verify no JavaScript exceptions
- [ ] ✅ **Checkpoint:** After this step, ESLint/Prettier/browser tests should all pass

**Step 4: Manual Audit**
Focus on architecture, logic, and patterns that tools can't catch:
- [ ] Review data filtering and sorting logic
- [ ] Check for efficient data structures
- [ ] Verify proper state management
- [ ] Consistent naming conventions (camelCase)
- [ ] Proper use of `const`, `let` (no `var`)
- [ ] Arrow functions vs regular functions consistency
- [ ] Remove `console.log()` statements
- [ ] Remove bug reference comments (e.g., `// Bug #5`)
- [ ] Add JSDoc comments for public methods
- [ ] Remove commented-out code blocks

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [ ] Document what was changed and why
- [ ] Update any affected browser tests
- [ ] 🔄 **Loop back to Step 1** and repeat until file is perfect

If Step 4 resulted in NO modifications:
- [ ] Mark task as COMPLETE ✅
- [ ] Commit changes with message: `refactor(table): audit and improve table-data.js [Phase 3.6]`
- [ ] Move to Task 3.7

---

#### Task 3.7: Table Configuration (`src/static/js/advanced-table/table-config.js`)

**Step 1: ESLint Linting**
- [ ] Run `eslint src/static/js/advanced-table/table-config.js` to identify code quality issues
- [ ] Fix any problems found (style, unused vars, etc.)
- [ ] Proceed to Step 2

**Step 2: Prettier Formatting**
- [ ] Run `prettier --write src/static/js/advanced-table/table-config.js` to auto-format code
- [ ] Review changes for consistency
- [ ] Proceed to Step 3

**Step 3: Browser Testing**
- [ ] Load application in browser
- [ ] Test table configuration save/load
- [ ] Check browser console for errors
- [ ] Verify no JavaScript exceptions
- [ ] ✅ **Checkpoint:** After this step, ESLint/Prettier/browser tests should all pass

**Step 4: Manual Audit**
Focus on architecture, logic, and patterns that tools can't catch:
- [ ] Review configuration persistence
- [ ] Check for efficient data structures
- [ ] Verify proper state management
- [ ] Consistent naming conventions (camelCase)
- [ ] Proper use of `const`, `let` (no `var`)
- [ ] Arrow functions vs regular functions consistency
- [ ] Remove `console.log()` statements
- [ ] Remove bug reference comments (e.g., `// Bug #5`)
- [ ] Add JSDoc comments for public methods
- [ ] Remove commented-out code blocks

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [ ] Document what was changed and why
- [ ] Update any affected browser tests
- [ ] 🔄 **Loop back to Step 1** and repeat until file is perfect

If Step 4 resulted in NO modifications:
- [ ] Mark task as COMPLETE ✅
- [ ] Commit changes with message: `refactor(table): audit and improve table-config.js [Phase 3.7]`
- [ ] Move to Task 3.8

---

#### Task 3.8: Table Export (`src/static/js/advanced-table/table-export.js`)

**Step 1: ESLint Linting**
- [ ] Run `eslint src/static/js/advanced-table/table-export.js` to identify code quality issues
- [ ] Fix any problems found (style, unused vars, etc.)
- [ ] Proceed to Step 2

**Step 2: Prettier Formatting**
- [ ] Run `prettier --write src/static/js/advanced-table/table-export.js` to auto-format code
- [ ] Review changes for consistency
- [ ] Proceed to Step 3

**Step 3: Browser Testing**
- [ ] Load application in browser
- [ ] Test table CSV export functionality
- [ ] Check browser console for errors
- [ ] Verify no JavaScript exceptions
- [ ] ✅ **Checkpoint:** After this step, ESLint/Prettier/browser tests should all pass

**Step 4: Manual Audit**
Focus on architecture, logic, and patterns that tools can't catch:
- [ ] Check export functionality correctness
- [ ] Review data formatting logic
- [ ] Verify proper error handling
- [ ] Consistent naming conventions (camelCase)
- [ ] Proper use of `const`, `let` (no `var`)
- [ ] Arrow functions vs regular functions consistency
- [ ] Remove `console.log()` statements
- [ ] Remove bug reference comments (e.g., `// Bug #5`)
- [ ] Add JSDoc comments for public methods
- [ ] Remove commented-out code blocks

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [ ] Document what was changed and why
- [ ] Update any affected browser tests
- [ ] 🔄 **Loop back to Step 1** and repeat until file is perfect

If Step 4 resulted in NO modifications:
- [ ] Mark task as COMPLETE ✅
- [ ] Commit changes with message: `refactor(table): audit and improve table-export.js [Phase 3.8]`
- [ ] Move to Task 3.9

---

#### Task 3.9: Table Events (`src/static/js/advanced-table/table-events.js`)

**Step 1: ESLint Linting**
- [ ] Run `eslint src/static/js/advanced-table/table-events.js` to identify code quality issues
- [ ] Fix any problems found (style, unused vars, etc.)
- [ ] Proceed to Step 2

**Step 2: Prettier Formatting**
- [ ] Run `prettier --write src/static/js/advanced-table/table-events.js` to auto-format code
- [ ] Review changes for consistency
- [ ] Proceed to Step 3

**Step 3: Browser Testing**
- [ ] Load application in browser
- [ ] Test table event handling
- [ ] Check browser console for errors
- [ ] Verify no JavaScript exceptions
- [ ] ✅ **Checkpoint:** After this step, ESLint/Prettier/browser tests should all pass

**Step 4: Manual Audit**
Focus on architecture, logic, and patterns that tools can't catch:
- [ ] Review event handling patterns
- [ ] Check for proper error handling (try-catch)
- [ ] Check for race conditions
- [ ] Verify proper event delegation
- [ ] Check for memory leaks (event listener cleanup)
- [ ] Consistent naming conventions (camelCase)
- [ ] Proper use of `const`, `let` (no `var`)
- [ ] Arrow functions vs regular functions consistency
- [ ] Remove `console.log()` statements
- [ ] Remove bug reference comments (e.g., `// Bug #5`)
- [ ] Add JSDoc comments for public methods
- [ ] Remove commented-out code blocks

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [ ] Document what was changed and why
- [ ] Update any affected browser tests
- [ ] 🔄 **Loop back to Step 1** and repeat until file is perfect

If Step 4 resulted in NO modifications:
- [ ] Mark task as COMPLETE ✅
- [ ] Commit changes with message: `refactor(table): audit and improve table-events.js [Phase 3.9]`
- [ ] Move to Task 3.10

---

#### Task 3.10: Table Loading (`src/static/js/advanced-table/table-loading.js`)

**Step 1: ESLint Linting**
- [ ] Run `eslint src/static/js/advanced-table/table-loading.js` to identify code quality issues
- [ ] Fix any problems found (style, unused vars, etc.)
- [ ] Proceed to Step 2

**Step 2: Prettier Formatting**
- [ ] Run `prettier --write src/static/js/advanced-table/table-loading.js` to auto-format code
- [ ] Review changes for consistency
- [ ] Proceed to Step 3

**Step 3: Browser Testing**
- [ ] Load application in browser
- [ ] Test table loading states
- [ ] Check browser console for errors
- [ ] Verify no JavaScript exceptions
- [ ] ✅ **Checkpoint:** After this step, ESLint/Prettier/browser tests should all pass

**Step 4: Manual Audit**
Focus on architecture, logic, and patterns that tools can't catch:
- [ ] Review loading state management
- [ ] Check for proper error handling (try-catch)
- [ ] Verify timing and state transitions
- [ ] Check for race conditions
- [ ] Consistent naming conventions (camelCase)
- [ ] Proper use of `const`, `let` (no `var`)
- [ ] Arrow functions vs regular functions consistency
- [ ] Remove `console.log()` statements
- [ ] Remove bug reference comments (e.g., `// Bug #5`)
- [ ] Add JSDoc comments for public methods
- [ ] Remove commented-out code blocks

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [ ] Document what was changed and why
- [ ] Update any affected browser tests
- [ ] 🔄 **Loop back to Step 1** and repeat until file is perfect

If Step 4 resulted in NO modifications:
- [ ] Mark task as COMPLETE ✅
- [ ] Commit changes with message: `refactor(table): audit and improve table-loading.js [Phase 3.10]`
- [ ] Move to Task 3.11

---

#### Task 3.11: Table Retry (`src/static/js/advanced-table/table-retry.js`)

**Step 1: ESLint Linting**
- [ ] Run `eslint src/static/js/advanced-table/table-retry.js` to identify code quality issues
- [ ] Fix any problems found (style, unused vars, etc.)
- [ ] Proceed to Step 2

**Step 2: Prettier Formatting**
- [ ] Run `prettier --write src/static/js/advanced-table/table-retry.js` to auto-format code
- [ ] Review changes for consistency
- [ ] Proceed to Step 3

**Step 3: Browser Testing**
- [ ] Load application in browser
- [ ] Test table retry logic
- [ ] Check browser console for errors
- [ ] Verify no JavaScript exceptions
- [ ] ✅ **Checkpoint:** After this step, ESLint/Prettier/browser tests should all pass

**Step 4: Manual Audit**
Focus on architecture, logic, and patterns that tools can't catch:
- [ ] Verify retry logic with exponential backoff
- [ ] Check for proper error handling (try-catch)
- [ ] Review timing and backoff calculations
- [ ] Check for race conditions
- [ ] Consistent naming conventions (camelCase)
- [ ] Proper use of `const`, `let` (no `var`)
- [ ] Arrow functions vs regular functions consistency
- [ ] Remove `console.log()` statements
- [ ] Remove bug reference comments (e.g., `// Bug #5`)
- [ ] Add JSDoc comments for public methods
- [ ] Remove commented-out code blocks

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [ ] Document what was changed and why
- [ ] Update any affected browser tests
- [ ] 🔄 **Loop back to Step 1** and repeat until file is perfect

If Step 4 resulted in NO modifications:
- [ ] Mark task as COMPLETE ✅
- [ ] Commit changes with message: `refactor(table): audit and improve table-retry.js [Phase 3.11]`
- [ ] Move to Task 3.12

---

#### Task 3.12: Toast Notification (`src/static/js/toast-notification.js`)

**Step 1: ESLint Linting**
- [ ] Run `eslint src/static/js/toast-notification.js` to identify code quality issues
- [ ] Fix any problems found (style, unused vars, etc.)
- [ ] Proceed to Step 2

**Step 2: Prettier Formatting**
- [ ] Run `prettier --write src/static/js/toast-notification.js` to auto-format code
- [ ] Review changes for consistency
- [ ] Proceed to Step 3

**Step 3: Browser Testing**
- [ ] Load application in browser
- [ ] Test toast notification functionality
- [ ] Check browser console for errors
- [ ] Verify no JavaScript exceptions
- [ ] ✅ **Checkpoint:** After this step, ESLint/Prettier/browser tests should all pass

**Step 4: Manual Audit**
Focus on architecture, logic, and patterns that tools can't catch:
- [ ] Review component API design
- [ ] Check for proper error handling
- [ ] Verify browser compatibility (ES6+ features)
- [ ] Review timing and auto-dismiss logic
- [ ] Consistent naming conventions (camelCase)
- [ ] Proper use of `const`, `let` (no `var`)
- [ ] Arrow functions vs regular functions consistency
- [ ] Remove `console.log()` statements
- [ ] Remove bug reference comments (e.g., `// Bug #5`)
- [ ] Add JSDoc comments for public methods
- [ ] Remove commented-out code blocks

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [ ] Document what was changed and why
- [ ] Update any affected browser tests
- [ ] 🔄 **Loop back to Step 1** and repeat until file is perfect

If Step 4 resulted in NO modifications:
- [ ] Mark task as COMPLETE ✅
- [ ] Commit changes with message: `refactor(ui): audit and improve toast-notification.js [Phase 3.12]`
- [ ] Move to Task 3.13

---

#### Task 3.13: Flash Messages (`src/static/js/flash-messages.js`)

**Step 1: ESLint Linting**
- [ ] Run `eslint src/static/js/flash-messages.js` to identify code quality issues
- [ ] Fix any problems found (style, unused vars, etc.)
- [ ] Proceed to Step 2

**Step 2: Prettier Formatting**
- [ ] Run `prettier --write src/static/js/flash-messages.js` to auto-format code
- [ ] Review changes for consistency
- [ ] Proceed to Step 3

**Step 3: Browser Testing**
- [ ] Load application in browser
- [ ] Test flash message functionality
- [ ] Check browser console for errors
- [ ] Verify no JavaScript exceptions
- [ ] ✅ **Checkpoint:** After this step, ESLint/Prettier/browser tests should all pass

**Step 4: Manual Audit**
Focus on architecture, logic, and patterns that tools can't catch:
- [ ] Review component API design
- [ ] Check for proper error handling
- [ ] Verify browser compatibility (ES6+ features)
- [ ] Review Flask flash message integration
- [ ] Consistent naming conventions (camelCase)
- [ ] Proper use of `const`, `let` (no `var`)
- [ ] Arrow functions vs regular functions consistency
- [ ] Remove `console.log()` statements
- [ ] Remove bug reference comments (e.g., `// Bug #5`)
- [ ] Add JSDoc comments for public methods
- [ ] Remove commented-out code blocks

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [ ] Document what was changed and why
- [ ] Update any affected browser tests
- [ ] 🔄 **Loop back to Step 1** and repeat until file is perfect

If Step 4 resulted in NO modifications:
- [ ] Mark task as COMPLETE ✅
- [ ] Commit changes with message: `refactor(ui): audit and improve flash-messages.js [Phase 3.13]`
- [ ] Move to Phase 3 Final Verification

---

#### Phase 3 Final Verification (After All Tasks Complete)
- [ ] Run `eslint src/static/js/` (verify 0 errors)
- [ ] Test all JavaScript functionality in browser
- [ ] Check browser console for any warnings/errors
- [ ] Verify no memory leaks (DevTools Memory profiler)
- [ ] Document all findings in audit report
- [ ] Mark Phase 3 COMPLETE ✅

**Deliverable:** Formatted, audited JavaScript codebase with documented findings (13 commits total)

---

### Phase 4: CSS Styling Analysis
**Focus:** Iterative quality loop per file with one commit per task.
**Strategy:** Each task below represents one file or logical group. Follow the 5-step iterative loop for each task until perfect, then commit before moving to the next task.

---

#### Task 4.1: Main Styles (`src/static/css/main.css`)

**Step 1: Stylelint Linting**
- [ ] Run `stylelint src/static/css/main.css` to identify CSS issues
- [ ] Fix any problems found (syntax, order, etc.)
- [ ] Proceed to Step 2

**Step 2: Prettier Formatting**
- [ ] Run `prettier --write src/static/css/main.css` to auto-format CSS
- [ ] Review changes for consistency
- [ ] Proceed to Step 3

**Step 3: Visual Testing**
- [ ] Load application in browser
- [ ] Verify styles render correctly
- [ ] Test responsive breakpoints
- [ ] Check for visual regressions
- [ ] ✅ **Checkpoint:** After this step, Stylelint/Prettier/visual tests should all pass

**Step 4: Manual Audit**
Focus on organization, optimization, and patterns that tools can't catch:
- [ ] Review file structure and organization
- [ ] Check for logical grouping of styles
- [ ] Verify proper use of CSS custom properties (variables)
- [ ] Review color consistency (use variables)
- [ ] Check for magic numbers (use named variables)
- [ ] Remove duplicate styles
- [ ] Check for unused CSS rules
- [ ] Verify proper specificity (avoid `!important` overuse)
- [ ] Review selector performance

**Responsive Design:**
- [ ] Verify mobile-first approach
- [ ] Check breakpoint consistency
- [ ] Review media query organization
- [ ] Test on multiple screen sizes

**Performance & Optimization:**
- [ ] Remove unused vendor prefixes
- [ ] Optimize selectors for performance
- [ ] Check for CSS that could be simplified
- [ ] Verify efficient use of inheritance

**Naming Conventions:**
- [ ] Consistent naming (BEM, kebab-case, etc.)
- [ ] Remove bug reference comments
- [ ] Ensure comments are descriptive

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [ ] Document what was changed and why
- [ ] Update any affected visual tests
- [ ] 🔄 **Loop back to Step 1** and repeat until file is perfect

If Step 4 resulted in NO modifications:
- [ ] Mark task as COMPLETE ✅
- [ ] Commit changes with message: `refactor(css): audit and improve main.css [Phase 4.1]`
- [ ] Move to Task 4.2

---

#### Task 4.2: Advanced Table Styles (`src/static/css/advanced-table.css`)

**Step 1: Stylelint Linting**
- [ ] Run `stylelint src/static/css/advanced-table.css` to identify CSS issues
- [ ] Fix any problems found (syntax, order, etc.)
- [ ] Proceed to Step 2

**Step 2: Prettier Formatting**
- [ ] Run `prettier --write src/static/css/advanced-table.css` to auto-format CSS
- [ ] Review changes for consistency
- [ ] Proceed to Step 3

**Step 3: Visual Testing**
- [ ] Load application in browser
- [ ] Verify table styles render correctly
- [ ] Test responsive breakpoints
- [ ] Check for visual regressions
- [ ] ✅ **Checkpoint:** After this step, Stylelint/Prettier/visual tests should all pass

**Step 4: Manual Audit**
Focus on organization, optimization, and patterns that tools can't catch:
- [ ] Review component-specific organization
- [ ] Check for unused CSS rules
- [ ] Verify proper specificity (avoid `!important` overuse)
- [ ] Review selector performance
- [ ] Check for duplicate selectors
- [ ] Verify proper use of CSS custom properties (variables)
- [ ] Review color consistency (use variables)
- [ ] Check for magic numbers (use named variables)

**Responsive Design:**
- [ ] Verify mobile-first approach
- [ ] Check breakpoint consistency
- [ ] Review media query organization
- [ ] Test on multiple screen sizes

**Performance & Optimization:**
- [ ] Remove unused vendor prefixes
- [ ] Optimize selectors for performance
- [ ] Check for CSS that could be simplified
- [ ] Verify efficient use of inheritance

**Naming Conventions:**
- [ ] Consistent naming (BEM, kebab-case, etc.)
- [ ] Remove bug reference comments
- [ ] Ensure comments are descriptive

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [ ] Document what was changed and why
- [ ] Update any affected visual tests
- [ ] 🔄 **Loop back to Step 1** and repeat until file is perfect

If Step 4 resulted in NO modifications:
- [ ] Mark task as COMPLETE ✅
- [ ] Commit changes with message: `refactor(css): audit and improve advanced-table.css [Phase 4.2]`
- [ ] Move to Task 4.3

---

#### Task 4.3: Advanced Table Sidebar Styles (`src/static/css/advanced-table-sidebar.css`)

**Step 1: Stylelint Linting**
- [ ] Run `stylelint src/static/css/advanced-table-sidebar.css` to identify CSS issues
- [ ] Fix any problems found (syntax, order, etc.)
- [ ] Proceed to Step 2

**Step 2: Prettier Formatting**
- [ ] Run `prettier --write src/static/css/advanced-table-sidebar.css` to auto-format CSS
- [ ] Review changes for consistency
- [ ] Proceed to Step 3

**Step 3: Visual Testing**
- [ ] Load application in browser
- [ ] Verify sidebar styles render correctly
- [ ] Test responsive breakpoints
- [ ] Check for visual regressions
- [ ] ✅ **Checkpoint:** After this step, Stylelint/Prettier/visual tests should all pass

**Step 4: Manual Audit**
Focus on organization, optimization, and patterns that tools can't catch:
- [ ] Review component-specific organization
- [ ] Check for unused CSS rules
- [ ] Verify proper specificity (avoid `!important` overuse)
- [ ] Review selector performance
- [ ] Check for duplicate selectors
- [ ] Verify proper use of CSS custom properties (variables)
- [ ] Review color consistency (use variables)
- [ ] Check for magic numbers (use named variables)

**Responsive Design:**
- [ ] Verify mobile-first approach
- [ ] Check breakpoint consistency
- [ ] Review media query organization
- [ ] Test on multiple screen sizes

**Performance & Optimization:**
- [ ] Remove unused vendor prefixes
- [ ] Optimize selectors for performance
- [ ] Check for CSS that could be simplified
- [ ] Verify efficient use of inheritance

**Naming Conventions:**
- [ ] Consistent naming (BEM, kebab-case, etc.)
- [ ] Remove bug reference comments
- [ ] Ensure comments are descriptive

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [ ] Document what was changed and why
- [ ] Update any affected visual tests
- [ ] 🔄 **Loop back to Step 1** and repeat until file is perfect

If Step 4 resulted in NO modifications:
- [ ] Mark task as COMPLETE ✅
- [ ] Commit changes with message: `refactor(css): audit and improve advanced-table-sidebar.css [Phase 4.3]`
- [ ] Move to Phase 4 Final Verification

---

#### Phase 4 Final Verification (After All Tasks Complete)
- [ ] Run `stylelint src/static/css/` (verify 0 errors)
- [ ] Visual regression test on all pages
- [ ] Test responsive design on multiple devices
- [ ] Verify no unused CSS (coverage tools)
- [ ] Document all findings in audit report
- [ ] Mark Phase 4 COMPLETE ✅

**Deliverable:** Formatted, audited CSS codebase with documented findings (3 commits total)

---

### Phase 5: HTML Templates Analysis
**Focus:** Iterative quality loop per file with one commit per task.
**Strategy:** Each task below represents one file or logical group. Follow the 5-step iterative loop for each task until perfect, then commit before moving to the next task.

---

#### Task 5.1: Base Template (`src/templates/base.html`)

**Step 1: HTML Validation**
- [ ] Run HTML validator (W3C or `html-validate`) on rendered output
- [ ] Fix any syntax errors or warnings
- [ ] Proceed to Step 2

**Step 2: Prettier Formatting**
- [ ] Run `prettier --write src/templates/base.html` to auto-format HTML
- [ ] Review changes for consistency
- [ ] Proceed to Step 3

**Step 3: Render Testing**
- [ ] Load page in browser
- [ ] Verify template renders correctly
- [ ] Test all dynamic content
- [ ] Check for template errors in Flask logs
- [ ] ✅ **Checkpoint:** After this step, validation/formatting/rendering should all pass

**Step 4: Manual Audit**
Focus on structure, accessibility, and patterns that tools can't catch:
- [ ] Review Jinja2 template inheritance structure
- [ ] Check for proper block definitions
- [ ] Verify meta tags and SEO elements
- [ ] Review script/style loading order

**Separation of Concerns:**
- [ ] Identify inline JavaScript (`<script>` blocks in template)
- [ ] Identify inline CSS (`<style>` blocks in template)
- [ ] Identify inline styles (`style="..."` attributes)
- [ ] Identify inline event handlers (`onclick="..."` attributes)
- [ ] Create extraction plan for each violation

**HTML Quality & Standards:**
- [ ] Semantic HTML usage (header, nav, main, section, article)
- [ ] Proper heading hierarchy (h1, h2, h3...)
- [ ] Accessibility (ARIA labels, alt text, role attributes)
- [ ] Form accessibility (labels, fieldsets, error messages)
- [ ] Remove commented-out HTML blocks
- [ ] Remove bug reference comments (e.g., `<!-- Bug #5 -->`)

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [ ] Document what was changed and why
- [ ] Update any affected render tests
- [ ] Extract inline code to separate files if needed
- [ ] 🔄 **Loop back to Step 1** and repeat until file is perfect

If Step 4 resulted in NO modifications:
- [ ] Mark task as COMPLETE ✅
- [ ] Commit changes with message: `refactor(templates): audit and improve base.html [Phase 5.1]`
- [ ] Move to Task 5.2

---

#### Task 5.2: Assets List Page (`src/templates/assets.html`)

**Step 1: HTML Validation**
- [ ] Run HTML validator on rendered output
- [ ] Fix any syntax errors or warnings
- [ ] Proceed to Step 2

**Step 2: Prettier Formatting**
- [ ] Run `prettier --write src/templates/assets.html` to auto-format HTML
- [ ] Review changes for consistency
- [ ] Proceed to Step 3

**Step 3: Render Testing**
- [ ] Load assets page in browser
- [ ] Verify template renders correctly
- [ ] Test all dynamic content
- [ ] Check for template errors in Flask logs
- [ ] ✅ **Checkpoint:** After this step, validation/formatting/rendering should all pass

**Step 4: Manual Audit**
- [ ] Check for duplicate template blocks
- [ ] Verify proper use of includes and macros
- [ ] Review table structure and accessibility
- [ ] Check for inline JavaScript/CSS violations
- [ ] Verify proper form structure

**Separation of Concerns:**
- [ ] Identify inline JavaScript (`<script>` blocks in template)
- [ ] Identify inline CSS (`<style>` blocks in template)
- [ ] Identify inline styles (`style="..."` attributes)
- [ ] Identify inline event handlers (`onclick="..."` attributes)
- [ ] Create extraction plan for each violation

**HTML Quality & Standards:**
- [ ] Semantic HTML usage (header, nav, main, section, article)
- [ ] Proper heading hierarchy (h1, h2, h3...)
- [ ] Accessibility (ARIA labels, alt text, role attributes)
- [ ] Form accessibility (labels, fieldsets, error messages)
- [ ] Remove commented-out HTML blocks
- [ ] Remove bug reference comments

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [ ] Document what was changed and why
- [ ] Extract inline code to separate files if needed
- [ ] 🔄 **Loop back to Step 1** and repeat until file is perfect

If Step 4 resulted in NO modifications:
- [ ] Mark task as COMPLETE ✅
- [ ] Commit changes with message: `refactor(templates): audit and improve assets.html [Phase 5.2]`
- [ ] Move to Task 5.3

---

#### Task 5.3: Maintenance Orders List Page (`src/templates/maintenance_orders.html`)

**Step 1: HTML Validation**
- [ ] Run HTML validator on rendered output
- [ ] Fix any syntax errors or warnings
- [ ] Proceed to Step 2

**Step 2: Prettier Formatting**
- [ ] Run `prettier --write src/templates/maintenance_orders.html` to auto-format HTML
- [ ] Review changes for consistency
- [ ] Proceed to Step 3

**Step 3: Render Testing**
- [ ] Load maintenance orders page in browser
- [ ] Verify template renders correctly
- [ ] Test all dynamic content
- [ ] Check for template errors in Flask logs
- [ ] ✅ **Checkpoint:** After this step, validation/formatting/rendering should all pass

**Step 4: Manual Audit**
- [ ] Check for duplicate template blocks
- [ ] Verify proper use of includes and macros
- [ ] Review table structure and accessibility
- [ ] Check for inline JavaScript/CSS violations
- [ ] Verify proper form structure

**Separation of Concerns:**
- [ ] Identify inline JavaScript (`<script>` blocks in template)
- [ ] Identify inline CSS (`<style>` blocks in template)
- [ ] Identify inline styles (`style="..."` attributes)
- [ ] Identify inline event handlers (`onclick="..."` attributes)
- [ ] Create extraction plan for each violation

**HTML Quality & Standards:**
- [ ] Semantic HTML usage (header, nav, main, section, article)
- [ ] Proper heading hierarchy (h1, h2, h3...)
- [ ] Accessibility (ARIA labels, alt text, role attributes)
- [ ] Form accessibility (labels, fieldsets, error messages)
- [ ] Remove commented-out HTML blocks
- [ ] Remove bug reference comments

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [ ] Document what was changed and why
- [ ] Extract inline code to separate files if needed
- [ ] 🔄 **Loop back to Step 1** and repeat until file is perfect

If Step 4 resulted in NO modifications:
- [ ] Mark task as COMPLETE ✅
- [ ] Commit changes with message: `refactor(templates): audit and improve maintenance_orders.html [Phase 5.3]`
- [ ] Move to Task 5.4

---

#### Task 5.4: Spare Parts List Page (`src/templates/spare_parts.html`)

**Step 1: HTML Validation**
- [ ] Run HTML validator on rendered output
- [ ] Fix any syntax errors or warnings
- [ ] Proceed to Step 2

**Step 2: Prettier Formatting**
- [ ] Run `prettier --write src/templates/spare_parts.html` to auto-format HTML
- [ ] Review changes for consistency
- [ ] Proceed to Step 3

**Step 3: Render Testing**
- [ ] Load spare parts page in browser
- [ ] Verify template renders correctly
- [ ] Test all dynamic content
- [ ] Check for template errors in Flask logs
- [ ] ✅ **Checkpoint:** After this step, validation/formatting/rendering should all pass

**Step 4: Manual Audit**
- [ ] Check for duplicate template blocks
- [ ] Verify proper use of includes and macros
- [ ] Review table structure and accessibility
- [ ] Check for inline JavaScript/CSS violations
- [ ] Verify proper form structure

**Separation of Concerns:**
- [ ] Identify inline JavaScript (`<script>` blocks in template)
- [ ] Identify inline CSS (`<style>` blocks in template)
- [ ] Identify inline styles (`style="..."` attributes)
- [ ] Identify inline event handlers (`onclick="..."` attributes)
- [ ] Create extraction plan for each violation

**HTML Quality & Standards:**
- [ ] Semantic HTML usage (header, nav, main, section, article)
- [ ] Proper heading hierarchy (h1, h2, h3...)
- [ ] Accessibility (ARIA labels, alt text, role attributes)
- [ ] Form accessibility (labels, fieldsets, error messages)
- [ ] Remove commented-out HTML blocks
- [ ] Remove bug reference comments

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [ ] Document what was changed and why
- [ ] Extract inline code to separate files if needed
- [ ] 🔄 **Loop back to Step 1** and repeat until file is perfect

If Step 4 resulted in NO modifications:
- [ ] Mark task as COMPLETE ✅
- [ ] Commit changes with message: `refactor(templates): audit and improve spare_parts.html [Phase 5.4]`
- [ ] Move to Task 5.5

---

#### Task 5.5: Users List Page (`src/templates/users.html`)

**Step 1: HTML Validation**
- [ ] Run HTML validator on rendered output
- [ ] Fix any syntax errors or warnings
- [ ] Proceed to Step 2

**Step 2: Prettier Formatting**
- [ ] Run `prettier --write src/templates/users.html` to auto-format HTML
- [ ] Review changes for consistency
- [ ] Proceed to Step 3

**Step 3: Render Testing**
- [ ] Load users page in browser
- [ ] Verify template renders correctly
- [ ] Test all dynamic content
- [ ] Check for template errors in Flask logs
- [ ] ✅ **Checkpoint:** After this step, validation/formatting/rendering should all pass

**Step 4: Manual Audit**
- [ ] Check for duplicate template blocks
- [ ] Verify proper use of includes and macros
- [ ] Review table structure and accessibility
- [ ] Check for inline JavaScript/CSS violations
- [ ] Verify proper form structure

**Separation of Concerns:**
- [ ] Identify inline JavaScript (`<script>` blocks in template)
- [ ] Identify inline CSS (`<style>` blocks in template)
- [ ] Identify inline styles (`style="..."` attributes)
- [ ] Identify inline event handlers (`onclick="..."` attributes)
- [ ] Create extraction plan for each violation

**HTML Quality & Standards:**
- [ ] Semantic HTML usage (header, nav, main, section, article)
- [ ] Proper heading hierarchy (h1, h2, h3...)
- [ ] Accessibility (ARIA labels, alt text, role attributes)
- [ ] Form accessibility (labels, fieldsets, error messages)
- [ ] Remove commented-out HTML blocks
- [ ] Remove bug reference comments

**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [ ] Document what was changed and why
- [ ] Extract inline code to separate files if needed
- [ ] 🔄 **Loop back to Step 1** and repeat until file is perfect

If Step 4 resulted in NO modifications:
- [ ] Mark task as COMPLETE ✅
- [ ] Commit changes with message: `refactor(templates): audit and improve users.html [Phase 5.5]`
- [ ] Move to Task 5.6

---

#### Task 5.6: Index/Dashboard Page (`src/templates/index.html`)
**Step 1-3:** Follow standard HTML validation, formatting, and render testing
**Step 4: Manual Audit**
- [ ] Review form handling and validation
- [ ] Check for inline styles/JavaScript/event handlers
- [ ] Verify proper error message display
- [ ] Review template variable naming
- [ ] Check separation of concerns
- [ ] Verify HTML quality & standards (semantic HTML, accessibility, etc.)
**Step 5:** Document & Loop or Commit with message: `refactor(templates): audit and improve index.html [Phase 5.6]`

---

#### Task 5.7: Login Page (`src/templates/login.html`)
**Step 1-3:** Follow standard HTML validation, formatting, and render testing
**Step 4: Manual Audit**
- [ ] Review form handling and validation
- [ ] Check for inline styles/JavaScript/event handlers
- [ ] Verify proper error message display
- [ ] Review template variable naming
- [ ] Check separation of concerns
- [ ] Verify HTML quality & standards (semantic HTML, accessibility, etc.)
**Step 5:** Document & Loop or Commit with message: `refactor(templates): audit and improve login.html [Phase 5.7]`

---

#### Task 5.8: Asset Detail Page (`src/templates/asset_detail.html`)
**Step 1-3:** Follow standard HTML validation, formatting, and render testing
**Step 4: Manual Audit**
- [ ] Review form handling and validation
- [ ] Check for inline styles/JavaScript/event handlers
- [ ] Verify proper error message display
- [ ] Review template variable naming
- [ ] Check separation of concerns
- [ ] Verify HTML quality & standards (semantic HTML, accessibility, etc.)
**Step 5:** Document & Loop or Commit with message: `refactor(templates): audit and improve asset_detail.html [Phase 5.8]`

---

#### Task 5.9: Maintenance Order Detail Page (`src/templates/maintenance_order_detail.html`)
**Step 1-3:** Follow standard HTML validation, formatting, and render testing
**Step 4: Manual Audit**
- [ ] Review form handling and validation
- [ ] Check for inline styles/JavaScript/event handlers
- [ ] Verify proper error message display
- [ ] Review template variable naming
- [ ] Check separation of concerns
- [ ] Verify HTML quality & standards (semantic HTML, accessibility, etc.)
**Step 5:** Document & Loop or Commit with message: `refactor(templates): audit and improve maintenance_order_detail.html [Phase 5.9]`

---

#### Task 5.10: Spare Part Detail Page (`src/templates/spare_part_detail.html`)
**Step 1-3:** Follow standard HTML validation, formatting, and render testing
**Step 4: Manual Audit**
- [ ] Review form handling and validation
- [ ] Check for inline styles/JavaScript/event handlers
- [ ] Verify proper error message display
- [ ] Review template variable naming
- [ ] Check separation of concerns
- [ ] Verify HTML quality & standards (semantic HTML, accessibility, etc.)
**Step 5:** Document & Loop or Commit with message: `refactor(templates): audit and improve spare_part_detail.html [Phase 5.10]`

---

#### Task 5.11: Technician Detail Page (`src/templates/technician_detail.html`)
**Step 1-3:** Follow standard HTML validation, formatting, and render testing
**Step 4: Manual Audit**
- [ ] Review form handling and validation
- [ ] Check for inline styles/JavaScript/event handlers
- [ ] Verify proper error message display
- [ ] Review template variable naming
- [ ] Check separation of concerns
- [ ] Verify HTML quality & standards (semantic HTML, accessibility, etc.)
**Step 5:** Document & Loop or Commit with message: `refactor(templates): audit and improve technician_detail.html [Phase 5.11]`

---

#### Task 5.12: User Detail Page (`src/templates/user_detail.html`)
**Step 1-3:** Follow standard HTML validation, formatting, and render testing
**Step 4: Manual Audit**
- [ ] Review form handling and validation
- [ ] Check for inline styles/JavaScript/event handlers
- [ ] Verify proper error message display
- [ ] Review template variable naming
- [ ] Check separation of concerns
- [ ] Verify HTML quality & standards (semantic HTML, accessibility, etc.)
**Step 5:** Document & Loop or Commit with message: `refactor(templates): audit and improve user_detail.html [Phase 5.12]`

---

#### Task 5.13: Shift Calendar Page (`src/templates/shift_calendar.html`)
**Step 1-3:** Follow standard HTML validation, formatting, and render testing
**Step 4: Manual Audit**
- [ ] Review complex template logic
- [ ] Check for JavaScript extraction opportunities
- [ ] Verify proper data binding
- [ ] Check for inline styles/JavaScript/event handlers
- [ ] Check separation of concerns
- [ ] Verify HTML quality & standards (semantic HTML, accessibility, etc.)
**Step 5:** Document & Loop or Commit with message: `refactor(templates): audit and improve shift_calendar.html [Phase 5.13]`

---

#### Task 5.14: Maintenance Grid Page (`src/templates/maintenance_grid.html`)
**Step 1-3:** Follow standard HTML validation, formatting, and render testing
**Step 4: Manual Audit**
- [ ] Review complex template logic
- [ ] Check for JavaScript extraction opportunities
- [ ] Verify proper data binding
- [ ] Check for inline styles/JavaScript/event handlers
- [ ] Check separation of concerns
- [ ] Verify HTML quality & standards (semantic HTML, accessibility, etc.)
**Step 5:** Document & Loop or Commit with message: `refactor(templates): audit and improve maintenance_grid.html [Phase 5.14]`

---

#### Task 5.15: Planning Pages (`src/templates/planning.html`, `planning_embed.html`, `ticket.html`)
**Step 1-3:** Follow standard HTML validation, formatting, and render testing for all 3 files
**Step 4: Manual Audit** (all 3 files)
- [ ] Review complex template logic
- [ ] Check for JavaScript extraction opportunities
- [ ] Verify proper data binding
- [ ] Check for inline styles/JavaScript/event handlers
- [ ] Check separation of concerns
- [ ] Verify HTML quality & standards (semantic HTML, accessibility, etc.)
**Step 5:** Document & Loop or Commit with message: `refactor(templates): audit and improve planning pages [Phase 5.15]`

---

#### Task 5.16: Advanced Table Component (`src/templates/components/advanced_table.html`)
**Step 1-3:** Follow standard HTML validation, formatting, and render testing
**Step 4: Manual Audit**
- [ ] Review component structure
- [ ] Check for inline styles/JavaScript/event handlers
- [ ] Verify proper use of includes and macros
- [ ] Check separation of concerns
- [ ] Verify HTML quality & standards (semantic HTML, accessibility, etc.)
**Step 5:** Document & Loop or Commit with message: `refactor(templates): audit and improve advanced_table.html [Phase 5.16]`

---

#### Phase 5 Final Verification (After All Tasks Complete)
- [ ] Validate all rendered HTML (W3C validator)
- [ ] Run accessibility audit (axe DevTools or Lighthouse)
- [ ] Verify no inline JavaScript/CSS/styles remain
- [ ] Test all templates render without errors
- [ ] Document all findings in audit report
- [ ] Mark Phase 5 COMPLETE ✅

**Deliverable:** Formatted, audited HTML templates with documented findings (16 commits total)

---

### Phase 6: Root-Level & Configuration Files
**Focus:** Iterative quality loop per file with one commit per task.
**Strategy:** Each task below represents one file or logical group. Follow the 5-step iterative loop for each task until perfect, then commit before moving to the next task.

---

#### Task 6.1: Application Entry Point (`run.py`)
**Step 1: Format/Lint Check**
- [x] Run `flake8 run.py` to identify style issues
- [x] Fix any problems found
- [x] Proceed to Step 2
**Step 2: Auto-Formatting**
- [x] Run `black run.py` to auto-format code
- [x] Review changes
- [x] Proceed to Step 3
**Step 3: Functional Testing**
- [x] Start application with `python run.py`
- [x] Verify no errors or warnings
- [x] ✅ **Checkpoint:** After this step, linting/formatting/functionality should all pass
**Step 4: Manual Audit**
- [x] Review structure and error handling
- [x] Check for proper environment variable loading
- [x] Verify development vs production configuration
- [x] Review command-line argument handling
- [x] Check security settings
**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [x] Document what was changed and why
- [x] 🔄 **Loop back to Step 1** and repeat until file is perfect
If Step 4 resulted in NO modifications:
- [x] Mark task as COMPLETE ✅
- [x] Commit changes with message: `refactor(root): audit and improve run.py [Phase 6.1]`
- [x] Move to Task 6.2

---

#### Task 6.2: Dependency Management (`requirements.txt`, `requirements-dev.txt`)
**Step 1: Format/Lint Check**
- [x] Review file format and organization
- [x] Check for syntax issues
- [x] Proceed to Step 2
**Step 2: Auto-Formatting**
- [x] Sort dependencies alphabetically if needed
- [x] Review changes
- [x] Proceed to Step 3
**Step 3: Functional Testing**
- [x] Test dependency installation: `pip install -r requirements.txt`
- [x] Verify no errors or warnings
- [x] ✅ **Checkpoint:** After this step, formatting/functionality should all pass
**Step 4: Manual Audit**
- [x] Review organization and grouping
- [x] Check for unused dependencies
- [x] Verify version pinning strategy
- [x] Run `pip-audit` for security vulnerabilities
- [x] Check for outdated packages
**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [x] Document what was changed and why
- [x] 🔄 **Loop back to Step 1** and repeat until files are perfect
If Step 4 resulted in NO modifications:
- [x] Mark task as COMPLETE ✅
- [x] Commit changes with message: `refactor(deps): audit and improve requirements files [Phase 6.2]`
- [x] Move to Task 6.3

---

#### Task 6.3: Configuration Files (`.env.example`, `.gitignore`)
**Step 1: Format/Lint Check**
- [x] Review file format and organization
- [x] Check for syntax issues
- [x] Proceed to Step 2
**Step 2: Auto-Formatting**
- [x] Format files if needed
- [x] Review changes
- [x] Proceed to Step 3
**Step 3: Functional Testing**
- [x] Verify `.env.example` can be copied to `.env`
- [x] Test `.gitignore` patterns
- [x] ✅ **Checkpoint:** After this step, formatting/functionality should all pass
**Step 4: Manual Audit**
- [x] Verify `.env.example` completeness
- [x] Check for sensitive data patterns
- [x] Review `.gitignore` coverage
- [x] Verify all necessary files are ignored
**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [x] Document what was changed and why
- [x] 🔄 **Loop back to Step 1** and repeat until files are perfect
If Step 4 resulted in NO modifications:
- [x] Mark task as COMPLETE ✅
- [x] Commit changes with message: `refactor(config): audit and improve configuration files [Phase 6.3]`
- [x] Move to Task 6.4

---

#### Task 6.4: Documentation Files (`README.md`, `CHANGELOG.md`, `GEMINI.md`)
**Step 1: Format/Lint Check**
- [x] Run `markdownlint` on all markdown files
- [x] Fix any problems found
- [x] Proceed to Step 2
**Step 2: Auto-Formatting**
- [x] Run `prettier --write` on markdown files
- [x] Review changes
- [x] Proceed to Step 3
**Step 3: Functional Testing**
- [x] Verify all links work
- [x] Check markdown rendering
- [x] ✅ **Checkpoint:** After this step, linting/formatting/links should all pass
**Step 4: Manual Audit**
- [x] Review accuracy and completeness
- [x] Check CHANGELOG.md format and updates
- [x] Verify GEMINI.md consistency with copilot-instructions.md
- [x] Validate all cross-references and links
- [x] Check for outdated information
- [x] Verify setup instructions are current
**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [x] Document what was changed and why
- [x] 🔄 **Loop back to Step 1** and repeat until files are perfect
If Step 4 resulted in NO modifications:
- [x] Mark task as COMPLETE ✅
- [x] Commit changes with message: `docs: audit and improve documentation files [Phase 6.4]`
- [x] Move to Task 6.5

---

#### Task 6.5: GitHub Configuration (`.github/` files)
**Step 1: Format/Lint Check**
- [x] Run `markdownlint` on markdown files
- [x] Check YAML syntax for templates
- [x] Fix any problems found
- [x] Proceed to Step 2
**Step 2: Auto-Formatting**
- [x] Run `prettier --write` on markdown and YAML files
- [x] Review changes
- [x] Proceed to Step 3
**Step 3: Functional Testing**
- [x] Verify all links work
- [x] Test issue template rendering (if possible)
- [x] ✅ **Checkpoint:** After this step, linting/formatting/functionality should all pass
**Step 4: Manual Audit**
- [x] Review issue templates functionality
- [x] Check CONTRIBUTING.md accuracy
- [x] Verify GIT_WORKFLOW.md reflects actual practices
- [x] Review CODEOWNERS assignments
- [x] Check PR template completeness
- [x] Verify workflow files (if any)
**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [x] Document what was changed and why
- [x] 🔄 **Loop back to Step 1** and repeat until files are perfect
If Step 4 resulted in NO modifications:
- [x] Mark task as COMPLETE ✅
- [x] Commit changes with message: `docs(github): audit and improve GitHub configuration [Phase 6.5]`
- [x] Move to Task 6.6

---

#### Task 6.6: Test Infrastructure (`tests/conftest.py`, `test_data/dummy_data.json`)
**Step 1: Format/Lint Check**
- [x] Run `flake8 tests/conftest.py`
- [x] Run `jsonlint test_data/dummy_data.json`
- [x] Fix any problems found
- [x] Proceed to Step 2
**Step 2: Auto-Formatting**
- [x] Run `black tests/conftest.py`
- [x] Run `prettier --write test_data/dummy_data.json`
- [x] Review changes
- [x] Proceed to Step 3
**Step 3: Functional Testing**
- [x] Run `pytest tests/` to verify configuration works
- [x] Verify test data loads correctly
- [x] ✅ **Checkpoint:** After this step, linting/formatting/functionality should all pass
**Step 4: Manual Audit**
- [x] Review pytest configuration
- [x] Check test fixture organization
- [x] Verify test data in `test_data/dummy_data.json`
- [x] Review test coverage configuration
**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [x] Document what was changed and why
- [x] 🔄 **Loop back to Step 1** and repeat until files are perfect
If Step 4 resulted in NO modifications:
- [x] Mark task as COMPLETE ✅
- [x] Commit changes with message: `test: audit and improve test infrastructure [Phase 6.6]`
- [x] Move to Task 6.7

---

#### Task 6.7: Scripts & Automation (`scripts/setup.ps1`)
**Step 1: Format/Lint Check**
- [x] Run `PSScriptAnalyzer` on setup.ps1
- [x] Fix any problems found
- [x] Proceed to Step 2
**Step 2: Auto-Formatting**
- [x] Format PowerShell script if needed
- [x] Review changes
- [x] Proceed to Step 3
**Step 3: Functional Testing**
- [x] Run setup script in test environment
- [x] Verify no errors or warnings
- [x] ✅ **Checkpoint:** After this step, linting/formatting/functionality should all pass
**Step 4: Manual Audit**
- [x] Review functionality and logic
- [x] Check for error handling
- [x] Verify cross-platform compatibility notes
- [x] Check for hardcoded paths or values
- [x] Review user feedback messages
**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [x] Document what was changed and why
- [x] 🔄 **Loop back to Step 1** and repeat until files are perfect
If Step 4 resulted in NO modifications:
- [x] Mark task as COMPLETE ✅
- [x] Commit changes with message: `chore(scripts): audit and improve setup.ps1 [Phase 6.7]`
- [x] Move to Phase 6 Final Verification

---

#### Phase 6 Final Verification (After All Tasks Complete)
- [x] Run full application setup from scratch (test `setup.ps1`)
- [x] Verify all documentation links work
- [x] Run `pip-audit` for security vulnerabilities
- [x] Test application startup with `run.py`
- [x] Document all findings in audit report
- [x] Mark Phase 6 COMPLETE ✅

**Deliverable:** Formatted, audited root-level files with documented findings (7 commits total)

---

### Phase 7: Cross-Cutting Concerns
**Focus:** Iterative quality loop for consistency checks with one commit per task.
**Strategy:** Each task below represents a cross-cutting concern. Follow the 5-step iterative loop for each task until perfect, then commit before moving to the next task.

---

#### Task 7.1: Naming Conventions Audit
**Step 1: Automated Consistency Checks**
- [ ] Run naming convention checker across all files
- [ ] Check for inconsistent patterns
- [ ] Proceed to Step 2
**Step 2: Generate Consistency Report**
- [ ] Create report of naming violations
- [ ] Categorize by file type and severity
- [ ] Proceed to Step 3
**Step 3: Verify No Regressions**
- [ ] Run all tests (`pytest tests/`)
- [ ] Test application functionality
- [ ] Verify all previous phases still pass
- [ ] ✅ **Checkpoint:** After this step, all automated checks should all pass
**Step 4: Manual Audit**
Focus on consistency and patterns across the entire codebase:
- [ ] **Files & Directories:**
  - Python: `snake_case.py`
  - JavaScript: `kebab-case.js`
  - CSS: `kebab-case.css`
  - Templates: `snake_case.html`
  - Document any violations
- [ ] **Variables & Functions:**
  - Python: `snake_case`
  - JavaScript: `camelCase`
  - Document any violations
- [ ] **Classes:**
  - Python: `PascalCase`
  - JavaScript: `PascalCase`
  - CSS: `kebab-case` or BEM
  - Document any violations
- [ ] **Constants:**
  - Python: `UPPER_SNAKE_CASE`
  - JavaScript: `UPPER_SNAKE_CASE`
  - Document any violations
- [ ] **Database:**
  - Tables: `snake_case`
  - Columns: `snake_case`
  - Document any violations
**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [ ] Document what was changed and why
- [ ] Update affected files
- [ ] 🔄 **Loop back to Step 1** and repeat until perfect
If Step 4 resulted in NO modifications:
- [ ] Mark task as COMPLETE ✅
- [ ] Commit changes with message: `refactor(naming): standardize naming conventions across codebase [Phase 7.1]`
- [ ] Move to Task 7.2

---

#### Task 7.2: Environment Configuration Audit
**Step 1: Automated Consistency Checks**
- [ ] Scan codebase for environment variable usage
- [ ] Check for undocumented variables
- [ ] Proceed to Step 2
**Step 2: Generate Consistency Report**
- [ ] List all environment variables used in code
- [ ] Compare with `.env.example`
- [ ] Proceed to Step 3
**Step 3: Verify No Regressions**
- [ ] Run all tests (`pytest tests/`)
- [ ] Test application functionality
- [ ] ✅ **Checkpoint:** After this step, all automated checks should pass
**Step 4: Manual Audit**
- [ ] Review `.env.example` completeness
- [ ] Check for sensitive data in version control
- [ ] Verify all environment variables are documented
- [ ] Review default values and fallbacks
- [ ] Cross-reference with actual usage in code
**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [ ] Document what was changed and why
- [ ] Update affected files
- [ ] 🔄 **Loop back to Step 1** and repeat until perfect
If Step 4 resulted in NO modifications:
- [ ] Mark task as COMPLETE ✅
- [ ] Commit changes with message: `refactor(config): audit and standardize environment configuration [Phase 7.2]`
- [ ] Move to Task 7.3

---

#### Task 7.3: Code Duplication Analysis
**Step 1: Automated Consistency Checks**
- [ ] Run duplicate code detector (jscpd) across entire codebase
- [ ] Generate duplication report
- [ ] Proceed to Step 2
**Step 2: Generate Consistency Report**
- [ ] List duplicate code blocks
- [ ] Prioritize by size and impact
- [ ] Proceed to Step 3
**Step 3: Verify No Regressions**
- [ ] Run all tests (`pytest tests/`)
- [ ] Test application functionality
- [ ] ✅ **Checkpoint:** After this step, all automated checks should pass
**Step 4: Manual Audit**
- [ ] Review jscpd report for duplicate blocks
- [ ] Identify opportunities for refactoring
- [ ] Check for duplicate logic across Python/JavaScript
- [ ] Verify no duplicate CSS rules
- [ ] Check for duplicate template blocks
**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [ ] Document what was changed and why
- [ ] Update affected files
- [ ] 🔄 **Loop back to Step 1** and repeat until perfect
If Step 4 resulted in NO modifications:
- [ ] Mark task as COMPLETE ✅
- [ ] Commit changes with message: `refactor(duplication): remove code duplicates [Phase 7.3]`
- [ ] Move to Task 7.4

---

#### Task 7.4: Final Consistency Check
**Step 1: Automated Consistency Checks**
- [ ] Run all linters one final time
- [ ] Run all formatters one final time
- [ ] Proceed to Step 2
**Step 2: Generate Consistency Report**
- [ ] Create final audit summary
- [ ] List any remaining issues
- [ ] Proceed to Step 3
**Step 3: Verify No Regressions**
- [ ] Run all tests (`pytest tests/`)
- [ ] Test application functionality
- [ ] Verify all previous phases still pass
- [ ] ✅ **Checkpoint:** After this step, all automated checks should pass
**Step 4: Manual Audit**
- [ ] Verify naming consistency across all files
- [ ] Check for remaining code duplicates
- [ ] Review overall code organization
- [ ] Verify all standards are applied consistently
- [ ] Check for any missed issues from previous phases
**Step 5: Document & Loop (If Changes Made)**
If Step 4 resulted in modifications:
- [ ] Document what was changed and why
- [ ] Update affected files
- [ ] 🔄 **Loop back to Step 1** and repeat until perfect
If Step 4 resulted in NO modifications:
- [ ] Mark task as COMPLETE ✅
- [ ] Commit changes with message: `refactor(final): final consistency check and cleanup [Phase 7.4]`
- [ ] Move to Phase 7 Final Verification

---

#### Phase 7 Final Verification (After All Tasks Complete)
- [ ] Run all automated tools one final time:
  - [ ] `ruff check src/`
  - [ ] `pylint src/`
  - [ ] `eslint src/static/js/`
  - [ ] `stylelint src/static/css/`
  - [ ] `jscpd src/`
- [ ] Run full test suite (`pytest --cov=src tests/`)
- [ ] Verify all 210 tests pass
- [ ] Verify coverage remains 82.99%+
- [ ] Test full application functionality
- [ ] Document all findings in final audit report
- [ ] Update `audit_results/baseline_metrics.md` with final scores
- [ ] Mark Phase 7 COMPLETE ✅

**Deliverable:** Cross-cutting concerns audit report with final consistency verification (4 commits total)

---

## 🧪 Phase 8: Test Files Quality Audit (FUTURE)

> [!NOTE]
> **Status:** ⏳ **PLANNED** - To be executed after all source file audits are complete.
> **Prerequisites:** Phases 1-7 complete. All source files audited and stable.
> **Format Note:** All test files were Black formatted on December 17, 2025.

### Phase 8 Overview

**Objective:** Apply the 5-Step Iterative Loop to all test files in `tests/` to ensure:
- Consistent code style and formatting
- Proper test organization and naming
- No duplicate test logic
- Comprehensive docstrings
- Adherence to testing best practices

**Scope:** 13 test files (see "Test Files" section above)

### Phase 8.1: Test Configuration (`tests/conftest.py`)

**Tasks:**
- [ ] Review fixture organization and naming
- [ ] Check for proper docstrings on all fixtures
- [ ] Verify no duplicate fixture logic
- [ ] Ensure proper scope management (function, class, module, session)

### Phase 8.2: Unit Tests (`tests/unit/`)

**Files:** `test_app.py`, `test_db_utils.py`, `test_shift_utils.py`

**Tasks:**
- [ ] Verify test isolation (no external dependencies)
- [ ] Check for proper mocking patterns
- [ ] Ensure descriptive test names
- [ ] Review assertion quality

### Phase 8.3: Functional Tests (`tests/functional/`)

**Files:** `test_api_routes.py`, `test_main_routes.py`

**Tasks:**
- [ ] Verify REST convention testing
- [ ] Check for proper HTTP status code assertions
- [ ] Review request/response validation

### Phase 8.4: Integration Tests (`tests/integration/`)

**Files:** `test_integration.py`

**Tasks:**
- [ ] Verify end-to-end workflow coverage
- [ ] Check for proper database state management
- [ ] Review cleanup procedures

### Phase 8.5: Security Tests (`tests/security/`)

**Files:** `test_auth.py`, `test_validation.py`, `test_advanced_validation.py`

**Tasks:**
- [ ] Verify OWASP coverage
- [ ] Check for injection prevention tests
- [ ] Review authentication/authorization tests

### Phase 8.6: Performance & Reliability Tests

**Files:** `test_performance.py`, `test_errors.py`

**Tasks:**
- [ ] Review performance baseline assertions
- [ ] Check error handling coverage
- [ ] Verify timeout and edge case handling

---

## 🔧 Implementation Workflow

### Step-by-Step Process (Per Issue Found)

1. **Analysis & Discovery**
   - AI identifies issue during audit phase
   - Documents finding with file location, line numbers, description

2. **Proposal & Discussion**
   - AI presents finding to user
   - Explains the problem and impact
   - Proposes solution(s) with pros/cons
   - **WAIT FOR USER APPROVAL** before proceeding

3. **Implementation**
   - AI implements approved solution
   - Follows coding standards and best practices
   - Updates related files if necessary

4. **Testing**
   - Run automated tests (if applicable)
   - Perform manual testing following test plan template
   - Verify no regressions or crashes
   - **WAIT FOR USER CONFIRMATION** that tests pass

5. **Documentation**
   - Update audit report with resolution
   - Document changes in commit message
   - Update relevant documentation files

6. **Commit**
   - Create detailed commit message
   - Commit only after user confirms everything works
   - Move to next issue

---

## 🧪 Testing Strategy

### Automated Testing
- [ ] Run existing pytest suite: `pytest tests/`
- [ ] Check for Python linting errors: `flake8 src/`
- [ ] Check for JavaScript errors: Browser console inspection

### Manual Testing (Per Phase)
After each phase implementation, perform comprehensive manual testing:

1. **Smoke Test:** Verify application starts without errors
2. **Feature Test:** Test all major features (Assets, MOs, Spare Parts, Technicians)
3. **UI Test:** Verify all pages render correctly
4. **Advanced Table Test:** Run subset of `table_features_test_plan.md` tests
5. **Browser Console:** Check for JavaScript errors
6. **Network Tab:** Verify API calls succeed

### Test Plan Template (Per Major Change)
```markdown
## Test Plan: [Change Description]

**Files Modified:** [List files]
**Change Type:** [Bug Fix / Refactor / Optimization]

### Test Cases
1. [ ] Application starts without errors
2. [ ] [Specific feature] works as expected
3. [ ] No JavaScript console errors
4. [ ] No Python exceptions in logs
5. [ ] [Additional specific tests]

### Results
- [ ] All tests passed
- [ ] User confirmed functionality
```

---

## 📊 Progress Tracking

### Phase Completion Checklist
- [x] **Phase 1:** Automated Code Quality Analysis - ✅ COMPLETE (December 13, 2025)
- [x] **Phase 2:** Python Backend Analysis (6 tasks, 6 commits) - ✅ COMPLETE (December 15, 2025)
- [ ] **Phase 3:** JavaScript Frontend Analysis (13 tasks, 13 commits) - PENDING
  - [ ] Task 3.1-3.2: Table Core & Init
  - [ ] Task 3.3-3.5: Table Rendering (render, sidebar, resize)
  - [ ] Task 3.6-3.8: Table Data (data, config, export)
  - [ ] Task 3.9-3.11: Table Events & Loading (events, loading, retry)
  - [ ] Task 3.12-3.13: UI Components (toast, flash)
- [ ] **Phase 4:** CSS Styling Analysis (3 tasks, 3 commits) - PENDING
  - [ ] Task 4.1: Main Styles
  - [ ] Task 4.2: Advanced Table Styles
  - [ ] Task 4.3: Advanced Table Sidebar Styles
- [ ] **Phase 5:** HTML Templates Analysis (16 tasks, 16 commits) - PENDING
  - [ ] Task 5.1: Base Template
  - [ ] Task 5.2-5.5: List Pages (assets, MOs, spare parts, users)
  - [ ] Task 5.6-5.7: Index & Login
  - [ ] Task 5.8-5.12: Detail Pages (asset, MO, spare part, technician, user)
  - [ ] Task 5.13-5.15: Specialized Pages (shift calendar, maintenance grid, planning)
  - [ ] Task 5.16: Advanced Table Component
- [x] **Phase 6:** Root-Level & Configuration Files (7 tasks, 7 commits) - ✅ COMPLETE
  - [x] Task 6.1: Application Entry Point
  - [x] Task 6.2: Dependency Management
  - [x] Task 6.3: Configuration Files
  - [x] Task 6.4: Documentation Files
  - [x] Task 6.5: GitHub Configuration
  - [x] Task 6.6: Test Infrastructure
  - [x] Task 6.7: Scripts & Automation
- [ ] **Phase 7:** Cross-Cutting Concerns (4 tasks, 4 commits) - PENDING
  - [ ] Task 7.1: Naming Conventions Audit
  - [ ] Task 7.2: Environment Configuration Audit
  - [ ] Task 7.3: Code Duplication Analysis
  - [ ] Task 7.4: Final Consistency Check

**Total Tasks:** 49 tasks across 7 phases  
**Total Commits:** 49 commits (one per task)

### Metrics to Track
- **Issues Found:** Total number of issues identified
- **Issues Resolved:** Number of issues fixed and tested
- **Files Modified:** Count of files changed
- **Lines Changed:** Approximate lines added/removed
- **Test Coverage:** Percentage of code tested
- **Commits Made:** Number of commits during cleanup

---

## 📝 Reporting Format

### Issue Report Template
```markdown
## Issue #[N]: [Brief Description]

**File:** `path/to/file.ext`
**Lines:** [Start-End]
**Severity:** [Critical / High / Medium / Low]
**Category:** [Code Quality / Performance / Security / Standards]

### Current State
[Description of the problem with code snippet]

### Impact
[Why this is a problem]

### Proposed Solution
[Detailed explanation of the fix]

### Alternative Solutions (if applicable)
[Other approaches considered]

### Files to Modify
- `file1.ext` - [What changes]
- `file2.ext` - [What changes]

### Testing Plan
[How to verify the fix works]

### User Approval Required
- [ ] User reviewed and approved solution
```

---

## 🚀 Getting Started

### Prerequisites
1. Ensure mockCMMS server is running: `python run.py`
2. Ensure all dependencies are installed: `pip install -r requirements.txt`
3. Backup current database: Copy `instance/mockcmms.db` to safe location
4. Create a new branch for cleanup work: `git checkout -b code-quality-cleanup`

### Phase 1 Kickoff
1. AI will analyze all Python files (root + `src/` + `tests/` + `scripts/`)
2. Generate Phase 1 Audit Report
3. Present findings to user for review
4. Begin implementation of approved fixes

---

## 📚 References

- **Coding Standards:** `.github/copilot-instructions.md`
- **Testing Guide:** `docs/table_features_test_plan.md`
- **Project Roadmap:** `docs/mockCMMS_roadmap.md`
- **Bug Tracking:** `docs/bug_tracking.md`

---

## ⚠️ Important Notes

1. **No Automatic Changes:** AI will NEVER make changes without user approval
2. **Test Everything:** Every change must be tested before committing
3. **Commit Frequently:** Commit after each major fix (with user approval)
4. **Document Everything:** All findings and resolutions must be documented
5. **Preserve Functionality:** Code quality improvements must not break existing features
6. **User is Final Authority:** User has final say on all decisions

---

**Next Step:** Begin Phase 3 - Frontend Test Suite Foundation
