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

## 🔥 CRITICAL BUGS

### Bug #2: CSRF Token Missing - MO and Spare Parts Forms
**Priority:** Critical  
**Status:** Open

**Description:**  
When attempting to add a Maintenance Order (MO) from the Assets page or MOs page, or when adding/updating Spare Parts, the form submission fails with "Bad Request - The CSRF token is missing."

**Current Behavior:**
- Clicking "Add Maintenance Order" from Asset Details or MO page shows form
- Submitting the form returns: `400 Bad Request - The CSRF token is missing`
- Same issue occurs for Spare Parts add/update forms

**Expected Behavior:**
- Forms should include CSRF token and submit successfully
- User should be redirected to the appropriate page with success message

**Possible Solution:**
1. Add CSRF token hidden input field to all forms:
   ```html
   <input type="hidden" name="csrf_token" value="{{ csrf_token() }}" />
   ```
2. Ensure Flask-WTF CSRF protection is properly configured in `app.py`
3. Add CSRF token to all POST forms in templates

**Affected Files:**
- `src/templates/maintenance_order_detail.html` (lines 18-126)
- `src/templates/spare_part_detail.html` (entire form)
- `src/templates/asset_detail.html` (lines 17-81)
- `src/app.py` (verify CSRF configuration)

**Additional Info:**
- CSRF token is already present in `base.html` (line 14) as meta tag
- CSRF token is present in `user_detail.html` (line 27) and `login.html` (line 8)
- Need to follow the same pattern for all other forms

---

## 🚨 HIGH PRIORITY BUGS

### Bug #1: Missing Delete Functionality for Assets
**Priority:** High  
**Status:** Open

**Description:**  
Assets cannot be deleted from the Asset Detail page. There is no delete button or option available.

**Current Behavior:**
- Asset Detail page only shows "Update Asset" and "Cancel" buttons
- No way to delete an asset from the UI
- Delete route exists in backend (`/assets/<id>/delete`) but no UI trigger

**Expected Behavior:**
- Asset Detail page should have a "Delete" button
- Clicking delete should show confirmation dialog
- After confirmation, asset should be deleted and user redirected to Assets list

**Possible Solution:**
1. Add delete button to `asset_detail.html` after the Cancel button
2. Use POST form with confirmation dialog (similar to MO delete in lines 107-110)
3. Add red asterisk to required fields
4. Add note about required fields at bottom

**Affected Files:**
- `src/templates/asset_detail.html` (add delete button around line 80)

**Additional Info:**
- Backend route already exists: `@main_bp.route('/assets/<int:asset_id>/delete', methods=['POST'])` in `src/routes/main.py` (lines 87-94)
- Follow same pattern as MO delete in `asset_detail.html` lines 107-110

---

### Bug #3: Incorrect Back Button Navigation from MO Add Page
**Priority:** High  
**Status:** Open

**Description:**  
When navigating to "Add Maintenance Order" from an Asset Detail page, the "Back" button incorrectly navigates to the Maintenance Orders list instead of returning to the Asset Detail page.

**Current Behavior:**
- User is on Asset Detail page (e.g., `/assets/5`)
- User clicks "Add Maintenance Order" button
- User is taken to `/maintenance_orders/add`
- "Back to Maintenance Orders" button goes to `/maintenance_orders` (incorrect)

**Expected Behavior:**
- "Back" button should return to the originating page (Asset Detail)
- If coming from Asset Detail, back button should say "Back to Asset Details"
- If coming from MO list, back button should say "Back to Maintenance Orders"

**Possible Solution:**
1. Add `referrer` or `return_to` query parameter when navigating to add MO page
2. Modify "Add Maintenance Order" link in `asset_detail.html` (line 119):
   ```html
   <a href="{{ url_for('main.add_mo', return_to='asset', asset_id=asset.id) }}" class="btn btn-success mt-3">Add Maintenance Order</a>
   ```
3. Update `maintenance_order_detail.html` to check for `return_to` parameter
4. Dynamically set back button URL and text based on referrer

**Affected Files:**
- `src/templates/asset_detail.html` (line 119 - modify link)
- `src/templates/maintenance_order_detail.html` (lines 11-14 - dynamic back button)
- `src/routes/main.py` (lines 108-146 - handle return_to parameter)

**Additional Info:**
- Consider using `request.referrer` or explicit query parameters
- Same pattern may apply to other "Add" pages accessed from detail views

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
**Status:** Open

**Description:**  
In "Edit Maintenance Order" page, there is no delete button to remove the MO. Similar to Bug #1 for Assets.

**Current Behavior:**
- Edit MO page only shows "Update MO" and "Cancel" buttons
- No way to delete an MO from the edit page
- Delete route exists in backend but no UI trigger on edit page

**Expected Behavior:**
- Edit MO page should have a "Delete" button
- Clicking delete should show confirmation dialog
- After confirmation, MO should be deleted and user redirected to MO list

**Possible Solution:**
1. Add delete button to `maintenance_order_detail.html` after Cancel button
2. Use POST form with confirmation dialog
3. Only show delete button when editing (not when adding new MO)

**Affected Files:**
- `src/templates/maintenance_order_detail.html` (add delete button around line 125)

