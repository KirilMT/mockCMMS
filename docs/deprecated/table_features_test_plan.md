# Advanced Table Features Test Plan

**Last Tests Passed:** 2025-11-30
**Last Updated:** 2025-11-30

This document outlines the mandatory testing procedures for the Advanced Table component in the mockCMMS application. These tests must be performed automatically by the AI agent using the `browser_subagent` tool whenever changes are made to the table component or related features.

**Target Page:** `http://127.0.0.1:5000/assets` (or any page using `AdvancedTable`)

## 1. Prerequisites
- Ensure the mockCMMS server is running (`python run.py`).
- Navigate to the Assets page: `http://127.0.0.1:5000/assets`.

> [!NOTE]
> **Iterative Improvement Approach**
>
> This test plan represents a working baseline for the Advanced Table component. The current implementation is functional and ready for use. Tests will be improved and expanded iteratively as:
> - New bugs are discovered and fixed
> - New features are implemented
> - Edge cases are identified
> - User feedback is received
>
> The goal is to maintain a working version at all times while continuously improving quality and coverage.

## 2. Test Scenarios

### 2.1. Sidebar & Layout Tests

#### Test 2.1.1: Toggle Sidebar Collapse/Expand
1. Navigate to `http://127.0.0.1:5000/assets`
2. Locate the sidebar toggle button (hamburger icon `☰`) in the table controls (needs to be part of the table and not the one in the page!)
3. Click the toggle button
4. Verify the sidebar collapses (check for `collapsed` class on `.table-sidebar`)
5. Click the toggle button again
6. Verify the sidebar expands (check `collapsed` class is removed)

#### Test 2.1.2: Expand/Collapse All Sections
1. Navigate to `http://127.0.0.1:5000/assets`
2. Click on the "Filters" section header in the sidebar
3. Verify the section content expands (check `.section-content` does not have `collapsed` class)
4. Click on the "Filters" section header again
5. Verify the section content collapses (check `.section-content` has `collapsed` class)
6. Repeat steps 2-5 for "Columns" section
7. Repeat steps 2-5 for "Saved Views" section

#### Test 2.1.3: Sidebar State Persistence
1. Navigate to `http://127.0.0.1:5000/assets`
2. Collapse the sidebar using the toggle button
3. Expand the "Filters" section
4. Refresh the page (F5 or browser refresh)
5. Verify the sidebar remains collapsed
6. Verify the "Filters" section remains expanded

### 2.2. Column Management Tests

#### Test 2.2.1: Hide Single Column
1. Navigate to `http://127.0.0.1:5000/assets`
2. Expand the "Columns" section in the sidebar
3. Count the number of visible columns in the table header
4. Uncheck the checkbox for "Status" column
5. Click the "Apply" button in the Columns section
6. Verify "Status" column is NOT visible in the table header
7. Verify the number of visible columns decreased by 1

#### Test 2.2.2: Hide Multiple Columns
1. Navigate to `http://127.0.0.1:5000/assets`
2. Expand the "Columns" section in the sidebar
3. Uncheck checkboxes for "Type", "Cost Center", and "Description" columns
4. Click the "Apply" button
5. Verify all three columns are NOT visible in the table header

#### Test 2.2.3: Show Hidden Column
1. Navigate to `http://127.0.0.1:5000/assets`
2. Expand the "Columns" section
3. Uncheck "Status" column and click "Apply"
4. Verify "Status" column is hidden
5. Check the "Status" column checkbox again
6. Click "Apply"
7. Verify "Status" column IS visible in the table header

#### Test 2.2.4: Reset Columns to Default
1. Navigate to `http://127.0.0.1:5000/assets`
2. Expand the "Columns" section
3. Hide 2-3 columns by unchecking them and clicking "Apply"
4. Click the "Reset" button in the Columns section
5. Verify all columns are visible again
6. Verify columns are in their original order

#### Test 2.2.5: Hide All Columns Except One
1. Navigate to `http://127.0.0.1:5000/assets`
2. Expand the "Columns" section
3. Uncheck all columns except "ID"
4. Click "Apply"
5. Verify only "ID" column is visible in the table header
6. Verify table body shows data in the ID column

### 2.3. Filtering Tests

