# Comprehensive Testing Plan for mockCMMS

**Created:** December 11, 2025  
**Last Updated:** December 12, 2025  
**Status:** 🔄 **IN PROGRESS** - Phase 1 Complete (96/144), Phase 2 In Progress (126/144)  
**Priority:** Critical

---

> [!IMPORTANT]
> **📚 Related Documentation:** This plan is part of a larger implementation strategy. For full context, see:
> - **[Implementation Priority Guide](IMPLEMENTATION_PRIORITY_GUIDE.md)** - Overall phased approach and timeline
> - **[mockCMMS Roadmap](mockCMMS_roadmap.md)** - Strategic features and current active work
> - **[Core Code Quality Plan](core_code_quality_plan.md)** - Postponed code audit (resumes after testing)
> 
> **Current Status:** This is the **active Phase 1 work** (Week 2 of implementation plan).

---

> [!TIP]
> **🤖 For AI Assistants:**
> 1. This plan defines **144 specific tests** that must be implemented (96 complete + 48 pending)
> 2. **Phase 1 (Days 1-6):** Foundation tests ✅ COMPLETE
> 3. **Phase 2 (Days 7-12):** Security & Robustness tests ⏳ CURRENT
> 4. After completing this plan, update the "ACTIVE WORK" section in `mockCMMS_roadmap.md`
> 5. Mark completed tests with `[x]` in this document
> 6. Once all tests pass, move to Week 3 Phase 2 (Code Quality) in `IMPLEMENTATION_PRIORITY_GUIDE.md`
> 7. Update `core_code_quality_plan.md` status from "Postponed" to "In Progress" when starting Week 3
> 8. **Need help navigating?** See [AI Agent Guide](AI_AGENT_GUIDE.md) for workflow details and example prompts

---

## 1. Overview & Objectives

This document outlines the strategy for creating a comprehensive, automated test suite for the core `mockCMMS` application. The primary objective is to establish a robust verification process that ensures code quality, prevents regressions, and enables safe refactoring and future development, including the postponed code formatting task.

This plan supersedes the previous code quality audit plan as the main priority.

### Key Objectives:
-   **High Test Coverage:** Achieve significant unit and integration test coverage for all core backend files (`run.py`, `app.py`, `routes/*.py`, `services/*.py`).
-   **Automated Verification:** Create a test suite that can be run automatically via `pytest` to validate the application's functionality from the command line.
-   **CI/CD Integration:** Ensure the new test suite is fully integrated into the existing GitHub Actions CI workflow.
-   **Enable Safe Refactoring:** Build the foundation required to safely perform large-scale changes, such as applying `black` formatting, with confidence.

---

## 1.1. Testing Philosophy: What Tests Actually Verify

