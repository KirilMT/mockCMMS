# Apps Comprehensive Testing & Quality Plan

**Created:** January 17, 2026
**Last Updated:** March 12, 2026
**Status:** 🟡 **NEARLY COMPLETE** — ~23 tests remaining
**Scope:** `apps/planning/` and `apps/reports/`

---

> [!IMPORTANT]
> **📚 Related Documentation:**
>
> - **[Core Testing Plan](deprecated/comprehensive_testing_plan.md)** — Reference (261 tests, 82.99% coverage)
> - **[Core Audit Plan](deprecated/core_code_quality_plan.md)** — 5-step iterative loop methodology
> - **[Frontend Testing Plan](deprecated/frontend_testing_plan.md)** — Reference (519 tests, 80.8% coverage)
> - **[Visual Testing Strategy](visual_testing_strategy.md)** — Docker-based visual regression strategy

---

## 📋 Overview

### Context & Architecture Notes

**Planning App:** Imported from WorkforceManager and fully integrated into mockCMMS.

- Old `Technician`/`TechnicianSkill` model references have been replaced with `User`/`UserSkill`.
- Legacy files (`extract_data.py`, `dashboard.py`, `data_processing.py`) omitted from coverage — their tests removed.
- Tests organized in `unit/`, `functional/`, `integration/` subdirectories.

**Reports App:** Built and refactored. The Incidents module was removed during architecture redesign.

- Report storage is now database-driven (JSON column), not file-based.
- Unified Shift + Weekend report rendering pipeline.
- `test_reports_validation.py` (security) was removed and not replaced.

---

## 📊 Current Test Counts (March 12, 2026)

### Planning App

| Layer | Files | Test Functions |
| :---- | :---- | :------------ |
| Backend unit | 15 files | ~190 tests |
| Backend functional | 3 files | ~45 tests |
| Backend integration | 1 file | ~17 tests |
| Frontend Jest (unit) | 2 files | ~34 tests |
| Frontend Playwright (E2E) | 4 spec files | ~7 tests |
| **Total** | **25** | **~252 backend + ~41 frontend** |

### Reports App

| Layer | Files | Test Functions |
| :---- | :---- | :------------ |
| Backend unit | 3 files | ~80 tests |
| Backend functional | 5 files | ~118 tests |
| Frontend Jest (unit) | 2 files | ~55 tests |
| Frontend Playwright (E2E) | 6 spec files | ~13 tests |
| **Total** | **16** | **~198 backend + ~68 frontend** |

### Overall Coverage

**Last recorded: `89.97%`** (commit `5c49fca`) — exceeds 80% floor and 85% threshold.

---

## ✅ Completed Work

### Phase 0 — Prerequisites & Environment

- [x] Apps load at `/planning` and `/reports` without errors
- [x] DB tables exist (`Schedule`, `PlanningTask`, `Report`)
- [x] Core models accessible (`User`, `UserSkill`, `MaintenanceOrder`, `Asset`)
- [x] `conftest.py` with in-memory SQLite DB isolation (no production DB touched during tests)
- [x] Dynamic test skipping via `PLANNING_ENABLED` / `REPORTS_ENABLED` env vars
- [x] Playwright, Jest, pytest all configured and working

---

### Phase 1 — Planning App

#### 1.1 Test Validation & Rewrite

- [x] `test_core.py` deleted (deprecated, old SQLite)
- [x] `test_domain_models.py` rewritten — uses `User(role='Technician')` + `UserSkill`
- [x] `test_planning_engine.py` rewritten — all `Technician`/`TechnicianSkill` refs replaced
- [x] All remaining test files validated and updated for current architecture
- [x] Tests reorganized into `unit/`, `functional/`, `integration/` directories

#### 1.2 Backend Test Files

```
apps/planning/tests/
├── backend/
│   ├── conftest.py
│   ├── functional/
│   │   ├── test_planning_api.py
│   │   ├── test_planning_conditions_api.py
│   │   └── test_planning_routes.py
│   ├── integration/
│   │   └── test_inventory_integration.py
│   └── unit/
│       ├── test_app_factory.py
│       ├── test_assignment_strategy.py
│       ├── test_data_services.py
│       ├── test_domain_models.py
│       ├── test_planning_core.py
│       ├── test_planning_db_utils.py
│       ├── test_planning_engine_unit.py
│       ├── test_planning_health.py
│       ├── test_planning_logging.py
│       ├── test_planning_managers.py
│       ├── test_planning_services.py
│       ├── test_pm_strategy.py
│       ├── test_rep_strategy.py
│       ├── test_security.py
│       ├── test_shift_rotation.py
│       ├── test_strategies.py
│       ├── test_task_assigner.py
│       └── test_weekend_planning.py
```

#### 1.3 Frontend Tests

```
apps/planning/tests/frontend/
├── unit/
│   ├── gantt_custom.test.js
│   └── gantt_utils.test.js
└── e2e/
    ├── 00_visual.spec.js
    ├── 02_crud.spec.js
    ├── 03_smoke.spec.js
    └── planning_dashboard.spec.js
```

#### 1.4 Code Quality Audit

- [x] `ruff`, `black`, `isort`, `docformatter` passing for all files
- [x] `mypy` passing
- [x] `bandit` security scan passing
- [x] All templates pass `djlint --check` (0 issues)

---

### Phase 2 — Reports App

#### 2.1 Backend Test Files