#### Test 2.3.1: Add Single Filter
1. Navigate to `http://127.0.0.1:5000/assets`
2. Expand the "Filters" section in the sidebar
3. Click the "Add" button
4. Select "Name" from the column dropdown
5. Select "Contains" from the operator dropdown
6. Enter "Robot" in the value input field
7. Click the "Apply" button
8. Verify the table shows only rows where Name contains "Robot"
9. Verify the "Filters" badge shows count "1"

#### Test 2.3.2: Add Multiple Filters with AND Logic
1. Navigate to `http://127.0.0.1:5000/assets`
2. Expand the "Filters" section
3. Add first filter: Column="Status", Operator="Equals", Value="Operational"
4. Click "Apply"
5. Note the number of rows displayed
6. Click "Add" to add a second filter
7. Select "Category" from column dropdown
8. Select "Equals" from operator dropdown
9. Enter "Equipment" in value field
10. Ensure the logic connector shows "AND" (default)
11. Click "Apply"
12. Verify the table shows only rows matching BOTH conditions
13. Verify the "Filters" badge shows count "2"

#### Test 2.3.3: Add Multiple Filters with OR Logic
1. Navigate to `http://127.0.0.1:5000/assets`
2. Expand the "Filters" section
3. Add first filter: Column="Status", Operator="Equals", Value="Operational"
4. Click "Apply"
5. Click "Add" to add a second filter
6. Select "Status" from column dropdown
7. Select "Equals" from operator dropdown
8. Enter "Maintenance" in value field
9. Click the "OR" radio button in the logic connector
10. Click "Apply"
11. Verify the table shows rows with Status="Operational" OR Status="Maintenance"
12. Verify more rows are shown than with just the first filter

#### Test 2.3.4: Remove Single Filter
1. Navigate to `http://127.0.0.1:5000/assets`
2. Expand the "Filters" section
3. Add a filter: Column="Status", Operator="Equals", Value="Operational"
4. Click "Apply"
5. Click the "×" (remove) button on the filter row
6. Verify the filter row is removed
7. Verify the table shows all rows again (filter auto-applies on removal)
8. Verify the "Filters" badge shows count "0" or is hidden

#### Test 2.3.5: Clear All Filters
1. Navigate to `http://127.0.0.1:5000/assets`
2. Expand the "Filters" section
3. Add 3 different filters and click "Apply"
4. Verify filters are applied (reduced row count)
5. Click the "Clear" button in the Filters section
6. Verify all filter rows are removed
7. Verify the table shows all rows again
8. Verify the "Filters" badge shows count "0" or is hidden

#### Test 2.3.6: Filter with Different Operators
1. Navigate to `http://127.0.0.1:5000/assets`
2. Expand the "Filters" section
3. Test "Contains": Add filter Column="Name", Operator="Contains", Value="Robot", Apply
4. Verify results contain "Robot" in Name
5. Clear filters
6. Test "Starts With": Add filter Column="Name", Operator="Starts With", Value="P", Apply
7. Verify all results start with "P"
8. Clear filters
9. Test "Ends With": Add filter Column="Name", Operator="Ends With", Value="1", Apply
10. Verify all results end with "1"
11. Clear filters
12. Test "Not Contains": Add filter Column="Name", Operator="Does Not Contain", Value="Robot", Apply
13. Verify no results contain "Robot"

### 2.4. Global Search Tests

#### Test 2.4.1: Basic Global Search
1. Navigate to `http://127.0.0.1:5000/assets`
2. Locate the global search input field (`#globalSearchInput`) in the top bar
3. Type "Robot" in the search field
4. Click the search button (magnifying glass icon) or press Enter
5. Verify only rows containing "Robot" in ANY column are displayed
6. Verify the row count updates to show filtered count

#### Test 2.4.2: Clear Global Search
1. Navigate to `http://127.0.0.1:5000/assets`
2. Type "Robot" in the global search field and press Enter
3. Verify results are filtered
4. Click the "Clear search" button (× icon)
5. Verify the search input is cleared
6. Verify all rows are displayed again

#### Test 2.4.3: Global Search with No Results
1. Navigate to `http://127.0.0.1:5000/assets`
2. Type "XYZNONEXISTENT123" in the global search field
3. Press Enter
4. Verify the table shows "No results found" message
5. Verify the row count shows "0 of X rows"

