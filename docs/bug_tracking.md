# mockCMMS Bug Tracking Document
_Created: November 30, 2025 - 6:57 PM_

---

## 📋 DOCUMENT PURPOSE

This document tracks all identified bugs in the mockCMMS application. Each bug includes:
- **Description**: What the bug is and how it manifests
- **Current Behavior**: What happens now (incorrect behavior)
- **Expected Behavior**: What should happen (correct behavior)
- **Possible Solution**: Technical approach to fix the bug
- **Priority**: Critical, High, Medium, or Low
- **Affected Files**: Files that need to be modified
- **Additional Info**: Context, dependencies, or related issues

---

## ✅ RESOLVED BUGS

### Bug #R1: Redirect After MO Creation/Edit/Delete from Asset Detail Page
**Priority:** High  
**Status:** ✅ RESOLVED - December 2, 2025

**Description:**  
Creating, editing, or deleting a Maintenance Order from an Asset Detail page resulted in incorrect redirects. Multiple navigation issues were discovered and fixed to ensure users always return to the page they came from.

**Issues Found:**
1. Creating MO from Asset Detail → redirected to MO list (incorrect)
2. "Back" button on MO add/edit page → linked to `edit_asset` instead of `asset_detail`
3. Editing MO from Asset Detail → redirected to MO list (incorrect)
4. Deleting MO from Asset Detail → redirected to MO list (incorrect)
5. Form didn't pass `return_to` parameter to preserve redirect context

**Solution Implemented:**
1. **add_mo() route** (line 165): Changed redirect from `edit_asset` to `asset_detail`
2. **maintenance_order_detail.html** (line 13): Fixed "Back" button from `edit_asset` to `asset_detail`
3. **maintenance_order_detail.html** (line 25): Added `return_to` and `asset_id` to form action URLs
4. **edit_mo() route** (lines 170-206): Added return_to parameter handling for proper redirect
5. **asset_detail.html** (line 109): Added return_to and asset_id to Edit MO link
6. **delete_mo() route** (lines 207-219): Added referrer checking to redirect back to asset detail

**Affected Files:**
- `src/routes/main.py` (lines 165, 170-206, 207-219)
- `src/templates/maintenance_order_detail.html` (lines 13, 25)
- `src/templates/asset_detail.html` (line 109)

**Testing Scenarios:**
✅ Create MO from Asset Detail → redirects to Asset Detail  
✅ Create MO from MO list → redirects to MO list  
✅ Edit MO from Asset Detail → redirects to Asset Detail  
✅ Edit MO from MO list → redirects to MO list  
✅ Delete MO from Asset Detail → redirects to Asset Detail  
✅ Delete MO from MO list → redirects to MO list  
✅ "Back" button navigates correctly in all scenarios  

---

### Bug #R2: Frequency Not Pre-selected on Edit PM Order
**Priority:** Medium  
**Status:** ✅ RESOLVED - December 2, 2025

**Description:**  
When editing an existing PM (Preventive Maintenance) order, the "Frequency" dropdown field appeared empty instead of showing the saved frequency value.

**Root Cause:**  
**Case sensitivity mismatch** between database values and template comparisons:
- Database stores: `'Monthly'`, `'Weekly'` (capitalized)
- Template checked: `mo.frequency=='monthly'` (lowercase)
- The comparison failed, so `selected` attribute was never set

**Solution Implemented:**  
Use case-insensitive comparison in the Jinja2 template by converting the database value to lowercase before comparing:

```jinja2
{% if mo and mo.frequency and mo.frequency.lower()=='monthly' %}selected{% endif %}
```

This ensures the comparison works regardless of how the frequency is stored in the database (capitalized, lowercase, or mixed case).

**Key Insight:**  
The issue was NOT with JavaScript interfering - it was a simple **case sensitivity bug** in the template comparison. The database stored capitalized values (`'Monthly'`) but the template compared against lowercase values (`'monthly'`). By using `.lower()` filter, we make the comparison case-insensitive and robust.

**Affected Files:**
- `src/templates/maintenance_order_detail.html` (lines 103-114 - frequency dropdown options)

**Testing Scenarios:**
✅ Edit existing PM order with frequency → frequency is pre-selected  
✅ Edit existing PM order without frequency → dropdown shows "Select Frequency"  
✅ Create new PM order → frequency starts empty  
✅ Change from PM to Reactive → frequency is cleared and disabled  
✅ Change from Reactive to PM → frequency is enabled but empty  
✅ Field disabled for non-PM order types  
✅ Works with any case variation: 'monthly', 'Monthly', 'MONTHLY', 'MoNtHlY'

---

### Bug #R3: Delete Button Placement and Duplicated Forms in Detail Pages
**Priority:** High  
**Status:** ✅ RESOLVED - December 2, 2025

**Description:**  
Multiple issues were found with delete buttons and form duplication across detail pages:
1. Delete buttons were misaligned or in wrong positions
2. Asset Detail page had Jinja2 syntax errors causing template crashes
3. Maintenance Order Detail page had duplicated form fields
4. Spare Parts Detail page had duplicated form fields
5. Delete functionality was broken due to incorrect form structure
6. Users Detail page delete had foreign key constraint errors

**Issues Found:**
1. **Delete button placement**: Buttons were moved to separate lines or misaligned
2. **Template syntax errors**: Unclosed Jinja2 blocks causing crashes
3. **Duplicated forms**: Edit forms were rendered twice in MO and Spare Parts pages
4. **Delete logic broken**: Toast messages showed "updated" instead of "deleted"
5. **Foreign key errors**: Deleting users failed due to UserSkill relationship constraints
6. **Asset delete error**: IntegrityError when deleting assets with MOs

