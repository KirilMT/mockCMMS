# Comprehensive Frontend Testing Plan for mockCMMS

**Created:** December 17, 2025  
**Last Updated:** December 17, 2025  
**Status:** 🔄 **IN PROGRESS**  
**Priority:** Critical - Blocks Code Quality Phases 3-5  
**Proposed Tools:** Jest (Unit/Integration), Playwright (E2E/Visual Regression)

---

> [!IMPORTANT]
> **📋 Workflow Context:** This plan establishes the frontend testing foundation required before the JavaScript/CSS/HTML audit phases can begin.
> 
> **Related Documentation:**
> - **[Core Code Quality Plan](core_code_quality_plan.md)** - Parent audit plan (Phases 3-5 blocked)
> - **[Comprehensive Testing Plan](comprehensive_testing_plan.md)** - Backend testing reference
> - **[mockCMMS Roadmap](mockCMMS_roadmap.md)** - Strategic context
> 
> **Prerequisites:**
> 1. ✅ Backend test suite complete (210 tests, 82.99% coverage)
> 2. ⬜ Node.js 18+ installed
> 3. ⬜ npm available in PATH
> 
> **Status:** Phase 1 Ready to Start

---

## 📄 LIVING DOCUMENT GUIDELINES

**This is a living document that must be updated continuously.**

### Maintenance Rules

1. **Update Progress Continuously**
   - Mark checkboxes `[x]` when items are completed
   - Add completion dates and notes to completed items
   - Update "Last Updated" timestamp at the top

2. **Avoid Duplicates**
   - Before adding new tests, search to ensure they don't already exist
   - Consolidate related test cases

3. **Do Not Delete - Mark as Complete**
   - Never delete completed items
   - Mark items as complete with `[x]` and add resolution notes

4. **Synchronize with Roadmap**
   - Update `mockCMMS_roadmap.md` when phases complete
   - Update `core_code_quality_plan.md` Phase 3 status

---

## 🎯 Objectives

1. **Automated UI Validation:** Verify functionality of critical UI components
2. **Enable Safe Refactoring:** Build confidence for large-scale JS/CSS changes
3. **Cross-Browser Consistency:** Ensure consistent behavior across browsers
4. **Regression Prevention:** Catch UI regressions automatically
5. **CI/CD Integration:** Run tests on every commit via GitHub Actions

---

## 📁 Scope: Files to Test

### JavaScript Files (`src/static/js/`)

#### Advanced Table Module (11 files, ~110KB total)
- [ ] `src/static/js/advanced-table/table-core.js` (4.4KB) - Core class and state management
- [ ] `src/static/js/advanced-table/table-init.js` (0.6KB) - Initialization logic
- [ ] `src/static/js/advanced-table/table-render.js` (8.1KB) - DOM rendering
- [ ] `src/static/js/advanced-table/table-data.js` (5.7KB) - Data processing, filtering, sorting
- [ ] `src/static/js/advanced-table/table-config.js` (4.7KB) - Configuration persistence
- [ ] `src/static/js/advanced-table/table-events.js` (4.6KB) - Event handling
- [ ] `src/static/js/advanced-table/table-export.js` (1.6KB) - CSV export
- [ ] `src/static/js/advanced-table/table-sidebar.js` (61KB) - Sidebar UI, filters, views
- [ ] `src/static/js/advanced-table/table-resize.js` (12KB) - Column resizing
- [ ] `src/static/js/advanced-table/table-loading.js` (3.8KB) - Loading states
- [ ] `src/static/js/advanced-table/table-retry.js` (3.3KB) - Retry logic

#### Standalone Modules (2 files)
- [ ] `src/static/js/toast-notification.js` (4.8KB) - Toast notifications
- [ ] `src/static/js/flash-messages.js` (2.5KB) - Flask flash message integration

### CSS Files (`src/static/css/`)
- [ ] `src/static/css/main.css` - Main application styles
- [ ] `src/static/css/advanced-table.css` - Table component styles
- [ ] `src/static/css/advanced-table-sidebar.css` - Sidebar styles

### HTML Templates (`src/templates/`)
- [ ] Critical pages with Advanced Table integration
- [ ] Form validation behavior
- [ ] Navigation and layout

---

## 🔄 Standard Workflow: Test Development Loop

For all test development, follow this process:

1. **Setup** - Install tools and configure environment
2. **Write Test** - Create test case with clear assertions
3. **Run Test** - Execute and verify it fails correctly (TDD)
4. **Implement/Fix** - Make the test pass
5. **Refactor** - Clean up both test and implementation
6. **Document** - Update this plan with completion notes

---

## 📋 Phase 1: JavaScript Unit & Integration Tests (Jest)

**Goal:** Test individual JavaScript functions, classes, and modules in isolation.
**Why First:** Fast feedback, easy to write, perfect foundation for refactoring.

