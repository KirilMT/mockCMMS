# Test Suite Organization

**Total Tests:** 574+ tests (223 backend + 293 Jest + 71 E2E = 587 actual)
**Coverage:** 82%+ (Backend), 80%+ (Frontend)
**Last Updated:** February 7, 2026

---

## 📁 Directory Structure

The test suite is organized by **backend/frontend** separation and **testing concern**:

```
tests/
├── README.md                    # This file
├── backend/                     # Python/pytest tests
│   ├── conftest.py              # Shared fixtures
│   ├── unit/                    # Unit tests - isolated component tests
│   ├── functional/              # API and route endpoint tests
│   ├── integration/             # End-to-end workflow tests
│   ├── security/                # Auth, validation, security tests
│   ├── performance/             # Scalability and optimization tests
│   └── reliability/             # Error handling and robustness tests
└── frontend/                    # JavaScript tests
    ├── unit/                    # Jest unit tests
    │   ├── advanced-table/      # Advanced table component tests
    │   ├── toast-notification.test.js
    │   └── flash-messages.test.js
    └── e2e/                     # Playwright E2E tests
        ├── e2e-test-setup.js    # Global setup
        ├── e2e-test-teardown.js # Global teardown
        ├── 00_visual.spec.js    # Visual regression tests
        ├── 01_advanced-table.spec.js
        ├── 02_crud.spec.js
        └── 03_smoke.spec.js
```

---

## 🎯 Test Categories

### Backend Tests (`tests/backend/`) - pytest

#### 1. Unit Tests (`tests/backend/unit/`)

**Purpose:** Test individual components in isolation
**Speed:** Fast (<10 seconds)
**Run:** `pytest tests/backend/unit/`

#### 2. Functional Tests (`tests/backend/functional/`)

**Purpose:** Test API endpoints and web routes
**Speed:** Medium (<20 seconds)
**Run:** `pytest tests/backend/functional/`

#### 3. Integration Tests (`tests/backend/integration/`)

**Purpose:** Test complete workflows end-to-end
**Speed:** Medium-Slow (<15 seconds)
**Run:** `pytest tests/backend/integration/`

#### 4. Security Tests (`tests/backend/security/`)

**Purpose:** Validate security, authentication, and input validation
**Speed:** Fast-Medium (<10 seconds)
**Run:** `pytest tests/backend/security/`

#### 5. Performance Tests (`tests/backend/performance/`)

**Purpose:** Validate system performance and scalability
**Speed:** Slow (<30 seconds)
**Run:** `pytest tests/backend/performance/`

#### 6. Reliability Tests (`tests/backend/reliability/`)

**Purpose:** Test error handling and system robustness
**Speed:** Fast (<5 seconds)
**Run:** `pytest tests/backend/reliability/`

---

### Frontend Tests (`tests/frontend/`)

#### Jest Unit Tests (`tests/frontend/unit/`)

**Purpose:** Test JavaScript components and logic
**Speed:** Fast (~10 seconds for 293 tests)
**Run:** `npm test`

**Files:**

- `advanced-table/` - 12 test files for table component
- `toast-notification.test.js` - Toast notification tests
- `flash-messages.test.js` - Flash message tests

#### Playwright E2E Tests (`tests/frontend/e2e/`)

**Purpose:** Test full user workflows in browser
**Speed:** Slow (~4 minutes for 71 tests)
**Run:** `npm run test:e2e` or `npx playwright test`

**Files:**

- `00_visual.spec.js` - Visual regression tests (19 snapshots)
- `01_advanced-table.spec.js` - Table feature tests
- `02_crud.spec.js` - CRUD operation tests
- `03_smoke.spec.js` - Navigation and auth tests

---

## 🚀 Running Tests

### Run All Backend Tests

```bash
pytest tests/backend/
# 223 passed in ~90 seconds
```

### Run All Frontend Tests

```bash
npm test                              # Jest (293 tests, ~10s)
npm run test:e2e:chromium             # Playwright (71 tests, ~4min)
```

### Run Everything

```bash
npm run test:all                      # Jest + Playwright
pytest tests/backend/                 # Backend tests
```

### Quick Development Cycle