#### Test 2.4.4: Global Search Case Insensitivity
1. Navigate to `http://127.0.0.1:5000/assets`
2. Type "robot" (lowercase) in the global search field
3. Press Enter
4. Note the number of results
5. Clear the search
6. Type "Robot" (uppercase) in the global search field
7. Press Enter
8. Verify the same number of results are returned

### 2.5. Sorting Tests

#### Test 2.5.1: Sort Single Column Ascending
1. Navigate to `http://127.0.0.1:5000/assets`
2. Click the "ID" column header
3. Verify the sort icon changes to up arrow (↑)
4. Verify rows are sorted by ID in ascending order (check first and last row IDs)

#### Test 2.5.2: Sort Single Column Descending
1. Navigate to `http://127.0.0.1:5000/assets`
2. Click the "ID" column header once (ascending)
3. Click the "ID" column header again
4. Verify the sort icon changes to down arrow (↓)
5. Verify rows are sorted by ID in descending order

#### Test 2.5.3: Sort Different Column Types
1. Navigate to `http://127.0.0.1:5000/assets`
2. Click "Name" column header (text sorting)
3. Verify alphabetical sorting (A-Z)
4. Click "ID" column header (number sorting)
5. Verify numerical sorting (1, 2, 3... not 1, 10, 2...)

#### Test 2.5.4: Sort Persistence After Filter
1. Navigate to `http://127.0.0.1:5000/assets`
2. Click "Name" column header to sort ascending
3. Add a filter: Column="Status", Operator="Equals", Value="Operational"
4. Click "Apply"
5. Verify the filtered results remain sorted by Name

### 2.6. Table Views (Save/Load) Tests - CRITICAL

#### Test 2.6.1: Save New View with Basic Configuration
1. Navigate to `http://127.0.0.1:5000/assets`
2. Click "Name" column header to sort ascending
3. Expand "Columns" section and hide "Description" column, click "Apply"
4. Expand "Saved Views" section in the sidebar
5. Click the "Save" button (`#saveViewBtn`)
6. Wait for the save modal to appear
7. Enter "Test View Basic" in the `#configName` input field
8. Click the "Save" button in the modal
9. Verify a success message appears (alert or notification)
10. Verify "Test View Basic" appears in the `#savedViewsList`

#### Test 2.6.2: Load Saved View
1. Navigate to `http://127.0.0.1:5000/assets`
2. Verify the table is in default state (all columns visible, no sort)
3. Expand "Saved Views" section
4. Click on "Test View Basic" in the saved views list
5. Verify "Name" column is sorted ascending
6. Verify "Description" column is hidden
7. Verify the view item is highlighted as Operational

#### Test 2.6.3: Save View with Filters
1. Navigate to `http://127.0.0.1:5000/assets`
2. Add filter: Column="Status", Operator="Equals", Value="Operational"
3. Click "Apply"
4. Sort by "Name" ascending
5. Expand "Saved Views" section
6. Click "Save" button
7. Enter "Test View With Filters" in the modal
8. Click "Save"
9. Verify the view is saved
10. Clear all filters and reset sort
11. Load "Test View With Filters"
12. Verify the filter is reapplied (Status=Operational)
13. Verify the sort is restored (Name ascending)

#### Test 2.6.4: Update Existing View
1. Navigate to `http://127.0.0.1:5000/assets`
2. Load "Test View Basic" from saved views
3. Show the "Location" column (that was previously hidden)
4. Click "Apply" in Columns section
5. Click the "Update" button (`#updateViewBtn`) in Saved Views section
6. Verify a success message appears
7. Refresh the page (F5)
8. Load "Test View Basic" again
9. Verify "Location" column is now visible (update persisted)

#### Test 2.6.5: Set View as Default
1. Navigate to `http://127.0.0.1:5000/assets`
2. Expand "Saved Views" section
3. Click the star icon (⭐) next to "Test View Basic"
4. Verify the view now shows "(Default)" badge
5. Refresh the page
6. Verify the default view is automatically loaded on page load

