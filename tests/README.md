# Test Suite Organization

**Total Tests:** 200 tests (144 implemented, 56 to be added in Phase 3)  
**Coverage:** 75.64% (Target: 85-90% after Phase 3)  
**Last Updated:** December 12, 2025

---

## 📁 Directory Structure

The test suite is organized by **testing concern** into 6 categories:

```
tests/
├── unit/          # Unit Tests (26 tests) - Fast, isolated component tests
├── functional/    # Functional Tests (70 tests) - API and route endpoint tests
├── integration/   # Integration Tests (10 → 18 tests) - End-to-end workflows
├── security/      # Security Tests (24 tests) - Auth, validation, security
├── performance/   # Performance Tests (8 tests) - Scalability and optimization
└── reliability/   # Reliability Tests (6 tests) - Error handling and robustness
```

---

## 🎯 Test Categories

### 1. Unit Tests (`tests/unit/`) - 26 tests

**Purpose:** Test individual components in isolation  
**Speed:** Fast (< 10 seconds)  
**When to run:** During development, before every commit

**Files:**
- `test_app.py` (18 → 28 tests) - App initialization and configuration
- `test_db_utils.py` (3 → 11 tests) - Database utilities and models
- `test_shift_utils.py` (5 tests) - Shift scheduling utilities ✅ 100% coverage

**Run:** `pytest tests/unit/`

---

### 2. Functional Tests (`tests/functional/`) - 70 tests

**Purpose:** Test API endpoints and web routes  
**Speed:** Medium (< 20 seconds)  
**When to run:** Before commits affecting APIs or routes

**Files:**
- `test_api_routes.py` (41 → 51 tests) - REST API endpoints
- `test_main_routes.py` (29 → 39 tests) - Web application routes

**Run:** `pytest tests/functional/`

---

### 3. Integration Tests (`tests/integration/`) - 10 → 18 tests

**Purpose:** Test complete workflows end-to-end  
**Speed:** Medium-Slow (< 15 seconds)  
**When to run:** Before PRs, after major changes

**Files:**
- `test_integration.py` (10 → 18 tests) - Complete business workflows

**Run:** `pytest tests/integration/`

---

### 4. Security Tests (`tests/security/`) - 24 tests

**Purpose:** Validate security, authentication, and input validation  
**Speed:** Fast-Medium (< 10 seconds)  
**When to run:** Before any security-related changes, during security audits

**Files:**
- `test_auth.py` (8 tests) - Authentication and authorization ✅
- `test_validation.py` (6 tests) - Input validation and XSS/SQL injection ✅
- `test_advanced_validation.py` (10 tests) - Edge cases and boundary conditions ✅

**Run:** `pytest tests/security/`

---

### 5. Performance Tests (`tests/performance/`) - 8 tests

**Purpose:** Validate system performance and scalability  
**Speed:** Slow (< 30 seconds)  
**When to run:** Before releases, during performance optimization

**Files:**
- `test_performance.py` (8 tests) - Query performance, pagination, concurrency ✅

**Run:** `pytest tests/performance/`

---

### 6. Reliability Tests (`tests/reliability/`) - 6 tests

**Purpose:** Test error handling and system robustness  
**Speed:** Fast (< 5 seconds)  
**When to run:** Before commits affecting error handling

**Files:**
- `test_errors.py` (6 tests) - Error pages, exception handling ✅

**Run:** `pytest tests/reliability/`

---

## 🚀 Running Tests

### Run All Tests
```bash
pytest tests/
# 144 passed in ~45 seconds
```

### Run by Category (Fast → Slow)
```bash
# Fastest: Unit + Reliability (< 15 seconds)
pytest tests/unit/ tests/reliability/

# Medium: Functional + Security (< 30 seconds)
pytest tests/functional/ tests/security/

# Integration tests (< 15 seconds)
pytest tests/integration/

# Slowest: Performance (< 30 seconds)
pytest tests/performance/
```

### Run for Quick Development Cycle
```bash
# Run only fast tests (unit + reliability)
pytest tests/unit/ tests/reliability/ -q
# ~32 tests in ~12 seconds
```

