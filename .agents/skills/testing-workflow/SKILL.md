---
name: testing-workflow
description: Use when writing tests, debugging coverage gaps, running validation, or investigating test failures.
---

# Testing Workflow

## Use this skill when

- Writing new tests for existing or new code
- Debugging why coverage is below threshold
- Running the full validation pipeline
- Investigating test failures after code changes
- Adding coverage for uncovered code paths
- Performing code quality audits

## Do not use this skill when

- Simply running `pytest` for a quick check (just run it)
- The question is about test configuration files (those are IMMUTABLE — see AGENTS.md)

---

## 1. Testing Philosophy

### What Tests DO Verify ✅

- **Regression prevention** — future changes won't break existing functionality
- **Behavior documentation** — tests document how the system currently works
- **API contracts** — tests show what data endpoints expect/return
- **Safe refactoring** — code can be restructured without breaking features

### What Tests DON'T Verify ❌

- **Business logic correctness** — only that logic is CONSISTENT, not necessarily RIGHT
- **Code quality** — tests don't check style, complexity, or maintainability
- **Security vulnerabilities** — need dedicated security scanning tools (bandit, etc.)
- **Performance** — need separate performance/load testing

### 4-Layer Verification Strategy

Complete code verification requires 4 complementary layers:

| Layer                          | What It Verifies                   | Tools                              |
| ------------------------------ | ---------------------------------- | ---------------------------------- |
| **1. Regression Tests**        | Behavior consistency               | pytest, jest, playwright           |
| **2. Code Quality Analysis**   | Style, syntax, security            | ruff, pylint, mypy, bandit, eslint |
| **3. Requirements Validation** | Business logic correctness         | Manual review                      |
| **4. Enhanced Testing**        | Workflows, performance, edge cases | pytest-benchmark, locust           |

**Key insight:** Tests alone ≠ complete verification. Layer 2 is automated via `scripts/validate_code.py`. Layers 3-4 require human judgment.

---

## 2. Pre-Flight Checks

Before writing any tests:

```bash
# Find existing tests to avoid duplicates
findstr /S "def test_" tests\backend\*.py
# or for frontend:
findstr /S "describe\|it(" tests\frontend\unit\*.js
```

Check what's uncovered:

```bash
# Backend (comprehensive — all Python sources)
pytest --cov=src --cov=apps --cov=scripts --cov=.collab \
  --cov=run.py --cov=collab.py --cov=conftest.py \
  --cov-report=term-missing tests/backend

# Frontend
npm run test:coverage
```

### Key Fixtures Available (conftest.py)

| Fixture             | Purpose                               |
| ------------------- | ------------------------------------- |
| `app`               | Flask app in testing mode             |
| `client`            | Test client for HTTP requests         |
| `auth_client`       | Authenticated test client (logged in) |
| `db_session`        | Database session with auto-rollback   |
| `sample_asset`      | Pre-created asset                     |
| `sample_mo`         | Pre-created maintenance order         |
| `sample_user`       | Pre-created user                      |
| `sample_admin_user` | Admin user for permission tests       |
| `sample_role`       | Sample role (Technician)              |
| `sample_team`       | Sample team with shift info           |
| `multiple_assets`   | 3 assets for list/filter testing      |

### SQLAlchemy Connection Safety in Tests

Always ensure proper cleanup to avoid "unclosed connection" warnings:

```python
# In fixtures or teardown:
db.session.remove()         # Return connection to pool
db.engine.pool.dispose()    # Close checked-out connections
db.engine.dispose()         # Shutdown engine
```

---

## 3. Writing Backend Tests (Pytest)

### Test File Placement

| Test Type           | Directory                    | Example                  |
| ------------------- | ---------------------------- | ------------------------ |
| Unit (isolated)     | `tests/backend/unit/`        | `test_db_utils.py`       |
| Functional (routes) | `tests/backend/functional/`  | `test_api_routes.py`     |
| Integration (E2E)   | `tests/backend/integration/` | `test_mo_workflow.py`    |
| Security (auth)     | `tests/backend/security/`    | `test_auth.py`           |
| Performance         | `tests/backend/performance/` | `test_query_perf.py`     |
| Reliability         | `tests/backend/reliability/` | `test_error_handling.py` |

