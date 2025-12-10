# mockCMMS Bug Tracking Document
_Created: November 30, 2025_
_Last Updated: December 10, 2025_

---

## 📋 DOCUMENT PURPOSE

This document tracks all identified bugs in the mockCMMS application. Each bug includes:
- **Description**: What the bug is and how it manifests
- **Priority**: Critical, High, Medium, or Low
- **Status**: Open, In Progress, or Fixed
- **Affected Files**: Files that need to be modified

> [!NOTE]
> For Planning App bugs, see `apps/planning/docs/planning_bug_tracking.md`.

---

## 🤖 AI AGENT INSTRUCTIONS

> [!NOTE]
> **For detailed AI workflow rules**, see `GEMINI.md` Section 1.10 (Bug Tracking & Discovery).

### Status Definitions

| Icon | Status | Meaning |
|------|--------|---------|
| (none) | Open | Bug identified, not yet addressed |
| 🔄 | In Progress | Currently being worked on |
| ✅ FIXED | Fixed | Code applied, user confirmed |

### Document Quality Rules

> [!CAUTION]
> **MANDATORY:** Follow these rules to maintain document quality for AI interaction.

| Rule | Action |
|------|--------|
| **Update Summary Counts** | After EVERY status change, update the Summary table |
| **Apply 5-Day Rule** | After bug is FIXED for 5+ days, simplify entry (see below) |
| **Avoid Duplicates** | ALWAYS search document before adding new bug |
| **Keep Open Bugs Detailed** | New/Open bugs MUST have: Description, Current/Expected Behavior, Possible Solution, Affected Files |
| **Target: ~600 Lines Max** | Simplify resolved bugs aggressively to prevent bloat |

### Resolved Bug Simplification Rule

> [!IMPORTANT]
> After a bug is marked **RESOLVED for 5+ days**, simplify its entry:
> 1. **Keep:** Status, Resolution date, 1-2 sentence summary, Affected files
> 2. **Remove:** Current/Expected Behavior, Possible Solution, Code snippets, Testing scenarios
> 3. **Purpose:** Reduce document size for efficient AI processing

---

## 🔥 CRITICAL BUGS

### Bug #35: Delete Functionality Regression
**Priority:** Critical  
**Status:** Open  
**Identified:** December 10, 2025

**Description:**  
Delete buttons are visible but not working on multiple detail pages. This is a regression of the fixes from Bug #R3, #1, and #6.

**Current Behavior:**
- Delete buttons are rendered and visible on all detail pages
- Clicking the Delete button does NOT trigger the delete action
- No error message is shown
- User remains on the same page with no feedback

**Expected Behavior:**
- Clicking Delete should show a confirmation dialog
- After confirmation, the item should be deleted
- User should be redirected to the list page with a success message
- Flash message should say "deleted" (not "updated")

**Affected Areas:**
1. **Asset Detail Page** - Delete button present but action fails
2. **MO Detail Page** - Delete button present but action fails
3. **Spare Part Detail Page** - Delete button present but action fails
4. **User Detail Page** - Delete button present but action fails
5. **Asset Details → MO Section** - Delete buttons in MO table not working

**Possible Solution:**
1. Check if delete forms have correct `action` URL
2. Verify CSRF tokens are present in delete forms
3. Check if JavaScript is preventing form submission
4. Verify delete routes exist and are correctly defined in `main.py`
5. Check browser console for JavaScript errors
6. Test each delete form individually

**Affected Files:**
- `src/templates/asset_detail.html`
- `src/templates/maintenance_order_detail.html`
- `src/templates/spare_part_detail.html`
- `src/templates/user_detail.html`
- `src/routes/main.py` (delete routes)

**Related Bugs:**
- Bug #R3: Delete Button Placement and Duplicated Forms
- Bug #1: Missing Delete Button on Asset Details Page
- Bug #6: Missing Delete Button on MO Details Page
- Bug #20: Missing Delete Functionality for Users

---

### Bug #2: CSRF Token Missing - MO and Spare Parts Forms
**Priority:** Critical  
**Status:** ✅ RESOLVED - Prior to December 2, 2025  
**Resolution:** Added CSRF tokens to all forms (`maintenance_order_detail.html`, `spare_part_detail.html`, `asset_detail.html`, `user_detail.html`).  
**Files:** `src/templates/*.html`

---

## 🚨 HIGH PRIORITY BUGS