#### Test 2.6.6: Delete Saved View
1. Navigate to `http://127.0.0.1:5000/assets`
2. Expand "Saved Views" section
3. Click the trash icon (🗑️) next to "Test View Basic"
4. Confirm deletion if a confirmation dialog appears
5. Verify "Test View Basic" is removed from the saved views list

### 2.7. Feature Interaction Tests

#### Test 2.7.1: Filters + Global Search
1. Navigate to `http://127.0.0.1:5000/assets`
2. Add filter: Column="Status", Operator="Equals", Value="Operational"
3. Click "Apply"
4. Note the number of filtered rows
5. Type "Robot" in the global search field
6. Press Enter
7. Verify the table shows only rows that are BOTH Status="Operational" AND contain "Robot"
8. Verify the row count reflects both filters applied

#### Test 2.7.2: Filters + Sorting
1. Navigate to `http://127.0.0.1:5000/assets`
2. Click "Name" column header to sort ascending
3. Add filter: Column="Type", Operator="Equals", Value="Equipment"
4. Click "Apply"
5. Verify the filtered results remain sorted by Name ascending
6. Click "Name" column header again
7. Verify the filtered results are now sorted descending

#### Test 2.7.3: Hidden Columns + Filters
1. Navigate to `http://127.0.0.1:5000/assets`
2. Hide "Status" column via Columns section
3. Try to add a filter on "Status" column
4. Verify "Status" column is NOT available in the filter column dropdown
5. Show "Status" column again
6. Verify "Status" column now appears in the filter dropdown

#### Test 2.7.4: Global Search + Sorting + Hidden Columns
1. Navigate to `http://127.0.0.1:5000/assets`
2. Hide "Description" column
3. Sort by "Name" ascending
4. Type "Robot" in global search
5. Press Enter
6. Verify: Description column is hidden, results are sorted by Name, only "Robot" results shown
7. Clear search
8. Verify: Description still hidden, sort still Operational

#### Test 2.7.5: Save View with All Features Combined
1. Navigate to `http://127.0.0.1:5000/assets`
2. Hide "Description" and "Type" columns
3. Add filter: Column="Status", Operator="Equals", Value="Operational"
4. Click "Apply"
5. Sort by "Name" descending
6. Type "Robot" in global search and press Enter
7. Save this view as "Test Complex View"
8. Reset everything (clear search, clear filters, reset columns, clear sort)
9. Load "Test Complex View"
10. Verify: Description and Type hidden, Status filter applied, Name sorted descending, "Robot" search applied

#### Test 2.7.6: Export with Filters Applied
1. Navigate to `http://127.0.0.1:5000/assets`
2. Add filter: Column="Status", Operator="Equals", Value="Operational"
3. Click "Apply"
4. Click the "Export CSV" button
5. Verify the exported file contains only the filtered rows (Status=Operational)
6. Verify the exported file includes all visible columns

#### Test 2.7.7: Export with Hidden Columns
1. Navigate to `http://127.0.0.1:5000/assets`
2. Hide "Description" column
3. Click "Apply"
4. Click "Export CSV" button
5. Verify the exported file does NOT include the "Description" column
6. Verify all other visible columns are included

### 2.8. Page Interaction Tests