### Test Structure (AAA Pattern)

```python
def test_create_maintenance_order_with_valid_data(app, db_session):
    """Create MO with valid data returns 201 and persists to database."""
    # Arrange
    data = {"title": "Fix pump", "priority": "high"}

    # Act
    response = client.post("/api/maintenance-orders", json=data)

    # Assert
    assert response.status_code == 201
    assert db_session.query(MaintenanceOrder).count() == 1
```

### Generate Test Stubs

```bash
python scripts/generate_tests.py src/services/new_module.py --dry-run  # Preview
python scripts/generate_tests.py src/services/new_module.py           # Create
python scripts/generate_tests.py --scan                               # Find untested modules
```

---

## 4. Writing Frontend Tests (Jest)

### Project-Specific Gotchas

**Route naming:** Flask uses underscores (`/maintenance_orders`), NOT hyphens (`/maintenance-orders`). Always match real routes in E2E tests.

**Use `data-testid` attributes** for robust E2E selectors instead of relying on text content or CSS classes.

### Common Coverage Mistakes

```javascript
// BAD: Event dispatch in JSDOM often doesn't trigger coverage
element.dispatchEvent(new Event("click"));

// GOOD: Call the function directly with specific inputs
await tableModals.saveTableConfiguration(); // Triggers the uncovered branch
```

### Mock Timing

```javascript
// BAD: Mocking after instantiation — handlers already bound
const instance = new MyClass();
jest.spyOn(instance, "method"); // Too late!

// GOOD: Mock on prototype BEFORE instantiation
jest.spyOn(MyClass.prototype, "method").mockImplementation(() => {});
const instance = new MyClass();
```

---

## 5. Coverage Strategy

### Thresholds (IMMUTABLE)

| Scope         | Tool       | Threshold                                     | Enforced By                           |
| ------------- | ---------- | --------------------------------------------- | ------------------------------------- |
| Backend total | pytest     | ≥85%                                          | `ci.yml` + `validate_code.py` Step 10 |
| Backend diff  | diff-cover | ≥92% on new/changed code                      | `ci.yml` + `validate_code.py` Step 11 |
| Frontend      | jest       | ≥80% (branches, functions, lines, statements) | `package.json` (`coverageThreshold`)  |

**80% is the absolute floor.** 79.9% = FAILURE. Fix by adding tests, never by lowering config.

**All-Python-Files Policy:** Every `.py` file must be covered — `src/`, `apps/`, `tests/`, `scripts/`, `.collab/`, `run.py`, `collab.py`, `conftest.py`. No exclusions.

### Coverage Improvement Strategy

**Target error paths, not more happy paths.** This is the single most effective strategy for improving coverage with minimal test count.

| Approach                        | Coverage Impact            | Test Count |
| ------------------------------- | -------------------------- | ---------- |
| ❌ More happy path tests        | Low (+1-2% per 10 tests)   | Many       |
| ✅ Target uncovered error paths | High (+5-10% per 10 tests) | Few        |

**How to find uncovered error paths:**

1. Run `pytest --cov-report=term-missing` to see exact uncovered line numbers
2. Focus on: error handlers, validation failures, authorization checks, exception catches
3. Write tests that trigger those specific paths

---

## 6. Full Validation Pipeline

```bash
# Step 1: Auto-fix formatting
python scripts/format_code.py

# Step 2: Full validation (lint + test + coverage)
python scripts/validate_code.py

# Options for faster iteration:
python scripts/validate_code.py --quick      # Fast: honors .env, targeted tests, skips slow checks
python scripts/validate_code.py <files>      # Targeted: Validates ONLY specific files (simulates pre-commit)
python scripts/validate_code.py --backend    # Python only
python scripts/validate_code.py --frontend   # JS only
```

**validate_code.py runs:** isort, black, docformatter, ruff, flake8, mypy, bandit, pytest, eslint, jest, playwright, visual regression.

**Health Mode** (no flags): forces all modular apps ENABLED for full project health check.

### Frontend 5-Step Quality Loop