### Phase 1.1: Environment Setup

#### Step 1.1.1: Install Jest and Dependencies

```bash
# Install Jest and Babel for ES6+ support
npm install --save-dev jest babel-jest @babel/core @babel/preset-env

# Install jsdom for DOM testing
npm install --save-dev jest-environment-jsdom
```

#### Step 1.1.2: Create Configuration Files

**`jest.config.js`:**
```javascript
module.exports = {
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/src/static/js/', '<rootDir>/tests/js/'],
  testMatch: ['**/*.test.js'],
  transform: {
    '^.+\\.js$': 'babel-jest',
  },
  collectCoverageFrom: [
    'src/static/js/**/*.js',
    '!src/static/js/**/*.test.js',
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },
};
```

**`babel.config.js`:**
```javascript
module.exports = {
  presets: [
    ['@babel/preset-env', { targets: { node: 'current' } }],
  ],
};
```

#### Step 1.1.3: Create Test Directory Structure

```
tests/
└── js/
    ├── advanced-table/
    │   ├── table-core.test.js
    │   ├── table-data.test.js
    │   ├── table-config.test.js
    │   ├── table-sidebar.test.js
    │   └── ...
    ├── toast-notification.test.js
    └── flash-messages.test.js
```

### Phase 1.2: Core Class Tests

#### Task 1.2.1: `AdvancedTable` Class (`table-core.js`)

**Test File:** `tests/js/advanced-table/table-core.test.js`

| Test ID | Test Name | Description | Priority |
|---------|-----------|-------------|----------|
| TC-1.1 | `test_constructor_initializes_default_state` | Verify default properties are set | High |
| TC-1.2 | `test_constructor_accepts_custom_options` | Verify options override defaults | High |
| TC-1.3 | `test_saveTableState_persists_to_localStorage` | Mock localStorage, verify save | High |
| TC-1.4 | `test_restoreTableState_loads_from_localStorage` | Mock localStorage, verify restore | High |
| TC-1.5 | `test_saveTableState_handles_localStorage_quota_error` | Simulate quota exceeded | Medium |
| TC-1.6 | `test_restoreTableState_handles_corrupted_data` | Pass invalid JSON | Medium |

**Sample Test:**
```javascript
describe('AdvancedTable', () => {
  beforeEach(() => {
    localStorage.clear();
    document.body.innerHTML = '<div id="table-container"></div>';
  });

  test('constructor initializes default state', () => {
    const table = new AdvancedTable('#table-container');
    expect(table.currentPage).toBe(1);
    expect(table.pageSize).toBe(25);
    expect(table.sortColumn).toBeNull();
    expect(table.sortDirection).toBe('asc');
  });

  test('saveTableState persists to localStorage', () => {
    const table = new AdvancedTable('#table-container');
    table.currentPage = 3;
    table.saveTableState();
    
    const saved = JSON.parse(localStorage.getItem('advancedTable_state'));
    expect(saved.currentPage).toBe(3);
  });
});
```

#### Task 1.2.2: `TableData` Module (`table-data.js`)

**Test File:** `tests/js/advanced-table/table-data.test.js`

| Test ID | Test Name | Description | Priority |
|---------|-----------|-------------|----------|
| TD-1.1 | `test_filter_by_single_condition` | Filter with one condition | High |
| TD-1.2 | `test_filter_by_multiple_AND_conditions` | Multiple filters with AND | High |
| TD-1.3 | `test_filter_by_OR_conditions` | Multiple filters with OR | High |
| TD-1.4 | `test_sort_ascending_string_column` | Sort strings A-Z | High |
| TD-1.5 | `test_sort_descending_numeric_column` | Sort numbers high-low | High |
| TD-1.6 | `test_sort_handles_null_values` | Nulls sorted consistently | Medium |
| TD-1.7 | `test_paginate_returns_correct_slice` | Pagination math correct | High |
| TD-1.8 | `test_paginate_handles_empty_data` | Empty array edge case | Medium |

#### Task 1.2.3: `TableConfig` Module (`table-config.js`)

**Test File:** `tests/js/advanced-table/table-config.test.js`

| Test ID | Test Name | Description | Priority |
|---------|-----------|-------------|----------|
| TG-1.1 | `test_saveView_creates_named_configuration` | Save view with name | High |
| TG-1.2 | `test_loadView_restores_configuration` | Load saved view | High |
| TG-1.3 | `test_deleteView_removes_configuration` | Delete view by name | High |
| TG-1.4 | `test_setDefaultView_persists_preference` | Set default view | Medium |
| TG-1.5 | `test_getViews_returns_all_saved_views` | List all views | Medium |

#### Task 1.2.4: `TableSidebar` Class (`table-sidebar.js`)

**Test File:** `tests/js/advanced-table/table-sidebar.test.js`