```bash
# Fast backend tests only
pytest tests/backend/unit/ tests/backend/reliability/ -q

# Fast frontend tests only
npm test
```

### Before Commit

```bash
pytest tests/backend/unit/ tests/backend/functional/ tests/backend/security/
npm test
```

### Before Release

```bash
pytest tests/backend/
npm test
npm run test:e2e
```

---

## 🏗️ Modular App Testing

The mockCMMS monorepo uses a **Smart Collector** logic to optimize development speed.

### 1. Dynamic Test Discovery

Modular apps in `apps/` (e.g., `Planning`, `Reports`) have their tests dynamically skipped if the app is disabled via environment variables.

- **How it works:** Pytest checks your `.env` for variables like `PLANNING_ENABLED` or `REPORTS_ENABLED`.
- **Developer Benefit:** You only run tests for the apps you are currently developing.
- **Default:** New apps are considered ENABLED (to ensure tests are written) unless explicitly set to `false`.

### 2. Validation Modes (`scripts/validate_code.py`)

- **Quick Mode (`--quick` flag):** Efficient developer iteration. Honors your `.env` settings and skips disabled apps.
- **Health Mode (Default):** Exhaustive project check. Forces **all modular apps ENABLED** to ensure total project stability. All CI runs use Health Mode.

### 3. Global Quality Enforcement

Linting (`ruff`), Formatting (`black`), and Type Checking (`mypy`) **always run on every file** in the repository, regardless of whether an app is enabled. This prevents code rot in inactive modules.

## 📊 Test Summary

| Category            | Tests    | Tool       |
| ------------------- | -------- | ---------- |
| Backend Unit        | ~26      | pytest     |
| Backend Functional  | ~70      | pytest     |
| Backend Integration | ~18      | pytest     |
| Backend Security    | ~24      | pytest     |
| Backend Performance | ~8       | pytest     |
| Backend Reliability | ~6       | pytest     |
| **Backend Total**   | **~223** | **pytest** |
| Frontend Unit       | 293      | Jest       |
| Frontend E2E        | 71       | Playwright |
| **Frontend Total**  | **364**  | **npm**    |
| **GRAND TOTAL**     | **~587** | -          |

---

## 🔧 Configuration Files

| Config     | Tool       | Location                                   |
| ---------- | ---------- | ------------------------------------------ |
| pytest     | pytest     | `pyproject.toml` [tool.pytest.ini_options] |
| coverage   | pytest-cov | `pyproject.toml` [tool.coverage.*]         |
| jest       | Jest       | `package.json` "jest" section              |
| babel      | babel-jest | `package.json` "babel" section             |
| playwright | Playwright | `playwright.config.js`                     |
| flake8     | flake8     | `.flake8`                                  |
| ruff       | ruff       | `pyproject.toml` [tool.ruff]               |
| black      | black      | `pyproject.toml` [tool.black]              |

---

## 📝 Adding New Tests

### Backend Tests

Add to appropriate category in `tests/backend/`:

- **Isolated component test?** → `unit/`
- **API or route test?** → `functional/`
- **Multi-step workflow?** → `integration/`
- **Auth or validation?** → `security/`
- **Query performance?** → `performance/`
- **Error handling?** → `reliability/`

### Frontend Tests

Add to appropriate category in `tests/frontend/`:

- **JavaScript logic test?** → `unit/*.test.js`
- **Browser workflow test?** → `e2e/*.spec.js`

---

## 🗄️ Database Isolation (CRITICAL)

**All backend pytest tests MUST use in-memory SQLite databases. NO file-based databases should ever be created during `pytest` runs.**

### The Golden Rules

> 1. When `app.testing == True`, NO file-based databases should be created.
> 2. If you see `*.db` files appearing in `apps/*/instance/` after running pytest, it's a **BUG**.
> 3. E2E databases (`*_e2e.db`) are ONLY for Playwright tests, NEVER for pytest.

### Database Types and When They're Used

| Database Type | Example | Created By | When |
|--------------|---------|------------|------|
| **Production** | `planning.db`, `reports.db`, `mockcmms.db` | `run.py` | Running the app normally |
| **E2E** | `planning_e2e.db`, `reports_e2e.db`, `mockcmms_e2e.db` | Playwright tests | E2E tests with `E2E_TEST=true` |
| **In-Memory** | `sqlite:///:memory:` | pytest | ALL backend unit/functional/integration tests |

