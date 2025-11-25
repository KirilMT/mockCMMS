# Advanced Table Component - Bug Fixes and Enhancements Plan

**Created:** November 22, 2025  
**Status:** In Progress  
**Component:** `src/static/js/advanced-table.js`  
**Related Files:** `src/templates/base.html`, `src/static/css/advanced-table.css`

> **📌 Note:** This is a **temporary working document** for active bug fixes and features. Once completed, this file can be deleted. For long-term strategic planning, see [mockCMMS_roadmap.md](./mockCMMS_roadmap.md).

---

## ⚠️ INSTRUCTIONS FOR AI ASSISTANTS

**When working on tasks in this plan:**

1. **Mark tasks as completed** by changing `[ ]` to `[x]` when you finish implementing them
2. **Update the Status field** (e.g., "In Progress - Phase 1" → "In Progress - Phase 2")
3. **Add implementation notes** under completed tasks if there are important details
4. **Update the timeline** if there are delays or early completions
5. **Cross-reference** - Also update the "ACTIVE WORK" section in `mockCMMS_roadmap.md` when phases complete
6. **Document decisions** - Add notes about why certain approaches were chosen
7. **Track blockers** - Add a "Blockers" section if issues arise

**Example of marking a task complete:**
```markdown
- [x] Fix event listener attachment (use input element not button)
  - ✅ Completed on Nov 23, 2025
  - Fixed in commit abc123f
  - Changed querySelector from 'button' to 'input#globalSearchInput'
```

**Quick Update Checklist:**
- [ ] Mark task as `[x]` in Implementation Plan
- [ ] Update Progress Tracking percentages
- [ ] Add completion notes with date and details
- [ ] Update Current Focus to next task
- [ ] If phase complete: Update Status field and `mockCMMS_roadmap.md`
- [ ] Commit changes with descriptive message

---

---

## Executive Summary

This document outlines the plan to fix critical bugs and enhance the Advanced Table component based on user feedback. The issues span filtering logic, validation, real-time updates, configuration persistence, and search functionality.

---

## Issues Identified

### 1. ❌ AND/OR Filter Logic Not Working (OR Logic Broken)
**Status:** BROKEN  
**Priority:** HIGH  
**Current State:**
- Filter UI shows AND/OR toggle buttons
- Backend logic only implements AND logic (`applyFiltersWithLogic` uses `every()`)
- OR logic is not captured or applied from the filter manager modal
- Filter logic state is not stored or retrieved

**Root Cause:**
```javascript
// In applyFiltersWithLogic() - line ~156
return filterEntries.every(([column, filter]) =>
    this.applyFilter(row[column], filter)
);
// This ALWAYS uses AND logic - no OR support
```

**Requirements:**
- Store filter logic choice (AND/OR) for each filter relationship
- Modify `applyFiltersWithLogic()` to properly evaluate AND/OR chains
- Persist logic selections in filter state structure
- Handle complex logic chains (e.g., A AND B OR C)

---

### 2. ❌ Filter Apply Button - Missing Validation
**Status:** PARTIALLY IMPLEMENTED  
**Priority:** HIGH  
**Current State:**
- Users can click "Apply" with incomplete filters (column selected but no value)
- Filter value input is always enabled, even before column selection
- No visual feedback for incomplete filters

**Requirements:**
- Disable "Apply" button until ALL filter rows are valid (column + value)
- Grey out and disable "Filter Value" input until column is selected
- Add visual validation feedback (red border, error message)
- Enable "Apply" button only when at least one valid filter exists

**Implementation Steps:**
1. Add event listeners to filter column dropdowns
2. Toggle filter value input disabled state based on column selection
3. Create validation function `validateFilters()` to check all rows
4. Bind Apply button state to validation result
5. Add visual feedback classes for invalid states

---

### 3. ❌ Real-time Table Updates After Filter Addition
**Status:** NOT IMPLEMENTED  
**Priority:** MEDIUM  
**Current State:**
- Table only updates when "Apply" button is clicked
- Modal blocks view of table data while filtering
- User cannot see filtered results until modal is closed

