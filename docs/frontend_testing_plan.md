# Comprehensive Frontend Testing Plan for mockCMMS

**Status:** 📝 **PROPOSED**
**Priority:** Critical
**Proposed Tools:** Jest (Unit/Integration), Playwright (E2E/Visual Regression)

---

> [!IMPORTANT]
> **Purpose:** This document proposes a new phase of work to create a robust suite of frontend automated tests. This effort is now the highest priority and **blocks** the frontend code quality audit (Phases 3, 4, and 5 of the `core_code_quality_plan.md`).

---

## 1. Overview & Objectives

This document outlines a multi-layered strategy for creating a comprehensive, automated frontend test suite for the `mockCMMS` application. The primary objective is to build a safety net that enables safe refactoring, prevents UI regressions, and ensures a consistent user experience. This plan is modeled after the successful backend testing strategy and will serve as the foundation for future frontend development.

### Key Objectives:
-   **Automated UI Validation:** Create a suite of tests that automatically verify the functionality of critical UI components, with a strong focus on the Advanced Table.
-   **Enable Safe Refactoring:** Build the confidence to perform large-scale changes, such as modularizing the JavaScript code or refactoring CSS, without breaking the user interface.
-   **Cross-Browser Consistency:** Use modern testing frameworks to ensure the application behaves consistently across different browsers.
-   **CI/CD Integration:** Integrate the frontend test suite into the CI/CD pipeline to automatically catch UI regressions on every commit.

---

## 2. A Multi-Layered Testing Strategy

To achieve comprehensive test coverage, I propose a multi-layered testing strategy that includes:

1.  **Layer 1: JavaScript Unit & Integration Testing (Jest):**
    -   **Purpose:** To test individual JavaScript functions, classes, and modules in isolation, ensuring that the core business logic is correct.
    -   **Why it's first:** These tests are fast, easy to write, and provide immediate feedback, making them the perfect foundation for refactoring.

2.  **Layer 2: End-to-End (E2E) Testing (Playwright):**
    -   **Purpose:** To simulate real user workflows in a browser, ensuring that all the individual components work together as expected.
    -   **Why it's second:** E2E tests are slower and more complex than unit tests, so they should be used to cover critical user journeys that are not easily tested at the unit level.

3.  **Layer 3: Visual Regression Testing (Playwright):**
    -   **Purpose:** To catch unintended visual changes by comparing screenshots of the application before and after a change.
    -   **Why it's third:** This is the final layer of defense against regressions, ensuring that the application not only works correctly but also looks correct.

---

## 3. Detailed Test Specifications

### Layer 1: JavaScript Unit & Integration Tests (Jest)

**Setup:**
1.  Install Jest and its dependencies (`jest`, `babel-jest`, `@babel/preset-env`).
2.  Configure Babel to transpile JavaScript for Jest.
3.  Create a `jest.config.js` file to configure the test environment.

**Test Cases:**

-   **`AdvancedTable` Class (`table-core.js`):**
    -   Test constructor and default state initialization.
    -   Test `saveTableState` and `restoreTableState` methods.
-   **`TableSidebar` Class (`table-sidebar.js`):**
    -   Test filter management logic (`addFilterRow`, `applyAllFilters`, `clearAllFilters`).
    -   Test column management logic (`populateColumns`, `applyColumnChanges`, `resetColumns`).
-   **`ToastNotification` (`toast-notification.js`):**
    -   Test that notifications are created and dismissed correctly.

### Layer 2: End-to-End Tests (Playwright)

**Setup:**
1.  Install Playwright.
2.  Configure Playwright to run against the local development server.

**Test Cases:**

-   **Smoke Tests:**
    -   `test_login_and_logout`
    -   `test_navigate_to_assets_page`
    -   `test_navigate_to_maintenance_orders_page`
-   **Functional Tests:**
    -   `test_create_and_delete_asset`
    -   `test_create_and_delete_maintenance_order`
-   **Advanced Table E2E Tests:**
    -   `test_sort_column_ascending_and_descending`
    -   `test_add_and_apply_single_filter`
    -   `test_hide_and_show_column`
    -   `test_save_and_load_view`

### Layer 3: Visual Regression Tests (Playwright)

**Setup:**
-   Configure Playwright's screenshot capabilities.
-   Establish a baseline set of screenshots for each page.

**Test Cases:**

-   **`test_visual_regression_of_main_pages`**:
    -   Take screenshots of the Assets, Maintenance Orders, and Spare Parts pages and compare them to the baseline.
-   **`test_visual_regression_of_advanced_table`**:
    -   Take screenshots of the Advanced Table in various states (e.g., with filters applied, with the sidebar open) and compare them to the baseline.

---

## 4. Implementation Plan

I propose the following phased approach to implement the frontend test suite:

1.  **Phase 1: JavaScript Unit & Integration Tests (Jest)**
    -   Set up the Jest testing environment.
    -   Write unit tests for the core JavaScript classes.
2.  **Phase 2: End-to-End and Visual Regression Tests (Playwright)**
    -   Set up the Playwright testing environment.
    -   Implement the smoke, functional, and visual regression tests.
3.  **Phase 3: CI/CD Integration**
    -   Integrate the Jest and Playwright test suites into the GitHub Actions workflow.

This plan provides a clear path to building a comprehensive frontend test suite that will enable safe and efficient development in the future.
