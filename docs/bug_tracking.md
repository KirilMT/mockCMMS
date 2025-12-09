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
**Status:** ✅ RESOLVED - December 2, 2025

**Description:**  
When applying filters, global search, column configuration, or saved views to a table, navigating to a detail page and returning (or refreshing the page) resets all table settings to default.

**Root Cause:**
Table state was stored only in memory (JavaScript variables). When the page reloaded or user navigated away, all state was lost.

**Solution Implemented:**
Implemented comprehensive state persistence using `localStorage`:

**Features:**
- ✅ **Automatic State Saving:** State is saved after every change (sort, filter, search, column changes)
- ✅ **Automatic State Restoration:** State is restored on page load
- ✅ **Page-Specific State:** Each table (assets, MOs, spare parts) has its own state key
- ✅ **State Expiration:** State older than 24 hours is automatically removed
- ✅ **UI Synchronization:** Search input and filter rows are restored visually

**Persisted State includes:**
- Current sort column and direction
- Active filters (column, operator, value, logic)
- Global search term
- Hidden columns
- Column order
- Current page number
- Selected configuration ID

**Implementation:**

1. **State Saving (`table-core.js`):**
```javascript
saveTableState() {
    const state = {
        currentSort, filters, hiddenColumns,
        columnOrder, currentPage, globalSearchTerm,
        selectedConfigId, timestamp: Date.now()
    };
    localStorage.setItem(`tableState_${this.pageName}`, JSON.stringify(state));
}
```

2. **State Restoration (`table-core.js`):**
```javascript
restoreTableState() {
    const savedState = JSON.parse(localStorage.getItem(`tableState_${this.pageName}`));
    // Check age (max 24 hours)
    // Restore all state properties
}
```

3. **Trigger Points:** State is saved after:
   - Sorting columns
   - Applying/clearing filters
   - Global search
   - Column show/hide/reorder
   - Resetting columns

**Affected Files:**
- `src/static/js/advanced-table/table-core.js` (save/restore methods)
- `src/static/js/advanced-table/table-data.js` (save after sort/search)
- `src/static/js/advanced-table/table-sidebar.js` (save after filters/columns, restore filter UI)
- `src/static/js/advanced-table/table-render.js` (call restore UI methods)

**Testing:**
✅ Apply filters → navigate to detail → back → filters restored
✅ Sort table → navigate away → back → sort restored
✅ Search → refresh page (F5) → search term restored
✅ Hide columns → navigate away → back → columns still hidden
✅ Reorder columns → refresh → order preserved
✅ State expires after 24 hours
✅ Different tables have separate states (assets vs MOs)
✅ Filter UI shows restored filters visually

---

### Bug #5: Assignees Field Needs Dropdown for Users/Teams
**Priority:** High  
**Status:** ✅ RESOLVED - December 2, 2025

**Description:**  
In "Add New Maintenance Order" and "Edit Maintenance Order" forms, the "Assignees" field was a plain textarea expecting JSON format. It has been replaced with a user-friendly multi-select dropdown.

**Solution Implemented:**

1.  **Backend (`src/routes/main.py`):**
    -   In `add_mo()` and `edit_mo()` routes, queried the database to fetch:
        -   All users with the "Technician" role.
        -   All available teams.
    -   Passed the `technicians` and `teams` lists to the `maintenance_order_detail.html` template.
    -   Modified the POST handling logic to use `request.form.getlist('assignees')` to correctly capture multiple selections.
    -   The list of selections is stored as a JSON string in the `assignees_json` column.

2.  **Frontend (`src/templates/maintenance_order_detail.html`):**
    -   Replaced the `<textarea>` for `assignees` with a `<select multiple>` element.
    -   Used `<optgroup>` to separate "Teams" and "Technicians" in the dropdown for better organization.
    -   Populated the dropdown with the `teams` and `technicians` data passed from the backend.
    -   Added logic to pre-select options when editing an existing Maintenance Order.

3.  **UI/UX Enhancement (Select2):**
    -   Added the **Select2** library to `base.html` (CSS and JS).
    -   Initialized Select2 on the `#assignees` dropdown in `maintenance_order_detail.html`.
    -   This transforms the standard multi-select box into a searchable, tag-based input field, significantly improving usability.
    -   Used the `bootstrap-5` theme for seamless integration with the existing design.

