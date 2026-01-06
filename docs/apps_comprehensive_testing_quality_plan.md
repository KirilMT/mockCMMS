# Apps Comprehensive Testing & Quality Plan

**Created:** January 17, 2026
**Last Updated:** January 17, 2026
**Status:** 🔴 **PLANNING PHASE**
**Scope:** `apps/planning/` and `apps/reports/`
**Architecture:** Monorepo with independent app testing

---

> [!IMPORTANT]
> **📚 Related Documentation:**
> - **[Core Testing Plan](deprecated/comprehensive_testing_plan.md)** - Reference (261 tests, 82.99% coverage)
> - **[Core Audit Plan](deprecated/core_code_quality_plan.md)** - 5-step iterative loop methodology
> - **[Frontend Testing Plan](deprecated/frontend_testing_plan.md)** - Reference (519 tests, 80.8% coverage)
> - **[Implementation Guide](deprecated/IMPLEMENTATION_PRIORITY_GUIDE.md)** - Overall strategy
> - **[Task Spec](task_automated_specialized_reporting.md)** - Reports app requirements

---

## 📋 Overview & Objectives

### Context

**Planning App:** Imported from [WorkforceManager](https://github.com/KirilMT/WorkforceManager) and adapted to mockCMMS
- ✅ Has 11 backend test files (70 tests counted)
- ❌ **CRITICAL:** Tests use `Technician`/`TechnicianSkill` models (don't exist in mockCMMS)
- ❌ **CRITICAL:** Tests may not run at all (import errors expected)
- ❌ No frontend tests (Jest/Playwright)
- ❌ No security tests
- ❌ No performance tests
- ❌ No route/API tests
- ⚠️ Code quality audit status unknown

**Reports App:** Newly implemented by Google Jules
- ✅ Implementation complete (weekend/shift/incident reports)
- ⚠️ Only 5 basic tests in `test_reports.py`
- ❌ No unit tests (models, services)
- ❌ No integration tests
- ❌ No security tests
- ❌ No frontend tests
- ❌ No code quality audit

### Objectives

1. **Validate & Fix Planning Tests** - 70 existing tests likely broken, need rewrite
2. **Add Missing Planning Tests** - Security, performance, routes (43 tests)
3. **Build Reports Test Suite** - From scratch (76 backend + 20 frontend)
4. **Add Frontend Testing** - Both apps (60 total E2E tests)
5. **Code Quality Audit** - Apply 5-step loop to all files
6. **Achieve 80%+ Coverage** - Match core mockCMMS standards

---

## 🏗️ Monorepo Testing Architecture

### Directory Structure

```
mockCMMS/
├── apps/
│   ├── planning/
│   │   ├── src/
│   │   ├── tests/
│   │   │   ├── conftest.py
│   │   │   ├── unit/              # Reorganize existing
│   │   │   ├── functional/        # Reorganize existing
│   │   │   ├── integration/       # Reorganize existing
│   │   │   └── frontend/          # NEW
│   │   │       ├── unit/          # Jest
│   │   │       └── e2e/           # Playwright
│   │   ├── pytest.ini
│   │   └── .coveragerc
│   │
│   └── reports/
│       ├── src/
│       ├── tests/
│       │   ├── conftest.py
│       │   ├── unit/              # NEW
│       │   ├── functional/        # NEW
│       │   ├── integration/       # NEW
│       │   ├── security/          # NEW
│       │   └── frontend/          # NEW
│       │       └── e2e/           # Playwright
│       ├── pytest.ini
│       └── .coveragerc
│
├── pyproject.toml                 # Shared config
└── .flake8                        # Shared linting
```

### Execution Commands

```bash
# Planning app
cd apps/planning
pytest tests/                      # All tests
pytest tests/unit/                 # Unit only
pytest --cov=src --cov-report=html # With coverage

# Reports app
cd apps/reports
pytest tests/                      # All tests
pytest tests/unit/                 # Unit only
pytest --cov=src --cov-report=html # With coverage

# Linting (from root)
ruff check apps/planning/src/
ruff check apps/reports/src/
```

---

## 🎯 Phase 0: Prerequisites & Environment Setup

### Phase 0.1: Verify Core mockCMMS Integration

**Priority:** 🔴 **CRITICAL - MUST COMPLETE FIRST**

**Tasks:**

**Task 0.1.1: Verify Planning App Integration**
- [ ] Start mockCMMS: `python run.py`
- [ ] Verify Planning app loads: Navigate to `/planning`
- [ ] Check for errors in console/logs
- [ ] Verify database tables exist (Schedule, PlanningTask)
- [ ] Verify core models accessible (User, Skill, MaintenanceOrder)
- [ ] Document any integration issues

**Task 0.1.2: Verify Reports App Integration**
- [ ] Verify Reports app loads: Navigate to `/reports`
- [ ] Check for errors in console/logs
- [ ] Verify database tables exist (Incident)
- [ ] Verify core models accessible (MaintenanceOrder)
- [ ] Test basic functionality (create incident)
- [ ] Document any integration issues

**Task 0.1.3: Setup Test Environment**
- [ ] Install test dependencies: `pip install -r requirements-dev.txt`
- [ ] Verify pytest works: `pytest --version`
- [ ] Verify coverage works: `pytest --cov=src tests/backend/unit/ --cov-report=term`
- [ ] Install Playwright: `playwright install`
- [ ] Verify Playwright works: `playwright --version`
- [ ] Install Jest: `npm install` (if package.json exists)

**Task 0.1.4: Create Test Databases**
- [ ] Planning: Create `apps/planning/instance/test_planning.db`
- [ ] Reports: Create `apps/reports/instance/test_reports.db`
- [ ] Verify in-memory SQLite works in tests

**BLOCKERS - DO NOT PROCEED IF:**
- ❌ Apps don't load in browser
- ❌ Database tables missing
- ❌ Core models not accessible
- ❌ Test tools not installed

---

## 🎯 Phase 1: Planning App Test Validation & Update

### Phase 1.1: Test Audit & Validation

**Priority:** 🔴 **CRITICAL**

**Current Test Files (70 tests total):**
1. `test_core.py` (12 tests) - ❌ **DELETE** (marked deprecated, uses old SQLite)
2. `test_domain_models.py` (4 tests) - ❌ **BROKEN** (uses Technician/TechnicianSkill - don't exist)
3. `test_health.py` (11 tests) - ⚠️ **VALIDATE**
4. `test_integration.py` (1 test) - ⚠️ **VALIDATE**
5. `test_inventory_integration.py` (5 tests) - ⚠️ **VALIDATE**
6. `test_planning_engine.py` (11 tests) - ❌ **BROKEN** (uses Technician/TechnicianSkill - don't exist)
7. `test_planning_modes.py` (6 tests) - ⚠️ **VALIDATE**
8. `test_shift_rotation.py` (4 tests) - ⚠️ **VALIDATE**
9. `test_team_formation.py` (6 tests) - ⚠️ **VALIDATE**
10. `test_transformation_layer.py` (6 tests) - ⚠️ **VALIDATE**
11. `test_weekend_planning.py` (4 tests) - ⚠️ **VALIDATE**

**Critical Issue:** Tests reference `Technician`, `TechnicianSkill` models that don't exist in mockCMMS.
**mockCMMS uses:** `User` (with role='Technician'), `UserSkill`

**Validation Tasks:**

**Task 1.1.1: Run All Tests & Document Failures**
- [ ] Execute `pytest apps/planning/tests/ -v`
- [ ] **Expected:** Most/all tests will FAIL
- [ ] Document each failure:
  - Import errors (Technician, TechnicianSkill not found)
  - Model mismatches
  - Missing dependencies
  - Architecture incompatibilities
- [ ] Create failure report: `apps/planning/tests/TEST_FAILURES.md`
- [ ] Estimate rewrite effort per file

**Task 1.1.2: Analyze Failures**
- [ ] Check for old model references (Technician vs User)
- [ ] Check for old architecture patterns
- [ ] Check for missing dependencies
- [ ] Document required fixes per file

**Task 1.1.3: Fix or Delete (MAJOR REWRITE REQUIRED)**
- [ ] **DELETE** `test_core.py` (12 tests) - Already marked deprecated
- [ ] **REWRITE** `test_domain_models.py` (4 tests - 100% rewrite):
  - Remove all `Technician` references → `User(role='Technician')`
  - Remove all `TechnicianSkill` references → `UserSkill`
  - Remove `Shift` model tests (if using old model)
  - Add tests for Planning-specific models: `Schedule`, `PlanningTask`
  - Verify relationships: `User` ↔ `UserSkill` ↔ `Skill`
- [ ] **REWRITE** `test_planning_engine.py` (11 tests - 80% rewrite):
  - Replace all `Technician` → `User(role='Technician')`
  - Replace all `TechnicianSkill` → `UserSkill`
  - Update fixture: `sample_technicians` → `sample_users`
  - Update all assertions (technician_names → user names)
  - Verify all 11 tests pass
- [ ] **VALIDATE** remaining 8 test files (43 tests):
  - `test_health.py` (11 tests) - Check for model references
  - `test_integration.py` (1 test) - Full workflow validation
  - `test_inventory_integration.py` (5 tests) - Check SparePart integration
  - `test_planning_modes.py` (6 tests) - Validate shift/weekend logic
  - `test_shift_rotation.py` (4 tests) - Check team/technician references
  - `test_team_formation.py` (6 tests) - Check technician references
  - `test_transformation_layer.py` (6 tests) - Validate MO transformation
  - `test_weekend_planning.py` (4 tests) - Validate shift logic
  - Fix imports and model references
  - Update fixtures if needed
- [ ] Run full test suite: `pytest apps/planning/tests/ -v`
- [ ] **Target:** 100% pass rate (58 tests after deleting 12)

**Task 1.1.4: Reorganize Tests**
- [ ] Create `tests/unit/` directory
- [ ] Create `tests/functional/` directory
- [ ] Create `tests/integration/` directory
- [ ] Create `tests/security/` directory
- [ ] Create `tests/performance/` directory
- [ ] Move tests to appropriate directories:
  - **Unit:** `test_domain_models.py`
  - **Functional:** `test_planning_engine.py`, `test_planning_modes.py`
  - **Integration:** `test_integration.py`, `test_inventory_integration.py`, `test_shift_rotation.py`, `test_team_formation.py`, `test_transformation_layer.py`, `test_weekend_planning.py`
  - **Delete:** `test_core.py`, `test_health.py` (if redundant)
- [ ] Update imports in conftest.py
- [ ] Verify all tests still pass after reorganization

**Estimated:** 70 existing tests (15 rewrite + 43 validate + 12 delete = 58 remaining)

**CRITICAL BLOCKERS:**
- ❌ Tests use non-existent models (Technician, TechnicianSkill)
- ❌ Tests imported from WorkforceManager (different architecture)
- ❌ Tests likely won't run at all (import errors)
- ❌ Major rewrite required (not just fixes)
- ⚠️ Must run tests FIRST to assess damage
- ⚠️ Budget significant time for rewrites

### Phase 1.2: Missing Backend Tests

**Priority:** 🔴 **CRITICAL**

**Core mockCMMS has these test categories - Planning app is missing:**

**Missing Test Categories:**
- [ ] **Security Tests** (0 tests) - XSS, SQL injection, CSRF, authentication
- [ ] **Performance Tests** (0 tests) - Load testing, query optimization
- [ ] **Route Tests** (0 tests) - All `/planning` endpoints
- [ ] **API Tests** (0 tests) - All `/api/planning` endpoints
- [ ] **Error Handling Tests** (0 tests) - 404, 500, validation errors

**Required New Tests:**

**`tests/security/test_planning_security.py` (15 tests):**
- [ ] `test_xss_prevention_in_task_names`
- [ ] `test_sql_injection_prevention`
- [ ] `test_csrf_protection_on_forms`
- [ ] `test_authentication_required_for_planning`
- [ ] `test_authorization_technician_vs_supervisor`
- [ ] `test_file_upload_validation`
- [ ] `test_file_upload_size_limit`
- [ ] `test_file_upload_type_validation`
- [ ] `test_input_sanitization_task_data`
- [ ] `test_input_sanitization_technician_data`
- [ ] `test_session_management`
- [ ] `test_rate_limiting_api_endpoints`
- [ ] `test_secure_headers_present`
- [ ] `test_no_sensitive_data_in_logs`
- [ ] `test_password_hashing_if_applicable`

**`tests/functional/test_planning_routes.py` (20 tests):**
- [ ] `test_planning_index_loads`
- [ ] `test_planning_index_requires_auth`
- [ ] `test_manage_mappings_loads`
- [ ] `test_supervisor_dashboard_loads`
- [ ] `test_technician_dashboard_loads`
- [ ] `test_schedule_view_loads`
- [ ] `test_upload_excel_success`
- [ ] `test_upload_excel_invalid_file`
- [ ] `test_upload_excel_missing_data`
- [ ] `test_generate_plan_success`
- [ ] `test_generate_plan_no_tasks`
- [ ] `test_generate_plan_no_technicians`
- [ ] `test_export_schedule_csv`
- [ ] `test_export_schedule_pdf`
- [ ] `test_api_get_technicians`
- [ ] `test_api_get_tasks`
- [ ] `test_api_update_assignment`
- [ ] `test_api_delete_assignment`
- [ ] `test_404_invalid_route`
- [ ] `test_500_server_error_handling`

**`tests/performance/test_planning_performance.py` (8 tests):**
- [ ] `test_large_dataset_planning` (100+ tasks)
- [ ] `test_planning_engine_performance` (<5s for 50 tasks)
- [ ] `test_gantt_rendering_performance`
- [ ] `test_database_query_optimization`
- [ ] `test_concurrent_planning_requests`
- [ ] `test_memory_usage_large_schedules`
- [ ] `test_excel_parsing_performance`
- [ ] `test_dashboard_load_time`

**Estimated:** 43 new backend tests needed

### Phase 1.3: Frontend Testing (NEW)

**Priority:** 🔴 **CRITICAL**

**JavaScript Files to Test:**
- `static/js/index.js` (~200 lines)
- `static/js/manage_mappings_main.js` (~300 lines)
- `static/js/manage_mappings_globals.js`
- `static/js/manage_mappings_satellite_lines.js`
- `static/js/manage_mappings_task_technology.js`
- `static/js/manage_mappings_technician_data.js`
- `static/js/manage_mappings_technician_groups.js`
- `static/js/manage_mappings_technician_skills.js`
- `static/js/manage_mappings_technologies.js`
- `static/js/manage_mappings_utils.js`
- `static/js/planning-gantt.js` (~500 lines)
- `static/js/planning-gantt-custom.js` (~300 lines)

**Total:** ~12 JavaScript files, ~2000+ lines of code

**Test Structure:**
```
tests/frontend/
├── unit/                          # Jest
│   ├── index.test.js
│   ├── manage_mappings.test.js
│   └── planning_gantt.test.js
└── e2e/                           # Playwright
    ├── planning_workflow.spec.js
    ├── gantt_interactions.spec.js
    └── manage_mappings.spec.js
```

**E2E Test Scenarios:**

1. **Complete Planning Workflow**
   - [ ] Navigate to planning page
   - [ ] Upload Excel file (if applicable)
   - [ ] Trigger assignment
   - [ ] View results
   - [ ] Verify assignments

2. **Gantt Chart Interactions**
   - [ ] Load Gantt chart
   - [ ] Zoom in/out
   - [ ] Drag tasks
   - [ ] Filter by technician
   - [ ] Verify visual updates

3. **Manage Mappings CRUD**
   - [ ] Add technician
   - [ ] Assign skills
   - [ ] Update mappings
   - [ ] Delete mappings
   - [ ] Verify persistence

4. **Technician Dashboard**
   - [ ] Navigate to dashboard
   - [ ] View assigned tasks
   - [ ] Switch views (table/Gantt)
   - [ ] Verify data accuracy

5. **Supervisor Dashboard**
   - [ ] View all assignments
   - [ ] Filter by shift
   - [ ] Export report
   - [ ] Verify completeness

**Estimated:** ~40 frontend tests

### Phase 1.4: Code Quality Audit

**Priority:** 🟡 **HIGH**

**Tasks:**

**Task 1.4.1: Automated Analysis**
- [ ] Run `ruff check apps/planning/src/`
- [ ] Run `pylint apps/planning/src/`
- [ ] Run `mypy apps/planning/src/`
- [ ] Run `radon cc apps/planning/src/ -a`
- [ ] Run `bandit -r apps/planning/src/`
- [ ] Generate baseline metrics
- [ ] Categorize issues by severity

**Task 1.4.2: Python Backend Audit (5-Step Loop)**

**Files to Audit (13 files):**
- [ ] `src/routes/planning.py`
- [ ] `src/services/planning_engine.py`
- [ ] `src/services/planning_models.py`
- [ ] `src/services/planning_result.py`
- [ ] `src/services/task_assigner.py`
- [ ] `src/services/data_processing.py`
- [ ] `src/services/data_transformation.py`
- [ ] `src/services/dashboard.py`
- [ ] `src/services/planning_db_utils.py`
- [ ] `src/services/extract_data.py`
- [ ] `src/services/config_manager.py`
- [ ] `src/services/security.py`
- [ ] `src/services/seeding.py`

**Per File (5-Step Loop):**
1. **Lint:** `ruff check [file]` → Fix all issues
2. **Format:** `black [file]` → Review changes
3. **Test:** `pytest tests/` → All must pass ✅
4. **Audit:** Manual review
   - Logic correctness
   - Security vulnerabilities
   - Error handling
   - Code duplication
   - Performance issues
5. **Loop/Complete:** If changes → Step 1; else commit ✅

**Task 1.4.3: Frontend Audit**
- [ ] Audit all templates (no inline JS/CSS)
- [ ] Audit all JavaScript files (ESLint)
- [ ] Audit all CSS files (Stylelint)
- [ ] Verify accessibility
- [ ] Document findings

---

## 🎯 Phase 2: Reports App Comprehensive Testing

### Phase 2.1: Backend Test Expansion

**Priority:** 🔴 **CRITICAL**

**Current:** 1 file (`test_reports.py`) with 5 basic tests
**Target:** 76 comprehensive tests

**Test Structure:**
```
tests/
├── conftest.py                    # Fixtures
├── unit/
│   ├── test_models.py             # 9 tests
│   └── test_services.py           # 22 tests
├── functional/
│   └── test_routes.py             # 30 tests
├── integration/
│   └── test_workflows.py          # 5 tests
└── security/
    └── test_validation.py         # 10 tests
```

**Task 2.1.1: Setup Test Infrastructure**
- [ ] Create `tests/conftest.py` with fixtures:
  - `app` - Flask app with reports enabled
  - `client` - Test client
  - `db_session` - Database session
  - `sample_incident` - Sample incident
  - `sample_maintenance_order` - Sample MO from core
  - `auth_client` - Authenticated client
- [ ] Create `tests/unit/` directory
- [ ] Create `tests/functional/` directory
- [ ] Create `tests/integration/` directory
- [ ] Create `tests/security/` directory
- [ ] Create `pytest.ini` configuration
- [ ] Create `.coveragerc` configuration

**Task 2.1.2: Unit Tests (31 tests)**

**`tests/unit/test_models.py` (9 tests):**
- [ ] `test_incident_creation`
- [ ] `test_incident_to_dict`
- [ ] `test_incident_required_fields`
- [ ] `test_incident_default_values`
- [ ] `test_incident_timestamp_auto_set`
- [ ] `test_incident_resolved_default_false`
- [ ] `test_incident_string_representation`
- [ ] `test_incident_severity_validation`
- [ ] `test_incident_type_validation`

**`tests/unit/test_services.py` (22 tests):**

**DataAggregator (12 tests):**
- [ ] `test_get_weekend_tasks_empty`
- [ ] `test_get_weekend_tasks_with_data`
- [ ] `test_get_weekend_tasks_date_filtering`
- [ ] `test_get_shift_data_morning`
- [ ] `test_get_shift_data_afternoon`
- [ ] `test_get_shift_data_night`
- [ ] `test_get_shift_data_empty`
- [ ] `test_get_incidents_no_filters`
- [ ] `test_get_incidents_filter_by_type`
- [ ] `test_get_incidents_filter_by_severity`
- [ ] `test_get_incidents_filter_by_date_range`
- [ ] `test_get_incidents_multiple_filters`

**ReportGenerator (10 tests):**
- [ ] `test_generate_csv_with_tasks`
- [ ] `test_generate_csv_with_incidents`
- [ ] `test_generate_csv_empty_data`
- [ ] `test_generate_summary_stats_tasks`
- [ ] `test_generate_summary_stats_incidents`
- [ ] `test_generate_summary_stats_completion_rate`
- [ ] `test_generate_report_creates_file`
- [ ] `test_generate_report_pdf_placeholder`
- [ ] `test_generate_report_markdown`
- [ ] `test_reports_directory_creation`

**Task 2.1.3: Functional Tests (30 tests)**

**`tests/functional/test_routes.py` (30 tests):**

**Weekend Report (7 tests):**
- [ ] `test_weekend_report_get_default_dates`
- [ ] `test_weekend_report_get_custom_dates`
- [ ] `test_weekend_report_with_tasks`
- [ ] `test_weekend_report_empty`
- [ ] `test_weekend_report_export_csv`
- [ ] `test_weekend_report_export_pdf`
- [ ] `test_weekend_report_invalid_dates`

**Shift Report (8 tests):**
- [ ] `test_shift_report_get_morning`
- [ ] `test_shift_report_get_afternoon`
- [ ] `test_shift_report_get_night`
- [ ] `test_shift_report_with_data`
- [ ] `test_shift_report_empty`
- [ ] `test_shift_report_export_csv`
- [ ] `test_shift_report_export_pdf`
- [ ] `test_shift_report_invalid_shift`

**Incident Routes (11 tests):**
- [ ] `test_incident_list_empty`
- [ ] `test_incident_list_with_data`
- [ ] `test_incident_list_filter_by_type`
- [ ] `test_incident_list_filter_by_severity`
- [ ] `test_incident_new_form_loads`
- [ ] `test_incident_create_success`
- [ ] `test_incident_create_missing_fields`
- [ ] `test_incident_create_invalid_data`
- [ ] `test_incident_aggregate_report`
- [ ] `test_incident_aggregate_export_csv`
- [ ] `test_incident_aggregate_export_pdf`

**Original Reports (4 tests):**
- [ ] `test_reports_index_loads`
- [ ] `test_report_detail_loads`
- [ ] `test_report_generate_form`
- [ ] `test_report_generate_success`

**Task 2.1.4: Integration Tests (5 tests)**

**`tests/integration/test_workflows.py` (5 tests):**
- [ ] `test_complete_weekend_report_workflow`
- [ ] `test_complete_shift_report_workflow`
- [ ] `test_complete_incident_workflow`
- [ ] `test_cross_report_data_consistency`
- [ ] `test_report_with_core_app_data`

**Task 2.1.5: Security Tests (10 tests)**

**`tests/security/test_validation.py` (10 tests):**
- [ ] `test_incident_xss_prevention`
- [ ] `test_incident_sql_injection_prevention`
- [ ] `test_report_authentication_required`
- [ ] `test_report_authorization_checks`
- [ ] `test_incident_input_validation`
- [ ] `test_date_range_validation`
- [ ] `test_shift_parameter_validation`
- [ ] `test_export_file_path_traversal_prevention`
- [ ] `test_csv_injection_prevention`
- [ ] `test_report_data_sanitization`

### Phase 2.2: Frontend Testing (NEW)

**Priority:** 🟡 **HIGH**

**Test Structure:**
```
tests/frontend/
└── e2e/                           # Playwright
    ├── weekend_report.spec.js
    ├── shift_report.spec.js
    └── incident_workflow.spec.js
```

**E2E Test Scenarios:**

1. **Weekend Report E2E**
   - [ ] Navigate to weekend report
   - [ ] Select date range
   - [ ] View report data
   - [ ] Export CSV
   - [ ] Verify download

2. **Shift Report E2E**
   - [ ] Navigate to shift report
   - [ ] Select shift and date
   - [ ] View report data
   - [ ] Export PDF
   - [ ] Verify download

3. **Incident Workflow E2E**
   - [ ] Navigate to incident form
   - [ ] Fill out form
   - [ ] Submit incident
   - [ ] Verify in list
   - [ ] Filter incidents
   - [ ] Generate aggregate report
   - [ ] Export report

4. **Report Navigation E2E**
   - [ ] Test all navigation links
   - [ ] Verify breadcrumbs
   - [ ] Test back button

**Estimated:** ~20 frontend tests

### Phase 2.3: Code Quality Audit

**Priority:** 🔴 **CRITICAL**

**Task 2.3.1: Automated Analysis**
- [ ] Run `ruff check apps/reports/src/`
- [ ] Run `pylint apps/reports/src/`
- [ ] Run `mypy apps/reports/src/`
- [ ] Run `radon cc apps/reports/src/ -a`
- [ ] Run `bandit -r apps/reports/src/`
- [ ] Generate baseline metrics
- [ ] Categorize issues by severity

**Task 2.3.2: Python Backend Audit (5-Step Loop)**

**Files to Audit:**
- [ ] `src/models.py`
- [ ] `src/routes/reports.py`
- [ ] `src/routes/weekend_report.py`
- [ ] `src/routes/shift_report.py`
- [ ] `src/routes/incidents.py`
- [ ] `src/services/data_aggregator.py`
- [ ] `src/services/report_generator.py`

**Per File:**
1. Lint → 2. Format → 3. Test → 4. Audit → 5. Loop/Complete

**Task 2.3.3: Frontend Audit**
- [ ] Audit all templates (no inline JS/CSS)
- [ ] Audit CSS files
- [ ] Verify accessibility
- [ ] Document findings

---

## 🔧 Shared Configuration

### pytest.ini (Per App)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers --cov=src --cov-report=term --cov-report=html
markers =
    unit: Unit tests
    functional: Functional tests
    integration: Integration tests
    security: Security tests
    frontend: Frontend tests
```

### .coveragerc (Per App)

```ini
[run]
source = src
omit =
    */tests/*
    */conftest.py

[report]
precision = 2
show_missing = True

[html]
directory = htmlcov
```

### pyproject.toml (Root - Shared)

```toml
[tool.ruff]
line-length = 88
target-version = "py312"

[tool.black]
line-length = 88
target-version = ['py312']

[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
```

---

## 📊 Success Criteria

### Planning App

- [ ] All existing tests validated/fixed (70 tests → 58 after cleanup)
- [ ] Tests reorganized (unit/functional/integration/security/performance)
- [ ] 43 new backend tests implemented (security, routes, performance)
- [ ] 40 frontend tests implemented (Jest + Playwright)
- [ ] 80%+ backend coverage achieved
- [ ] 80%+ JavaScript coverage achieved
- [ ] All quality metrics met (ruff, pylint, bandit)
- [ ] 0 security vulnerabilities
- [ ] 100% test pass rate (58 backend + 43 new + 40 frontend = 141 total)

### Reports App

- [ ] 76 backend tests implemented
- [ ] 20 frontend tests implemented
- [ ] 80%+ backend coverage achieved
- [ ] All quality metrics met
- [ ] 0 security vulnerabilities
- [ ] All templates validated

### Quality Metrics (Both Apps)

- **Ruff:** 0 issues
- **Pylint:** 9.0+/10
- **Mypy:** 0 type errors
- **Radon:** Average complexity < 10
- **Bandit:** 0 critical/high security issues
- **Test Pass Rate:** 100%

---

## 🔄 5-Step Iterative Loop

### Standard Workflow (Per File)

1. **Lint:** Run `ruff check [file]` → Fix all issues
2. **Format:** Run `black [file]` → Review changes
3. **Test:** Run `pytest tests/` → All must pass ✅
4. **Audit:** Manual review (logic, security, patterns)
5. **Loop/Complete:** If changes → Step 1; else commit ✅

---

## 📈 Progress Tracking

### Phase 0: Prerequisites (MUST COMPLETE FIRST)

- [ ] Phase 0.1: Verify core integration & setup environment

**Blockers:** Apps must load, test tools must work

### Phase 1: Planning App

- [ ] Phase 1.1: Test validation & update (70 tests → 58 after cleanup)
- [ ] Phase 1.2: Missing backend tests (43 tests)
- [ ] Phase 1.3: Frontend testing (40 tests)
- [ ] Phase 1.4: Code quality audit

**Total Planning Tests:** 141 tests (58 existing + 43 new backend + 40 frontend)

### Phase 2: Reports App

- [ ] Phase 2.1: Backend test expansion (76 tests)
- [ ] Phase 2.2: Frontend testing (20 tests)
- [ ] Phase 2.3: Code quality audit

**Total Reports Tests:** 96 tests (76 backend + 20 frontend)

---

## 📊 Test Count Summary

### Planning App: 141 Total Tests

**Existing Tests: 70 tests (58 after cleanup)**
- `test_core.py`: 12 tests → **DELETE** (deprecated)
- `test_domain_models.py`: 4 tests → **REWRITE** (100%)
- `test_planning_engine.py`: 11 tests → **REWRITE** (80%)
- `test_health.py`: 11 tests → **VALIDATE**
- `test_integration.py`: 1 test → **VALIDATE**
- `test_inventory_integration.py`: 5 tests → **VALIDATE**
- `test_planning_modes.py`: 6 tests → **VALIDATE**
- `test_shift_rotation.py`: 4 tests → **VALIDATE**
- `test_team_formation.py`: 6 tests → **VALIDATE**
- `test_transformation_layer.py`: 6 tests → **VALIDATE**
- `test_weekend_planning.py`: 4 tests → **VALIDATE**
- **Subtotal:** 70 tests (15 rewrite + 43 validate - 12 delete = 58 remaining)

**New Backend Tests: 43 tests**
- Security: 15 tests
- Routes: 20 tests
- Performance: 8 tests

**New Frontend Tests: 40 tests**
- Jest unit: ~15 tests
- Playwright E2E: ~25 tests

### Reports App: 96 Total Tests

**Backend: 76 tests (ALL NEW)**
- Unit: 31 tests
  - Models: 9 tests
  - Services: 22 tests
- Functional: 30 tests
  - Weekend report: 7 tests
  - Shift report: 8 tests
  - Incident routes: 11 tests
  - Original reports: 4 tests
- Integration: 5 tests
- Security: 10 tests

**Frontend: 20 tests (ALL NEW)**
- Playwright E2E: 20 tests
  - Weekend report: 5 tests
  - Shift report: 5 tests
  - Incident workflow: 7 tests
  - Navigation: 3 tests

### Grand Total: 237 Tests

**Breakdown:**
- Planning: 141 tests (58 existing + 43 new backend + 40 frontend)
- Reports: 96 tests (76 backend + 20 frontend)

**Effort Estimate:**
- Planning: 15 tests to REWRITE + 43 tests to VALIDATE + 83 NEW tests
- Reports: 96 NEW tests (from scratch)
- **Total NEW/REWRITE:** 194 tests

**Comparison to Core mockCMMS:**
- Core: 780 tests (261 backend + 519 frontend) @ 82.99% coverage
- Apps: 237 tests (177 backend + 60 frontend) @ 80%+ target
- **Apps represent 30% of core test volume** (appropriate for modular apps)

---

**Status:** 🔴 **READY TO START** - Comprehensive plan complete
