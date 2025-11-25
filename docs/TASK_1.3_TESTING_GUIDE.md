# Task 1.3 - AND/OR Filter Logic - Testing Guide

**Date:** November 25, 2025  
**Task:** Implement AND/OR Filter Logic  
**Duration:** 5 minutes  
**Component:** Advanced Table Filter Manager

---

## 🎯 What Was Implemented

**Core Changes:**
1. ✅ **Structured Filter Array:** `this.filters` is now an array of objects `[{ logic, column, operator, value }]` instead of a simple object.
2. ✅ **AND/OR Logic Evaluation:** `applyFiltersWithLogic()` now correctly processes the structured array, applying AND/OR logic sequentially.
3. ✅ **State Persistence:** The Filter Manager now correctly displays saved filters and their corresponding AND/OR logic when reopened.
4. ✅ **Code Refactor:** `addFilterRow()` and `addFilterRowWithData()` were refactored for consistency and maintainability.

---

## ✅ Test Scenarios

### Test 1: Basic AND Logic (2 filters)

**Steps:**
1. Open Filter Manager.
2. Add first filter: `Username` `contains` `tech`.
3. Click "Add Filter".
4. Add second filter: `Roles` `contains` `technician`.
5. Ensure "AND" is selected between the two filters.
6. Click "Apply".

**Expected:**
- ✅ Table shows only rows where Username contains "tech" **AND** Roles contains "technician".
- ✅ For example, `mike.tech` should show, but `sarah.supervisor` should not.

**PASS:** [ ]  
**FAIL:** [ ] _____________________

---

### Test 2: Basic OR Logic (2 filters)

**Steps:**
1. Clear all filters.
2. Open Filter Manager.
3. Add first filter: `Roles` `equals` `Manager`.
4. Click "Add Filter".
5. Select "OR" logic.
6. Add second filter: `Roles` `equals` `Viewer`.
7. Click "Apply".

**Expected:**
- ✅ Table shows all rows where Role is "Manager" **OR** "Viewer".
- ✅ You should see users like `john.manager` and `anna.viewer`.

**PASS:** [ ]  
**FAIL:** [ ] _____________________

---

### Test 3: Complex Chain (AND, then OR)

**Steps:**
1. Clear all filters.
2. Open Filter Manager.
3. **Filter 1:** `Username` `contains` `tech`.
4. Click "Add Filter" (AND is default).
5. **Filter 2:** `Availability` `equals` `Available`.
6. Click "Add Filter".
7. **Select "OR"** for the next logic.
8. **Filter 3:** `Roles` `equals` `Manager`.
9. Click "Apply".

**Logic:** `(Username contains 'tech' AND Availability is 'Available') OR (Roles is 'Manager')`

**Expected:**
- ✅ You should see all technicians who are available (e.g., `mike.tech`).
- ✅ You should ALSO see all managers, regardless of their availability (e.g., `john.manager`, `robert.manager`).

**PASS:** [ ]  
**FAIL:** [ ] _____________________

---

### Test 4: State Persistence in Filter Manager

**Steps:**
1. Apply the complex filter from Test 3.
2. Close the filter window by clicking "Apply", "Cancel", or the background overlay.
3. Re-open the Filter Manager.

**Expected:**
- ✅ All 3 filter rows are still present.
- ✅ All columns, operators, and values are correct.
- ✅ The "AND" toggle between Filter 1 and 2 is correctly selected.
- ✅ The "OR" toggle between Filter 2 and 3 is correctly selected.

**PASS:** [ ]  
**FAIL:** [ ] _____________________

---

### Test 5: Removing a Filter

**Steps:**
1. With the 3 filters from Test 4 loaded, click the trash icon next to the **second filter** (`Availability` `equals` `Available`).
2. Observe the Filter Manager UI.

**Expected:**
- ✅ The second filter row is removed.
- ✅ The "AND" logic toggle that was *before* it is also removed.
- ✅ You are left with Filter 1, an "OR" toggle, and Filter 3.
- ✅ Click "Apply". The new logic `(Username contains 'tech') OR (Roles is 'Manager')` should be applied correctly.

**PASS:** [ ]  
**FAIL:** [ ] _____________________

---

## 🐛 Common Issues to Check

### Issue: OR logic not working
- **Check:** `applyFiltersWithLogic()` correctly uses `result = result || currentResult`.
- **File:** `src/static/js/advanced-table.js`

### Issue: Filter Manager doesn't show saved logic
- **Check:** `showFilterManager()` correctly reads `filter.logic` and sets the `checked` property on the radio buttons.
- **File:** `src/static/js/advanced-table.js`

### Issue: Adding a new filter doesn't add the AND/OR toggle
- **Check:** `addFilterRow()` correctly creates and appends the `.filter-logic` div.
- **File:** `src/static/js/advanced-table.js`

---

## ✅ Implementation Summary

**Files Modified:**
1. `src/static/js/advanced-table.js`
   - Changed `this.filters` to a structured array.
   - Rewrote `applyFilters()`, `applyFiltersWithLogic()`, and `showFilterManager()`.
   - Refactored `addFilterRow()` and `addFilterRowWithData()`.
   - Updated `resetTableState()` to handle the new array format.

**Result:** The filtering system is now significantly more powerful and can handle complex, multi-step logic with both AND and OR conditions.