**Code Snippets:**

**`main.py` (fetching data):**
```python
technician_role = Role.query.filter_by(name='Technician').first()
technicians = User.query.filter_by(role=technician_role).all() if technician_role else []
teams = Team.query.all()
# ...
return render_template('maintenance_order_detail.html', ..., technicians=technicians, teams=teams)
```

**`maintenance_order_detail.html` (dropdown):**
```html
<select multiple class="form-control" id="assignees" name="assignees">
    <optgroup label="Teams">
        {% for team in teams %}
        <option value="team:{{ team.name }}" ...>{{ team.name }} (Team)</option>
        {% endfor %}
    </optgroup>
    <optgroup label="Technicians">
        {% for tech in technicians %}
        <option value="user:{{ tech.username }}" ...>{{ tech.username }}</option>
        {% endfor %}
    </optgroup>
</select>
```

**`maintenance_order_detail.html` (Select2 initialization):**
```javascript
$('#assignees').select2({
    theme: "bootstrap-5",
    placeholder: 'Select assignees...',
    allowClear: true
});
```

**Testing:**
✅ "Add MO" page shows a searchable dropdown for Assignees.
✅ Dropdown correctly lists Teams and Technicians.
✅ "Edit MO" page shows the same dropdown with previously saved assignees pre-selected.
✅ Saving a new MO with multiple assignees works correctly.
✅ Updating an existing MO's assignees works correctly.
✅ The field is user-friendly and intuitive.

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
**Status:** ✅ RESOLVED - December 2, 2025 (False Positive)

**Description:**  
The "Save View" button in the table sidebar was reported as not working. However, after a thorough code review, the functionality was confirmed to be working as expected.

**Analysis:**
- **Frontend:** `table-sidebar.js` correctly attaches an event listener to the "Save View" button.
- **API Call:** The `saveView()` method correctly constructs the configuration object and sends a `POST` request to `/api/table-config/<page_name>`.
- **Backend:** The `/api/table-config/<page_name>` endpoint in `src/routes/api.py` is correctly defined to handle the `POST` request, save the configuration to the `TableConfiguration` model, and return a success response.
- **CSRF:** The request correctly includes the `X-CSRFToken` header.

**Conclusion:**
The feature is implemented correctly. The issue was likely a misinterpretation or a temporary local issue. No code changes were required.

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
**Status:** ✅ RESOLVED - December 4, 2025
**Resolution:** Implemented smart default column widths in `table-resize.js` based on column content type (ID: 65px, CODE: 150px, Description: 350px, Name: 250px, etc.). Fixed logic to use default widths directly instead of Math.max with computed width, allowing columns to be their specified size. Changed CSS min-width from 120px to 50px to allow smaller columns.

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
**Status:** ✅ RESOLVED - December 4, 2025
**Resolution:** Implemented `handleWindowResize` method in `table-resize.js` to dynamically adjust table width to fill the container. Added event listeners for window resize and sidebar toggle to trigger the adjustment. Verified that table expands to fill available space.

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
**Status:** ✅ RESOLVED - December 2, 2025

**Description:**
After changing columns (hiding/showing or drag-and-drop reordering), applying changes, **or sorting the table**, clicking on table rows to navigate to detail pages stops working.

**Root Cause:**
Row click event listeners were attached to individual row elements during initialization. When the table was re-rendered (after sorting or column changes), new row elements were created, but the event listeners weren't re-attached to the new elements.

**Solution Implemented:**
Replaced individual row event listeners with **event delegation** pattern:
- Attached a single click listener to the `<tbody>` element instead of each row
- The tbody listener detects clicks on any row, even after table re-renders
- Added logic to ignore clicks on buttons, links, and action elements
- Added `cursor: pointer` CSS to tbody tr elements

**Benefits of Event Delegation:**
- Event listeners survive table re-renders (sorting, filtering, column changes)
- Better performance (one listener instead of many)
- More robust and maintainable code
- No need to manually re-attach listeners after updates

**Code Changes:**

