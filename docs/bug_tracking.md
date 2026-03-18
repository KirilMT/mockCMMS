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
> **Document Relationship:** This document tracks bugs in existing functionality. For new features and strategic improvements, see `mockCMMS_roadmap.md`.
>
> **App-Specific Bug Tracking:**
>
> | Application       | Bug Tracker                                                            |
> | :---------------- | :--------------------------------------------------------------------- |
> | **Planning App**  | [See Planning Bugs](../apps/planning/docs/planning_bug_tracking.md)    |
> | **Reporting App** | [See Reporting Bugs](../apps/reporting/docs/reporting_bug_tracking.md) |

---

## 🤖 AI AGENT INSTRUCTIONS

> [!NOTE] > **For detailed AI workflow rules**, see `GEMINI.md` Section 1.10 (Bug Tracking & Discovery).

### Status Definitions

| Icon   | Status      | Meaning                           |
| ------ | ----------- | --------------------------------- |
| (none) | Open        | Bug identified, not yet addressed |
| 🔄     | In Progress | Currently being worked on         |
| ✅     | Resolved    | Code applied, user confirmed      |

### Document Quality Rules

> [!CAUTION] > **MANDATORY:** Follow these rules to maintain document quality for AI interaction.

| Rule                        | Action                                                                                             |
| --------------------------- | -------------------------------------------------------------------------------------------------- |
| **Update Summary Counts**   | After EVERY status change, update the Summary table                                                |
| **Apply 5-Day Rule**        | After bug is FIXED for 5+ days, simplify entry (see below)                                         |
| **Avoid Duplicates**        | ALWAYS search document before adding new bug                                                       |
| **Keep Open Bugs Detailed** | New/Open bugs MUST have: Description, Current/Expected Behavior, Possible Solution, Affected Files |
| **Target: ~600 Lines Max**  | Simplify resolved bugs aggressively to prevent bloat                                               |

### Resolved Bug Simplification Rule

> [!IMPORTANT]
> After a bug is marked **RESOLVED for 5+ days**, simplify its entry:
>
> 1. **Keep:** Status, Resolution date, 1-2 sentence summary, Affected files
> 2. **Remove:** Current/Expected Behavior, Possible Solution, Code snippets, Testing scenarios
> 3. **Purpose:** Reduce document size for efficient AI processing

---

## 🔥 CRITICAL BUGS

### Bug #35: Delete Functionality Regression (System Popup Issue)

**Priority:** Critical
**Status:** ✅ RESOLVED - December 18, 2025
**Resolved:** December 18, 2025
**Identified:** December 10, 2025

**Description:**
Delete functionality is compromised because the application relies on the browser's native `confirm()` system popup, which is unreliable in certain environments (e.g., Incognito mode, IDE embedded browsers). Additionally, the delete forms were improperly nested inside the main edit forms (Invalid HTML).

**Status Update:**

- **HTML Structure (Fixed):** The nested form issue has been resolved in the templates. Delete forms are now siblings to the main form.
- **Confirmation UI (Pending):** The native `confirm()` dialog needs to be replaced with a custom modal or inline confirmation to ensure reliability across all environments.

**Current Behavior:**

- In standard browsers: Delete works (after HTML fix).
- In IDEs/Incognito: Clicking Delete may show no popup or fail to confirm, effectively blocking the action.

**Expected Behavior:**

- User interaction should use a custom modal or inline UI, avoiding system popups.
- Delete action should be reliable in all browser environments.

**Required Actions (Blocked by JS restriction):**

1. Implement a custom confirmation modal (Bootstrap modal) or inline confirmation.
2. Update all delete buttons to trigger this modal instead of `onsubmit="return confirm(...)"`.

**Affected Files:**

- `src/templates/asset_detail.html` (HTML fixed)
- `src/templates/maintenance_order_detail.html` (HTML fixed)
- `src/templates/spare_part_detail.html` (HTML fixed)
- `src/templates/user_detail.html` (HTML fixed)
- `src/static/js/` (Needs updates for modal logic - **BLOCKED**)

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

### Bug #37: Edit/Delete Buttons Should Only Appear for Manually Added Report Items

**Priority:** High
**Status:** Open
**Identified:** March 11, 2026

**Description:**
In the Reporting app, edit and delete buttons currently appear for all report items (breakdowns, handovers, activities, tasks), regardless of whether they were automatically imported from Maintenance Orders or manually added by users. Since items linked to MOs are dependent on those MOs, they should not be editable or deletable within the report interface.

**Current Behavior:**

- All report items display edit and delete buttons
- Users can attempt to edit/delete items that are linked to MOs
- This creates confusion about data ownership and integrity
- Deleting MO-linked items could cause data inconsistencies

**Expected Behavior:**

- Edit and delete buttons should **only appear** for items that were manually added using the "+" button
- Items automatically imported from MOs should be read-only (no edit/delete buttons)
- This distinction should apply to all report types:
  - Shift Reporting: breakdowns, handovers, activities, tasks
  - Weekend Reporting: breakdowns, handovers, activities, tasks
- Users should understand which items are system-generated vs. user-added

**Possible Solution:**

1. Add a flag to report items indicating their source (e.g., `source: 'manual'` or `source: 'mo_linked'`)
2. Update report rendering logic to conditionally show edit/delete buttons based on source
3. Apply this logic consistently across all report types and item types
4. Consider adding a visual indicator (e.g., icon or badge) to distinguish MO-linked items

**Affected Files:**

- `apps/reporting/src/templates/shift_report_detail.html` (conditional button display)
- `apps/reporting/src/templates/weekend_report_detail.html` (conditional button display)
- `apps/reporting/src/services/report_generator.py` (add source metadata to items)
- `apps/reporting/src/services/data_aggregator.py` (track item source during aggregation)
- `apps/reporting/src/static/js/report-interactions.js` (update edit/delete handlers)
- `apps/reporting/src/routes/reporting.py` (validate source before allowing edits/deletes)

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

> [!TIP] > **Note:** Bug #9 was consolidated into this bug. The browser `window.prompt()` for entering view names works in normal browsers but may not appear in incognito/automated browsers. Consider replacing with inline UI input.

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
Forms do not clearly indicate which fields are required. Red asterisks (\*) have been added to most pages but not all.

**Current Behavior:**

- ✅ Asset Detail form has required indicators
- ✅ MO Detail form has required indicators
- ✅ Spare Parts form has required indicators
- ❌ User Detail form does NOT have required indicators

**Expected Behavior:**

- All forms should have red asterisks next to required field labels
- All forms should have "\* Required fields" note at bottom

**Remaining Work:**
Apply same pattern to `user_detail.html`:

1. Add `required-field` class to required field labels
2. Add "\* Required fields" note at bottom of form

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
> Last updated: March 11, 2026

### Summary Counts

| Category  | Open  | Partial | In Progress | Fixed  | Total  |
| --------- | ----- | ------- | ----------- | ------ | ------ |
| Critical  | 0     | 0       | 0           | 2      | 2      |
| High      | 3     | 0       | 0           | 9      | 12     |
| Medium    | 1     | 2       | 0           | 11     | 13     |
| Low       | 1     | 0       | 0           | 3      | 4      |
| **Total** | **5** | **2**   | **0**       | **25** | **31** |

> [!WARNING] > **Critical Bug:** #35 (Delete Functionality Regression) requires immediate attention.

### Open Bugs

- **Critical:** #35 Delete Functionality Regression
- **High:** #13 Table Views Save/Load, #36 Config Warning, #37 Edit/Delete Buttons for Manual Items
- **Low:** #34 Long Text Overflow

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
