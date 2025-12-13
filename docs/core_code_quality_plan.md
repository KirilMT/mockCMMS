# Core mockCMMS Code Quality & Architecture Audit Plan

**Created:** December 1, 2025  
**Last Updated:** December 13, 2025  
**Status:** 🔄 **PHASE 0 COMPLETE - PHASE 1 READY** (Ready for flake8 → black → manual audit)
**Prerequisites Met:** All 210 tests complete with 82.99% coverage. Phase 0 automated analysis complete (Ruff: 0, Pylint: 9.15/10, Radon: A, Bandit: 0).

---

> [!IMPORTANT]
> **📋 Workflow Context:** This plan is **Phase 2** of the overall implementation strategy.
> 
> **Related Documentation:**
> - **[Comprehensive Testing Plan](comprehensive_testing_plan.md)** - Phase 1 (must complete FIRST)
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
> **Status:** ✅ **READY TO START** - Week 2 complete (210/210 tests, 82.99% coverage)  
> **Current Progress:** All prerequisites met, ready to begin Week 3  
> **When to Start:** ✅ NOW - All requirements satisfied
> 
> **✅ SAFE FOR CODE FORMATTING:** 82.99% coverage achieved (target: 80-85%). All critical paths tested.

---  
**Scope:** Entire mockCMMS repository (excluding `apps/` directory)

---

> [!IMPORTANT]
> **🎯 Implementation Strategy:** This audit should be performed alongside GitHub best practices setup. See [Implementation Priority Guide](IMPLEMENTATION_PRIORITY_GUIDE.md) for a complete 6-week action plan showing how to integrate code quality work with infrastructure setup.

---

## 📋 Overview

This document outlines a comprehensive, systematic approach to auditing and improving the code quality of the core mockCMMS application. The focus is on ensuring the codebase is clean, organized, optimized, follows coding conventions, and contains no duplicates or technical debt.

**Philosophy:** Analyze first, propose solutions, get approval, implement, test, commit.

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

### Root-Level Files
- [ ] `run.py` - Application entry point
- [ ] `requirements.txt` - Python dependencies
- [ ] `.env.example` - Environment configuration template
- [ ] `CHANGELOG.md` - Version history
- [ ] `README.md` - Project documentation
- [ ] `GEMINI.md` - AI assistant instructions
- [ ] `.gitignore` - Git ignore rules

### Configuration Files (`.github/`)
- [ ] `.github/copilot-instructions.md` - GitHub Copilot instructions
- [ ] `.github/CONTRIBUTING.md` - Contribution guidelines
- [ ] `.github/GIT_WORKFLOW.md` - Git workflow documentation
- [ ] `.github/CODEOWNERS` - Code ownership definitions
- [ ] `.github/PULL_REQUEST_TEMPLATE.md` - PR template
- [ ] `.github/ISSUE_TEMPLATE/bug_report.md` - Bug report template
- [ ] `.github/ISSUE_TEMPLATE/feature_request.md` - Feature request template
- [ ] `.github/ISSUE_TEMPLATE/custom.md` - Custom issue template
- [ ] `.github/ISSUE_TEMPLATE/config.yml` - Issue template configuration

### Documentation Files (`docs/`)
- [ ] `docs/mockCMMS_roadmap.md` - Project roadmap
- [ ] `docs/bug_tracking.md` - Bug tracking document
- [ ] `docs/table_features_test_plan.md` - Advanced Table test plan
- [ ] `docs/HOW_TO_UPDATE_ROADMAPS.md` - Roadmap update guide
- [ ] `docs/core_code_quality_plan.md` - This document (self-audit)

### Test Files (`tests/`)
- [ ] `tests/conftest.py` - Pytest configuration
- [ ] `tests/test_api.py` - API endpoint tests

### Test Data (`test_data/`)
- [ ] `test_data/dummy_data.json` - Test fixtures