### ⚠️ Common Mistake: Testing E2E Configuration

**WRONG:** Setting `E2E_TEST=True` in a unit test without in-memory URIs:
```python
# ❌ THIS CREATES FILE-BASED DATABASES!
with patch.dict(os.environ, {"E2E_TEST": "True"}):
    app = create_app({"TESTING": True})  # Will create planning_e2e.db, etc.!
```

**CORRECT:** Always pass in-memory URIs when testing E2E configuration:
```python
# ✅ This uses in-memory databases even with E2E_TEST=True
with patch.dict(os.environ, {"E2E_TEST": "True"}):
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_BINDS": {
            "planning": "sqlite:///:memory:",
            "reports": "sqlite:///:memory:",
        },
    })
```

**Why?** When `E2E_TEST=True`, `src/app.py` configures file-based E2E database paths. SQLite creates these files when the engine connects, even if `db.create_all` is patched.

### Required Configuration in conftest.py

Every conftest.py that creates a Flask app MUST include ALL database binds:

```python
config_overrides = {
    "TESTING": True,
    "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    "SQLALCHEMY_BINDS": {
        "planning": "sqlite:///:memory:",  # ← REQUIRED
        "reports": "sqlite:///:memory:",   # ← REQUIRED
        # Add ALL new app binds here when creating new modules
    },
}
```

### Adding a New Modular App

When adding a new app (e.g., `apps/inventory/`):

1. **Update `src/app.py`** - Add the bind configuration with testing guard
2. **Update ALL conftest.py files** - Add `"inventory": "sqlite:///:memory:"`
   - `tests/backend/conftest.py`
   - `apps/planning/tests/backend/conftest.py`
   - `apps/reports/tests/backend/conftest.py`
   - Your new `apps/inventory/tests/backend/conftest.py`
3. **Update E2E teardown** - Add to `tests/frontend/e2e/e2e-test-teardown.js`
4. **Update isolation tests** - Add to `tests/backend/security/test_db_isolation_proof.py`

### Safety Net Tests

The `tests/backend/security/test_db_isolation_proof.py` file contains comprehensive tests that will **FAIL immediately** if:
- Any production database files are created during testing
- Any E2E database files are created during backend pytest
- Any database bind uses a file-based URI instead of in-memory
- Instance directories are created with new DB files

These tests catch isolation violations before they cause data corruption.

### Quick Verification

```powershell
# Clean up any stray DBs first
Remove-Item -Path "apps\*\instance" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "instance\*.db" -Force -ErrorAction SilentlyContinue

# Run tests
python scripts/validate_code.py --quick

# Check for leaks (should output NOTHING)
Get-ChildItem -Path "apps" -Recurse -Filter "*.db" | Select-Object FullName
Get-ChildItem -Path "instance" -Filter "*.db" | Select-Object FullName
```

### Troubleshooting Database Leaks

If you see `*.db` files after running tests:

1. **Identify the culprit:** Run tests one file at a time to find which test creates the files
2. **Check for `E2E_TEST=True`:** Search for tests that set this env var
3. **Add in-memory URIs:** Pass `SQLALCHEMY_DATABASE_URI` and `SQLALCHEMY_BINDS` with `:memory:`
4. **Mock `os.makedirs`:** Add `@patch("src.app.os.makedirs")` to prevent directory creation
5. **Run isolation tests:** `pytest tests/backend/security/test_db_isolation_proof.py -v`

---

## 🏆 Best Practices

1. **Keep unit tests fast** - No database, network, or file I/O
2. **Make functional tests focused** - One endpoint/route per test class
3. **Make integration tests comprehensive** - Test real user workflows
4. **Keep security tests isolated** - Easy to run for security audits
5. **Keep performance tests separate** - Don't slow down regular runs
6. **Run tests before commits** - Both backend and frontend
7. **Update snapshots intentionally** - Review visual changes

---

**For detailed test specifications, see:** `docs/comprehensive_testing_plan.md`