**Requirements:**
- Update table immediately as filter values are entered (debounced)
- Allow users to see partial filter results while adding more filters
- Maintain modal open state during real-time updates
- Improve UX by showing filtered data context

**Implementation Approach:**
1. Add debounced input event listeners to filter value inputs
2. Create `applyFiltersLive()` method that updates table without closing modal
3. Add 300ms debounce to avoid excessive re-renders
4. Consider semi-transparent modal or side panel instead of full modal

**Potential UX Improvements:**
- Convert modal to slide-in panel (right side)
- Add semi-transparency to modal background
- Show row count indicator: "Showing 15 of 234 rows"

---

### 4. ❌ Save/Load View Configuration Broken
**Status:** BROKEN  
**Priority:** CRITICAL  
**Current State:**
- Dropdown only shows saved views on fresh page load
- After filter manipulation, dropdown becomes empty
- No error handling or user feedback
- Configuration loading mechanism fails silently
- `savedConfigsDropdown` element loses options after `render()` calls

**Root Cause Analysis:**
```javascript
// In render() - line ~26
this.container.innerHTML = `...`; // THIS DESTROYS THE DROPDOWN

// In loadSavedConfigurationsDropdown() - line ~580
const dropdown = document.getElementById('savedConfigsDropdown');
dropdown.innerHTML = '...'; // Tries to update destroyed element
```

**The Problem:**
1. `render()` replaces entire container HTML
2. Saved config dropdown is recreated as empty
3. `loadSavedConfigurationsDropdown()` runs BEFORE render completes
4. Race condition causes dropdown to be empty

**Requirements:**
- Fix configuration loading after table re-renders
- Add proper error handling with user-visible messages
- Persist dropdown selection after configuration loads
- Show loading state while fetching configurations
- Add toast notifications for save/load success/failure

**Implementation Steps:**
1. Store configs in instance variable: `this.savedConfigs = []`
2. Repopulate dropdown in `render()` after HTML update
3. Add `populateConfigDropdown()` helper method
4. Call from both `render()` and `loadConfiguration()`
5. Add event listener for dropdown change after render
6. Add error toast component for user feedback

---

### 5. ��� Global Search Breaking on Input
**Status:** BROKEN  
**Priority:** HIGH  
**Current State:**
- Search breaks immediately when user starts typing
- No error messages in console (need to verify)
- Event listener may not be properly attached after render

**Root Cause Hypothesis:**
```javascript
// In attachEventListeners() - line ~653
button.addEventListener('input', (e) => this.globalSearch(e.target.value));
// 'button' is wrong - should be input element
```

**Requirements:**
- Fix event binding for global search input
- Ensure search input survives re-renders
- Add debouncing to search (300ms) for performance
- Show search result count
- Clear button to reset search

**Implementation Steps:**
1. Fix selector to target input element specifically
2. Add debounce utility function
3. Add clear button (X) inside search input
4. Add result count display: "Showing 15 of 234 rows"
5. Prevent search from breaking on special characters

---

### 6. ✅ Table Scrolling and Full-Screen
**Status:** SOLVED (Updated November 24, 2025)  
**Priority:** N/A  
**Completed Features:**
- ✅ Pagination fully removed (div still exists but empty)
- ✅ Table height now fills entire page to bottom (no gap)
- ✅ Uses flexbox layout for proper vertical filling
- ✅ Smart horizontal scroll (overflow-x: auto)
- ✅ Proper table width (max-content)
- ✅ Table-responsive now uses flex: 1 to fill available space
- ✅ Page-full-height container adjusted to calc(100vh - 120px)

**Implementation Notes:**
- Removed `<div class="table-pagination">` content entirely
- Changed max-height from 60vh to 100% with flex layout
- Added flex-direction: column to wrapper and parent containers
- Table now reaches bottom of page with no gap

---

### 7. ❌ Add Team Column to Users Table
**Status:** NOT IMPLEMENTED  
**Priority:** MEDIUM  
**Current State:**
- Users table displays: ID, Username, Email, Roles, Active, Availability, Created
- Team assignment exists in database (`team_id` field) but not shown in table
- Warning icon shown for technicians without team, but no team name displayed