**Additional Info:**
- Backend route already exists: `@main_bp.route('/maintenance_orders/<int:mo_id>/delete', methods=['POST'])` in `src/routes/main.py` (lines 180-187)
- Delete functionality already exists in MO list table (asset_detail.html lines 107-110)
- Follow same pattern

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
**Status:** Open

**Description:**  
Updating spare parts fails with "Bad Request - The CSRF token is missing." Same root cause as Bug #2.

**Current Behavior:**
- Navigating to `/spare_parts/add` or editing a spare part
- Submitting form returns: `400 Bad Request - The CSRF token is missing`

**Expected Behavior:**
- Form should include CSRF token and submit successfully
- User should be redirected to spare parts list with success message

**Possible Solution:**
Same as Bug #2 - add CSRF token to form:
```html
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}" />
```

**Affected Files:**
- `src/templates/spare_part_detail.html` (add CSRF token to form)

**Additional Info:**
- This is the same issue as Bug #2
- Can be fixed together with Bug #2 in a single commit

---

## 📊 MEDIUM PRIORITY BUGS

### Bug #7: Missing Required Field Indicators
**Priority:** Medium  
**Status:** Open

**Description:**  
Forms do not clearly indicate which fields are required. There are no red asterisks (*) next to required field labels, and no explanatory note at the bottom of forms.

**Current Behavior:**
- Required fields have `required` HTML attribute
- No visual indicator (red asterisk) next to labels
- No note at bottom explaining required fields
- Users only discover required fields when trying to submit

**Expected Behavior:**
- Required field labels should have red asterisk: `Field Name *`
- Bottom of form should have note: "* Required fields"
- Note should be next to "Add", "Cancel", and "Delete" buttons

**Possible Solution:**
1. Add CSS class for required field labels:
   ```css
   .required-field::after {
       content: " *";
       color: red;
   }
   ```
2. Add class to all required field labels
3. Add note at bottom of all forms:
   ```html
   <p class="text-muted"><small>* Required fields</small></p>
   ```

**Affected Files:**
- `src/static/css/style.css` or `src/static/css/advanced-table.css` (add CSS rule)
- `src/templates/asset_detail.html` (add class to labels, add note)
- `src/templates/maintenance_order_detail.html` (add class to labels, add note)
- `src/templates/spare_part_detail.html` (add class to labels, add note)
- `src/templates/user_detail.html` (add class to labels, add note)

**Additional Info:**
- Improves UX and accessibility
- Standard web form best practice

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

### Bug #14: Cannot Click Table Elements After Column Changes
**Priority:** Medium  
**Status:** Open

**Description:**  
After changing columns (hiding/showing or drag-and-drop reordering) and applying changes, clicking on table rows to navigate to detail pages stops working.

**Current Behavior:**
- User hides/shows columns or reorders columns via drag-and-drop
- User clicks "Apply" button
- Table updates with new column configuration
- Clicking on table rows no longer navigates to detail page
- Row click event is not firing

**Expected Behavior:**
- After applying column changes, row click should still work
- Clicking on a row should navigate to detail page
- All table interactions should remain functional

**Possible Solution:**
1. Check if event listeners are being removed during column update
2. Re-attach row click event listeners after column changes
3. Use event delegation (attach listener to table, not individual rows)
4. Verify that column reordering doesn't break DOM structure

**Affected Files:**
- `src/static/js/advanced-table/table-sidebar.js` (column apply logic)
- `src/static/js/advanced-table/table-render.js` (re-render after column changes)
- `src/static/js/advanced-table/table-events.js` (row click event listeners)

**Additional Info:**
- Event delegation pattern recommended: `table.addEventListener('click', (e) => { if (e.target.closest('tr')) { ... } })`
- Ensure event listeners are not duplicated

---

### Bug #16: Frequency Field Should Only Be Enabled for PM Orders
**Priority:** Medium  
**Status:** Open

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

## 🔵 LOW PRIORITY BUGS

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

**Critical (1 bug):**
- Bug #2: CSRF Token Missing - MO and Spare Parts Forms

**High (6 bugs):**
- Bug #1: Missing Delete Functionality for Assets
- Bug #3: Incorrect Back Button Navigation from MO Add Page
- Bug #4: Table State Not Preserved on Navigation/Refresh
- Bug #5: Assignees Field Needs Dropdown for Users/Teams
- Bug #6: Missing Delete Functionality for Maintenance Orders
- Bug #9: Table Sidebar - Save View Not Working
- Bug #11: Spare Parts Update Not Working - CSRF Token Missing

**Medium (6 bugs):**
- Bug #7: Missing Required Field Indicators
- Bug #8: Table Columns Too Narrow on Default Load
- Bug #10: Table Width Not Responsive to Window Resize
- Bug #13: Table Views - Save/Load Functionality Not Working
- Bug #14: Cannot Click Table Elements After Column Changes
- Bug #16: Frequency Field Should Only Be Enabled for PM Orders
- Bug #17: OR Filter Operator Clears Previous Filter Row

**Low (1 bug):**
- Bug #15: Status Field Should Be Hidden in MO Creation

**Total Bugs: 14** (Note: Bugs #11 and #2 are the same issue, Bug #13 encompasses Bug #9)

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