### Scripts (`scripts/`)
- [ ] `scripts/setup.ps1` - Setup automation script

### Python Files (`src/`)
- [x] `src/__init__.py` - Package initialization ✅ Phase 0
- [x] `src/app.py` - Flask application factory ✅ Phase 0
- [x] `src/routes/api.py` - REST API endpoints ✅ Phase 0
- [x] `src/routes/main.py` - Web interface routes ✅ Phase 0
- [x] `src/services/__init__.py` - Services package initialization ✅ Phase 0
- [x] `src/services/db_utils.py` - Database utilities ✅ Phase 0 (refactored)
- [x] `src/services/db_seeding.py` - Database seeding helpers ✅ Phase 0 (created)
- [x] `src/services/shift_utils.py` - Shift management utilities ✅ Phase 0

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

## 🤖 Phase 0: Automated Code Quality Analysis (PREREQUISITE)

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

### Phase 0 Execution Steps

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
ruff check src/ --output-format=text > audit_results/ruff_report.txt

# 2. Pylint - Comprehensive linting  
pylint src/ --output-format=text > audit_results/pylint_report.txt

# 3. Mypy - Type checking
mypy src/ > audit_results/mypy_report.txt

# 4. Radon - Complexity analysis
radon cc src/ -a -s > audit_results/radon_complexity.txt
radon mi src/ -s > audit_results/radon_maintainability.txt

# 5. Bandit - Security scanning
bandit -r src/ -f txt -o audit_results/bandit_security.txt

# 6. JSCPD - Duplicate detection
jscpd src/ --output audit_results/duplicates_report.txt

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

### Phase 0 Deliverables

- [x] **`audit_results/` directory** - All tool outputs ✅ Completed December 13, 2025
- [x] **`audit_results_full.txt`** - Combined results ✅ Completed December 13, 2025
- [x] **`baseline_metrics.md`** - Initial measurements ✅ Completed December 13, 2025
- [x] **`priority_issues.md`** - Categorized issue list ✅ Completed December 13, 2025
- [x] **All critical/high priority issues fixed** ✅ Completed December 13, 2025

### Phase 0 Results Summary

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

**After Phase 0 completion:**

- **Phase 1 (Python Backend)** - Focus on areas flagged by ruff, pylint, mypy, radon, bandit
- **Phase 2 (JavaScript Frontend)** - Focus on areas flagged by eslint, jscpd
- **Phase 3 (Templates)** - Focus on areas flagged by duplicate detection
- **Phase 4 (CSS)** - Focus on duplicate selectors and unused styles
- **Phase 5 (Standards)** - Use metrics to verify improvements

> [!NOTE]
> **Continuous Monitoring:** After initial analysis, add these tools to CI/CD to prevent regression. See Phase 6 for CI integration details.

---

## 🔍 Audit Phases

### Phase 1: Python Backend Analysis (Priority: Critical)
**Estimated Duration:** 1 day  
**Focus:** Iterative quality loop per file/group

**Strategy:** For each file or group of files, follow this iterative loop until perfect:

#### Iterative Quality Loop (Per File/Group)

**Step 1: Flake8 Linting**
- [ ] Run `flake8 [file]` to identify style issues
- [ ] Fix any problems found
- [ ] Proceed to Step 2

**Step 2: Black Formatting**
- [ ] Run `black [file]` to auto-format code
- [ ] Review changes
- [ ] Proceed to Step 3

**Step 3: Test Verification**
- [ ] Run `pytest tests/` (verify all 210 tests pass)
- [ ] Fix any broken tests
- [ ] ✅ **Checkpoint:** After this step, flake8/black/tests should all pass

**Step 4: Manual Audit**

Focus on logic, architecture, and patterns that tools can't catch:

**API Routes (`src/routes/api.py`) - 1 hour:**
- [ ] Verify RESTful conventions (proper HTTP methods, status codes)
- [ ] Check input validation and sanitization
- [ ] Review error responses and status codes
- [ ] Ensure proper authentication/authorization
- [ ] Check for duplicate code across endpoints
- [ ] Verify proper use of Flask patterns

**Web Routes (`src/routes/main.py`) - 1 hour:**
- [ ] Review route organization and naming
- [ ] Check for duplicate logic between routes
- [ ] Verify proper template rendering
- [ ] Review form handling and validation
- [ ] Check flash message usage
- [ ] Verify proper error handling

**Database Layer (`src/services/db_utils.py`) - 1 hour:**
- [ ] Check for SQL injection vulnerabilities
- [ ] Review query optimization opportunities
- [ ] Verify proper use of SQLAlchemy ORM
- [ ] Check for N+1 query problems
- [ ] Ensure proper transaction handling
- [ ] Review model relationships and constraints

**Application Core (`src/app.py`) - 30 min:**
- [ ] Verify Flask factory pattern implementation
- [ ] Check blueprint registration
- [ ] Review configuration handling
- [ ] Verify error handler setup
- [ ] Check security settings (SECRET_KEY, etc.)

**Utilities (`src/services/shift_utils.py`, `src/services/db_seeding.py`) - 30 min:**
- [ ] Review business logic correctness
- [ ] Check for edge cases
- [ ] Verify proper error handling

**Step 5: Document & Loop (If Changes Made)**

If Step 4 resulted in modifications:
- [ ] Document what was changed and why
- [ ] Update any affected tests
- [ ] 🔄 **Loop back to Step 1** and repeat until file is perfect

If Step 4 resulted in NO modifications:
- [ ] Mark file as COMPLETE ✅
- [ ] Move to next file/group

#### Final Verification (After All Files Complete)
- [ ] Run `ruff check src/` (verify 0 issues)
- [ ] Run `pylint src/` (verify 9.0+ score)
- [ ] Run `pytest --cov=src tests/` (verify 82.99%+ coverage)
- [ ] Update `audit_results/baseline_metrics.md` with final scores
- [ ] Document all findings in audit report
- [ ] Mark Phase 1 COMPLETE

**Deliverable:** Formatted, audited Python codebase with documented findings

**File Tracking Template:**
```markdown
### [filename] Status
- [ ] Step 1: Flake8
- [ ] Step 2: Black
- [ ] Step 3: Tests
- [ ] Step 4: Manual audit
- [ ] Step 5: Loop (if needed)
- [ ] COMPLETE ✅
```

---

### Phase 2: JavaScript Frontend Analysis (Priority: Critical)
**Estimated Duration:** 3-4 days  
**Focus:** Iterative quality loop per file/group

**Strategy:** For each JavaScript file or group of files, follow this iterative loop until perfect:

#### Iterative Quality Loop (Per File/Group)

**Step 1: ESLint Linting**
- [ ] Run `eslint [file]` to identify code quality issues
- [ ] Fix any problems found (style, unused vars, etc.)
- [ ] Proceed to Step 2

**Step 2: Prettier Formatting**
- [ ] Run `prettier --write [file]` to auto-format code
- [ ] Review changes for consistency
- [ ] Proceed to Step 3

**Step 3: Browser Testing**
- [ ] Load application in browser
- [ ] Test affected functionality
- [ ] Check browser console for errors
- [ ] Verify no JavaScript exceptions
- [ ] ✅ **Checkpoint:** After this step, ESLint/Prettier/browser tests should all pass

**Step 4: Manual Audit**

Focus on architecture, logic, and patterns that tools can't catch:

**Advanced Table Core (`table-core.js`, `table-init.js`) - 1 hour:**
- [ ] Review module organization and dependencies
- [ ] Check for circular dependencies
- [ ] Verify proper encapsulation and class structure
- [ ] Review initialization patterns
- [ ] Check for memory leaks (event listener cleanup)