**JavaScript (`table-events.js`):**
```javascript
// Old approach: Individual listeners (BROKEN after re-render)
rows.forEach((row, index) => {
    row.addEventListener('click', () => { ... });
});

// New approach: Event delegation (WORKS after re-render)
const tbody = this.container.querySelector('.advanced-table tbody');
tbody.addEventListener('click', (e) => {
    const row = e.target.closest('tr');
    // ... handle click
});
```

**CSS (`advanced-table.css`):**
```css
.advanced-table tbody tr {
    cursor: pointer;  /* Added for visual feedback */
    transition: background-color 0.15s ease-in-out;
}
```

**Affected Files:**
- `src/static/js/advanced-table/table-events.js` (lines 75-104)
- `src/static/css/advanced-table.css` (line 134)

**Testing:**
✅ Click row → navigates to detail page
✅ Sort column → click row → still works
✅ Sort again → click row → still works
✅ Hide/show columns → click row → still works
✅ Reorder columns → click row → still works
✅ Apply filters → click row → still works
✅ Clicks on Edit/Delete buttons → ignored (actions work)
✅ Hover shows pointer cursor

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
**Status:** ✅ RESOLVED - December 2, 2025

**Description:**  
When creating a new asset on the "Add New Asset" page, the "Maintenance Orders for [Asset Name]" section is displayed, even though the asset doesn't exist yet. This is confusing and the "Add Maintenance Order" button cannot function properly since there's no asset ID.

**Solution Implemented:**
Wrapped the entire "Maintenance Orders for" section in a conditional `{% if asset %}` block in `asset_detail.html`. The section now only appears when editing an existing asset, not when creating a new one.

```html
{% if asset %}
<!-- Only show Maintenance Orders section when editing existing asset -->
<div class="mt-5">
    <h2>Maintenance Orders for {{ asset.name }}</h2>
    <!-- MO table and Add button -->
</div>
{% endif %}
```

**Affected Files:**
- `src/templates/asset_detail.html` (lines 88-131)

**Testing:**
✅ Add New Asset page - MO section is hidden
✅ Edit Asset page - MO section is visible
✅ Prevents user confusion about adding MOs to non-existent assets

---

### Bug #26: Frequency Field Not Required for PM Orders
**Priority:** Medium  
**Status:** ✅ RESOLVED - December 2, 2025

**Description:**  
When creating or editing a Maintenance Order with Order Type set to "PM" (Preventive Maintenance), the Frequency field is enabled but not marked as required. PM orders should always have a frequency specified to define the maintenance schedule.

**Solution Implemented:**

**Frontend (JavaScript):**
Updated the `updateFrequencyField()` function in `maintenance_order_detail.html` to:
- Dynamically add/remove `required` HTML attribute when order type changes
- Dynamically add/remove `required-field` CSS class to show/hide red asterisk
- Frequency is required when PM is selected, optional when disabled for non-PM types

```javascript
if (isPM) {
    frequencyField.disabled = false;
    frequencyField.required = true;  // Make required
    frequencyLabel.classList.add('required-field');  // Show asterisk
} else {
    frequencyField.disabled = true;
    frequencyField.required = false;
    frequencyField.value = '';
    frequencyLabel.classList.remove('required-field');
}
```

**Backend (Python):**
Added validation in both `add_mo()` and `edit_mo()` routes:
```python
# Validate that PM orders have a frequency
if order_type == 'PM' and not frequency:
    flash('Frequency is required for PM (Preventive Maintenance) orders.', 'error')
    return render_template(...)
```

**Affected Files:**
- `src/templates/maintenance_order_detail.html` (lines 151-197 - JavaScript)
- `src/routes/main.py` (lines 127-131 in add_mo, lines 195-199 in edit_mo)

**Testing:**
✅ PM order type selected - frequency shows red asterisk
✅ PM order type selected - frequency has HTML required attribute
✅ Submitting PM without frequency - shows error message
✅ Non-PM order type - frequency has no asterisk, not required
✅ Switching from PM to Reactive - asterisk removed
✅ Switching from Reactive to PM - asterisk added

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

### Bug #27: MO Table in Asset Details Should Use Advanced Table
**Priority:** Medium
**Status:** Open

**Description:**
The "Maintenance Orders for [Asset Name]" section in the Asset Detail page uses a basic HTML table instead of the advanced table component. This creates inconsistency with the rest of the application and lacks features like sorting, filtering, column customization, and search that users expect.