> [!IMPORTANT]
> **Understanding Test Limitations:** The tests in this plan are **regression tests** written after code already exists. They verify **consistency** (behavior doesn't change) but NOT **correctness** (behavior is right). Complete code verification requires multiple complementary approaches.

### What Our Tests DO Verify ✅

1. **Regression Prevention** - Future changes won't break existing functionality
2. **Behavior Documentation** - Tests document how the system currently works
3. **API Contracts** - Tests show what data endpoints expect/return
4. **Safe Refactoring** - Code can be restructured without breaking features
5. **Syntax Correctness** - Code executes without runtime errors

### What Our Tests DON'T Verify ❌

1. **Business Logic Correctness** - Only that logic is CONSISTENT, not necessarily RIGHT
2. **Code Quality** - Tests don't check style, complexity, or maintainability
3. **Security Vulnerabilities** - Need dedicated security scanning tools
4. **Performance** - Need separate performance/load testing
5. **Requirements Compliance** - Need validation against business requirements

### Complete Verification Strategy (4 Phases)

Testing is just **Phase 1 of 4** in a complete code verification strategy:

```
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: Regression Tests (THIS PLAN)                   ✅    │
│  ─────────────────────────────────────────────────────────────  │
│  • Verify current behavior doesn't break                        │
│  • Document what code currently does                            │
│  • Provide safety net for refactoring                           │
│  • Tools: pytest, coverage.py                                   │
│  • Duration: Week 2 (Current)                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PHASE 2: Code Quality Analysis (Week 3)               ⏳      │
│  ─────────────────────────────────────────────────────────────  │
│  • Verify code style and syntax (linting)                       │
│  • Verify logic flow (type checking)                            │
│  • Measure code complexity                                      │
│  • Find code duplicates                                         ���
│  • Scan for security vulnerabilities                            │
│  • Tools: ruff, pylint, mypy, radon, bandit                     │
│  • See: core_code_quality_plan.md                               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PHASE 3: Requirements Validation (Week 4)             ⏳      │
│  ─────────────────────────────────────────────────────────────  │
│  • Review and document business requirements                    │
│  • Validate code logic against requirements                     │
│  • Add requirement-based test comments                          │
│  • Document design decisions and rationale                      │
│  • Create traceability matrix                                   │
│  • Tools: Manual review, requirement docs                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PHASE 4: Enhanced Testing (Week 5+)                   ⏳      │
│  ─────────────────────────────────────────────────────────────  │
│  • Add integration tests (complete workflows)                   │
│  • Add performance tests (load, stress testing)                 │
│  • Add security tests (penetration, vulnerability)              │
│  • Add edge case and boundary tests                             │
│  • Tools: pytest-benchmark, locust, OWASP ZAP                   │
└─────────────────────────────────────────────────────────────────┘
```

### Verification Methods Summary

| Method | What It Verifies | Tool/Phase |
|--------|-----------------|-----------|
| **Regression Tests** | Behavior consistency | pytest (Phase 1) |
| **Linting** | Code style & syntax | ruff, pylint (Phase 2) |
| **Type Checking** | Logic flow correctness | mypy (Phase 2) |
| **Complexity Analysis** | Code maintainability | radon (Phase 2) |
| **Duplicate Detection** | Code reusability | jscpd (Phase 2) |
| **Security Scanning** | Vulnerability detection | bandit (Phase 2) |
| **Requirements Review** | Business logic correctness | Manual (Phase 3) |
| **Code Review** | Overall quality | Human judgment (Phase 3) |
| **Integration Tests** | Workflow correctness | pytest (Phase 4) |
| **Performance Tests** | Speed & efficiency | pytest-benchmark (Phase 4) |

> [!NOTE]
> **Current Focus:** Phase 1 (Regression Tests). Phases 2-4 are documented in `IMPLEMENTATION_PRIORITY_GUIDE.md` and `core_code_quality_plan.md`.

---

## 2. Test Suite Statistics

**Total Tests:** 144 tests across 11 test files

### Breakdown by File:

**Phase 1: Foundation Tests (COMPLETED)**
-   `tests/test_app.py`: 18 tests ✅ **COMPLETED** (10 required + 8 bonus)
-   `tests/test_api_routes.py`: 41 tests ✅ **COMPLETED**
-   `tests/test_main_routes.py`: 29 tests ✅ **COMPLETED**
-   `tests/test_db_utils.py`: 3 tests ✅ **COMPLETED**
-   `tests/test_shift_utils.py`: 5 tests ✅ **COMPLETED**

**Phase 2: Security & Robustness Tests (IN PROGRESS)**
-   `tests/test_auth.py`: 8 tests ✅ **COMPLETED** 🔴 CRITICAL
-   `tests/test_validation.py`: 6 tests ✅ **COMPLETED** 🟡 HIGH
-   `tests/test_errors.py`: 6 tests ✅ **COMPLETED** 🟡 MEDIUM
-   `tests/test_integration.py`: 10 tests ✅ **COMPLETED** 🟡 MEDIUM
-   `tests/test_advanced_validation.py`: 10 tests ❌ **PENDING** 🟡 MEDIUM
-   `tests/test_performance.py`: 8 tests ❌ **PENDING** 🟢 LOW

**Current Progress:** 126/144 tests complete (87.5%)  
**Remaining Work:** 18 tests (Phase 2)  
**Coverage:** 75.29% (current), Target: 80%+ after Phase 2  
**Status:** Week 2 Extended - Security & Robustness Testing

---

## 3. Detailed Test Specifications

### 3.1. Application Tests (`tests/test_app.py`)

**Purpose:** Test the Flask application factory and configuration.

**Test Cases:** ✅ **Completed: December 11, 2025** (18 tests total: 10 required + 8 bonus)

1.  **[x] `test_create_app_default_config`** ✅
    -   Create app without specifying config
    -   Assert app is created successfully
    -   Assert default config values are set

2.  **[x] `test_create_app_testing_config`** ✅
    -   Create app with `TESTING=True`
    -   Assert testing mode is enabled
    -   Assert test database is used

3.  **[x] `test_database_initialization`** ✅
    -   Create app and initialize database
    -   Assert `db` object exists
    -   Assert database tables are created

4.  **[x] `test_blueprints_registered`** ✅
    -   Create app
    -   Assert `main_bp` is registered
    -   Assert `api_bp` is registered
    -   Assert `planning_bp` is registered (if enabled)
    -   Assert `reports_bp` is registered (if enabled)

5.  **[x] `test_secret_key_from_env`** ✅
    -   Set `SECRET_KEY` in environment
    -   Create app
    -   Assert app uses the environment's secret key

6.  **[x] `test_secret_key_fallback`** ✅
    -   Ensure `SECRET_KEY` is not in environment
    -   Create app
    -   Assert app generates a fallback secret key

7.  **[x] `test_database_uri_configuration`** ✅
    -   Create app
    -   Assert `SQLALCHEMY_DATABASE_URI` is set correctly

8.  **[x] `test_app_context`** ✅
    -   Create app
    -   Push app context
    -   Assert context is active
    -   Pop context

9.  **[x] `test_request_context`** ✅
    -   Create app
    -   Create request context
    -   Assert request context is active

10. **[x] `test_error_handlers_registered`** ✅
    -   Create app
    -   Assert 404 error handler exists
    -   Assert 500 error handler exists (if implemented)

**Bonus Tests Implemented:**
11. `test_csrf_protection_enabled_in_production`
12. `test_csrf_protection_disabled_in_testing`
13. `test_sqlalchemy_track_modifications_disabled`
14. `test_instance_folder_created`
15. `test_planning_blueprint_enabled`
16. `test_planning_blueprint_disabled`
17. `test_reports_blueprint_enabled`
18. `test_reports_blueprint_disabled`

**Estimated Tests:** 10 (Actual: 18)

---

### 3.2. API Endpoint Tests (`tests/test_api_routes.py`)

**Purpose:** Test all REST API endpoints for correct data handling, status codes, and error responses.

**✅ Completed: December 11, 2025** (41 tests, all passing)

**Test Structure:** For each endpoint, test:
1.  **Success case** (valid request, correct response)
2.  **Error case** (invalid data, missing data, not found, etc.)

**🐛 Bugs Fixed by Tests:**
- Fixed Asset API: Changed `location` → `asset_code`, `asset_type`, `cost_center`
- Fixed SparePart API: Changed `name`/`quantity` → `description`/`stock_quantity`

#### Assets API (`/v1/assets`)

1.  **[x] `test_get_assets_empty`** ✅
    -   GET `/v1/assets` with no assets in database
    -   Assert 200 status
    -   Assert empty list returned

2.  **[x] `test_get_assets_with_data`** ✅
    -   Add 3 assets to database
    -   GET `/v1/assets`
    -   Assert 200 status
    -   Assert 3 assets returned
    -   Assert each asset has required fields

3.  **[x] `test_get_asset_by_id_success`** ✅
    -   Add an asset to database
    -   GET `/v1/assets/<id>`
    -   Assert 200 status
    -   Assert correct asset data returned

4.  **[x] `test_get_asset_by_id_not_found`** ✅
    -   GET `/v1/assets/999` (non-existent ID)
    -   Assert 404 status
    -   Assert error message returned

5.  **[x] `test_add_asset_success`** ✅
    -   POST `/v1/assets` with valid data
    -   Assert 201 status
    -   Assert asset created in database
    -   Assert returned data matches input

6.  **[x] `test_add_asset_missing_name`** ✅
    -   POST `/v1/assets` without `name` field
    -   Assert 400 status
    -   Assert error message about missing name

7.  **[x] `test_update_asset_success`** ✅
    -   Add an asset to database
    -   PUT `/v1/assets/<id>` with updated data
    -   Assert 200 status
    -   Assert asset updated in database

8.  **[x] `test_update_asset_not_found`** ✅
    -   PUT `/v1/assets/999` with valid data
    -   Assert 404 status

9.  **[x] `test_delete_asset_success`** ✅
    -   Add an asset to database
    -   DELETE `/v1/assets/<id>`
    -   Assert 200 status
    -   Assert asset removed from database

10. **[x] `test_delete_asset_not_found`** ✅
    -   DELETE `/v1/assets/999`
    -   Assert 404 status

#### Maintenance Orders API (`/v1/mos`)

11. **[x] `test_get_mos_empty`** ✅
    -   GET `/v1/mos` with no MOs in database
    -   Assert 200 status
    -   Assert empty list returned

12. **[x] `test_get_mos_with_data`** ✅
    -   Add 3 MOs to database
    -   GET `/v1/mos`
    -   Assert 200 status
    -   Assert 3 MOs returned

13. **[x] `test_get_mo_by_id_success`** ✅
    -   Add an MO to database
    -   GET `/v1/mos/<id>`
    -   Assert 200 status
    -   Assert correct MO data returned

14. **[x] `test_get_mo_by_id_not_found`** ✅
    -   GET `/v1/mos/999`
    -   Assert 404 status

15. **[x] `test_add_mo_success`** ✅
    -   POST `/v1/mos` with valid data (asset_id, description, order_type)
    -   Assert 201 status
    -   Assert MO created in database

16. **[x] `test_add_mo_missing_required_fields`** ✅
    -   POST `/v1/mos` without `asset_id`
    -   Assert 400 status

17. **[x] `test_add_mo_with_skills`** ✅
    -   POST `/v1/mos` with `required_skills` array
    -   Assert 201 status
    -   Assert skills associated with MO

18. **[x] `test_update_mo_success`** ✅
    -   Add an MO to database
    -   PUT `/v1/mos/<id>` with updated data
    -   Assert 200 status
    -   Assert MO updated in database

19. **[x] `test_update_mo_not_found`** ✅
    -   PUT `/v1/mos/999` with valid data
    -   Assert 404 status

20. **[x] `test_delete_mo_success`** ✅
    -   Add an MO to database
    -   DELETE `/v1/mos/<id>`
    -   Assert 200 status
    -   Assert MO removed from database

21. **[x] `test_delete_mo_not_found`** ✅
    -   DELETE `/v1/mos/999`
    -   Assert 404 status

#### Spare Parts API (`/v1/spare_parts`)

22. **[x] `test_get_spare_parts_empty`** ✅
    -   GET `/v1/spare_parts`
    -   Assert 200 status
    -   Assert empty list

23. **[x] `test_get_spare_parts_with_data`** ✅
    -   Add 3 spare parts to database
    -   GET `/v1/spare_parts`
    -   Assert 200 status
    -   Assert 3 parts returned

24. **[x] `test_get_spare_part_by_id_success`** ✅
    -   Add a spare part to database
    -   GET `/v1/spare_parts/<id>`
    -   Assert 200 status

25. **[x] `test_get_spare_part_by_id_not_found`** ✅
    -   GET `/v1/spare_parts/999`
    -   Assert 404 status

26. **[x] `test_add_spare_part_success`** ✅
    -   POST `/v1/spare_parts` with valid data
    -   Assert 201 status

27. **[x] `test_add_spare_part_missing_required_fields`** ✅
    -   POST `/v1/spare_parts` without required fields
    -   Assert 400 status

28. **[x] `test_update_spare_part_success`** ✅
    -   Add a spare part to database
    -   PUT `/v1/spare_parts/<id>` with updated data
    -   Assert 200 status

29. **[x] `test_update_spare_part_not_found`** ✅
    -   PUT `/v1/spare_parts/999`
    -   Assert 404 status

30. **[x] `test_delete_spare_part_success`** ✅
    -   Add a spare part to database
    -   DELETE `/v1/spare_parts/<id>`
    -   Assert 200 status

31. **[x] `test_delete_spare_part_not_found`** ✅
    -   DELETE `/v1/spare_parts/999`
    -   Assert 404 status

#### Users API (`/v1/users`)

32. **[x] `test_get_users_empty`** ✅
    -   GET `/v1/users`
    -   Assert 200 status
    -   Assert empty list

33. **[x] `test_get_users_with_data`** ✅
    -   Add 3 users to database
    -   GET `/v1/users`
    -   Assert 200 status
    -   Assert 3 users returned

34. **[x] `test_get_user_by_id_success`** ✅
    -   Add a user to database
    -   GET `/v1/users/<id>`
    -   Assert 200 status

35. **[x] `test_get_user_by_id_not_found`** ✅
    -   GET `/v1/users/999`
    -   Assert 404 status

36. **[x] `test_add_user_success`** ✅
    -   POST `/v1/users` with valid data
    -   Assert 201 status

37. **[x] `test_add_user_missing_required_fields`** ✅
    -   POST `/v1/users` without username
    -   Assert 400 status

38. **[x] `test_update_user_success`** ✅
    -   Add a user to database
    -   PUT `/v1/users/<id>` with updated data
    -   Assert 200 status

39. **[x] `test_update_user_not_found`** ✅
    -   PUT `/v1/users/999`
    -   Assert 404 status

40. **[x] `test_delete_user_success`** ✅
    -   Add a user to database
    -   DELETE `/v1/users/<id>`
    -   Assert 200 status

41. **[x] `test_delete_user_not_found`** ✅
    -   DELETE `/v1/users/999`
    -   Assert 404 status

**Estimated Tests:** 41

---

### 3.3. Web Routes Tests (`tests/test_main_routes.py`)

**Purpose:** Test all web page routes for correct rendering and form handling.

**✅ Completed: December 11, 2025** (29 tests, all passing - 100%)

**Test Cases:**

#### General Pages

1.  **[x] `test_index_page_loads`** ✅
    -   GET `/`
    -   Assert 200 status
    -   Assert "Dashboard" or expected content in response

2.  **[x] `test_tickets_page_loads`** ✅
    -   GET `/tickets/TICKET-001`
    -   Assert 200 status

3.  **[x] `test_maintenance_grid_page_loads`** ✅
    -   GET `/maintenance_grid/1,2,3`
    -   Assert 200 status

#### Assets Pages

4.  **[x] `test_assets_list_page_loads`** ✅
    -   GET `/assets`
    -   Assert 200 status
    -   Assert page contains assets table or expected content

5.  **[x] `test_assets_add_page_get`** ✅
    -   GET `/assets/add`
    -   Assert 200 status
    -   Assert form is present

6.  **[x] `test_assets_add_page_post_success`** ✅
    -   POST `/assets/add` with valid form data
    -   Assert redirect to assets list (302 or 303)
    -   Assert asset created in database

7.  **[x] `test_assets_add_page_post_validation_error`** ✅
    -   POST `/assets/add` with invalid data
    -   Assert 200 status (form re-rendered with errors)
    -   Assert error message displayed

8.  **[x] `test_asset_detail_page_loads`** ✅
    -   Add an asset to database
    -   GET `/assets/<id>`
    -   Assert 200 status
    -   Assert asset details displayed

9.  **[x] `test_asset_detail_page_not_found`** ✅
    -   GET `/assets/999`
    -   Assert 404 status

10. **[x] `test_asset_edit_page_get`** ✅
    -   Add an asset to database
    -   GET `/assets/<id>/edit`
    -   Assert 200 status
    -   Assert form pre-filled with asset data

11. **[x] `test_asset_edit_page_post_success`** ✅
    -   Add an asset to database
    -   POST `/assets/<id>/edit` with updated data
    -   Assert redirect
    -   Assert asset updated in database

12. **[x] `test_asset_delete_post_success`** ✅
    -   Add an asset to database
    -   POST `/assets/<id>/delete`
    -   Assert redirect
    -   Assert asset removed from database

#### Maintenance Orders Pages

13. **[x] `test_mos_list_page_loads`** ✅
    -   GET `/maintenance_orders`
    -   Assert 200 status

14. **[x] `test_mo_add_page_get`** ✅
    -   GET `/maintenance_orders/add`
    -   Assert 200 status
    -   Assert form is present

15. **[x] `test_mo_add_page_post_success`** ✅
    -   Add an asset to database
    -   POST `/maintenance_orders/add` with valid data
    -   Assert redirect
    -   Assert MO created in database

16. **[x] `test_mo_detail_page_loads`** ✅
    -   Add an MO to database
    -   GET `/maintenance_orders/<id>`
    -   Assert 200 status

17. **[x] `test_mo_edit_page_get`** ✅
    -   Add an MO to database
    -   GET `/maintenance_orders/<id>/edit`
    -   Assert 200 status

18. **[x] `test_mo_edit_page_post_success`** ✅
    -   Add an MO to database
    -   POST `/maintenance_orders/<id>/edit` with updated data
    -   Assert redirect
    -   Assert MO updated in database

19. **[x] `test_mo_delete_post_success`** ✅
    -   Add an MO to database
    -   POST `/maintenance_orders/<id>/delete`
    -   Assert redirect
    -   Assert MO removed from database

#### Spare Parts Pages

20. **[x] `test_spare_parts_list_page_loads`** ✅
    -   GET `/spare_parts`
    -   Assert 200 status

21. **[x] `test_spare_part_add_page_get`** ✅
    -   GET `/spare_parts/add`
    -   Assert 200 status

22. **[x] `test_spare_part_add_page_post_success`** ✅
    -   POST `/spare_parts/add` with valid data
    -   Assert redirect
    -   Assert spare part created in database

23. **[x] `test_spare_part_detail_page_loads`** ✅
    -   Add a spare part to database
    -   GET `/spare_parts/<id>`
    -   Assert 200 status

24. **[x] `test_spare_part_edit_page_get`** ✅
    -   Add a spare part to database
    -   GET `/spare_parts/<id>/edit`
    -   Assert 200 status

25. **[x] `test_spare_part_edit_page_post_success`** ✅
    -   Add a spare part to database
    -   POST `/spare_parts/<id>/edit` with updated data
    -   Assert redirect
    -   Assert spare part updated in database

26. **[x] `test_spare_part_delete_post_success`** ✅
    -   Add a spare part to database
    -   POST `/spare_parts/<id>/delete`
    -   Assert redirect
    -   Assert spare part removed from database

#### Users Pages

27. **[x] `test_users_list_page_loads`** ✅
    -   GET `/users`
    -   Assert 200 status

28. **[x] `test_register_page_get`** ✅
    -   GET `/register`
    -   Assert 200 status
    -   Assert registration form is present

29. **[x] `test_register_page_post_success`** ✅
    -   POST `/register` with valid data
    -   Assert redirect
    -   Assert user created in database

**Estimated Tests:** 29

---

### 3.4. Database Utilities Tests (`tests/test_db_utils.py`)

**Purpose:** Test database utility functions and data population.

**✅ Completed: December 12, 2025** (3 tests, all passing)

**Test Cases:**

1.  **[x] `test_populate_dummy_data`** ✅
    -   Call `populate_dummy_data(logger)`
    -   Assert database is populated with sample data
    -   Assert assets exist
    -   Assert MOs exist
    -   Assert users exist

2.  **[x] `test_populate_dummy_data_idempotent`** ✅
    -   Call `populate_dummy_data(logger)` twice
    -   Assert unique constraints are enforced
    -   Verify IntegrityError is raised (expected behavior - not truly idempotent)

3.  **[x] `test_database_models_relationships`** ✅
    -   Create an Asset
    -   Create a MaintenanceOrder linked to that Asset
    -   Assert relationship works correctly
    -   Assert cascade behavior (cascade delete verified)

**Estimated Tests:** 3

---

### 3.5. Shift Utilities Tests (`tests/test_shift_utils.py`)

**Purpose:** Test shift calculation and rotation logic.

**✅ Completed: December 12, 2025** (5 tests, all passing)

**Test Cases:**

1.  **[x] `test_get_shift_teams_shift_a`** ✅
    -   Call `get_shift_teams(date, teams)` for a date that should be Shift A
    -   Assert correct shift team returned

2.  **[x] `test_get_shift_teams_shift_b`** ✅
    -   Call `get_shift_teams(date, teams)` for a date that should be Shift B
    -   Assert correct shift team returned

3.  **[x] `test_get_shift_teams_shift_c`** ✅
    -   Call `get_shift_teams(date, teams)` for a date that should be Shift C
    -   Assert correct shift team returned

4.  **[x] `test_get_shift_teams_rotation_cycle`** ✅
    -   Call `get_shift_teams(date, teams)` for multiple consecutive dates
    -   Assert correct rotation pattern (verified across weeks)

5.  **[x] `test_get_shift_teams_invalid_input`** ✅
    -   Call `get_shift_teams(None, teams)`
    -   Assert handles gracefully and returns None for missing teams

**Estimated Tests:** 5

---

### 3.6. Authentication & Security Tests (`tests/test_auth.py`)

**Purpose:** Test authentication, authorization, and security features.

**🔴 CRITICAL PRIORITY** - These tests are essential for production security.

**✅ Completed: December 12, 2025** (8 tests, all passing)

**Test Cases:**

1.  **[x] `test_login_success`** ✅
    -   POST to `/login` with valid credentials
    -   Assert 200/302 status (success or redirect)
    -   Assert session is created
    -   Assert user is logged in

2.  **[x] `test_login_invalid_credentials`** ✅
    -   POST to `/login` with invalid password
    -   Assert 401/403 status or error message
    -   Assert session is NOT created
    -   Assert user is NOT logged in

3.  **[x] `test_logout`** ✅
    -   Login first
    -   POST to `/logout`
    -   Assert session is destroyed
    -   Assert user is logged out
    -   Assert redirect to login page

4.  **[x] `test_protected_route_requires_auth`** ✅
    -   Access protected route without login
    -   Assert 401/403 status or redirect to login
    -   Login and try again
    -   Assert 200 status (access granted)

5.  **[x] `test_admin_only_route_blocks_technician`** ✅
    -   Login as Technician role
    -   Access admin-only route
    -   Assert 403 status (forbidden)
    -   Login as Admin role
    -   Assert 200 status (access granted)

6.  **[x] `test_password_hashing`** ✅
    -   Create user with password
    -   Assert password is hashed (not plain text in DB)
    -   Assert hash verification works
    -   Assert incorrect password fails verification

7.  **[x] `test_session_management`** ✅
    -   Login and get session cookie
    -   Make authenticated request with session
    -   Assert request succeeds
    -   Logout and try same session
    -   Assert session is invalid

8.  **[x] `test_csrf_protection`** ✅
    -   POST to form without CSRF token
    -   Assert 400/403 status (CSRF validation fails)
    -   POST with valid CSRF token
    -   Assert 200 status (request succeeds)

**Estimated Tests:** 8

---

### 3.7. Data Validation Tests (`tests/test_validation.py`)

**Purpose:** Test input validation and security against common attacks.

**🟡 HIGH PRIORITY** - Prevents data corruption and security vulnerabilities.

**✅ Completed: December 12, 2025** (6 tests, all passing)

**Test Cases:**

1.  **[x] `test_sql_injection_prevention`** ✅
    -   Submit form with SQL injection payload (e.g., `'; DROP TABLE assets; --`)
    -   Assert payload is escaped/sanitized
    -   Assert database is not affected
    -   Assert data is stored safely

2.  **[x] `test_xss_prevention`** ✅
    -   Submit form with XSS payload (e.g., `<script>alert('XSS')</script>`)
    -   Assert payload is escaped in HTML output
    -   Assert script does not execute
    -   Assert data is displayed safely

3.  **[x] `test_required_fields_validation`** ✅
    -   POST to create asset without required field (e.g., no name)
    -   Assert 400 status or validation error
    -   Assert error message indicates missing field
    -   Assert database record is NOT created

4.  **[x] `test_unique_constraint_handling`** ✅
    -   Create asset with asset_code "TEST-001"
    -   Try to create another asset with same code
    -   Assert 400/409 status or validation error
    -   Assert error message indicates duplicate
    -   Assert only one record exists

5.  **[x] `test_data_type_validation`** ✅
    -   POST asset with invalid data type (e.g., string for integer field)
    -   Assert 400 status or validation error
    -   Assert error message indicates type mismatch

6.  **[x] `test_max_length_validation`** ✅
    -   POST asset with name exceeding max length (256+ chars)
    -   Assert 400 status or validation error
    -   Assert data is not truncated silently

**Estimated Tests:** 6

---

### 3.8. Error Handling Tests (`tests/test_errors.py`)

**Purpose:** Test error pages and exception handling.

**🟡 MEDIUM PRIORITY** - Ensures graceful failure and good UX.

**✅ Completed: December 12, 2025** (6 tests, all passing)

**Test Cases:**

1.  **[x] `test_404_page_renders`** ✅
    -   GET non-existent route (e.g., `/nonexistent`)
    -   Assert 404 status
    -   Assert custom 404 page renders
    -   Assert page contains helpful message

2.  **[x] `test_500_error_handling`** ✅
    -   Trigger server error (e.g., force exception in route)
    -   Assert 500 status
    -   Assert custom 500 page renders (if implemented)
    -   Assert error is logged

3.  **[x] `test_database_error_recovery`** ✅
    -   Simulate database error (e.g., disconnect)
    -   Make request that requires database
    -   Assert graceful error handling
    -   Assert error message to user

4.  **[x] `test_invalid_id_handling`** ✅
    -   GET asset detail with invalid ID (e.g., 999999)
    -   Assert 404 status
    -   Assert error message displayed
    -   GET asset with non-integer ID (e.g., "abc")
    -   Assert 400/404 status

5.  **[x] `test_concurrent_update_conflict`** ✅
    -   Load asset for editing (timestamp T1)
    -   Another user updates same asset (timestamp T2)
    -   Submit first edit
    -   Assert conflict detection or last-write-wins behavior

6.  **[x] `test_transaction_rollback_on_error`** ✅
    -   Start transaction to create MO with invalid data
    -   Assert transaction is rolled back
    -   Assert database is unchanged
    -   Assert no partial data is saved

**Estimated Tests:** 6

---

### 3.9. Integration Tests (`tests/test_integration.py`)

**Purpose:** Test complete workflows and multi-step processes.

**🟡 MEDIUM PRIORITY** - Validates end-to-end functionality.

**✅ Completed: December 12, 2025** (10 tests, all passing)

**Test Cases:**

1.  **[x] `test_complete_maintenance_workflow`** ✅
    -   Create asset
    -   Create maintenance order for asset
    -   Assign technician to MO
    -   Update MO status to "In Progress"
    -   Complete MO
    -   Assert all state transitions work
    -   Assert data consistency throughout

2.  **[x] `test_user_registration_to_assignment`** ✅
    -   Register new user as Technician
    -   Assign skill to technician
    -   Assign technician to team
    -   Create MO requiring that skill
    -   Assign MO to technician
    -   Assert complete user lifecycle works

3.  **[x] `test_asset_lifecycle`** ✅
    -   Create new asset
    -   Create PM schedule for asset
    -   Generate MOs from schedule
    -   Complete MOs
    -   Update asset status to "Maintenance"
    -   Complete maintenance and return to "Operational"
    -   Assert asset state tracking works

4.  **[x] `test_data_flow_across_modules`** ✅
    -   Create spare part
    -   Create MO requiring that spare part
    -   Link spare part to MO
    -   Complete MO
    -   Assert spare part inventory is updated
    -   Assert data flows correctly between modules

5.  **[x] `test_planning_integration`** ✅
    -   Create multiple MOs with different skills
    -   Create technicians with various skills
    -   Trigger planning/assignment logic
    -   Assert MOs are assigned based on skills
    -   Assert workload distribution is balanced

6.  **[x] `test_shift_team_rotation_workflow`** ✅
    -   Create teams with shift assignments
    -   Query shift for specific dates
    -   Create MOs for those dates
    -   Assert MOs are assigned to correct shift
    -   Assert rotation pattern is followed

7.  **[x] `test_cascade_relationships`** ✅
    -   Create asset with multiple MOs
    -   Delete asset
    -   Assert cascade delete of MOs (or prevention)
    -   Create MO with spare parts
    -   Delete MO
    -   Assert spare parts are handled correctly

8.  **[x] `test_multi_user_concurrent_access`** ✅
    -   Two users access same asset simultaneously
    -   Both try to edit
    -   Assert concurrent access is handled
    -   Assert data integrity maintained

9.  **[x] `test_reports_integration`** ✅
    -   Create MOs with different statuses
    -   Generate report
    -   Assert report contains correct data
    -   Assert report filters work
    -   Assert export functionality works

10. **[x] `test_search_and_filter_integration`** ✅
    -   Create assets with various attributes
    -   Search by name, code, type
    -   Filter by status, cost center
    -   Assert search results are correct
    -   Assert filters work in combination

**Estimated Tests:** 10-12

---

### 3.10. Advanced Validation Tests (`tests/test_advanced_validation.py`)

**Purpose:** Test boundary conditions, edge cases, and advanced scenarios.

**🟡 MEDIUM PRIORITY** - Ensures robustness under edge conditions.

**Test Cases:**

1.  **[ ] `test_boundary_conditions`**
    -   Create asset with minimum valid values
    -   Create asset with maximum valid values
    -   Assert both are accepted
    -   Try just beyond boundaries
    -   Assert validation rejects

2.  **[ ] `test_null_and_none_handling`**
    -   Submit form with null/None values in optional fields
    -   Assert nulls are handled gracefully
    -   Query data with null values
    -   Assert queries work correctly

3.  **[ ] `test_empty_string_validation`**
    -   POST asset with empty string for required field
    -   Assert validation rejects
    -   POST with whitespace-only string
    -   Assert validation rejects

4.  **[ ] `test_concurrent_updates`**
    -   Two requests update same asset simultaneously
    -   Assert no data loss
    -   Assert integrity is maintained
    -   Assert last-write-wins or optimistic locking works

5.  **[ ] `test_transaction_rollbacks`**
    -   Create MO with invalid related data
    -   Assert transaction is rolled back
    -   Assert partial data is not saved
    -   Assert database is consistent

6.  **[ ] `test_cascade_delete_prevention`**
    -   Create asset with completed MOs
    -   Try to delete asset
    -   Assert cascade delete is prevented (if business rule)
    -   Or assert cascade works correctly (if allowed)

7.  **[ ] `test_unique_constraint_race_condition`**
    -   Two requests create asset with same code simultaneously
    -   Assert only one succeeds
    -   Assert database constraint is enforced

8.  **[ ] `test_foreign_key_constraint_enforcement`**
    -   Try to create MO with non-existent asset_id
    -   Assert foreign key constraint prevents creation
    -   Assert error message is helpful

9.  **[ ] `test_date_boundary_validation`**
    -   Create MO with past due date
    -   Create MO with far future date
    -   Assert dates are validated
    -   Assert date logic works correctly

10. **[ ] `test_pagination_edge_cases`**
    -   Query with page beyond available pages
    -   Query with negative page number
    -   Query with zero items per page
    -   Assert pagination handles edge cases

**Estimated Tests:** 10

---

### 3.11. Performance Tests (`tests/test_performance.py`)

**Purpose:** Test query performance and scalability.

**🟢 LOW PRIORITY** - Ensures application scales well.

**Test Cases:**

1.  **[ ] `test_large_dataset_queries`**
    -   Populate database with 1000+ assets
    -   Query all assets
    -   Assert query completes in < 2 seconds
    -   Assert pagination works efficiently

2.  **[ ] `test_pagination_performance`**
    -   Query page 1, 50, 100 of large dataset
    -   Assert all pages load in similar time
    -   Assert no degradation on later pages

3.  **[ ] `test_n_plus_one_query_detection`**
    -   Query assets with related MOs
    -   Monitor SQL query count
    -   Assert eager loading is used
    -   Assert query count is optimal (not N+1)

4.  **[ ] `test_search_performance`**
    -   Search large dataset by name
    -   Assert search completes in < 1 second
    -   Assert indexes are being used

5.  **[ ] `test_complex_filter_performance`**
    -   Apply multiple filters (status, type, center)
    -   Assert query is optimized
    -   Assert response time is acceptable

6.  **[ ] `test_concurrent_request_handling`**
    -   Simulate 10 concurrent requests
    -   Assert all complete successfully
    -   Assert no deadlocks or timeouts

7.  **[ ] `test_memory_usage_with_large_results`**
    -   Query very large result set
    -   Assert memory usage is reasonable
    -   Assert no memory leaks

8.  **[ ] `test_database_connection_pooling`**
    -   Make multiple sequential requests
    -   Assert connections are reused
    -   Assert no connection exhaustion

**Estimated Tests:** 8

---

## 4. Test Infrastructure

### 4.1. Configuration Files

**[x] Create `pytest.ini`:** ✅ **Completed: December 11, 2025**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

**[x] Create `pyproject.toml` (if not exists):** ✅ **Completed: December 11, 2025**
```toml
[tool.pytest.ini_options]
minversion = "6.0"
addopts = "-ra -q"
testpaths = [
    "tests",
]
```

### 4.2. Test Fixtures (`tests/conftest.py`)

**[x] Enhance `conftest.py` with:** ✅ **Completed: December 11, 2025**
-   `app` fixture: Creates Flask app in testing mode ✅
-   `client` fixture: Provides test client for making requests ✅
-   `db_session` fixture: Provides database session with auto-rollback ✅
-   `sample_asset` fixture: Creates a sample asset for tests ✅
-   `sample_mo` fixture: Creates a sample maintenance order ✅
-   `sample_user` fixture: Creates a sample user ✅
-   `auth_client` fixture: Provides authenticated test client ✅

**Bonus Fixtures Added:**
-   `runner` fixture: CLI test runner for Click commands
-   `sample_role` fixture: Sample role (Technician)
-   `sample_admin_user` fixture: Admin user for permission tests
-   `sample_team` fixture: Sample team with shift information
-   `sample_skill` fixture: Sample skill (e.g., Welding)
-   `sample_spare_part` fixture: Sample spare part with inventory
-   `multiple_assets` fixture: 3 assets for list/filter testing
-   `multiple_mos` fixture: Multiple MOs for list/pagination testing

---

## 5. Implementation Timeline

### Phase 1: Foundation Tests (Days 1-6) ✅ COMPLETED
-   [x] Configure `pytest.ini` and `pyproject.toml` ✅ **Completed: December 11, 2025**
-   [x] Enhance `tests/conftest.py` with comprehensive fixtures ✅ **Completed: December 11, 2025**
-   [x] Create `tests/test_app.py` (18 tests) ✅ **Completed: December 11, 2025**
-   [x] Run and verify all tests pass ✅

### Phase 2: API & Routes Coverage (Days 3-5) ✅ COMPLETED
-   [x] Create `tests/test_api_routes.py` (41 tests) ✅ **Completed: December 11, 2025**
-   [x] Implement all API endpoint tests ✅
-   [x] Run and verify all tests pass ✅
-   [x] Fix API bugs discovered by tests ✅

### Phase 3: Web Routes Coverage (Day 5) ✅ COMPLETED
-   [x] Create `tests/test_main_routes.py` (29 tests) ✅ **Completed: December 11, 2025**
-   [x] Implement all web route tests ✅
-   [x] Run and verify all tests pass ✅

### Phase 4: Utilities Coverage (Days 5-6) ✅ COMPLETED
-   [x] Create `tests/test_db_utils.py` (3 tests) ✅ **Completed: December 12, 2025**
-   [x] Create `tests/test_shift_utils.py` (5 tests) ✅ **Completed: December 12, 2025**
-   [x] Run and verify all tests pass ✅ **96/96 passing!**

### Phase 5: Security & Validation (Days 7-9) 🔄 CURRENT
-   [x] Create `tests/test_auth.py` (8 tests) ✅ **Completed: December 12, 2025** 🔴 CRITICAL
-   [ ] Create `tests/test_validation.py` (6 tests) 🟡 **HIGH - Day 7-8**
-   [ ] Create `tests/test_errors.py` (6 tests) 🟡 **MEDIUM - Day 8**
-   [ ] Run and verify all 116 tests pass

### Phase 6: Integration & Advanced Testing (Days 9-11) ⏳ PENDING
-   [ ] Create `tests/test_integration.py` (10 tests) 🟡 **MEDIUM - Day 9-10**
-   [ ] Create `tests/test_advanced_validation.py` (10 tests) 🟡 **MEDIUM - Day 10**
-   [ ] Create `tests/test_performance.py` (8 tests) 🟢 **LOW - Day 11**
-   [ ] Run and verify all 144 tests pass

### Phase 7: Final Validation & CI Integration (Day 12) ⏳ PENDING
-   [ ] Run complete test suite (144 tests)
-   [ ] Verify 80%+ code coverage achieved
-   [ ] Update CI workflow to run full test suite
-   [ ] Add coverage reporting to CI
-   [ ] Verify all tests pass in CI environment
-   [ ] Documentation updates complete

**Estimated Total Time:** 12 days (extended from original 7 days)

---

## 6. Success Criteria

### Test Coverage Goals:
-   **Overall:** 80%+ code coverage (current: 73.60%)
-   **Critical paths:** 90%+ coverage (API endpoints, database operations, authentication)
-   **Security:** 90%+ coverage (authentication, authorization, input validation)
-   **All tests pass:** 100% pass rate in CI

### Quality Metrics:
-   All 144 tests implemented ✅ (96 complete, 48 pending)
-   All tests pass locally and in CI
-   Test execution time < 60 seconds ✅
-   No flaky tests (tests that randomly fail/pass) ✅
-   Security vulnerabilities: 0 critical, 0 high
-   Code quality: All automated checks passing

---

## 8. Workflow & Integration

### 8.1. How This Plan Fits into the Overall Strategy

This testing plan is **Phase 1** of the comprehensive implementation strategy outlined in `IMPLEMENTATION_PRIORITY_GUIDE.md`.

**Sequential Workflow:**
```
Phase 0: Foundation Setup (Week 1) ✅ COMPLETED
    ↓
Phase 1: Test Suite Foundation (Week 2) 🔄 CURRENT (THIS PLAN)
    ↓
Phase 2: Core Python Backend Audit (Week 3) ⏸️ POSTPONED
    - Resumes after test suite is complete
    - See: core_code_quality_plan.md
    ↓
Phase 3-5: Frontend, Templates, Standards (Weeks 4-7) ⏸️ POSTPONED
```

### 8.2. Document Update Workflow

**After completing each milestone in this plan:**

1.  **Mark Progress in This Document:**
    -   Update test checkboxes from `[ ]` to `[x]`
    -   Update "Last Updated" date at the top
    -   Update "Status" field when phases complete

2.  **Update `IMPLEMENTATION_PRIORITY_GUIDE.md`:**
    -   Mark corresponding Week 2 tasks as complete
    -   Update Quick Start Checklist progress

3.  **Update `mockCMMS_roadmap.md`:**
    -   Update "ACTIVE WORK" section status
    -   Move completed sprint to "RECENTLY COMPLETED" when done
    -   Add completion date and summary

4.  **Update `core_code_quality_plan.md`:**
    -   ✅ When all 96 tests pass, change status from "⏸️ Postponed" to "🟢 Ready to Start"
    -   ✅ COMPLETED - Status updated, ready for Phase 2

### 8.3. When to Start Code Quality Audit

**⏳ Prerequisites NOT YET MET - Continue with Phase 2 tests:**
-   ✅ Phase 1 tests implemented (96/144 tests)
-   ✅ Phase 1 tests pass locally (100% pass rate)
-   ⏳ Phase 2 tests implemented (0/48 tests) ← **CURRENT BLOCKER**
-   ⏳ All 144 tests pass locally (100% pass rate)
-   ⏳ All 144 tests pass in CI (GitHub Actions)
-   ⏳ Code coverage reaches 80%+ overall (current: 73.60%)
-   ⏳ Security coverage reaches 90%+ (current: 0%)

**Do NOT start `core_code_quality_plan.md` until:**
- ✅ All 144 tests in this plan are implemented
- ✅ All 144 tests pass (100% pass rate)
- ✅ Coverage reaches 80%+
- ✅ Security tests validate authentication/authorization
- ✅ Integration tests validate end-to-end workflows

**Why extended scope matters:**
- 🔴 **Security:** Authentication/authorization vulnerabilities are critical
- 🟡 **Robustness:** Validation/error handling prevents data corruption
- 🟡 **Quality:** Integration tests validate real-world usage
- 🟢 **Confidence:** Performance tests ensure scalability

**Current Status:** Week 2 Extended - Must complete Phase 2 tests before Week 3

**Why this order matters:**
-   Code formatting with `black` will modify many files
-   Tests provide automated verification that nothing broke
-   Without tests, formatting changes are high-risk
-   Tests enable safe refactoring throughout the audit

### 8.4. CI/CD Integration

**Current State:**
-   ✅ Basic CI workflow exists (`.github/workflows/ci.yml`)
-   ✅ Runs `pytest` on push/PR
-   ⏸️ Needs enhancement to run comprehensive test suite

**Required Updates to CI:**
```yaml
# .github/workflows/ci.yml
- name: Test with pytest and generate coverage
  run: |
    pytest --cov=src --cov=tests --cov-report=xml --cov-report=term
    
- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
    
- name: Enforce coverage thresholds
  run: |
    pytest --cov=src --cov-fail-under=70
```

**When to update CI:**
-   After Phase 1 Day 2 (when test infrastructure is ready)
-   Before Phase 1 Day 5 (before running full test suite)

---

## 7. Postponed Tasks

The following tasks are officially postponed until the test suite provides adequate coverage:
-   **Code Formatting:** Applying `black` to the codebase.
-   **Comprehensive Code Audit:** The detailed line-by-line audit described in `core_code_quality_plan.md`.

**This testing plan is now the single source of truth for the current development sprint.**