**Table Rendering (`table-render.js`, `table-sidebar.js`, `table-resize.js`) - 1 hour:**
- [ ] Review DOM manipulation efficiency
- [ ] Check for unnecessary re-renders
- [ ] Verify proper use of event delegation
- [ ] Review template string usage
- [ ] Check for duplicate rendering logic

**Table Data Management (`table-data.js`, `table-config.js`, `table-export.js`) - 1 hour:**
- [ ] Review data filtering and sorting logic
- [ ] Check for efficient data structures
- [ ] Verify proper state management
- [ ] Review configuration persistence
- [ ] Check export functionality correctness

**Table Events & Loading (`table-events.js`, `table-loading.js`, `table-retry.js`) - 1 hour:**
- [ ] Review event handling patterns
- [ ] Check for proper error handling (try-catch)
- [ ] Verify retry logic with exponential backoff
- [ ] Review loading state management
- [ ] Check for race conditions

**UI Components (`toast-notification.js`, `flash-messages.js`) - 30 min:**
- [ ] Review component API design
- [ ] Check for proper error handling
- [ ] Verify browser compatibility (ES6+ features)
- [ ] Review timing and auto-dismiss logic

**Code Quality Checks (All Files):**
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
- [ ] Mark file as COMPLETE ✅
- [ ] Move to next file/group

#### Final Verification (After All Files Complete)
- [ ] Run `eslint src/static/js/` (verify 0 errors)
- [ ] Test all JavaScript functionality in browser
- [ ] Check browser console for any warnings/errors
- [ ] Verify no memory leaks (DevTools Memory profiler)
- [ ] Document all findings in audit report
- [ ] Mark Phase 2 COMPLETE

**Deliverable:** Formatted, audited JavaScript codebase with documented findings

**File Tracking Template:**
```markdown
### [filename] Status
- [ ] Step 1: ESLint
- [ ] Step 2: Prettier
- [ ] Step 3: Browser tests
- [ ] Step 4: Manual audit
- [ ] Step 5: Loop (if needed)
- [ ] COMPLETE ✅
```

---

### Phase 3: CSS Styling Analysis (Priority: High)
**Estimated Duration:** 1-2 days  
**Focus:** Iterative quality loop per file/group

**Strategy:** For each CSS file or group of files, follow this iterative loop until perfect:

#### Iterative Quality Loop (Per File/Group)

**Step 1: Stylelint Linting**
- [ ] Run `stylelint [file]` to identify CSS issues
- [ ] Fix any problems found (syntax, order, etc.)
- [ ] Proceed to Step 2

**Step 2: Prettier Formatting**
- [ ] Run `prettier --write [file]` to auto-format CSS
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

**Main Styles (`main.css`) - 1 hour:**
- [ ] Review file structure and organization
- [ ] Check for logical grouping of styles
- [ ] Verify proper use of CSS custom properties (variables)
- [ ] Review color consistency (use variables)
- [ ] Check for magic numbers (use named variables)
- [ ] Remove duplicate styles

**Advanced Table Styles (`advanced-table.css`, `advanced-table-sidebar.css`) - 1 hour:**
- [ ] Review component-specific organization
- [ ] Check for unused CSS rules
- [ ] Verify proper specificity (avoid `!important` overuse)
- [ ] Review selector performance
- [ ] Check for duplicate selectors across files

**Responsive Design (All Files):**
- [ ] Verify mobile-first approach
- [ ] Check breakpoint consistency
- [ ] Review media query organization
- [ ] Test on multiple screen sizes

**Performance & Optimization (All Files):**
- [ ] Remove unused vendor prefixes
- [ ] Optimize selectors for performance
- [ ] Check for CSS that could be simplified
- [ ] Verify efficient use of inheritance

**Naming Conventions (All Files):**
- [ ] Consistent naming (BEM, kebab-case, etc.)
- [ ] Remove bug reference comments
- [ ] Ensure comments are descriptive