### Run for Security Audit
```bash
# Run all security-related tests
pytest tests/security/ -v
# 24 tests covering auth, validation, edge cases
```

### Run Before Commit
```bash
# Unit + Functional + Security (most common changes)
pytest tests/unit/ tests/functional/ tests/security/
# ~120 tests in ~30 seconds
```

### Run Before Release
```bash
# Everything including slow performance tests
pytest tests/
# All 144 tests in ~45 seconds
```

---

## 📊 Test Count by Category

| Category | Current | Phase 3 Target | Total |
|----------|---------|----------------|-------|
| Unit | 26 | +18 | 44 |
| Functional | 70 | +20 | 90 |
| Integration | 10 | +8 | 18 |
| Security | 24 | +0 | 24 |
| Performance | 8 | +0 | 8 |
| Reliability | 6 | +0 | 6 |
| **TOTAL** | **144** | **+56** | **200** |

---

## 🎯 Coverage Goals

**Current:** 75.64%  
**Minimum:** 70% ✅  
**Phase 3 Target:** 85-90%  
**Stretch Goal:** 95%+

**Coverage by File:**
- ✅ shift_utils.py: 100% (Perfect!)
- ✅ db_utils.py: 85.66% (Target: 95%+)
- ✅ main.py: 80.05% (Target: 90%+)
- 🟡 app.py: 67.68% (Target: 85%+)
- 🔴 api.py: 62.50% (Target: 85%+)

---

## 🔧 CI/CD Integration

Tests can be run in stages for optimized CI/CD:

**Stage 1: Fast Checks (< 15s)**
```yaml
- name: Unit Tests
  run: pytest tests/unit/
  
- name: Reliability Tests  
  run: pytest tests/reliability/
```

**Stage 2: Functional Validation (< 35s)**
```yaml
- name: Functional Tests
  run: pytest tests/functional/
  
- name: Security Tests
  run: pytest tests/security/
```

**Stage 3: Integration (< 15s)**
```yaml
- name: Integration Tests
  run: pytest tests/integration/
```

**Stage 4: Performance (Nightly)**
```yaml
- name: Performance Tests
  run: pytest tests/performance/
  schedule: nightly
```

---

## 📝 Adding New Tests

**Rule:** Add tests to the appropriate category directory based on **what you're testing**, not **when you're adding it**.

### Decision Tree:

**Testing a single component/function in isolation?**
→ Add to `tests/unit/`

**Testing an API endpoint or web route?**
→ Add to `tests/functional/`

**Testing a complete workflow (multiple steps)?**
→ Add to `tests/integration/`

**Testing authentication, authorization, or validation?**
→ Add to `tests/security/`

**Testing performance, scalability, or query optimization?**
→ Add to `tests/performance/`

**Testing error handling or error pages?**
→ Add to `tests/reliability/`

---

## 🏆 Best Practices

1. **Keep unit tests fast** - No database, no network, no file I/O
2. **Make functional tests focused** - One endpoint/route per test class
3. **Make integration tests comprehensive** - Test real user workflows
4. **Keep security tests isolated** - Easy to run for security audits
5. **Keep performance tests separate** - Don't slow down regular test runs
6. **Document edge cases** - Explain why advanced validation tests exist

---

## ✅ Phase 3 Plan

**Goal:** Add 56 tests to existing files to reach 85-90% coverage

**Additions:**
- `unit/test_app.py`: +10 tests (module loading, configuration)
- `functional/test_api_routes.py`: +10 tests (error handling, complex queries)
- `functional/test_main_routes.py`: +10 tests (DELETE operations)
- `unit/test_db_utils.py`: +8 tests (model methods, constraints)
- `integration/test_integration.py`: +8 tests (critical path workflows)

**Timeline:** Days 13-15  
**After Phase 3:** 200 tests, 85-90% coverage, ready for code formatting (black)

---

**For detailed test specifications, see:** `docs/comprehensive_testing_plan.md`