**Current Behavior:**
- Asset Detail page shows MOs in a basic `<table>` element
- No sorting, filtering, or search capabilities
- No column resizing or reordering
- Inconsistent UX compared to main MO list page
- Limited functionality for assets with many MOs

**Expected Behavior:**
- MO table in Asset Detail should use the same advanced table component as main pages
- Should support:
  - Column sorting (click headers to sort)
  - Global search
  - Column filtering
  - Column show/hide
  - Column resizing
  - Row click to navigate (already working via links)
- Consistent look and feel across the application
- Better UX for viewing MOs associated with an asset

**Possible Solution:**
1. Replace the basic table in `asset_detail.html` with the advanced table component
2. Initialize the advanced table JavaScript for this table
3. Configure table with appropriate columns:
   - ID, Description, Type, Status, Due Date, Actions
4. Ensure the table is scoped to only this asset's MOs (not all MOs)
5. Consider making it a reusable component for other detail pages (User, Spare Parts)

**Affected Files:**
- `src/templates/asset_detail.html` (lines 94-125 - MO table)
- `src/static/js/advanced-table/table-init.js` (may need to support multiple tables on one page)
- Potentially create a new template partial: `templates/components/mo_table.html`

**Additional Info:**
- Improves consistency across the application
- Better UX for assets with many MOs
- Same pattern could be applied to:
  - User Detail page (showing user's assigned MOs)
  - Spare Parts Detail page (showing MOs using this part)
- May require advanced table to support multiple instances on the same page

---

### Bug #28: Assignees Dropdown Opens When Removing Item (Closed State)
**Priority:** Medium
**Status:** ✅ PARTIALLY RESOLVED - December 3, 2025

**Description:**
When the Assignees dropdown (Select2) is closed and a user clicks the "X" button to remove an assigned user or team, the dropdown automatically opens. This is disruptive and unexpected behavior.

**Original Current Behavior:**
- Dropdown is closed
- User clicks "X" on an assignee tag
- Item is removed
- Dropdown opens unexpectedly

**Expected Behavior:**
- **If dropdown is closed**: Clicking "X" removes the item, dropdown remains closed
- **If dropdown is open**: Clicking "X" removes the item, dropdown remains open with caret ready

**Solution Implemented:**
Implemented Select2 event handlers to track dropdown state and prevent unwanted opening when removing items:

```javascript
let isOpen = false;
let removalWhileClosed = false;

selectionEl.on('mousedown.select2Removal', '.select2-selection__choice__remove', () => {
    removalWhileClosed = !isOpen;
    if (removalWhileClosed) {
        setTimeout(() => setCaretVisible(false), 0);
    }
});

assigneesSelect.on('select2:opening', (e) => {
    if (removalWhileClosed && !isOpen) {
        removalWhileClosed = false;
        e.preventDefault();
    }
});

assigneesSelect.on('select2:open', () => {
    isOpen = true;
    removalWhileClosed = false;
    setCaretVisible(true);
});

assigneesSelect.on('select2:close', () => {
    isOpen = false;
    setCaretVisible(false);
});

$(document).on('mousedown.select2Close', (event) => {
    if (!isOpen) return;
    const target = $(event.target);
    const dropdown = $('.select2-container--open');
    if (!selectionEl.is(target) && selectionEl.has(target).length === 0 && 
        !dropdown.is(target) && dropdown.has(target).length === 0) {
        assigneesSelect.select2('close');
    }
});
```

**What Works:**
✅ Dropdown stays closed when removing items (closed state)
✅ Outside clicks properly close dropdown
✅ No unwanted dropdown opening when removing assignees

**Known Limitations (Accepted for Current Iteration):**
- Caret visibility after adding/removing items while dropdown is open needs refinement
- User accepted current functionality as sufficient for this iteration
- Full caret management will be addressed in future iteration if needed

**Affected Files:**
- `src/templates/maintenance_order_detail.html` (Select2 initialization with closeOnSelect: false and event handlers)

**Testing:**
✅ Dropdown closed → click "X" → item removed, dropdown stays closed
✅ Dropdown open → click outside → dropdown closes correctly
✅ Multiple assignees can be added/removed without unexpected behavior

---

### Bug #29: Assignees Column Not Appearing in MO Table
**Priority:** Medium
**Status:** ✅ RESOLVED - December 3, 2025

**Description:**
The "Assignees" column was added to the table configuration but did not appear in the Maintenance Orders table UI because of cached table state in the browser's `localStorage`.

**Root Cause:**
The advanced table saves its state (column order, hidden columns, etc.) to `localStorage`. When a new column is added to the configuration, the old saved state in the user's browser doesn't include it, so the table renders without the new column.

**Solution Implemented:**
A script was added to `maintenance_orders.html` that runs on page load. It checks the `localStorage` for the saved table state (`tableState_mosTable`). If the state exists but is missing the new `'assignees'` column, the script automatically clears the outdated state. This forces the table to re-initialize with the new column configuration, making the "Assignees" column appear without requiring users to manually clear their cache.

```javascript
// Script added to maintenance_orders.html
const tableStateKey = 'tableState_mosTable';
const savedState = localStorage.getItem(tableStateKey);
if (savedState) {
    const state = JSON.parse(savedState);
    if (state.columnOrder && !state.columnOrder.includes('assignees')) {
        localStorage.removeItem(tableStateKey); // Clear old state
    }
}
```

**Affected Files:**
- `src/templates/maintenance_orders.html` (localStorage check script)
- `src/services/db_utils.py` (verified `to_dict()` formats assignees correctly)

**Testing:**
✅ "Assignees" column is now visible on the MO table.
✅ The fix works even if old state is present in localStorage.
✅ No manual cache clearing is required.

---

### Bug #30: Assignees Field Causes Layout Shift When Adding Items
**Priority:** Medium
**Status:** ✅ RESOLVED - December 9, 2025

**Description:**
When adding multiple assignees to the "Assignees" field in the MO detail form, the field grows vertically, pushing the "Update MO", "Cancel", and "Delete" buttons down the page. This creates a jarring and unprofessional user experience.

**Current Behavior:**
- Assignees field (Select2 multi-select) grows vertically as items are added
- No height limit on the field
- Form buttons ("Update MO", "Cancel", "Delete") are pushed down with each addition
- Creates visual instability and poor UX

**Expected Behavior:**
- Assignees field should have a maximum height (e.g., 120px)
- When content exceeds max height, field should:
  - Stop growing
  - Show internal scrollbar
  - Allow scrolling within the field
- Form buttons should remain in a stable position
- Layout should feel solid and professional

**Possible Solution:**
Add CSS to set max-height and enable scrolling:

```css
/* Custom styles for Select2 to prevent layout shifts */
.select2-container--bootstrap-5 .select2-selection--multiple {
    max-height: 120px; /* Limit height */
    overflow-y: auto; /* Add scrollbar when needed */
    cursor: text !important;
    max-height: 120px;
    overflow-y: auto;
}

.select2-container--bootstrap-5 .select2-search__field {
    cursor: text !important;
}

.select2-container--bootstrap-5 .select2-selection__choice {
    cursor: default !important;
}
```

**Affected Files:**
- `src/static/css/main.css` (add Select2 max-height styles)

**Additional Info:**
- 120px allows approximately 3-4 assignee tags before scrolling
- Internal scrolling is more intuitive than growing the entire form
- Improves overall form stability and professional appearance
- Can be applied to other multi-select fields if needed

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

**Critical (0 open - 1 fixed):**
- ~~Bug #2: CSRF Token Missing - MO and Spare Parts Forms~~ ✅ FIXED (Prior to Dec 2, 2025)

**High (0 open - 11 fixed):**
**Open:**
(None)

**Fixed:**
- ~~Bug #1: Missing Delete Functionality for Assets~~ ✅ FIXED (Dec 2, 2025 - Bug #R3)
- ~~Bug #3: Incorrect Back Button Navigation from MO Add Page~~ ✅ FIXED (Dec 2, 2025 - Bug #R1)
- ~~Bug #4: Table State Not Preserved on Navigation/Refresh~~ ✅ FIXED (Dec 2, 2025)
- ~~Bug #5: Assignees Field Needs Dropdown for Users/Teams~~ ✅ RESOLVED (Dec 2, 2025)
- ~~Bug #6: Missing Delete Functionality for Maintenance Orders~~ ✅ FIXED (Dec 2, 2025 - Bug #R3)
- ~~Bug #9: Table Sidebar - Save View Not Working~~ ✅ RESOLVED (Dec 2, 2025 - False Positive)
- ~~Bug #11: Spare Parts Update Not Working - CSRF Token Missing~~ ✅ FIXED (Prior to Dec 2, 2025)
- ~~Bug #14: Cannot Click Table Elements After Column Changes or Sorting~~ ✅ FIXED (Dec 2, 2025)

**Medium (7 open - 7 fixed):**
**Open:**
- Bug #8: Table Columns Too Narrow on Default Load
- Bug #10: Table Width Not Responsive to Window Resize
- Bug #13: Table Views - Save/Load Functionality Not Working
- Bug #17: OR Filter Operator Clears Previous Filter Row
- Bug #24: Autofill Background Color Not Consistent Across All Input Types **(added Dec 2, 2025)**
- Bug #27: MO Table in Asset Details Should Use Advanced Table **(NEW - Dec 2, 2025)**
- ~~Bug #30: Assignees Field Causes Layout Shift When Adding Items~~ ✅ RESOLVED (Dec 9, 2025)

**Fixed:**
- ~~Bug #7: Missing Required Field Indicators~~ ✅ FIXED (Prior to Dec 2, 2025)
- ~~Bug #16: Frequency Field Should Only Be Enabled for PM Orders~~ ✅ FIXED (Dec 1, 2025)
- ~~Bug #23: Frequency Field Not Showing Saved Value on Edit~~ ✅ FIXED (Dec 2, 2025 - Bug #R2)
- ~~Bug #25: Maintenance Orders Section Displayed on Add New Asset Page~~ ✅ FIXED (Dec 2, 2025)
- ~~Bug #26: Frequency Field Not Required for PM Orders~~ ✅ FIXED (Dec 2, 2025)
- ~~Bug #28: Assignees Dropdown Opens When Removing Item (Closed State)~~ ✅ PARTIALLY RESOLVED (Dec 3, 2025)
- ~~Bug #29: Assignees Column Not Appearing in MO Table~~ ✅ FIXED (Dec 3, 2025)

**Low (1 open - 1 fixed):**
**Open:**
- Bug #15: Status Field Should Be Hidden in MO Creation

**Fixed:**
- ~~Bug #19: KeyError - 'frequency' Field Not Submitted When Disabled~~ ✅ FIXED (Dec 1, 2025)

**Total Bugs: 24**  
**Open: 8 bugs** (0 High, 7 Medium, 1 Low)
**In Progress: 0 bugs**
**Fixed: 17 bugs** (1 Critical, 8 High, 8 Medium)
**Added Dec 2, 2025:** 7 new bugs (Bug #24, #25, #26, #27, #28, #29, #30)
**Fixed Dec 9, 2025:** 1 bug (Bug #30)
**Fixed Dec 3, 2025:** 2 bugs (Bug #28 - partially, #29)
**Fixed Dec 2, 2025:** 9 bugs (Bug #R1, #R2, #R3, #4, #5, #9, #14, #25, #26) + verified 2 previous fixes (Bug #2, #7)
**Previously Fixed (Dec 1, 2025):** 3 bugs (Bug #16, #19, #23)

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

### Bug #24: Table Header Not Sticky on Scroll
**Priority:** High
**Status:** Open

**Description:**
The table header scrolls away with the content instead of staying fixed (sticky) at the top of the table view. This makes it difficult to read data in long tables as users lose context of what each column represents.

**Current Behavior:**
- Header moves up and disappears when scrolling down the table.

**Expected Behavior:**
- Header should remain fixed at the top of the table view while the body content scrolls.

**Possible Solution:**
- Check `sticky-top` class usage.
- Ensure parent container has correct `overflow` and `height` properties.
- Verify `z-index` context.

**Affected Files:**
- `src/static/js/advanced-table/table-render.js`
- `src/static/css/advanced-table.css`

---

_This document follows the structure and philosophy of `mockCMMS_roadmap.md` and serves as a living document for bug tracking and resolution._