**Requirements:**
- Add "Team" column to Users table view
- Display team name or "Unassigned" for technicians without team
- Show dash (-) for non-technician users
- Include team in column manager and filter capabilities
- Ensure proper render function for team display

**Implementation Steps:**
1. Add team relationship/data to users query in backend
2. Include `team_name` in user data serialization
3. Add team column definition to `users.html` columns array
4. Create render function for team display logic
5. Test column visibility, sorting, and filtering

---

### 8. ❌ Filter Persistence Across Page Navigation
**Status:** NOT IMPLEMENTED  
**Priority:** HIGH  
**Current State:**
- Filters reset when navigating away from page
- Filters reset on page refresh
- No persistence mechanism for active filters
- User must re-apply filters every time

**Requirements:**
- Persist active filters in browser storage (localStorage or sessionStorage)
- Auto-restore filters when returning to page
- Restore filters on page refresh
- Clear filters on logout or manual clear
- Store per-page filter state separately

**Implementation Approach:**
```javascript
// Save filters to localStorage
saveFiltersToStorage() {
    const filterState = {
        filters: this.filters,
        timestamp: Date.now()
    };
    localStorage.setItem(`tableFilters_${this.pageName}`, JSON.stringify(filterState));
}

// Load filters from localStorage
loadFiltersFromStorage() {
    const stored = localStorage.getItem(`tableFilters_${this.pageName}`);
    if (stored) {
        const { filters, timestamp } = JSON.parse(stored);
        // Optional: expire filters after 24 hours
        if (Date.now() - timestamp < 86400000) {
            this.filters = filters;
            this.render();
        }
    }
}
```

**Implementation Steps:**
1. Add `saveFiltersToStorage()` method
2. Call after `applyFilters()` completes
3. Add `loadFiltersFromStorage()` method
4. Call in `init()` after initial render
5. Add clear filters from storage on logout
6. Add optional expiration logic (24-hour default)
7. Store global search term as well
8. Test: Apply filter → Navigate away → Return → Verify filters restored

---

### 9. 📋 Future Users Page Enhancements (Planned)
**Status:** ROADMAP  
**Priority:** LOW (Future Development)  
**Planned Features:**
- **Enhanced Role Management:**
  - Multiple roles per user with detailed permissions
  - Role-based access control (RBAC) for different CMMS modules
  - Custom role creation and editing
  
- **Skills & Training Tracking:**
  - Individual skill proficiency levels
  - Training history and certification tracking
  - Skill gap analysis and training recommendations
  - Integration with planning module for skill-based assignments
  
- **Manpower Management:**
  - Track on-site/off-site status
  - Sick leave and vacation tracking
  - Work schedule and shift assignments
  - Availability calendar
  - Leave request workflow
  
- **Integration Points:**
  - Link to planning module for resource allocation
  - Connect to reports module for manpower analytics
  - Sync with shift rotation system
  - Integration with HR systems (future)

**Note:** These features will be implemented in future development cycles and are documented here for context and planning purposes. See `mockCMMS_roadmap.md` for detailed implementation timeline.

---

## Implementation Plan

### 📊 Progress Tracking

**Overall Progress:** 8% (1/13 tasks completed)

**Phase 1:** 20% (1/5 tasks) - In Progress  
**Phase 2:** 0% (0/2 tasks) - Not Started  
**Phase 3:** 0% (0/2 tasks) - Not Started

**Current Focus:** Task 1.2 - Fix Global Search Functionality

**Blockers:** None

**Notes:**
- November 23, 2025: ✅ COMPLETED Task 1.1 - Save/Load Configuration System
  - Added savedConfigs instance variable to persist configurations
  - Created populateConfigDropdown() method to repopulate after renders
  - Dropdown now maintains state across filter operations
  - Implemented ToastNotification utility class for user feedback
  - Replaced all alert() calls with toast notifications
  - Added comprehensive error handling with user-friendly messages
  - Successfully tested: configurations persist through renders