### Bug #36: "Could Not Load Saved Configurations" Warning
**Priority:** High  
**Status:** Open  
**Identified:** December 10, 2025

**Description:**  
When navigating to the Assets page, a warning toast appears with the message: "Could not load saved configurations". This suggests an issue with the table configuration API or local storage.

**Current Behavior:**
- User navigates to Assets page (`/assets`)
- Warning toast displays: "Could not load saved configurations"
- Table still renders but without saved view/column preferences
- Issue may occur on other pages with advanced tables

**Expected Behavior:**
- No error should appear on page load
- Saved configurations should load silently
- If no saved config exists, use defaults without warning
- Only show errors for actual failures (network, server errors)

**Possible Causes:**
1. API endpoint `/api/table-config/assets` returning error
2. Local storage data corruption or malformed JSON
3. Missing or malformed configuration data in database
4. CORS or authentication issues with API call
5. JavaScript error in `loadConfigurations()` function

**Possible Solution:**
1. Check browser console for specific error details
2. Verify `/api/table-config/assets` endpoint returns valid JSON
3. Check if localStorage has corrupted data - try clearing
4. Add try/catch around JSON parsing in sidebar.js
5. Improve error handling to fail silently for missing configs

**Affected Files:**
- `src/static/js/advanced-table/table-sidebar.js` (loadConfigurations method)
- `src/routes/api.py` (table-config endpoints)

---

### Bug #13: Table Views - Save/Load Functionality Not Working
**Priority:** High  
**Status:** Open  
**Identified:** Prior to December 2, 2025

**Description:**  
The complete table views save/load functionality is not working properly. Users cannot reliably save, load, or manage named table configurations.

**Current Behavior:**
- "Save View" button may not respond or show prompt (in some browsers)
- Saved views may not persist across sessions
- Loading a saved view may not restore the exact table state
- Deleting views may not work
- Setting a default view may not persist

**Expected Behavior:**
- Users can save current table configuration as a named view
- Users can load saved views and see exact same table state
- Users can delete saved views
- Users can set a view as default (loads automatically on page load)
- All view operations should provide clear feedback (toast messages)
- Works consistently across all browsers

> [!TIP]
> **Note:** Bug #9 was consolidated into this bug. The browser `window.prompt()` for entering view names works in normal browsers but may not appear in incognito/automated browsers. Consider replacing with inline UI input.

**Possible Solution:**
1. Replace `window.prompt()` with inline modal or input field
2. Verify API endpoints work correctly:
   - POST `/api/table-config/<page>` (save)
   - GET `/api/table-config/<page>` (load)
   - DELETE `/api/table-config/<page>/<id>` (delete)
3. Test each operation with browser dev tools open
4. Check database for saved TableConfiguration records
5. Verify localStorage state matches saved configuration

**Affected Files:**
- `src/static/js/advanced-table/table-sidebar.js` (view management UI)
- `src/static/js/advanced-table/table-config.js` (view save/load logic)
- `src/routes/api.py` (table-config endpoints)
- `src/services/db_utils.py` (TableConfiguration model)

---

### Bug #27: MO Table in Asset Details Should Use Advanced Table
**Priority:** High  
**Status:** ✅ FIXED - December 10, 2025  
**Resolution:** Replaced basic Bootstrap table in `asset_detail.html` with Advanced Table component. Updated `main.py` to pass serialized MO data.  
**Files:** `src/templates/asset_detail.html`, `src/routes/main.py`

---

### Bug #1: Missing Delete Functionality for Assets
**Priority:** High  
**Status:** ✅ RESOLVED - December 2, 2025  
**Resolution:** Fixed as part of Bug #R3. Delete buttons added to all detail pages.  
**See:** Bug #R3

---

### Bug #3: Incorrect Back Button Navigation
**Priority:** High  
**Status:** ✅ RESOLVED - December 2, 2025  
**Resolution:** Fixed as part of Bug #R1. Back button now returns to originating page.  
**See:** Bug #R1

---

### Bug #4: Table State Not Preserved on Navigation
**Priority:** High  
**Status:** ✅ RESOLVED - December 2, 2025  
**Resolution:** Implemented `localStorage` state persistence with 24-hour expiration. Saves/restores sort, filters, search, columns.  
**Files:** `src/static/js/advanced-table/table-core.js`, `table-data.js`, `table-sidebar.js`

---