**Solution Implemented:**
1. **Standardized delete button placement**: All detail pages now have consistent 3-button layout (Update, Cancel, Delete)
2. **Fixed template syntax**: Corrected all unclosed `{% block %}` and `{% if %}` tags
3. **Removed duplicated forms**: Cleaned up MO and Spare Parts detail templates
4. **Fixed delete routes**: Proper deletion logic with correct flash messages
5. **Fixed asset delete**: Cascade delete or set null for related MOs
6. **Fixed user delete**: Delete related UserSkill records before deleting user

**Affected Files:**
- `src/templates/asset_detail.html` (delete button, template syntax)
- `src/templates/maintenance_order_detail.html` (delete button, removed duplicate forms)
- `src/templates/spare_part_detail.html` (delete button, removed duplicate forms)
- `src/templates/user_detail.html` (delete button)
- `src/routes/main.py` (delete_asset, delete_mo, delete_spare_part, delete_user routes)
- `src/services/db_utils.py` (relationship cascades)

**Testing Scenarios:**
✅ Delete button present and correctly positioned on all detail pages  
✅ Delete functionality works for Assets  
✅ Delete functionality works for Maintenance Orders  
✅ Delete functionality works for Spare Parts  
✅ Delete functionality works for Users  
✅ No duplicated forms in any detail pages  
✅ No template syntax errors  
✅ Correct toast messages ("deleted" not "updated")  
✅ Proper redirect after deletion  

---

## 🔥 CRITICAL BUGS

### Bug #2: CSRF Token Missing - MO and Spare Parts Forms
**Priority:** Critical  
**Status:** ✅ RESOLVED - Prior to December 2, 2025

**Description:**  
When attempting to add a Maintenance Order (MO) from the Assets page or MOs page, or when adding/updating Spare Parts, the form submission fails with "Bad Request - The CSRF token is missing."

**Solution Implemented:**
CSRF tokens have been added to all forms:
- ✅ `maintenance_order_detail.html` (lines 26, 146)
- ✅ `spare_part_detail.html` (lines 19, 63)
- ✅ `asset_detail.html` (lines 19, 82, 111)
- ✅ `user_detail.html` (lines 27, 66)

All forms now include:
```html
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}" />
```

**Testing:**
✅ Add/Edit Asset forms work correctly
✅ Add/Edit MO forms work correctly
✅ Add/Edit Spare Parts forms work correctly
✅ Delete forms work correctly

---

## 🚨 HIGH PRIORITY BUGS

### Bug #1: Missing Delete Functionality for Assets
**Priority:** High  
**Status:** ✅ RESOLVED - December 2, 2025  
**Resolution:** Fixed as part of Bug #R3

**Description:**  
Assets cannot be deleted from the Asset Detail page. There is no delete button or option available.

**Solution:**
This was resolved as part of Bug #R3 (Delete Button Placement and Duplicated Forms in Detail Pages). Delete buttons have been added to all detail pages including Asset Detail, with proper styling and functionality.

**See:** Bug #R3 in RESOLVED BUGS section for full details.

---

### Bug #3: Incorrect Back Button Navigation from MO Add Page
**Priority:** High  
**Status:** ✅ RESOLVED - December 2, 2025  
**Resolution:** Fixed as part of Bug #R1

**Description:**  
When navigating to "Add Maintenance Order" from an Asset Detail page, the "Back" button incorrectly navigates to the Maintenance Orders list instead of returning to the Asset Detail page.

**Solution:**
This was resolved as part of Bug #R1 (Redirect After MO Creation/Edit/Delete from Asset Detail Page). The back button now correctly returns to the originating page based on return_to parameter.

**See:** Bug #R1 in RESOLVED BUGS section for full details.

---

### Bug #4: Table State Not Preserved on Navigation/Refresh
**Priority:** High  
**Status:** Open

**Description:**  
When applying filters, global search, column configuration, or saved views to a table, navigating to a detail page and returning (or refreshing the page) resets all table settings to default.

**Current Behavior:**
- User applies filters, search, column hiding, or loads a saved view
- User clicks on a row to view detail page
- User clicks "Back" or browser back button
- All table settings are reset (filters cleared, columns reset, search cleared)
- Same issue occurs when refreshing the page (F5)

**Expected Behavior:**
- Table settings should persist when navigating away and returning
- Settings should persist on page refresh
- Settings should be stored in browser (localStorage or sessionStorage)
- User should see the same table state they left

**Possible Solution:**
1. Store table state in `localStorage` or `sessionStorage`:
   - Active filters (column, operator, value, logic)
   - Global search term
   - Column order and visibility
   - Active saved view ID
2. On page load, check for saved state and restore it
3. Update state whenever user makes changes
4. Consider using URL query parameters for shareable state

**Affected Files:**
- `src/static/js/advanced-table/table-init.js` (add state restoration on init)
- `src/static/js/advanced-table/table-sidebar.js` (save state on filter/column changes)
- `src/static/js/advanced-table/table-data.js` (save state on search)
- `src/static/js/advanced-table/table-config.js` (integrate with saved views)

**Additional Info:**
- This used to work in older versions - check git history for previous implementation
- State should be page-specific (different state for assets vs MOs vs spare parts)
- Consider expiration time for stored state (e.g., 24 hours)