| Test ID | Test Name | Description | Priority |
|---------|-----------|-------------|----------|
| TS-1.1 | `test_addFilterRow_creates_new_filter_UI` | Add filter row | High |
| TS-1.2 | `test_removeFilterRow_deletes_filter` | Remove filter row | High |
| TS-1.3 | `test_applyAllFilters_returns_filter_config` | Apply filters | High |
| TS-1.4 | `test_clearAllFilters_resets_state` | Clear all filters | High |
| TS-1.5 | `test_populateColumns_shows_all_columns` | Populate column list | Medium |
| TS-1.6 | `test_toggleColumn_visibility` | Hide/show column | Medium |
| TS-1.7 | `test_resetColumns_restores_defaults` | Reset columns | Medium |

### Phase 1.3: Standalone Module Tests

#### Task 1.3.1: `ToastNotification` (`toast-notification.js`)

**Test File:** `tests/js/toast-notification.test.js`

| Test ID | Test Name | Description | Priority |
|---------|-----------|-------------|----------|
| TN-1.1 | `test_show_creates_toast_element` | Toast appears in DOM | High |
| TN-1.2 | `test_show_with_different_types` | success/error/warning/info | High |
| TN-1.3 | `test_auto_dismiss_after_timeout` | Auto-dismiss works | High |
| TN-1.4 | `test_manual_dismiss_on_click` | Click to dismiss | Medium |
| TN-1.5 | `test_multiple_toasts_stack_correctly` | Queue management | Medium |

#### Task 1.3.2: `FlashMessages` (`flash-messages.js`)

**Test File:** `tests/js/flash-messages.test.js`

| Test ID | Test Name | Description | Priority |
|---------|-----------|-------------|----------|
| FM-1.1 | `test_converts_flask_flash_to_toast` | Flask integration | High |
| FM-1.2 | `test_handles_multiple_flash_messages` | Multiple messages | Medium |
| FM-1.3 | `test_maps_flask_categories_correctly` | Category mapping | Medium |

### Phase 1 Deliverables

- [x] Jest environment configured and working
- [x] `tests/js/` directory structure created
- [x] **40+ unit tests** covering core JavaScript modules (41 tests passing)
- [x] **70%+ code coverage** for JavaScript (Target modules achieved 70%+, aggregated coverage lower due to out-of-scope files)
- [x] All tests passing
- [x] `npm test` command configured in `package.json`

---

## 📋 Phase 2: End-to-End Tests (Playwright)

**Goal:** Simulate real user workflows in a browser.
**Why Second:** Validates integration between frontend and backend.

### Phase 2.1: Environment Setup

#### Step 2.1.1: Install Playwright

```bash
# Install Playwright
npm install --save-dev @playwright/test

# Install browsers
npx playwright install
```

#### Step 2.1.2: Create Configuration

**`playwright.config.js`:**
```javascript
const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests/e2e',
  timeout: 30000,
  retries: 1,
  use: {
    baseURL: 'http://127.0.0.1:5000',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
  ],
  webServer: {
    command: 'python run.py',
    url: 'http://127.0.0.1:5000',
    reuseExistingServer: !process.env.CI,
  },
});
```

### Phase 2.2: Smoke Tests

| Test ID | Test Name | Description | Priority |
|---------|-----------|-------------|----------|
| E2E-S1 | `test_login_and_logout` | Full auth flow | Critical |
| E2E-S2 | `test_navigate_to_assets_page` | Assets page loads | Critical |
| E2E-S3 | `test_navigate_to_maintenance_orders_page` | MO page loads | Critical |
| E2E-S4 | `test_navigate_to_spare_parts_page` | Spare parts loads | High |
| E2E-S5 | `test_navigate_to_users_page` | Users page loads | High |

### Phase 2.3: CRUD Functional Tests

| Test ID | Test Name | Description | Priority |
|---------|-----------|-------------|----------|
| E2E-C1 | `test_create_asset` | Create new asset | High |
| E2E-C2 | `test_edit_asset` | Edit existing asset | High |
| E2E-C3 | `test_delete_asset` | Delete asset | High |
| E2E-C4 | `test_create_maintenance_order` | Create new MO | High |
| E2E-C5 | `test_edit_maintenance_order` | Edit existing MO | High |
| E2E-C6 | `test_delete_maintenance_order` | Delete MO | High |
| E2E-C7 | `test_create_spare_part` | Create spare part | Medium |
| E2E-C8 | `test_create_user` | Create new user | Medium |

### Phase 2.4: Advanced Table E2E Tests