**Step 5: Document & Loop (If Changes Made)**

If Step 4 resulted in modifications:
- [ ] Document what was changed and why
- [ ] Update any affected visual tests
- [ ] 🔄 **Loop back to Step 1** and repeat until file is perfect

If Step 4 resulted in NO modifications:
- [ ] Mark file as COMPLETE ✅
- [ ] Move to next file/group

#### Final Verification (After All Files Complete)
- [ ] Run `stylelint src/static/css/` (verify 0 errors)
- [ ] Visual regression test on all pages
- [ ] Test responsive design on multiple devices
- [ ] Verify no unused CSS (coverage tools)
- [ ] Document all findings in audit report
- [ ] Mark Phase 3 COMPLETE

**Deliverable:** Formatted, audited CSS codebase with documented findings

**File Tracking Template:**
```markdown
### [filename] Status
- [ ] Step 1: Stylelint
- [ ] Step 2: Prettier
- [ ] Step 3: Visual tests
- [ ] Step 4: Manual audit
- [ ] Step 5: Loop (if needed)
- [ ] COMPLETE ✅
```

---

### Phase 4: HTML Templates Analysis (Priority: High)
**Estimated Duration:** 2-3 days  
**Focus:** Iterative quality loop per file/group

**Strategy:** For each HTML template file or group of files, follow this iterative loop until perfect:

#### Iterative Quality Loop (Per File/Group)

**Step 1: HTML Validation**
- [ ] Run HTML validator (W3C or `html-validate`) on rendered output
- [ ] Fix any syntax errors or warnings
- [ ] Proceed to Step 2

**Step 2: Prettier Formatting**
- [ ] Run `prettier --write [file]` to auto-format HTML
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

**Base Template (`base.html`) - 30 min:**
- [ ] Review Jinja2 template inheritance structure
- [ ] Check for proper block definitions
- [ ] Verify meta tags and SEO elements
- [ ] Review script/style loading order

**List Pages (`assets.html`, `maintenance_orders.html`, `spare_parts.html`, `users.html`) - 2 hours:**
- [ ] Check for duplicate template blocks
- [ ] Verify proper use of includes and macros
- [ ] Review table structure and accessibility
- [ ] Check for inline JavaScript/CSS violations
- [ ] Verify proper form structure

**Detail Pages (`asset_detail.html`, `maintenance_order_detail.html`, etc.) - 2 hours:**
- [ ] Review form handling and validation
- [ ] Check for inline styles (`style="..."` attributes)
- [ ] Check for inline event handlers (`onclick="..."` attributes)
- [ ] Verify proper error message display
- [ ] Review template variable naming

**Specialized Pages (`shift_calendar.html`, `maintenance_grid.html`, `planning.html`) - 1 hour:**
- [ ] Review complex template logic
- [ ] Check for JavaScript extraction opportunities
- [ ] Verify proper data binding

**Separation of Concerns (All Files):**
- [ ] Identify inline JavaScript (`<script>` blocks in templates)
- [ ] Identify inline CSS (`<style>` blocks in templates)
- [ ] Identify inline styles (`style="..."` attributes)
- [ ] Identify inline event handlers (`onclick="..."` attributes)
- [ ] Create extraction plan for each violation

**HTML Quality & Standards (All Files):**
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
- [ ] Mark file as COMPLETE ✅
- [ ] Move to next file/group

#### Final Verification (After All Files Complete)
- [ ] Validate all rendered HTML (W3C validator)
- [ ] Run accessibility audit (axe DevTools or Lighthouse)
- [ ] Verify no inline JavaScript/CSS/styles remain
- [ ] Test all templates render without errors
- [ ] Document all findings in audit report
- [ ] Mark Phase 4 COMPLETE

**Deliverable:** Formatted, audited HTML templates with documented findings