#### Test 2.8.1: Table State After Page Refresh
1. Navigate to `http://127.0.0.1:5000/assets`
2. Add filter: Column="Status", Operator="Equals", Value="Operational"
3. Click "Apply"
4. Sort by "Name" ascending
5. Hide "Description" column
6. Refresh the page (F5)
7. Verify the filter is cleared (default behavior - filters don't persist across refreshes)
8. Verify the sort is cleared
9. Verify the hidden column is restored (default behavior)

#### Test 2.8.2: Navigate Away and Return
1. Navigate to `http://127.0.0.1:5000/assets`
2. Apply some filters and sort
3. Click a link to navigate to another page (e.g., click on an asset detail)
4. Click the browser back button
5. Verify the table returns to default state (filters/sort cleared)

#### Test 2.8.3: Saved View Persistence Across Sessions
1. Navigate to `http://127.0.0.1:5000/assets`
2. Create and save a view "Test Persistence"
3. Close the browser tab completely
4. Open a new browser tab
5. Navigate to `http://127.0.0.1:5000/assets`
6. Expand "Saved Views" section
7. Verify "Test Persistence" view is still in the saved views list
8. Load the view and verify it works correctly

#### Test 2.8.4: Multiple Filters Then Navigate
1. Navigate to `http://127.0.0.1:5000/assets`
2. Add 3 different filters
3. Click "Apply"
4. Click on an asset row to view details (if clickable)
5. Return to the assets page
6. Verify filters are cleared (default behavior)

### 2.9. Edge Cases and Error Handling

#### Test 2.9.1: Save View with Empty Name
1. Navigate to `http://127.0.0.1:5000/assets`
2. Make some table changes
3. Click "Save" in Saved Views section
4. Leave the config name field empty
5. Click "Save" in the modal
6. Verify an error message appears ("Please enter a configuration name")
7. Verify the modal does not close

#### Test 2.9.2: Save View with Duplicate Name
1. Navigate to `http://127.0.0.1:5000/assets`
2. Save a view as "Test Duplicate"
3. Make different changes
4. Try to save another view as "Test Duplicate"
5. Verify the system either: prevents duplicate names OR overwrites with confirmation

#### Test 2.9.3: Filter with Empty Value
1. Navigate to `http://127.0.0.1:5000/assets`
2. Expand "Filters" section
3. Click "Add"
4. Select "Name" column
5. Select "Contains" operator
6. Leave the value field empty
7. Try to click "Apply"
8. Verify the "Apply" button is disabled OR an error message appears

#### Test 2.9.4: Apply Filter Without Selecting Column
1. Navigate to `http://127.0.0.1:5000/assets`
2. Expand "Filters" section
3. Click "Add"
4. Leave column dropdown at "Select Column"
5. Try to enter a value
6. Verify the value field is disabled
7. Verify the "Apply" button is disabled

#### Test 2.9.5: Hide All Columns
1. Navigate to `http://127.0.0.1:5000/assets`
2. Expand "Columns" section
3. Uncheck ALL column checkboxes
4. Click "Apply"
5. Verify the table shows a message "All columns are hidden"
6. Verify a helpful message appears: "Use the Columns panel in the sidebar to show columns"

#### Test 2.9.6: Very Long Filter Value
1. Navigate to `http://127.0.0.1:5000/assets`
2. Expand "Filters" section
3. Add filter with a very long value (500+ characters)
4. Click "Apply"
5. Verify the filter is applied without errors
6. Verify the UI handles the long value gracefully (truncation, scrolling, etc.)

#### Test 2.9.7: Special Characters in Search
1. Navigate to `http://127.0.0.1:5000/assets`
2. Type special characters in global search: `!@#$%^&*()`
3. Press Enter
4. Verify the search executes without JavaScript errors
5. Verify appropriate results or "No results found" message

#### Test 2.9.8: Rapid Filter Changes
1. Navigate to `http://127.0.0.1:5000/assets`
2. Add a filter and click "Apply"
3. Immediately change the filter value
4. Click "Apply" again very quickly
5. Repeat 5 times rapidly
6. Verify the table updates correctly without errors
7. Verify no duplicate requests are made (check network tab)

## 3. Evidence Requirements
For every PR or task involving table features, you must provide:
1. **Video Recording:** A continuous recording of the `browser_subagent` executing the above steps.
2. **Screenshots:** Key states (e.g., "View Saved", "Filter Applied", "All Columns Hidden").
3. **Console Logs:** Check browser console for any JavaScript errors during the process.
4. **Network Logs:** Verify API calls to `/api/table-config/` succeed (200 status).

## 4. Test Execution Guidelines
- Execute tests in the order listed
- If a test fails, document the failure with screenshot and error message
- Fix the issue before proceeding to the next test
- After fixing, re-run ALL previous tests to ensure no regression
- Mark each test as PASS or FAIL in your verification report

## 5. Troubleshooting
- If "Save" button doesn't work, check `table-sidebar.js` event listeners
- If views don't load, check network requests to `/api/table-config/...`
- If filters don't apply, check `table-sidebar.js` `applyAllFilters()` method
- If columns don't hide, check `table-render.js` `renderHeader()` method
- Ensure `localStorage` is not interfering (try clearing it before tests)
- Check browser console for JavaScript errors
- Verify the server is running and responding on the correct port