### Bug #5: Assignees Field Needs Dropdown
**Priority:** High  
**Status:** ✅ RESOLVED - December 2, 2025  
**Resolution:** Replaced textarea with Select2 multi-select dropdown. Added Teams and Technicians optgroups.  
**Files:** `src/routes/main.py`, `src/templates/maintenance_order_detail.html`, `src/templates/base.html`

---

### Bug #6: Missing Delete Functionality for MOs
**Priority:** High  
**Status:** ✅ RESOLVED - December 2, 2025  
**Resolution:** Fixed as part of Bug #R3.  
**See:** Bug #R3

---

### Bug #11: Spare Parts CSRF Token Missing
**Priority:** High  
**Status:** ✅ RESOLVED - Prior to December 2, 2025  
**Resolution:** Fixed together with Bug #2.  
**See:** Bug #2

---

### Bug #14: Cannot Click Table Elements After Column Changes
**Priority:** High  
**Status:** ✅ RESOLVED - December 2, 2025  
**Resolution:** Replaced individual row listeners with event delegation on `<tbody>`. Listeners now survive table re-renders.  
**Files:** `src/static/js/advanced-table/table-events.js`, `src/static/css/advanced-table.css`

---

### Bug #31: Table Header Not Sticky on Scroll
**Priority:** High  
**Status:** ✅ FIXED - December 10, 2025  
**Resolution:** Fixed `overflow: hidden` causing sticky failure. Applied `overflow: visible` to `.advanced-table`.  
**Files:** `src/static/css/advanced-table.css`, `src/static/js/advanced-table/table-render.js`

---

## 📊 MEDIUM PRIORITY BUGS

### Bug #7: Missing Required Field Indicators
**Priority:** Medium  
**Status:** Partially Resolved - Prior to December 2, 2025

**Description:**  
Forms do not clearly indicate which fields are required. Red asterisks (*) have been added to most pages but not all.

**Current Behavior:**
- ✅ Asset Detail form has required indicators
- ✅ MO Detail form has required indicators
- ✅ Spare Parts form has required indicators
- ❌ User Detail form does NOT have required indicators

**Expected Behavior:**
- All forms should have red asterisks next to required field labels
- All forms should have "* Required fields" note at bottom

**Remaining Work:**
Apply same pattern to `user_detail.html`:
1. Add `required-field` class to required field labels
2. Add "* Required fields" note at bottom of form

**Affected Files:**
- `src/templates/user_detail.html` (needs update)

---

### Bug #8: Table Columns Too Narrow on Default Load
**Priority:** Medium  
**Status:** Partially Resolved - December 4, 2025

**Description:**  
When tables load, columns are too narrow, causing text to wrap or truncate. Smart default widths have been implemented but only for the MO table.

**Current Behavior:**
- ✅ MO table has smart default column widths
- ❌ Assets table uses generic widths
- ❌ Spare Parts table uses generic widths
- ❌ Users table uses generic widths

**Expected Behavior:**
- All tables should have content-type-based default widths
- ID columns: 65-80px
- Code columns: 150px
- Name columns: 250px
- Description columns: 350px
- Date columns: 120px
- Status columns: 100px

**Remaining Work:**
Apply `getDefaultWidth()` logic to all tables, not just MO table.

**Affected Files:**
- `src/static/js/advanced-table/table-resize.js` (expand logic to all tables)

---

### Bug #10: Table Width Not Responsive to Window Resize
**Priority:** Medium  
**Status:** ✅ RESOLVED - December 4, 2025  
**Resolution:** Added `handleWindowResize` method in `table-resize.js` with event listeners.  
**Files:** `src/static/js/advanced-table/table-resize.js`, `table-sidebar.js`

---

### Bug #16: Frequency Field Only for PM Orders
**Priority:** Medium  
**Status:** ✅ FIXED - December 1, 2025  
**Resolution:** Added JS event listener to enable/disable frequency based on order type.  
**Files:** `src/templates/maintenance_order_detail.html`

---

### Bug #17: OR Filter Operator Logic
**Priority:** Medium  
**Status:** ✅ FIXED - December 10, 2025  
**Resolution:** Implemented "Conditional Mute" logic - previous filter muted until new OR row is complete.  
**Files:** `src/static/js/advanced-table/table-sidebar.js`

---

### Bug #20: Missing Delete Functionality for Users
**Priority:** Medium  
**Status:** ✅ FIXED - December 10, 2025  
**Resolution:** Added delete button and `delete_user` route with UserSkill relationship handling.  
**Files:** `src/templates/user_detail.html`, `src/routes/main.py`