**File Tracking Template:**
```markdown
### [filename] Status
- [ ] Step 1: HTML validation
- [ ] Step 2: Prettier
- [ ] Step 3: Render tests
- [ ] Step 4: Manual audit
- [ ] Step 5: Loop (if needed)
- [ ] COMPLETE ✅
```

---

### Phase 5: Root-Level & Configuration Files (Priority: High)
**Estimated Duration:** 1-2 days  
**Focus:** Iterative quality loop per file/group

**Strategy:** For each root-level file or group of files, follow this iterative loop until perfect:

#### Iterative Quality Loop (Per File/Group)

**Step 1: Format/Lint Check**
- [ ] Run appropriate linter for file type:
  - Python: `flake8 [file]`
  - Markdown: `markdownlint [file]`
  - JSON: `jsonlint [file]`
  - PowerShell: `PSScriptAnalyzer`
- [ ] Fix any problems found
- [ ] Proceed to Step 2

**Step 2: Auto-Formatting**
- [ ] Run appropriate formatter:
  - Python: `black [file]`
  - Markdown: `prettier --write [file]`
  - JSON: `prettier --write [file]`
- [ ] Review changes
- [ ] Proceed to Step 3

**Step 3: Functional Testing**
- [ ] Test file functionality:
  - `run.py`: Start application
  - `requirements.txt`: Install dependencies
  - `setup.ps1`: Run setup script
  - Documentation: Verify links and accuracy
- [ ] Verify no errors or warnings
- [ ] ✅ **Checkpoint:** After this step, linting/formatting/functionality should all pass

**Step 4: Manual Audit**

Focus on correctness, completeness, and patterns that tools can't catch:

**Application Entry Point (`run.py`) - 30 min:**
- [ ] Review structure and error handling
- [ ] Check for proper environment variable loading
- [ ] Verify development vs production configuration
- [ ] Review command-line argument handling
- [ ] Check security settings

**Dependency Management (`requirements.txt`, `requirements-dev.txt`) - 30 min:**
- [ ] Review organization and grouping
- [ ] Check for unused dependencies
- [ ] Verify version pinning strategy
- [ ] Run `pip-audit` for security vulnerabilities
- [ ] Check for outdated packages

**Configuration Files (`.env.example`, `.gitignore`) - 30 min:**
- [ ] Verify `.env.example` completeness
- [ ] Check for sensitive data patterns
- [ ] Review `.gitignore` coverage
- [ ] Verify all necessary files are ignored

**Documentation Files (`README.md`, `CHANGELOG.md`, `GEMINI.md`) - 1 hour:**
- [ ] Review accuracy and completeness
- [ ] Check CHANGELOG.md format and updates
- [ ] Verify GEMINI.md consistency with copilot-instructions.md
- [ ] Validate all cross-references and links
- [ ] Check for outdated information
- [ ] Verify setup instructions are current

**GitHub Configuration (`.github/` files) - 1 hour:**
- [ ] Review issue templates functionality
- [ ] Check CONTRIBUTING.md accuracy
- [ ] Verify GIT_WORKFLOW.md reflects actual practices
- [ ] Review CODEOWNERS assignments
- [ ] Check PR template completeness
- [ ] Verify workflow files (if any)

**Test Infrastructure (`tests/conftest.py`, `test_data/`) - 30 min:**
- [ ] Review pytest configuration
- [ ] Check test fixture organization
- [ ] Verify test data in `test_data/dummy_data.json`
- [ ] Review test coverage configuration

**Scripts & Automation (`scripts/setup.ps1`) - 30 min:**
- [ ] Review functionality and logic
- [ ] Check for error handling
- [ ] Verify cross-platform compatibility notes
- [ ] Check for hardcoded paths or values
- [ ] Review user feedback messages

**Step 5: Document & Loop (If Changes Made)**

If Step 4 resulted in modifications:
- [ ] Document what was changed and why
- [ ] Update any affected documentation
- [ ] 🔄 **Loop back to Step 1** and repeat until file is perfect