When auditing or modifying frontend code (JS/CSS/HTML):

1. **Pre-test baseline:** `npm test` + `npx playwright test --project=chromium` (must pass first)
2. **Lint:** `npx eslint src/static/js --report-unused-disable-directives`
3. **Format & fix:** `npx eslint src/static/js --fix` + `npx prettier --write src/static/js`
4. **Post-fix verify:** Re-run `npm test` + `npx playwright test` (must still pass)
5. **Report:** If tests fail → loop back to step 1. If pass → commit.

---

## 7. Test Failure Decision Tree

```
Test fails after code change:
├─ Did requirements change?
│  ├─ YES → Update test to match new requirements
│  └─ NO → Continue
├─ Is the test testing correct behavior?
│  ├─ YES → Fix the CODE (test is right, code is wrong)
│  └─ NO → Fix the TEST (test is wrong, code is right)
├─ When in doubt:
│  └─ Prioritize test correctness (tests define expected behavior)
```

---

## 8. Self-Correction Loop

When tests or linting fail:

| Error Type                 | Action                          | Max Attempts |
| -------------------------- | ------------------------------- | ------------ |
| Import order (isort)       | Run `isort --fix`               | 1            |
| Code formatting (black)    | Run `black file.py`             | 1            |
| Unused imports (ruff F401) | Edit to remove                  | 2            |
| Missing type hints (mypy)  | Add type hints                  | 2            |
| Test failures              | Analyze error, fix code or test | 3            |
| Coverage below threshold   | Add more tests                  | 3            |

After 3 failed attempts, report to user with error details and what you tried.

---

## 9. Visual Regression Tests

### Baseline Screenshots

Screenshots are stored in `tests/frontend/e2e/__screenshots__/`. These are **SACRED** — never update unless UI was intentionally changed.

### When Visual Tests Fail

1. **Investigate the code** — the screenshot is the ground truth
2. Compare the diff screenshot to identify what changed
3. If the change was intentional (new CSS, layout update), update baselines:
   ```bash
   npx playwright test --update-snapshots
   ```
4. If the change was unintentional — fix the code, not the screenshots

---

## 10. Testing Documentation (Required for User-Facing Changes)

After implementing changes that affect **user-facing behavior** (UI, API responses, workflows), create or update a verification checklist in `docs/`.

**When to create:** Bug fixes with UI impact, new features, workflow changes, API modifications.
**When to skip:** Pure refactoring, test-only changes, CI/config updates, doc-only edits.

### Template (`docs/<feature>_test_guide.md`)

```markdown
# <Feature> — Verification Guide

## Prerequisites

- [ ] Server running (`python run.py`)
- [ ] Login: admin / admin123

## Test Cases

| #   | Action                         | Expected Result                 | ✅/❌ |
| --- | ------------------------------ | ------------------------------- | ----- |
| 1   | Navigate to /page              | Page loads without errors       |       |
| 2   | Click "Submit" with empty form | Validation error shown          |       |
| 3   | Submit valid data              | Success message, data persisted |       |

## Edge Cases

- [ ] Empty inputs
- [ ] Special characters
- [ ] Multiple rapid submissions

## Browser Console

- [ ] No JavaScript errors
- [ ] No failed network requests
```

**Rules:**

- One guide per feature/fix — don't create a new doc for every minor tweak.
- Update existing guides when modifying previously-documented features.
- Keep it scannable — tables over paragraphs, checkboxes over prose.
- Delete outdated test guides when features are removed.

### Evidence for Table Component Changes

When modifying the Advanced Table component, also provide:

- Video/screenshot evidence of browser testing
- Console logs (no JS errors)
- Network logs (API calls to `/api/table-config/` succeed)
- See `docs/table_features_test_plan.md` for the full manual test checklist.

---

## Safety

- **NEVER** modify `pyproject.toml`, `jest.config.js`, `playwright.config.js`, `eslint.config.js`, or `.flake8` to make tests pass.
- **NEVER** update visual test screenshots (`tests/frontend/e2e/__screenshots__/`) unless UI was intentionally changed.
- **NEVER** lower coverage thresholds.