---

### Bug #21: Asset Field Not Pre-filled on MO Creation
**Priority:** Medium  
**Status:** ✅ FIXED - December 1, 2025  
**Resolution:** Asset dropdown pre-selected and disabled when coming from asset page.  
**Files:** `src/routes/main.py`, `src/templates/maintenance_order_detail.html`

---

### Bug #22: CSRF Token Missing in MO Delete from Asset Details
**Priority:** Medium  
**Status:** ✅ FIXED - December 1, 2025  
**Resolution:** Added CSRF token to delete form in asset_detail.html.  
**Files:** `src/templates/asset_detail.html`

---

### Bug #23: Frequency Field Not Showing Saved Value
**Priority:** Medium  
**Status:** ✅ FIXED - December 1, 2025  
**Resolution:** Fixed case sensitivity in template comparison. Used `.lower()` filter.  
**Files:** `src/templates/maintenance_order_detail.html`

---

### Bug #24: Autofill Background Color Inconsistency
**Priority:** Medium  
**Status:** ✅ FIXED - December 10, 2025  
**Resolution:** CSS override for browser autofill styles in dark theme.  
**Files:** `src/static/css/main.css`

---

### Bug #25: MO Section on Add New Asset Page
**Priority:** Medium  
**Status:** ✅ RESOLVED - December 2, 2025  
**Resolution:** Wrapped MO section in `{% if asset %}` conditional.  
**Files:** `src/templates/asset_detail.html`

---

### Bug #26: Frequency Field Not Required for PM Orders
**Priority:** Medium  
**Status:** ✅ RESOLVED - December 2, 2025  
**Resolution:** Added dynamic `required` attribute and backend validation for PM orders.  
**Files:** `src/templates/maintenance_order_detail.html`, `src/routes/main.py`

---

### Bug #28: Assignees Dropdown Opens When Removing Item
**Priority:** Medium  
**Status:** ✅ FIXED - December 10, 2025  
**Resolution:** Implemented Select2 event handlers to track dropdown state and prevent unwanted opening.  
**Files:** `src/templates/maintenance_order_detail.html`

---

### Bug #29: Missing Assignees Column in MO Table
**Priority:** Medium  
**Status:** ✅ RESOLVED - December 3, 2025  
**Resolution:** Added localStorage check to clear outdated state missing new column.  
**Files:** `src/templates/maintenance_orders.html`, `src/services/db_utils.py`

---

### Bug #30: Layout Shift When Adding Assignees
**Priority:** Medium  
**Status:** ✅ RESOLVED - December 9, 2025  
**Resolution:** Added CSS max-height (120px) with overflow-y scroll for Select2 container.  
**Files:** `src/static/css/main.css`

---

## 🔵 LOW PRIORITY BUGS

### Bug #33: "Select All" Checkbox Behavior
**Priority:** Low  
**Status:** Open

**Description:**  
"Select All" checkbox in table header only selects visible rows on the current page. This is confusing if user wants to bulk action ALL rows across all pages.

**Current Behavior:**
- Click "Select All" checkbox in table header
- Only visible rows on current page are selected
- Rows on other pages are NOT selected
- No indication that selection is limited to current page

**Expected Behavior:**
- Option 1: Select all rows across ALL pages (with warning about data volume)
- Option 2: Show message "Selected X of Y rows on this page" to clarify
- Option 3: Add dropdown with "Select all on page" vs "Select all X items"

**Possible Solution:**
1. Add indicator showing "X of Y selected"
2. When "Select All" is checked, show option to "Select all X items"
3. Track selection state in table core, not just visible checkboxes
4. Consider performance for large datasets

**Affected Files:**
- `src/static/js/advanced-table/table-events.js` (checkbox logic)
- `src/static/js/advanced-table/table-render.js` (selection state)
- `src/static/css/advanced-table.css` (selection indicator styling)

---

### Bug #34: Long Text Overflow in Table Cells
**Priority:** Low  
**Status:** Open

**Description:**  
Long descriptions or text content in table cells don't wrap or truncate properly, causing columns to expand excessively or horizontal scrolling.

**Current Behavior:**
- Long text in cells pushes column width to fit content
- Table may become wider than viewport
- Horizontal scrolling required
- Layout looks broken with very long content