If Step 4 resulted in NO modifications:
- [ ] Mark file as COMPLETE ✅
- [ ] Move to next file/group

#### Final Verification (After All Files Complete)
- [ ] Run full application setup from scratch (test `setup.ps1`)
- [ ] Verify all documentation links work
- [ ] Run `pip-audit` for security vulnerabilities
- [ ] Test application startup with `run.py`
- [ ] Document all findings in audit report
- [ ] Mark Phase 5 COMPLETE

**Deliverable:** Formatted, audited root-level files with documented findings

**File Tracking Template:**
```markdown
### [filename] Status
- [ ] Step 1: Lint
- [ ] Step 2: Format
- [ ] Step 3: Functional test
- [ ] Step 4: Manual audit
- [ ] Step 5: Loop (if needed)
- [ ] COMPLETE ✅
```

---

### Phase 6: Cross-Cutting Concerns (Priority: Medium)
**Estimated Duration:** 1-2 days  
**Focus:** Iterative quality loop for consistency checks

**Strategy:** Perform cross-cutting analysis across all files, following iterative loop:

#### Iterative Quality Loop (Cross-Cutting)

**Step 1: Automated Consistency Checks**
- [ ] Run naming convention checker across all files
- [ ] Run duplicate code detector (jscpd) across entire codebase
- [ ] Check for inconsistent patterns
- [ ] Proceed to Step 2

**Step 2: Generate Consistency Report**
- [ ] Create report of naming violations
- [ ] List duplicate code blocks
- [ ] Identify inconsistent patterns
- [ ] Proceed to Step 3

**Step 3: Verify No Regressions**
- [ ] Run all tests (`pytest tests/`)
- [ ] Test application functionality
- [ ] Verify all previous phases still pass
- [ ] ✅ **Checkpoint:** After this step, all automated checks should pass

**Step 4: Manual Audit**

Focus on consistency and patterns across the entire codebase:

**Naming Conventions Audit (2 hours):**

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

**Environment Configuration (30 min):**
- [ ] Review `.env.example` completeness
- [ ] Check for sensitive data in version control
- [ ] Verify all environment variables are documented
- [ ] Review default values and fallbacks
- [ ] Cross-reference with actual usage in code

**Code Duplication Analysis (1 hour):**
- [ ] Review jscpd report for duplicate blocks
- [ ] Identify opportunities for refactoring
- [ ] Check for duplicate logic across Python/JavaScript
- [ ] Verify no duplicate CSS rules
- [ ] Check for duplicate template blocks

**Final Consistency Check (1 hour):**
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
- [ ] Mark Phase 6 as COMPLETE ✅

#### Final Verification (After All Checks Complete)
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
- [ ] Mark Phase 6 COMPLETE

**Deliverable:** Cross-cutting concerns audit report with final consistency verification

**Tracking Template:**
```markdown
### Cross-Cutting Concerns Status
- [ ] Step 1: Automated checks
- [ ] Step 2: Generate report
- [ ] Step 3: Verify no regressions
- [ ] Step 4: Manual audit
- [ ] Step 5: Loop (if needed)
- [ ] COMPLETE ✅
```

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
- [x] **Phase 0:** Automated Code Quality Analysis - ✅ COMPLETE (December 13, 2025)
- [ ] **Phase 1:** Python Backend Analysis - 🔄 IN PROGRESS
- [ ] **Phase 2:** JavaScript Frontend Analysis - PENDING
- [ ] **Phase 3:** CSS Styling Analysis - PENDING
- [ ] **Phase 4:** HTML Templates Analysis - PENDING
- [ ] **Phase 5:** Root-Level & Configuration Files - PENDING
- [ ] **Phase 6:** Cross-Cutting Concerns - PENDING

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

**Next Step:** Begin Phase 1 - Python Backend Analysis