| Test ID | Test Name | Description | Priority |
|---------|-----------|-------------|----------|
| E2E-T1 | `test_sort_column_ascending` | Click header to sort | High |
| E2E-T2 | `test_sort_column_descending` | Click again to reverse | High |
| E2E-T3 | `test_add_single_filter` | Add and apply filter | High |
| E2E-T4 | `test_add_multiple_filters_AND` | Multiple AND filters | High |
| E2E-T5 | `test_add_multiple_filters_OR` | Multiple OR filters | Medium |
| E2E-T6 | `test_clear_all_filters` | Clear filters button | High |
| E2E-T7 | `test_hide_column` | Hide column via sidebar | Medium |
| E2E-T8 | `test_show_hidden_column` | Show hidden column | Medium |
| E2E-T9 | `test_save_view` | Save current view | High |
| E2E-T10 | `test_load_saved_view` | Load saved view | High |
| E2E-T11 | `test_delete_saved_view` | Delete saved view | Medium |
| E2E-T12 | `test_export_to_csv` | Export table data | Medium |
| E2E-T13 | `test_pagination_navigation` | Page through results | High |
| E2E-T14 | `test_resize_column` | Drag to resize column | Medium |

### Phase 2 Deliverables

- [ ] Playwright environment configured
- [ ] `tests/e2e/` directory structure created
- [ ] **5 smoke tests** passing
- [ ] **8 CRUD tests** passing
- [ ] **14 Advanced Table tests** passing
- [ ] Cross-browser verification (Chrome, Firefox)
- [ ] `npm run test:e2e` command configured

---

## 📋 Phase 3: Visual Regression Tests (Playwright)

**Goal:** Catch unintended visual changes via screenshot comparison.
**Why Third:** Final layer of defense against UI regressions.

### Phase 3.1: Baseline Screenshots

| Page | Viewport | States to Capture |
|------|----------|-------------------|
| Assets List | 1920x1080 | Default, With Sidebar Open |
| MO List | 1920x1080 | Default, With Filters Applied |
| Spare Parts | 1920x1080 | Default |
| Asset Detail | 1920x1080 | View Mode, Edit Mode |
| MO Detail | 1920x1080 | View Mode, Edit Mode |

### Phase 3.2: Visual Test Cases

| Test ID | Test Name | Description | Priority |
|---------|-----------|-------------|----------|
| VR-1 | `test_visual_assets_page_default` | Assets page screenshot | High |
| VR-2 | `test_visual_assets_page_sidebar_open` | With sidebar | High |
| VR-3 | `test_visual_mo_page_default` | MO page screenshot | High |
| VR-4 | `test_visual_mo_page_filtered` | With filters applied | Medium |
| VR-5 | `test_visual_login_page` | Login page | Medium |
| VR-6 | `test_visual_dark_mode` | Dark mode (if applicable) | Low |

### Phase 3 Deliverables

- [ ] Baseline screenshots stored in `tests/e2e/screenshots/`
- [ ] **6 visual regression tests** configured
- [ ] Threshold configured (e.g., 0.1% pixel difference allowed)
- [ ] Screenshots auto-update mechanism documented

---

## 📋 Phase 4: CI/CD Integration

**Goal:** Run all tests automatically on every commit.

### Phase 4.1: GitHub Actions Workflow

**`.github/workflows/frontend-tests.yml`:**
```yaml
name: Frontend Tests

on: [push, pull_request]

jobs:
  jest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
      - run: npm ci
      - run: npm test -- --coverage
      - uses: codecov/codecov-action@v3

  playwright:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run test:e2e
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/
```

### Phase 4 Deliverables

- [ ] Jest tests running in CI
- [ ] Playwright tests running in CI
- [ ] Coverage reports uploaded to Codecov
- [ ] Test failures block PR merges
- [ ] Playwright failure artifacts preserved

---

## 📊 Summary: Test Count Targets

| Phase | Test Type | Count | Coverage Target |
|-------|-----------|-------|-----------------|
| Phase 1 | Jest Unit/Integration | 40+ | 70% JS |
| Phase 2 | Playwright E2E | 27 | Critical paths |
| Phase 3 | Visual Regression | 6 | Key pages |
| **Total** | | **73+** | |

---

## 📅 Implementation Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1 (Jest) | 2-3 days | Node.js, npm |
| Phase 2 (E2E) | 3-4 days | Phase 1 complete |
| Phase 3 (Visual) | 1-2 days | Phase 2 complete |
| Phase 4 (CI/CD) | 1 day | All phases complete |
| **Total** | **7-10 days** | |

---

## 📝 Completion Checklist

- [ ] Phase 1: Jest environment setup complete
- [ ] Phase 1: All unit tests written and passing
- [ ] Phase 2: Playwright environment setup complete
- [ ] Phase 2: All E2E tests written and passing
- [ ] Phase 3: Visual regression baselines captured
- [ ] Phase 3: Visual tests passing
- [ ] Phase 4: CI/CD workflow configured
- [ ] Phase 4: All tests passing in CI
- [ ] Documentation updated
- [ ] `core_code_quality_plan.md` Phase 3 unblocked