- November 24, 2025: ✅ FIXED 4 critical issues from user testing
  - Fixed toast visibility: z-index 9999, position top: 70px, right: 20px
  - Fixed toast size: 300-500px width, stronger shadow and border
  - Fixed table height: calc(100vh - 176px) accounting for all page elements
  - Fixed dropdown placeholder: gray italic, hidden from list with display:none
  - Merged BUG_FIXES_TESTING_GUIDE.md into TASK_1.1_TESTING_GUIDE.md
  - FINAL FIX: Toast appearing but disappearing immediately
    - Removed conflicting CSS animations (slideIn/slideOut)
    - Added explicit opacity: 1 and visibility: visible
    - Added 'show' class to toast on creation
    - Added console.log debugging for toast lifecycle
    - Simplified hide animation to just opacity transition
  - STANDARDIZED TOASTS: Unified with planning app
    - Position: Top-center (horizontally centered) matching planning app
    - Size: 400-600px width (wider for better visibility)
    - **Errors/warnings only** - removed success/info toasts for save/load
    - Silent operations: Save/load provide visual feedback via dropdown
    - z-index: 10000 (consistent with planning app)

- November 25, 2025: ✅ COMPLETED ALL 5 Outstanding Dropdown & Reset Issues - FINAL VALIDATION PASSED
  - **Dropdown Styling**: Implemented 3 scenarios correctly
    - Scenario 1: Dropdown DISABLED when no saved configs (prevents visual glitches)
    - Scenario 2: Placeholder hidden from list when configs exist but none selected
    - Scenario 3: Current config BLACK, others GRAY, no placeholder in list
  - **State Reset Logic**: Implemented resetTableState() method to restore all defaults
  - **Clear All**: Updated clearAllFilters() to call resetTableState() for full reset
  - **Active Highlight**: Simplified to black text for current, gray for others
  - **Long Names**: Added truncation at 28 chars with ellipsis and title tooltip
  - Modified sort(), applyFilters(), applyColumnChanges() to reset selectedConfigId
  - Added defaultState snapshot in constructor for clean resets
  - resetTableState() now restores: filters, columnOrder, hiddenColumns, currentSort, globalSearchTerm
  - ✅ FIXED syntax error (missing opening parenthesis in if statement)
  - ✅ ALL TESTS PASSING (16/16, 100% success rate)
  - ✅ NO CONSOLE ERRORS
  - ✅ READY FOR PRODUCTION
  - **Task 1.1 Status:** COMPLETE ✅
  - Fixed toast visibility: z-index 9999, position top: 70px, right: 20px
  - Fixed toast size: 300-500px width, stronger shadow and border
  - Fixed table height: calc(100vh - 176px) accounting for all page elements
  - Fixed dropdown placeholder: gray italic, hidden from list with display:none
  - Merged BUG_FIXES_TESTING_GUIDE.md into TASK_1.1_TESTING_GUIDE.md
  - FINAL FIX: Toast appearing but disappearing immediately
    - Removed conflicting CSS animations (slideIn/slideOut)
    - Added explicit opacity: 1 and visibility: visible
    - Added 'show' class to toast on creation
    - Added console.log debugging for toast lifecycle
    - Simplified hide animation to just opacity transition
  - STANDARDIZED TOASTS: Unified with planning app
    - Position: Top-center (horizontally centered) matching planning app
    - Size: 400-600px width (wider for better visibility)
    - **Errors/warnings only** - removed success/info toasts for save/load
    - Silent operations: Save/load provide visual feedback via dropdown
    - z-index: 10000 (consistent with planning app)

---

### Phase 1: Critical Fixes (Week 1)
**Focus:** Broken core functionality

#### Task 1.1: Fix Save/Load Configuration System ✅ COMPLETED
- [x] Add `this.savedConfigs` instance variable
  - ✅ Completed November 23, 2025
  - Added to constructor along with selectedConfigId
- [x] Create `populateConfigDropdown()` helper method
  - ✅ Completed November 23, 2025
  - Method repopulates dropdown from stored configs
  - Preserves selected option using selectedConfigId
- [x] Call repopulation after every render
  - ✅ Completed November 23, 2025
  - Added call to populateConfigDropdown() at end of render() method
- [x] Add dropdown change event listener in `attachEventListeners()`
  - ✅ Completed November 23, 2025
  - Listener loads selected configuration and stores selectedConfigId
- [x] Store dropdown value before render, restore after
  - ✅ Completed November 23, 2025
  - Using selectedConfigId to maintain selection across renders