```
apps/reports/tests/
├── conftest.py
├── backend/
│   ├── conftest.py
│   ├── functional/
│   │   ├── test_reports_routes.py
│   │   ├── test_reports_routes_exceptions_core.py
│   │   ├── test_reports_routes_exceptions_io.py
│   │   ├── test_reports_routes_exceptions_updates.py
│   │   └── test_shift_weekend_routes.py
│   └── unit/
│       ├── test_data_aggregator.py
│       ├── test_reports_generator.py
│       └── test_reports_seeding.py
```

#### 2.2 Frontend Tests

```
apps/reports/tests/frontend/
├── unit/
│   ├── report_interactions.test.js
│   └── reports.test.js
└── e2e/
    ├── 00_visual.spec.js
    ├── 02_crud.spec.js
    ├── 03_smoke.spec.js
    ├── incident_workflow.spec.js  ← kept for historical workflow coverage
    ├── shift_report.spec.js
    └── weekend_report.spec.js
```

#### 2.3 Code Quality Audit

- [x] `ruff`, `black`, `isort`, `docformatter` passing for all files
- [x] `mypy` passing
- [x] `bandit` security scan passing

---

## 🔧 Remaining Work (~23 tests)

> These are the only items **not yet implemented** from the original plan.

### Gap 1 — Planning Performance Tests (8 tests)

**File to create:** `apps/planning/tests/backend/performance/test_planning_performance.py`

| Test | Description |
| :--- | :---------- |
| `test_large_dataset_planning` | Plan with 100+ tasks completes without error |
| `test_planning_engine_performance` | 50-task plan completes in < 5 seconds |
| `test_gantt_rendering_performance` | Gantt endpoint responds in < 2 seconds |
| `test_database_query_optimization` | No N+1 queries on schedule fetch |
| `test_concurrent_planning_requests` | Two simultaneous plan requests don't corrupt state |
| `test_memory_usage_large_schedules` | Memory stays bounded on 200-task schedule |
| `test_excel_parsing_performance` | Large Excel file parsed in < 3 seconds |
| `test_dashboard_load_time` | Dashboard endpoint responds in < 2 seconds |

---

### Gap 2 — Reports Security Tests (10 tests)

**File to create:** `apps/reports/tests/backend/security/test_reports_security.py`

| Test | Description |
| :--- | :---------- |
| `test_xss_prevention_in_report_fields` | HTML entities escaped in report output |
| `test_sql_injection_prevention` | Parameterized queries block injection attempts |
| `test_authentication_required` | All report routes return 302/401 without login |
| `test_authorization_role_check` | Non-admin roles cannot delete reports |
| `test_report_input_validation` | Missing required fields return 400 |
| `test_date_range_validation` | Invalid date formats rejected |
| `test_shift_parameter_validation` | Invalid shift values rejected |
| `test_export_path_traversal_prevention` | `../` in export filename blocked |
| `test_csv_injection_prevention` | Formulas (=CMD) stripped from CSV export |
| `test_report_data_sanitization` | Unsafe characters sanitized before storage |

---

### Gap 3 — Reports Integration Tests (5 tests)

**File to create:** `apps/reports/tests/backend/integration/test_reports_workflows.py`

| Test | Description |
| :--- | :---------- |
| `test_complete_shift_report_workflow` | Create → populate → export shift report end-to-end |
| `test_complete_weekend_report_workflow` | Create → populate → export weekend report end-to-end |
| `test_report_with_core_app_data` | Report aggregates live MO/User data from core app |
| `test_cross_report_data_consistency` | Same MO appears consistently across shift and weekend |
| `test_report_update_and_retrieve` | Update report data, verify persisted on re-fetch |

---

## 📈 Progress Summary

| Phase | Status | Notes |
| :---- | :----- | :---- |
| Phase 0 — Prerequisites | ✅ Complete | All infra set up |
| Phase 1.1 — Planning test rewrite | ✅ Complete | Old models fully replaced |
| Phase 1.2 — Planning backend tests | ✅ Complete | 252 tests (target: 101) |
| Phase 1.3 — Planning frontend tests | ✅ Complete | Jest + Playwright in place |
| Phase 1.4 — Planning code quality | ✅ Complete | All linting/formatting passing |
| Phase 2.1 — Reports backend tests | ✅ Complete | 198 tests (target: 76) |
| Phase 2.2 — Reports frontend tests | ✅ Complete | Jest + Playwright in place |
| Phase 2.3 — Reports code quality | ✅ Complete | All linting/formatting passing |
| **Gap 1** — Planning performance | ❌ Not started | 8 tests needed |
| **Gap 2** — Reports security | ❌ Not started | 10 tests needed |
| **Gap 3** — Reports integration | ❌ Not started | 5 tests needed |

---

## 🏆 Success Criteria

| Metric | Target | Current |
| :----- | :----- | :------ |
| Overall coverage | ≥ 80% | **89.97%** ✅ |
| Test pass rate | 100% | **100%** ✅ |
| Ruff issues | 0 | **0** ✅ |
| Mypy errors | 0 | **0** ✅ |
| Bandit high/critical | 0 | **0** ✅ |
| Planning backend tests | ≥ 101 | **252** ✅ |
| Reports backend tests | ≥ 76 | **198** ✅ |
| Performance tests | 8 | **0** ❌ |
| Reports security tests | 10 | **0** ❌ |
| Reports integration tests | 5 | **0** ❌ |