---

### Bug #5: Assignees Field Needs Dropdown for Users/Teams
**Priority:** High  
**Status:** Open

**Description:**  
In "Add New Maintenance Order" and "Edit Maintenance Order" forms, the "Assignees" field is a plain textarea expecting JSON format. It should be a dropdown allowing selection of Users (with Technician role) or Teams.

**Current Behavior:**
- Assignees field is a textarea with placeholder: "Enter user IDs or group names (JSON format)"
- Users must manually type JSON like `["user1", "user2"]` or `["maintenance_team"]`
- Error-prone and not user-friendly

**Expected Behavior:**
- Assignees field should be a multi-select dropdown or tag-based input
- Dropdown should show:
  - All Users with "Technician" role
  - All Teams
- Selecting a Team should assign all team members
- Selected assignees should be clearly visible as tags/chips

**Possible Solution:**
1. Replace textarea with multi-select dropdown using Select2 or similar library
2. Backend: Query Users with "Technician" role and all Teams
3. Pass data to template in `add_mo()` and `edit_mo()` routes
4. Frontend: Render dropdown with optgroups (Users / Teams)
5. On form submit, convert selections to appropriate format for backend

**Affected Files:**
- `src/templates/maintenance_order_detail.html` (lines 111-116 - replace textarea)
- `src/routes/main.py` (lines 108-146, 154-178 - pass users/teams to template)
- `src/services/db_utils.py` (verify User and Team models)
- `src/static/css/` (add Select2 or custom dropdown styles)
- `src/static/js/` (add Select2 or custom dropdown logic)

**Additional Info:**
- Consider using Select2 library for better UX: https://select2.org/
- Team selection should expand to individual user IDs on backend
- Store assignees as JSON array of user IDs in database

---

### Bug #6: Missing Delete Functionality for Maintenance Orders
**Priority:** High  
**Status:** ✅ RESOLVED - December 2, 2025  
**Resolution:** Fixed as part of Bug #R3

**Description:**  
In "Edit Maintenance Order" page, there is no delete button to remove the MO. Similar to Bug #1 for Assets.

**Solution:**
This was resolved as part of Bug #R3 (Delete Button Placement and Duplicated Forms in Detail Pages). Delete buttons have been added to all detail pages including Maintenance Order Detail, with proper styling and functionality.

**See:** Bug #R3 in RESOLVED BUGS section for full details.

---

### Bug #9: Table Sidebar - Save View Not Working
**Priority:** High  
**Status:** Open

**Description:**  
The "Save View" button in the table sidebar does not work. Users cannot save their current table configuration (filters, columns, sorting) as a named view.

**Current Behavior:**
- User configures table (filters, column order, hidden columns)
- User clicks "Save View" button in sidebar
- Nothing happens or error occurs
- View is not saved to database

**Expected Behavior:**
- User clicks "Save View" button
- Modal/prompt appears asking for view name
- User enters name and confirms
- View is saved to database with current configuration
- View appears in "Saved Views" list
- Success message is shown

**Possible Solution:**
1. Check `saveView()` function in `table-sidebar.js` (line 846)
2. Verify API endpoint `/table-config/<page_name>` is working (api.py lines 324-353)
3. Ensure CSRF token is included in AJAX request
4. Add proper error handling and user feedback
5. Test save/load functionality end-to-end

**Affected Files:**
- `src/static/js/advanced-table/table-sidebar.js` (lines 846-900 - saveView function)
- `src/routes/api.py` (lines 324-353 - save_table_config endpoint)
- `src/static/js/advanced-table/table-config.js` (verify integration)

**Additional Info:**
- Related to Bug #13 (Table Views - Save/Load functionality)
- May need to add CSRF token to AJAX requests
- Check browser console for JavaScript errors

---

### Bug #11: Spare Parts Update Not Working - CSRF Token Missing
**Priority:** High  
**Status:** ✅ RESOLVED - Prior to December 2, 2025  
**Resolution:** Fixed together with Bug #2

**Description:**  
Updating spare parts fails with "Bad Request - The CSRF token is missing." Same root cause as Bug #2.

**Solution:**
CSRF tokens have been added to spare_part_detail.html (lines 19, 63). All spare parts add/edit operations now work correctly.

**See:** Bug #2 in CRITICAL BUGS section for full details.

---

## 📊 MEDIUM PRIORITY BUGS

### Bug #7: Missing Required Field Indicators
**Priority:** Medium  
**Status:** ✅ RESOLVED - Prior to December 2, 2025

**Description:**  
Forms do not clearly indicate which fields are required. There are no red asterisks (*) next to required field labels, and no explanatory note at the bottom of forms.

**Solution Implemented:**
1. ✅ CSS rule added to `base.html` (line 96):
   ```css
   .required-field::after {
       content: " *";
       color: red;
   }
   ```
2. ✅ `required-field` class added to all required field labels in:
   - `maintenance_order_detail.html` (6 required fields)
   - `asset_detail.html`
   - `spare_part_detail.html`
   - `user_detail.html`
3. ✅ Required fields note added to all forms:
   ```html
   <p class="text-muted"><small>* Required fields</small></p>
   ```

**Testing:**
✅ All required fields show red asterisk
✅ Note appears at bottom of all forms
✅ Improves UX and accessibility

---

### Bug #8: Table Columns Too Narrow on Default Load
**Priority:** Medium  
**Status:** Open