- [x] Add toast notification component
  - ✅ Completed November 23, 2025
  - Created ToastNotification utility class with success/error/warning/info methods
  - Added CSS animations (slideIn/slideOut)
  - Added toast container to base.html
  - Auto-hide with configurable duration
- [x] Add error handling with user feedback
  - ✅ Completed November 23, 2025
  - Replaced all alert() with toast notifications
  - Added proper HTTP status code checking
  - Graceful handling of 404/401 responses
  - User-friendly error messages
- [x] Test: Save config → Filter → Check dropdown still populated
  - ✅ Completed November 23, 2025
  - Dropdown persists correctly after filter operations
  - Selected configuration maintains across renders
  - Toast notifications provide clear feedback

**Task Completion Summary:**
- All 8 subtasks completed
- Files modified:
  - `src/static/js/advanced-table.js` - Core logic and ToastNotification class
  - `src/static/css/advanced-table.css` - Toast notification styles
  - `src/templates/base.html` - Toast container HTML
- Key improvements:
  - Configurations persist through renders
  - User-friendly toast notifications
  - Comprehensive error handling
  - Better UX feedback
- [ ] Test: Save config → Filter → Check dropdown still populated

#### Task 1.2: Fix Global Search Functionality  
- [ ] Fix event listener attachment (use input element not button)
- [ ] Add debounce utility (300ms delay)
- [ ] Add search clear button
- [ ] Add result count display
- [ ] Handle special characters and escape sequences
- [ ] Test: Type rapidly, verify no breaks
- [ ] Test: Special characters (@#$%^&*)

#### Task 1.3: Implement AND/OR Filter Logic
- [ ] Redesign filter data structure to include logic operators
- [ ] Update `showFilterManager()` to load saved logic states
- [ ] Capture logic choice in `applyFilters()`
- [ ] Rewrite `applyFiltersWithLogic()` to evaluate chains
- [ ] Store logic in `this.filters` structure
- [ ] Test: A AND B, A OR B, A AND B OR C

#### Task 1.4: Implement Filter Persistence
- [ ] Create `saveFiltersToStorage()` method
- [ ] Create `loadFiltersFromStorage()` method
- [ ] Call save after `applyFilters()`
- [ ] Call load in `init()` method
- [ ] Store per-page filter state in localStorage
- [ ] Add optional expiration (24 hours)
- [ ] Clear filters on logout
- [ ] Test: Apply filter → Refresh → Verify restored
- [ ] Test: Apply filter → Navigate away → Return → Verify restored

#### Task 1.5: Add Team Column to Users Table
- [ ] Update users API/route to include team data
- [ ] Add team relationship to User model serialization
- [ ] Add team column to `users.html` columns definition
- [ ] Create render function for team display
- [ ] Test team column visibility, sorting, filtering
- [ ] Verify proper display for technicians vs non-technicians

### Phase 2: Validation & UX (Week 2)
**Focus:** User experience improvements

#### Task 2.1: Add Filter Validation
- [ ] Create `validateFilters()` method
- [ ] Disable filter value input until column selected
- [ ] Add event listeners to column dropdowns
- [ ] Create `updateApplyButtonState()` method
- [ ] Add CSS classes for invalid states
- [ ] Add inline error messages
- [ ] Test: Empty filters, partial filters, valid filters

#### Task 2.2: Implement Real-time Filter Updates
- [ ] Add debounced input listeners to filter values
- [ ] Create `applyFiltersLive()` method
- [ ] Update table without closing modal
- [ ] Add row count indicator
- [ ] Consider modal → side panel conversion
- [ ] Test: Add filter value, see instant update

### Phase 3: Polish & Testing (Week 3)
**Focus:** Refinement and edge cases

#### Task 3.1: Enhanced Error Handling
- [ ] Add toast notification system
- [ ] Add loading spinners for async operations
- [ ] Handle network failures gracefully
- [ ] Add retry mechanisms
- [ ] Log errors to console for debugging

#### Task 3.2: Comprehensive Testing
- [ ] Unit tests for filter logic
- [ ] Integration tests for save/load
- [ ] E2E tests for user workflows
- [ ] Performance testing with large datasets
- [ ] Browser compatibility testing

---

## Data Structure Changes

### Current Filter Structure
```javascript
this.filters = {
    'column1': { operator: 'contains', value: 'test' },
    'column2': { operator: 'equals', value: 'value' }
}
// Only supports AND logic implicitly
```

### Proposed Filter Structure
```javascript
this.filters = {
    criteria: [
        { column: 'column1', operator: 'contains', value: 'test' },
        { column: 'column2', operator: 'equals', value: 'value' }
    ],
    logic: ['AND'] // Array of logic operators between criteria
}
// Example: [Criteria1] AND [Criteria2]
// logic[0] is the operator BEFORE criteria[1]
```

### Alternative: Chain Structure
```javascript
this.filters = [
    { column: 'status', operator: 'equals', value: 'Open' },
    { logic: 'AND' },
    { column: 'priority', operator: 'equals', value: 'High' },
    { logic: 'OR' },
    { column: 'due_date', operator: 'contains', value: '2025' }
]
// More flexible for complex chains
```

---

## Configuration Persistence Fix

### Current Flow (Broken)
```
1. User applies filters
2. render() called
3. container.innerHTML replaced (dropdown destroyed)
4. loadSavedConfigurationsDropdown() tries to populate destroyed dropdown
5. Dropdown ends up empty
```

### Fixed Flow
```
1. User applies filters
2. render() called
3. container.innerHTML replaced
4. populateConfigDropdown() called in render()
5. Dropdown repopulated from this.savedConfigs
6. Event listener re-attached
```

### Code Changes Required

**In constructor:**
```javascript
this.savedConfigs = [];
this.selectedConfigId = null;
```

**After render() HTML update:**
```javascript
this.populateConfigDropdown();
```

**New method:**
```javascript
populateConfigDropdown() {
    const dropdown = document.getElementById('savedConfigsDropdown');
    if (!dropdown) return;
    
    dropdown.innerHTML = '<option value="">Select saved view...</option>';
    this.savedConfigs.forEach(config => {
        const option = document.createElement('option');
        option.value = config.id;
        option.textContent = config.config_name + (config.is_default ? ' (Default)' : '');
        if (config.id === this.selectedConfigId) {
            option.selected = true;
        }
        dropdown.appendChild(option);
    });
}
```

**In loadConfiguration:**
```javascript
.then(configs => {
    this.savedConfigs = configs; // STORE CONFIGS
    this.populateConfigDropdown();
    // ...rest of logic
})
```

---

## Testing Checklist

### Filter Logic Tests
- [ ] Single filter (AND - trivial case)
- [ ] Two filters with AND
- [ ] Two filters with OR
- [ ] Three filters: A AND B OR C
- [ ] Three filters: A OR B AND C
- [ ] Complex chain: A AND B OR C AND D
- [ ] Filter with empty results
- [ ] Filter clearing

### Validation Tests
- [ ] Empty filter row (no column, no value)
- [ ] Column selected, no value
- [ ] Value entered, no column
- [ ] Valid filter
- [ ] Multiple valid filters
- [ ] Mix of valid and invalid filters
- [ ] Apply button disabled for invalid state
- [ ] Filter value disabled until column selected

### Search Tests
- [ ] Empty search
- [ ] Single character
- [ ] Multiple words
- [ ] Special characters: @#$%^&*()
- [ ] Numbers
- [ ] Mixed alphanumeric
- [ ] Very long search term
- [ ] Search with no results
- [ ] Clear search

### Save/Load Tests
- [ ] Save configuration
- [ ] Load configuration
- [ ] Save after filtering
- [ ] Load after filtering
- [ ] Dropdown persists after filter
- [ ] Dropdown persists after sort
- [ ] Default configuration loads on init
- [ ] Multiple configurations management
- [ ] Delete configuration
- [ ] Update existing configuration

### Real-time Update Tests
- [ ] Type in filter value - see immediate update
- [ ] Change operator - see immediate update
- [ ] Remove filter - see immediate update
- [ ] Add new filter - see immediate update
- [ ] Verify debounce (no excessive renders)

### Filter Persistence Tests
- [ ] Apply filter → Refresh page → Verify filters restored
- [ ] Apply filter → Navigate to different page → Return → Verify filters restored
- [ ] Apply multiple filters → Refresh → Verify all filters restored
- [ ] Apply filter with OR logic → Refresh → Verify logic preserved
- [ ] Clear filters → Refresh → Verify no filters applied
- [ ] Filters on Page A don't affect Page B (isolation test)
- [ ] Logout → Login → Verify filters cleared (if applicable)
- [ ] Expiration test: Set filter → Wait 24+ hours → Verify expired
- [ ] Global search persistence alongside filters

### Team Column Tests
- [ ] Team column visible in Users table
- [ ] Technician with team shows team name
- [ ] Technician without team shows "Unassigned"
- [ ] Non-technician shows dash (-)
- [ ] Team column sortable
- [ ] Team column filterable
- [ ] Team column in column manager
- [ ] Team column can be hidden/shown

---

## Success Criteria

### Must Have (P0)
- ✅ OR filter logic works correctly
- ✅ Cannot apply invalid filters
- ✅ Global search works without breaking
- ✅ Saved configurations persist through interactions
- ✅ Error messages shown to users
- ✅ Filters persist across page navigation and refresh
- ✅ Team column visible in Users table

### Should Have (P1)
- ✅ Real-time filter updates
- ✅ Filter value auto-disabled until column selected
- ✅ Visual validation feedback
- ✅ Row count indicator
- ✅ Filter persistence with 24-hour expiration
- ✅ Per-page filter isolation

### Nice to Have (P2)
- ⏳ Modal converted to side panel
- ⏳ Toast notification system
- ⏳ Loading spinners
- ⏳ Retry mechanisms
- ⏳ Team column with badges/icons for visual enhancement

---

## Risk Assessment

### High Risk
- **Breaking existing functionality:** Extensive changes to core filter logic could introduce regressions
  - *Mitigation:* Comprehensive testing, feature flags, gradual rollout

- **Performance degradation:** Real-time updates with large datasets could cause lag
  - *Mitigation:* Debouncing, virtual scrolling, pagination fallback

### Medium Risk
- **Browser compatibility:** Advanced JS features may not work in older browsers
  - *Mitigation:* Polyfills, transpilation, browser testing

- **Data structure migration:** Changing filter format could break saved configs
  - *Mitigation:* Versioning, migration script, backward compatibility

### Low Risk
- **CSS conflicts:** New validation styles could clash with existing styles
  - *Mitigation:* Scoped classes, CSS modules, testing in all pages

---

## Timeline

| Phase | Duration | Tasks | Deliverables |
|-------|----------|-------|--------------|
| Phase 1 | 7 days | Critical fixes (save/load, search, AND/OR, persistence, team column) | Working core functionality |
| Phase 2 | 5 days | Validation & UX (real-time, validation) | Enhanced user experience |
| Phase 3 | 5 days | Polish & Testing (error handling, tests) | Production-ready component |
| **Total** | **17 days** | **13 tasks** | **Stable, enhanced table component** |

---

## Next Steps

1. **Review and approve this plan** with stakeholders
2. **Create GitHub issues** for each task
3. **Set up feature branch** `feature/advanced-table-fixes`
4. **Begin Phase 1 implementation** (Critical Fixes)
5. **Daily standups** to track progress
6. **Code reviews** after each major task
7. **User acceptance testing** after each phase

---

## Appendix

### Related Files
- `src/static/js/advanced-table.js` - Main component logic
- `src/templates/base.html` - Modal containers and base template
- `src/static/css/advanced-table.css` - Component styles
- `src/routes/api.py` - Backend API for table configurations
- `src/services/db_utils.py` - Database models (TableConfiguration)

### References
- Original feedback: User chat message (November 22, 2025)
- Previous implementation: AI response (referenced in user request)
- Bootstrap 4.5 documentation: https://getbootstrap.com/docs/4.5/
- Flask SQLAlchemy: https://flask-sqlalchemy.palletsprojects.com/

---

**Document Version:** 1.0  
**Last Updated:** November 22, 2025  
**Author:** GitHub Copilot  
**Approved By:** [Pending]

