# Test Suite Organization

**Total Tests:** 574+ tests (223 backend + 293 Jest + 71 E2E = 587 actual)
**Coverage:** 82%+ (Backend), 80%+ (Frontend)
**Last Updated:** December 19, 2025

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