**Description:**  
When tables load for the first time (or sometimes on refresh), columns are too narrow, causing text to wrap or be cut off. Minimum column width should be increased.

**Current Behavior:**
- Table loads with narrow columns
- Text is truncated or wrapped
- User must manually resize columns
- Inconsistent behavior (sometimes loads correctly)

**Expected Behavior:**
- Table should load with reasonable default column widths
- Text should be visible without wrapping (for most common data)
- Minimum column width should be enforced

**Possible Solution:**
1. Increase minimum column width in CSS or JavaScript
2. Set default column widths based on content type:
   - ID columns: 80px
   - Name/Description: 200px
   - Status/Type: 120px
   - Date: 120px
3. Implement auto-fit on initial load (measure content width)
4. Store column widths in saved views

**Affected Files:**
- `src/static/css/advanced-table.css` (set min-width for columns)
- `src/static/js/advanced-table/table-render.js` (set default widths on render)
- `src/static/js/advanced-table/table-resize.js` (enforce minimum width)

**Additional Info:**
- May be related to table width calculation
- Check if issue occurs on specific screen sizes
- Consider responsive breakpoints

---

### Bug #10: Table Width Not Responsive to Window Resize
**Priority:** Medium  
**Status:** Open

**Description:**  
When resizing the browser window or toggling the sidebar, the table does not adjust its width to fill the available space. This is especially noticeable when loading the page with a smaller window and then maximizing it.

**Current Behavior:**
- Load page with small window size
- Table fits small window
- Maximize window or resize to larger size
- Table remains narrow, not filling available width
- Same issue when toggling sidebar

**Expected Behavior:**
- Table should dynamically adjust width to fill container
- When window is resized, table should resize accordingly
- When sidebar is toggled, table should expand/contract
- All table features should continue working (column resizing, sorting, etc.)

**Possible Solution:**
1. Add window resize event listener
2. Recalculate table width on resize
3. Ensure table uses `width: 100%` or similar responsive CSS
4. Test that column resizing, sorting, highlighting still work after resize
5. Use `ResizeObserver` API for more efficient resize detection

**Affected Files:**
- `src/static/css/advanced-table.css` (ensure responsive width)
- `src/static/js/advanced-table/table-resize.js` (add resize listener)
- `src/static/js/advanced-table/table-sidebar.js` (trigger resize on sidebar toggle)

**Additional Info:**
- CRITICAL: Must not break existing features (column resize, sort, highlight)
- Test thoroughly before deploying
- Consider using CSS flexbox or grid for layout

---

### Bug #13: Table Views - Save/Load Functionality Not Working
**Priority:** Medium  
**Status:** Open

**Description:**  
The complete table views save/load functionality is not working properly. This is a broader issue than Bug #9, encompassing both saving and loading of views.