**Expected Behavior:**
- Text should truncate with ellipsis (...) after max width
- Hover tooltip should show full text
- Or: text wraps within fixed column width
- Table maintains consistent width regardless of content length

**Possible Solution:**
1. Add CSS `text-overflow: ellipsis; overflow: hidden; white-space: nowrap;`
2. Set max-width on description columns (e.g., 300px)
3. Add title attribute for hover tooltip
4. Consider expandable cells for long content

**Affected Files:**
- `src/static/css/advanced-table.css` (cell overflow styles)
- `src/static/js/advanced-table/table-render.js` (add title attributes)

---

### Bug #15: Status Field Should Be Hidden in MO Creation
**Priority:** Low  
**Status:** ✅ FIXED - December 10, 2025  
**Resolution:** Confirmed `{% if mo %}` logic already hides status field. Backend defaults to "Open".  
**Files:** `src/templates/maintenance_order_detail.html`, `src/routes/main.py`

---

### Bug #19: KeyError - 'frequency' Field
**Priority:** Low  
**Status:** ✅ FIXED - December 1, 2025  
**Resolution:** Changed `request.form['field']` to `request.form.get('field', '')` for optional fields.  
**Files:** `src/routes/main.py`

---

### Bug #32: Add Filter Button Enabled Prematurely
**Priority:** Low  
**Status:** ✅ FIXED - December 10, 2025  
**Resolution:** Updated `validateAllFilters` to disable button if any filter row is incomplete.  
**Files:** `src/static/js/advanced-table/table-sidebar.js`

---

## ✅ RESOLVED BUGS (Historical)

### Bug #R1: Redirect After MO Operations from Asset Detail
**Priority:** High  
**Status:** ✅ RESOLVED - December 2, 2025  
**Resolution:** Added `return_to` parameter handling for proper redirects. Fixed back button, form actions, and delete routes.  
**Files:** `src/routes/main.py`, `src/templates/maintenance_order_detail.html`, `src/templates/asset_detail.html`

---

### Bug #R2: Frequency Not Pre-selected on Edit PM Order
**Priority:** Medium  
**Status:** ✅ RESOLVED - December 2, 2025  
**Resolution:** Fixed case sensitivity mismatch - used `.lower()` filter in Jinja2 template.  
**Files:** `src/templates/maintenance_order_detail.html`

---

### Bug #R3: Delete Button Placement and Duplicated Forms
**Priority:** High  
**Status:** ✅ RESOLVED - December 2, 2025  
**Resolution:** Standardized delete button placement, fixed template syntax errors, removed duplicate forms, fixed cascade deletes for users and assets.  
**Files:** `src/templates/*.html`, `src/routes/main.py`, `src/services/db_utils.py`

---

## 📊 BUG SUMMARY BY PRIORITY

> [!NOTE]
> Last updated: December 10, 2025

### Summary Counts

| Category | Open | Partial | In Progress | Fixed | Total |
|----------|------|---------|-------------|-------|-------|
| Critical | 1 | 0 | 0 | 1 | 2 |
| High | 2 | 0 | 0 | 9 | 11 |
| Medium | 0 | 2 | 0 | 11 | 13 |
| Low | 2 | 0 | 0 | 3 | 5 |
| **Total** | **5** | **2** | **0** | **24** | **31** |

> [!WARNING]
> **Critical Bug:** #35 (Delete Functionality Regression) requires immediate attention.

### Open Bugs
- **Critical:** #35 Delete Functionality Regression
- **High:** #13 Table Views Save/Load, #36 Config Warning
- **Low:** #33 Select All Checkbox, #34 Long Text Overflow

### Partially Resolved
- **Medium:** #7 Required Field Indicators (needs Users page), #8 Column Widths (needs all tables)

---

## 📅 MAINTENANCE GUIDELINES

**When a bug is fixed:**
1. Change status to "✅ FIXED" with date
2. Add 1-2 sentence resolution summary
3. List affected files
4. Update summary counts

**After 5+ days resolved:**
1. Simplify entry per "Resolved Bug Simplification Rule"
2. Remove verbose details (behavior, solution steps, code snippets)

**When adding new bugs:**
1. Use next available bug number
2. Set priority (Critical, High, Medium, Low)
3. Add full details: Description, Current/Expected Behavior, Possible Solution, Affected Files
4. Add to appropriate section
5. Update summary counts

---

_This document tracks bugs for the main mockCMMS application._