**Current Behavior:**
- Saving views fails (Bug #9)
- Loading saved views may not restore correct state
- Deleting views may not work
- Setting default view may not persist

**Expected Behavior:**
- Users can save current table configuration as named view
- Users can load saved views and see exact same table state
- Users can delete saved views
- Users can set a view as default (loads automatically on page load)
- All view operations should provide clear feedback

**Possible Solution:**
1. Create comprehensive test plan for all table features (separate document)
2. Test each feature systematically:
   - Save view
   - Load view
   - Delete view
   - Set default view
   - View persistence across sessions
3. Fix issues found during testing
4. Document test results with screenshots/videos

**Affected Files:**
- `src/static/js/advanced-table/table-sidebar.js` (view management UI)
- `src/static/js/advanced-table/table-config.js` (view save/load logic)
- `src/routes/api.py` (table-config endpoints, lines 312-429)
- `src/services/db_utils.py` (TableConfiguration model)

**Additional Info:**
- Need to create comprehensive testing plan (see Bug #13 additional requirement)
- Test plan should be reusable for future testing
- AI should be able to follow plan and execute tests automatically

---

### Bug #14: Cannot Click Table Elements After Column Changes or Sorting
**Priority:** High  
**Status:** Open

**Description:**  
After changing columns (hiding/showing or drag-and-drop reordering), applying changes, **or sorting the table**, clicking on table rows to navigate to detail pages stops working.

**Current Behavior:**
- User hides/shows columns or reorders columns via drag-and-drop
- **OR** user clicks on a column header to sort
- User clicks "Apply" button (for column changes) or table re-renders (for sorting)
- Table updates with new configuration
- Clicking on table rows no longer navigates to detail page
- Row click event is not firing

**Expected Behavior:**
- After applying column changes **or sorting**, row click should still work
- Clicking on a row should navigate to detail page
- All table interactions should remain functional
- Sorting should not break row click handlers

**Possible Solution:**
1. Check if event listeners are being removed during column update **or sort**
2. Re-attach row click event listeners after column changes **and after sorting**
3. **Use event delegation** (attach listener to table, not individual rows) - this is the most robust solution
4. Verify that column reordering and sorting don't break DOM structure
5. Consider using MutationObserver to detect table changes and re-attach listeners if needed

**Affected Files:**
- `src/static/js/advanced-table/table-sidebar.js` (column apply logic)
- `src/static/js/advanced-table/table-render.js` (re-render after column changes **and sorting**)
- `src/static/js/advanced-table/table-events.js` (row click event listeners)
- `src/static/js/advanced-table/table-sort.js` (if exists - sorting logic)

**Additional Info:**
- Event delegation pattern recommended: `table.addEventListener('click', (e) => { if (e.target.closest('tr')) { ... } })`
- Ensure event listeners are not duplicated
- **Sorting is a common table operation** - this is a critical bug affecting usability
- **Priority upgraded from Medium to High** due to impact on core navigation functionality

---

### Bug #16: Frequency Field Should Only Be Enabled for PM Orders
**Priority:** Medium  
**Status:** Fixed  
**Fixed Date:** December 1, 2025  
**Fixed By:** AI Assistant

**Description:**  
In MO creation/edit forms, the "Frequency" field should only be enabled when "Order Type" is set to "PM" (Preventive Maintenance). For other order types (reactive, corrective), frequency is not applicable.

**Current Behavior:**
- Frequency field is always enabled
- Users can set frequency for reactive/corrective orders (doesn't make sense)
- No validation prevents this

**Expected Behavior:**
- When Order Type is "PM", Frequency field is enabled
- When Order Type is "reactive" or "corrective", Frequency field is disabled and cleared
- Dynamic enabling/disabling based on Order Type selection

**Possible Solution:**
1. Add JavaScript event listener to Order Type dropdown
2. When Order Type changes:
   - If "PM": enable Frequency field
   - If not "PM": disable Frequency field and clear value
3. On page load, check Order Type and set Frequency field state accordingly

**Affected Files:**
- `src/templates/maintenance_order_detail.html` (add JavaScript for dynamic enabling)
- `src/static/js/` (or inline script in template)

**Additional Info:**
- Improves data quality and UX
- Prevents invalid data entry

---

### Bug #23: Frequency Field Not Showing Saved Value on Edit
**Priority:** Medium  
**Status:** Fixed  
**Fixed Date:** December 1, 2025  
**Fixed By:** AI Assistant

**Description:**  
When editing a PM Maintenance Order, the frequency dropdown does not show the currently saved frequency value, even though the field is enabled.

**Current Behavior:**
- User edits a PM order with frequency set to "weekly"
- Frequency dropdown is enabled (correct)
- Dropdown shows empty/placeholder value instead of "weekly"

**Expected Behavior:**
- When editing a PM order, the frequency dropdown should show the saved frequency value
- The correct option should be pre-selected

**Possible Solution:**
1. The JavaScript logic was overriding the HTML pre-selection
2. Remove the JavaScript code that sets the value
3. Let Jinja2's `selected` attribute handle the pre-selection
4. JavaScript should only handle enabling/disabling based on order type

**Affected Files:**
- `src/templates/maintenance_order_detail.html`

**Additional Info:**
- The HTML template already has the correct `selected` logic in place
- JavaScript was interfering with the native HTML behavior

---

### Bug #22: CSRF Token Missing in MO Delete from Asset Details
**Priority:** High  
**Status:** Fixed  
**Fixed Date:** December 1, 2025  
**Fixed By:** AI Assistant

**Description:**  
When deleting a Maintenance Order from the Asset Details page MO table, the delete form is missing the CSRF token, causing a "Bad Request - The CSRF token is missing" error.

**Current Behavior:**
- User is on Asset Details page
- User clicks "Delete" button in the MO table
- Form submission fails with CSRF error

**Expected Behavior:**
- Delete button should work correctly with CSRF protection
- MO should be deleted and success message shown

**Possible Solution:**
Add CSRF token to the delete form in asset_detail.html:
```html
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}" />
```

**Affected Files:**
- `src/templates/asset_detail.html`

---

### Bug #21: Asset Field Not Pre-filled/Disabled on MO Creation
**Priority:** Medium  
**Status:** Fixed  
**Fixed Date:** December 1, 2025  
**Fixed By:** AI Assistant

**Description:**  
When creating a Maintenance Order from an Asset's detail page, the "Asset" field in the new MO form is not pre-filled with the asset being viewed, nor is it disabled.

**Current Behavior:**
- User navigates from "Asset X" detail page to "Add Maintenance Order".
- The "Asset" dropdown on the MO form is not pre-selected with "Asset X".
- The user can select any asset from the dropdown.

**Expected Behavior:**
- When coming from an asset's detail page, the "Asset" dropdown should be pre-selected with that specific asset.
- The "Asset" dropdown should be disabled to prevent the user from changing it.

**Possible Solution:**
1. In the `add_mo` route, when an `asset_id` is passed, fetch the specific `Asset` object.
2. Pass this `asset` object to the `maintenance_order_detail.html` template.
3. In the template, modify the "Asset" select field to be `disabled` if a specific asset object is passed.
4. Ensure the correct asset is selected.
5. Add a hidden input field with the asset_id so it still gets submitted when the dropdown is disabled.

**Affected Files:**
- `src/routes/main.py`
- `src/templates/maintenance_order_detail.html`

**Additional Info:**
- Disabled form fields are not submitted by browsers
- Solution: Use a hidden input field alongside the disabled dropdown
- The form submission logic must check for the hidden field value

---

### Bug #20: Missing Delete Functionality for Users
**Priority:** Medium  
**Status:** Open

**Description:**  
The User Detail page does not have a "Delete" button. While asset and MO deletion has been added, user deletion is missing.

**Current Behavior:**
- User Detail page only allows for updating user information.
- No way to delete a user from the UI.

**Expected Behavior:**
- User Detail page should have a "Delete" button.
- Deletion should have a confirmation dialog.
- The backend must handle foreign key constraints gracefully (e.g., re-assigning created MOs/assets to an admin or preventing deletion if the user has associated records).

**Possible Solution:**
1. Add a delete button to `user_detail.html`.
2. Create a `delete_user` route in `src/routes/main.py`.
3. Implement logic to handle or re-assign user's associated records before deletion. A soft-delete (marking as inactive) might be a safer alternative.

**Affected Files:**
- `src/templates/user_detail.html`
- `src/routes/main.py`

**Additional Info:**
- This requires careful implementation to avoid database integrity errors. Deleting a user could violate foreign key constraints on the `maintenance_order` or `asset` tables (`created_by`, `modified_by`, etc.).

---

### Bug #17: OR Filter Operator Clears Previous Filter Row
**Priority:** Medium  
**Status:** Open

**Description:**  
In the table sidebar, when adding a second filter, it automatically applies filters (good for AND operator). However, when user clicks OR operator, the previous filter row should be cleared (not removed) to allow user to see what OR options they can add.

**Current Behavior:**
- User adds first filter (e.g., Status = "Open")
- User adds second filter
- Filters are automatically applied with AND logic (correct)
- If user clicks OR operator, previous filter row remains filled
- User cannot easily see what OR options to add

**Expected Behavior:**
- When user clicks OR operator for a filter row:
  - Previous filter row values are cleared (column, operator, value)
  - Filter row remains visible (not removed)
  - User can now see available columns to add OR filter
- When user clicks AND operator, behavior remains as is

**Possible Solution:**
1. Add event listener to AND/OR operator toggle
2. When OR is selected:
   - Clear previous filter row's column, operator, and value
   - Keep the row visible
   - Do not apply filters yet (wait for user to fill in OR condition)
3. When AND is selected, keep current behavior

**Affected Files:**
- `src/static/js/advanced-table/table-sidebar.js` (filter logic operator handling)

**Additional Info:**
- This is a UX improvement for OR filter workflow
- Helps users understand what they're filtering

---

### Bug #24: Autofill Background Color Not Consistent Across All Input Types
**Priority:** Medium  
**Status:** Open

**Description:**  
When browser autofill populates text input fields, they get a blue background color to indicate they were autofilled. However, this visual indicator is not applied consistently to all form field types (dropdowns, select elements, textareas, etc.).

**Current Behavior:**
- Text `<input>` fields show blue background when autofilled
- Dropdown `<select>` elements don't show autofill indicator
- Textareas don't show autofill indicator
- Inconsistent visual feedback across different field types

**Expected Behavior:**
- All form field types should have consistent autofill styling
- Dropdowns, selects, and textareas should show the same blue background when autofilled
- Provides clear visual feedback to users about which fields were auto-populated

**Possible Solution:**
1. Add CSS rules to style autofilled elements consistently:
   ```css
   /* Text inputs - already working */
   input:-webkit-autofill {
       -webkit-box-shadow: 0 0 0 1000px #e8f0fe inset !important;
   }
   
   /* Apply same style to select/dropdown */
   select:-webkit-autofill,
   select:-webkit-autofill:hover,
   select:-webkit-autofill:focus {
       -webkit-box-shadow: 0 0 0 1000px #e8f0fe inset !important;
   }
   
   /* Apply to textareas */
   textarea:-webkit-autofill,
   textarea:-webkit-autofill:hover,
   textarea:-webkit-autofill:focus {
       -webkit-box-shadow: 0 0 0 1000px #e8f0fe inset !important;
   }
   ```
2. Test across different browsers (Chrome, Firefox, Safari, Edge)
3. Ensure color matches existing autofill blue (#e8f0fe)

**Affected Files:**
- `src/static/css/main.css` or `src/templates/base.html` (add CSS rules)

**Additional Info:**
- Improves UX consistency
- Helps users identify which fields were auto-populated
- Browser autofill styling varies across browsers, may need vendor prefixes

---

### Bug #25: Maintenance Orders Section Displayed on Add New Asset Page
**Priority:** Medium  
**Status:** Open

**Description:**  
When creating a new asset on the "Add New Asset" page, the "Maintenance Orders for [Asset Name]" section is displayed, even though the asset doesn't exist yet. This is confusing and the "Add Maintenance Order" button cannot function properly since there's no asset ID.

**Current Behavior:**
- Navigate to "Add New Asset" page
- "Maintenance Orders for" section is visible at the bottom
- "Add Maintenance Order" button is enabled
- Clicking the button would fail or create an MO without an associated asset
- Confusing UX - can't add MOs to an asset that doesn't exist yet

**Expected Behavior:**
- "Maintenance Orders for" section should be hidden on Add New Asset page
- Section should only appear when editing an existing asset
- After creating the asset, user can navigate to Asset Detail page to add MOs

**Possible Solution:**
In `asset_detail.html`, conditionally show the MO section only when editing:
```html
{% if asset %}
<!-- Only show when editing existing asset, not when creating new -->
<div class="mt-4">
    <h3>Maintenance Orders for {{ asset.name }}</h3>
    <!-- MO table and Add button -->
</div>
{% endif %}
```

**Affected Files:**
- `src/templates/asset_detail.html` (add conditional wrapper around MO section)

**Additional Info:**
- Prevents user confusion
- Follows logical workflow: create asset first, then add MOs
- Similar pattern should be checked in other detail pages (User, Spare Parts)

---

### Bug #26: Frequency Field Not Required for PM Orders
**Priority:** Medium  
**Status:** Open

**Description:**  
When creating or editing a Maintenance Order with Order Type set to "PM" (Preventive Maintenance), the Frequency field is enabled but not marked as required. PM orders should always have a frequency specified to define the maintenance schedule.

**Current Behavior:**
- User selects Order Type: "PM"
- Frequency field becomes enabled (correct)
- Frequency field has no red asterisk (*)
- Frequency field is not marked as `required` in HTML
- User can submit PM order without selecting a frequency
- Creates incomplete PM orders without maintenance schedule

**Expected Behavior:**
- When Order Type is "PM", Frequency field should be marked as required
- Red asterisk (*) should appear next to "Frequency" label
- HTML `required` attribute should be added dynamically
- Form validation should prevent submission if frequency is empty for PM orders
- When Order Type is not "PM", frequency should remain optional (disabled)

**Possible Solution:**
1. Add JavaScript to dynamically toggle `required` attribute:
   ```javascript
   function updateFrequencyField() {
       const isPM = orderTypeField.value === 'PM';
       frequencyField.disabled = !isPM;
       frequencyField.required = isPM; // Add this line
       
       // Update label styling
       const label = document.querySelector('label[for="frequency"]');
       if (isPM) {
           label.classList.add('required-field');
       } else {
           label.classList.remove('required-field');
           frequencyField.value = '';
       }
   }
   ```
2. Update on page load and when order type changes
3. Backend validation: verify frequency is present for PM orders before saving

**Affected Files:**
- `src/templates/maintenance_order_detail.html` (lines ~151-183 - update JavaScript)
- `src/routes/main.py` (add backend validation in add_mo and edit_mo routes)

**Additional Info:**
- Data quality improvement
- Prevents incomplete PM orders
- Frequency is essential for scheduling preventive maintenance
- Should work in conjunction with Bug #16 (frequency enable/disable logic)

---

## 🔵 LOW PRIORITY BUGS

### Bug #19: KeyError - 'frequency' Field Not Submitted When Disabled
**Priority:** Low (but breaking)  
**Status:** Fixed  
**Fixed Date:** December 1, 2025  
**Fixed By:** AI Assistant

**Description:**  
When adding a Maintenance Order with a non-PM order type (reactive/corrective), the frequency field is disabled by JavaScript (Bug #16 fix). However, disabled form fields don't get submitted with the form, causing a KeyError when the backend tries to access `request.form['frequency']`.

**Current Behavior:**
- Select Order Type: "reactive" or "corrective"
- Frequency field is disabled (correct)
- Submit form
- Server crashes with KeyError: 'frequency'

**Expected Behavior:**
- Disabled fields should be handled gracefully
- Form should submit successfully regardless of which fields are disabled
- Optional fields should use `.get()` method instead of direct dictionary access

**Possible Solution:**
1. Replace `request.form['field']` with `request.form.get('field', '')` for all optional fields
2. Apply to both `add_mo()` and `edit_mo()` routes
3. Fields to fix: schedule_name, frequency, estimated_completion_time, assignees, justification, due_date

**Affected Files:**
- `src/routes/main.py` (lines 121-127 in add_mo, lines 168-174 in edit_mo)

**Additional Info:**
- This bug was introduced by Bug #16 fix (frequency conditional enable)
- Disabled form fields are not submitted by browsers (HTML standard behavior)
- Root cause: using direct dictionary access instead of `.get()` for optional fields
- Fixed immediately upon discovery during Test 2.1

---

### Bug #15: Status Field Should Be Hidden in MO Creation
**Priority:** Low  
**Status:** Open

**Description:**  
When creating a new Maintenance Order, the status should always be "Open". The status field should be hidden from the creation form, as status changes should only happen through other pages or future apps.

**Current Behavior:**
- MO creation form shows "Status" dropdown
- User can select any status (Open, In Progress, Scheduled, Completed, Cancelled)
- New MOs can be created with any status (not ideal)

**Expected Behavior:**
- MO creation form should NOT show Status field
- Status should be automatically set to "Open" on creation
- Status can only be changed in Edit MO form or through workflow apps
- Edit MO form should still show Status field

**Possible Solution:**
1. In `maintenance_order_detail.html`, conditionally hide Status field:
   ```html
   {% if mo %}
   <!-- Show status field only when editing -->
   <div class="form-group">...</div>
   {% endif %}
   ```
2. In `add_mo()` route, hardcode status to "Open":
   ```python
   status = "Open"  # Always Open for new MOs
   ```

**Affected Files:**
- `src/templates/maintenance_order_detail.html` (lines 49-62 - conditionally hide)
- `src/routes/main.py` (line 116 - hardcode status for new MOs)

**Additional Info:**
- Simplifies MO creation workflow
- Enforces business logic (new MOs are always Open)
- Status transitions should be managed by workflow

---

## 📝 TESTING PLAN REQUIREMENT

### Bug #13 Additional Requirement: Comprehensive Table Testing Plan

**Requirement:**  
Create a comprehensive testing plan for all Advanced Table features. This plan should:

1. **Be Saved as Markdown File**: Store in `docs/` directory
2. **Be Reusable**: Can be used for future testing cycles
3. **Be AI-Executable**: AI assistant should be able to follow the plan and execute tests automatically
4. **Include All Features**: Cover every table feature:
   - Global search
   - Column filtering (AND/OR logic)
   - Column show/hide
   - Column reordering (drag-and-drop)
   - Column resizing
   - Column sorting
   - Saved views (save, load, delete, set default)
   - Row click navigation
   - Export functionality
   - Sidebar toggle
   - State persistence
5. **Provide Evidence**: Each test should produce:
   - Screenshots of UI state
   - Video recordings of interactions
   - Console logs (if applicable)
   - Pass/Fail status

**Deliverable:**  
Create `docs/table_features_test_plan.md` with detailed test cases and execution instructions.

**Note:**  
This testing plan already exists at `docs/table_features_test_plan.md` (20,689 bytes). Review and update if necessary.

---

## 📊 BUG SUMMARY BY PRIORITY

**Critical (0 open - 1 fixed):**
- ~~Bug #2: CSRF Token Missing - MO and Spare Parts Forms~~ ✅ FIXED (Prior to Dec 2, 2025)

**High (4 open - 7 fixed):**
**Open:**
- Bug #4: Table State Not Preserved on Navigation/Refresh
- Bug #5: Assignees Field Needs Dropdown for Users/Teams
- Bug #9: Table Sidebar - Save View Not Working
- Bug #14: Cannot Click Table Elements After Column Changes or Sorting **(upgraded from Medium)**

**Fixed:**
- ~~Bug #1: Missing Delete Functionality for Assets~~ ✅ FIXED (Dec 2, 2025 - Bug #R3)
- ~~Bug #3: Incorrect Back Button Navigation from MO Add Page~~ ✅ FIXED (Dec 2, 2025 - Bug #R1)
- ~~Bug #6: Missing Delete Functionality for Maintenance Orders~~ ✅ FIXED (Dec 2, 2025 - Bug #R3)
- ~~Bug #11: Spare Parts Update Not Working - CSRF Token Missing~~ ✅ FIXED (Prior to Dec 2, 2025)

**Medium (8 open - 4 fixed):**
**Open:**
- Bug #8: Table Columns Too Narrow on Default Load
- Bug #10: Table Width Not Responsive to Window Resize
- Bug #13: Table Views - Save/Load Functionality Not Working
- Bug #17: OR Filter Operator Clears Previous Filter Row
- Bug #24: Autofill Background Color Not Consistent Across All Input Types **(NEW - Dec 2, 2025)**
- Bug #25: Maintenance Orders Section Displayed on Add New Asset Page **(NEW - Dec 2, 2025)**
- Bug #26: Frequency Field Not Required for PM Orders **(NEW - Dec 2, 2025)**

**Fixed:**
- ~~Bug #7: Missing Required Field Indicators~~ ✅ FIXED (Prior to Dec 2, 2025)
- ~~Bug #16: Frequency Field Should Only Be Enabled for PM Orders~~ ✅ FIXED (Dec 1, 2025)
- ~~Bug #23: Frequency Field Not Showing Saved Value on Edit~~ ✅ FIXED (Dec 2, 2025 - Bug #R2)

**Low (0 open - 1 fixed):**
- ~~Bug #15: Status Field Should Be Hidden in MO Creation~~ ✅ FIXED (Dec 1, 2025)

**Total Bugs: 20**  
**Open: 11 bugs** (4 High, 7 Medium)  
**Fixed: 9 bugs** (1 Critical, 4 High, 3 Medium, 1 Low)  
**Added Today (Dec 2, 2025):** 3 new bugs (Bug #24, #25, #26)  
**Updated Today (Dec 2, 2025):** Bug #14 priority upgraded High (sorting issue added)  
**Fixed Today (Dec 2, 2025):** 3 bugs (Bug #R1, #R2, #R3) + verified 2 previous fixes (Bug #2, #7)  
**Previously Fixed (Dec 1, 2025):** 4 bugs (Bug #15, #16, #19, #21, #22, #23)

---

## 🔄 BUG DEPENDENCIES

- **Bug #2 and Bug #11** are the same root cause (CSRF token missing)
- **Bug #9** is a subset of **Bug #13** (save view is part of save/load functionality)
- **Bug #1** and **Bug #6** follow the same pattern (missing delete buttons)

**Recommended Fix Order:**
1. Fix Bug #2 (Critical - CSRF tokens) - fixes Bug #11 as well
2. Fix Bug #1 and Bug #6 together (missing delete buttons)
3. Fix Bug #3 (back button navigation)
4. Fix Bug #4 (table state persistence) - may help with Bug #13
5. Fix Bug #13 (table views) - includes Bug #9
6. Fix Bug #5 (assignees dropdown)
7. Fix remaining medium/low priority bugs

---

## 📅 MAINTENANCE GUIDELINES

**When a bug is fixed:**
1. Change status from "Open" to "Fixed"
2. Add "Fixed Date" and "Fixed By" information
3. Add reference to commit/PR that fixed the bug
4. Move to "Recently Fixed" section after 7 days
5. Archive to bottom after 30 days

**When adding new bugs:**
1. Assign next available bug number
2. Set priority (Critical, High, Medium, Low)
3. Fill in all sections (Description, Current/Expected Behavior, Solution, Files)
4. Add to appropriate priority section
5. Update bug summary counts

---

## 🎯 NEXT STEPS

1. Review this bug tracking document
2. Prioritize bugs based on business impact
3. Create implementation plan for Critical and High priority bugs
4. Begin fixing bugs in recommended order
5. Update this document as bugs are fixed
6. Create automated tests to prevent regression

---

_This document follows the structure and philosophy of `mockCMMS_roadmap.md` and serves as a living document for bug tracking and resolution._
