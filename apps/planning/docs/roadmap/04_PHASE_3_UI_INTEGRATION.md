# Phase 3 – Planning Page UI & Integration

**Goal:** Create the Planning page within `mockCMMS` that embeds `planning` functionality and presents results clearly.

**Status:** 🔄 **IN PROGRESS** (Started November 18, 2025)

**Implementation Summary:**

- ✅ Planning routes added to `planning` blueprint
- ✅ Main planning index page created
- ✅ Schedule view with mode selection (shift-break/weekend)
- ✅ Table view with advanced features (sorting, filtering, column management)
- ✅ Planning algorithm execution and result persistence
- ⏳ Gantt chart visualization (basic structure, needs full implementation)
- ⏳ Role-based capabilities (basic structure, needs full implementation)
- ⏳ Export options (needs implementation)

**⚠️ Known Issues from User Feedback (November 18-19, 2025):**

1. ✅ **RESOLVED:** Advanced table features broken after render - Fixed with event listener re-attachment
2. ✅ **RESOLVED:** Schedule terminology confusion - User wants "Schedule" renamed to "MaintenancePlan" (moved to Phase 4.1)
3. 🔄 **IN PROGRESS:** Team size assignment logic incomplete - Planning engine assigns single techs, not teams properly
4. 🔄 **IN PROGRESS:** Multi-technician grouping logic missing - Complex logic for forming teams based on skills
5. ⏳ **PENDING:** Gantt chart implementation incomplete - Basic route exists but visualization not built
6. ⏳ **PENDING:** Role-based UI not implemented - All users see same interface
7. ⏳ **PENDING:** Export options not implemented

**🎯 Current Focus Areas:**

1. **Team Assignment Logic Enhancement** - Improve algorithm to properly form multi-technician teams
2. **Gantt Chart Implementation** - Full visualization with timeline and resource allocation
3. **Role-Based Views** - Different interfaces for Planner/Supervisor/Technician
4. **Export Functionality** - PDF and Excel export for plans

- [x] 5.1. Planning page routing & layout
  - [x] 5.1.1. Add a **Planning** route to the main app (e.g., `src/routes/main.py` or a dedicated blueprint). ✅ Added to `planning.py` blueprint
  - [x] 5.1.2. Integrate `planning` blueprint/routes into the main app under `/planning` (renamed appropriately). ✅ Routes at `/planning-manager/planning`
  - [x] 5.1.3. Create a main Planning template that adheres to the existing `base.html` structure (navigation, styling). ✅ Created `planning/index.html`

- [x] 5.2. Planning page modes (Shift Break vs Weekend)
  - [x] 5.2.1. Add UI controls (e.g., two buttons or tabs) for **Shift Break Planning** and **Weekend Planning** modes. ✅ Mode selection radio buttons implemented
  - [x] 5.2.2. Ensure mode selection triggers the correct backend planning logic and refreshes the views. ✅ Mode parameter passed to planning engine

- [x] 5.3. Table view implementation
  - [x] 5.3.1. Build a table view for planned assignments using the same advanced table patterns as Assets/MOs/Spare Parts. ✅ Advanced table with full customization (sorting, filtering, column management, export)
  - [x] 5.3.2. Support filtering, sorting, and search on key fields (asset, technician, shift, status, priority, etc.). ✅ All advanced features working after November 19 fixes
  - [x] 5.3.3. Add visual indicators for tasks that could not be planned (e.g., missing parts, no matching skills). ✅ Color-coded status badges (Planned/Unplanned)
  - [x] 5.3.4. **BUG FIX:** Advanced table modals not appearing - Fixed by moving modals to base.html ✅ November 19, 2025
  - [x] 5.3.5. **BUG FIX:** Event listeners not persisting after table re-render - Fixed with attachEventListeners() in render() ✅ November 19, 2025

- [x] 5.4. Gantt chart view (critical - COMPLETE) ✅ **November 19, 2025**
  - **⚠️ IMPORTANT DISCREPANCY:** Documentation shows Frappe Gantt implementation, but actual code uses custom implementation
  - **What Actually Exists:**
    - ✅ Custom Gantt chart implementation in `planning-gantt-custom.js` (400+ lines)
    - ✅ Custom CSS in `planning-gantt-custom.css` matching original technician dashboard
    - ✅ Technician-row based layout (fixed left pane + scrollable timeline)
    - ✅ Task bars showing Maintenance Order IDs (not sequential task numbers)
    - ✅ Color-coded by priority (Red, Orange, Yellow, Green)
    - ✅ Click task → highlight corresponding table row
    - ✅ Column and row hover highlighting
    - ✅ Dynamic height calculation based on technician count
    - ❌ NO Frappe Gantt library (despite documentation claiming it)
  - **Documentation Mismatch:**
    - `PHASE3_GANTT_IMPLEMENTATION_REPORT.md` describes Frappe Gantt integration
    - Actual implementation is custom code without external library
    - Report may have been written as plan, not as-built documentation
  - [x] 5.4.1. Choose a Gantt visualization strategy (e.g., client-side JS library or custom timeline implementation). ✅ **Custom implementation selected (not Frappe Gantt)**
  - [x] 5.4.2. Design JSON/API data shape for Gantt data (tasks, start/end times, assigned technicians, status). ✅ `/planning/schedules/<id>/gantt-data` endpoint exists
  - [x] 5.4.3. Implement the Gantt chart view side-by-side or as a separate tab from the table view. ✅ **COMPLETE** - Custom Gantt matching original dashboard
  - [x] 5.4.4. Ensure interactions (hover, click, filtering) stay consistent with the table view. ✅ Click task → scroll to table row implemented
  - [x] 5.4.5. **NEW:** Add resource allocation view showing technician utilization over time ⚠️ **NOT IMPLEMENTED** (documentation claims it exists but not in custom version)
  - [ ] 5.4.6. **NEW:** Add drag-and-drop capability to reschedule tasks (Supervisor/Planner only) ⏳ **NOT IMPLEMENTED** - Future enhancement

  **Actual Implementation Details (Custom Gantt):**
  - Created `planning-gantt-custom.js` - Full custom Gantt implementation
  - Created `planning-gantt-custom.css` - Custom styling matching original dashboard
  - Features implemented:
    - Fixed left pane with technician names (scrolls with rows)
    - Scrollable right pane with time grid (12-hour view, 30-min columns)
    - Task bars positioned by planned start/end times
    - MO ID displayed on task bars (e.g., "MO-123")
    - Priority color coding (Critical=Red, High=Orange, Medium=Yellow, Low=Green)
    - Click task → scroll to and highlight corresponding table row
    - Time column headers (08:00, 08:30, 09:00, etc.)
    - Alternating column backgrounds for readability
    - Dynamic height based on technician count
    - No external dependencies (pure vanilla JavaScript)

  **Known Issues:**
  - ⚠️ Column hover highlighting not working (attempted fix in November 19, still broken)
  - ⚠️ No resource utilization cards (documentation claims they exist)
  - ⚠️ No view mode controls (Quarter Day, Half Day, Day)
  - ℹ️ Custom implementation gives more control but requires more maintenance

- [ ] 5.5. Role-based capabilities (NEEDS IMPLEMENTATION)
  - [ ] 5.5.1. Define roles: Technician, Supervisor, Maintenance Planner (reusing existing auth/roles where possible).
  - [ ] 5.5.2. For Technicians: read-only access with filters and search to see assigned tasks.
  - [ ] 5.5.3. For Supervisors: ability to adjust assignments on the fly, including adding tasks similar to the old "Additional Task Creation" modal.
  - [ ] 5.5.4. For Maintenance Planners: ability to trigger planning runs, lock/unlock schedules, and manage planning parameters.
  - [ ] 5.5.5. **NEW:** Add permission checks in routes to enforce role-based access

- [ ] 5.6. Export options (NEEDS IMPLEMENTATION)
  - [ ] 5.6.1. Design export formats (e.g., PDF and Excel) for the current plan.
  - [ ] 5.6.2. Implement export endpoints that generate downloads from the current `PlanningResult`.
  - [ ] 5.6.3. Ensure exports integrate with or reuse patterns from the `reporting` app where appropriate.
  - [ ] 5.6.4. **NEW:** Add email notification option to send plans to technicians automatically

- [ ] 5.6.5. **Configurable Shift Times** 🆕 **USER REQUEST - November 20, 2025**
  - **Requirement:** Make shift-break and weekend times configurable, not hardcoded
  - **Current State:**
    - Shift-break: Hardcoded 2-hour window (10:00-12:00)
    - Weekend: Hardcoded 12-hour window (08:00-20:00)
  - **Needed:**
    - [ ] **Shift-Break Configuration:**
      - Duration: Configurable (default 30 minutes, user wants 30min not 2 hours)
      - Start time: Configurable (e.g., 10:00, 14:00, etc.)
      - Break types: Morning break, afternoon break, lunch break
    - [ ] **Weekend Configuration (Complex):**
      - Friday: Half-shift (e.g., 08:00-14:00, 6 hours)
      - Saturday: Full shift (e.g., 08:00-20:00, 12 hours)
      - Sunday: Half-shift (e.g., 08:00-14:00, 6 hours)
      - User wants day-specific shift configurations
    - [ ] **UI Requirements:**
      - Configuration page for Maintenance Planner role
      - Set shift times per day of week
      - Save configurations to database
      - Apply configurations in planning engine
    - [ ] **Database Schema:**
      - New table: ShiftConfiguration
      - Fields: day_of_week, shift_type (morning/afternoon/weekend), start_time, end_time, duration_minutes
      - Link to Schedule or global configuration
  - **Priority:** 🟡 Medium - Important for real-world usage
  - **Location:** Planning settings/configuration page

- [x] 5.6.6. **Weekend Day/Shift Subdivision** 🆕 🔴 **CRITICAL - November 20, 2025**
  - **Requirement:** Weekend planning must be divided by days and shifts, not continuous
  - **Current Problem:** ~~Weekend shown as one continuous timeline (Friday-Sunday)~~ ✅ FIXED
  - **Status:** ✅ **COMPLETE** (November 21, 2025) - Core logic and visualization implemented.
  - **Needed:**
    - [x] **Day Subdivision:** ✅ COMPLETE
      - Friday, Saturday, Sunday shown separately in Gantt chart
      - Planning window: Friday 22:00 - Sunday 22:00
      - Day-specific shift labels implemented
    - [x] **Shift Subdivision (per day):** ✅ COMPLETE
      - Production shifts: Morning (06-14), Afternoon (14-22), Night (22-06)
      - Maintenance shifts: Early (06-18), Late (18-06)
      - Shift intersection logic implemented
      - Gantt chart shows shift separators
    - [ ] **Different Technician Teams per Shift:** ⚠️ NOT IMPLEMENTED
      - **CRITICAL MISSING FEATURE**
      - Each shift needs assigned technician team
      - Planning must respect shift team assignments
      - Cannot assign task to technician not in that shift's team
      - **Database Changes Needed:**
        - Add `ShiftTeam` model
        - Link `Technician` to `ShiftTeam`
        - Link `ShiftTeam` to shift pattern
      - **Planning Engine Changes:**
        - Filter technicians by shift team when assigning
        - Only consider technicians working in current shift
    - [x] **Gantt Chart Updates:** ✅ COMPLETE
      - Show day separators (Friday | Saturday | Sunday)
      - Show shift separators within each day
      - 3-level header: Day → Shift → Hour
      - ~~Different technician lists per shift (filtering)~~ ⚠️ Pending team implementation
      - **Nov 21 Update:** Fixed horizontal scrolling, header layout, and visual alignment.
    - [x] **Planning Engine Updates:** ✅ COMPLETE
      - Filter tasks by day/shift ✅
      - ~~Assign technicians from correct shift team~~ ⚠️ Pending team implementation
      - Respect shift time boundaries ✅
      - Handle multi-day tasks (if allowed) ✅
  - **What Was Completed (Nov 20, 2025):**
    - Configuration redesign: `shift_patterns` + `planning_windows`
    - Shift intersection logic in backend
    - Gantt visualization with day/shift/hour headers
    - Overnight shift support
    - Browser verified: Tasks assigned within maintenance window
  - **What Still Needs Work:**
    - Shift team database model
    - Technician-to-shift-team assignment
    - Planning engine filtering by shift team
  - **Files Modified:**
    - `apps/planning/config/config.example.json`
    - `apps/planning/src/services/planning_engine.py`
    - `apps/planning/src/static/js/planning-gantt-custom.js`
    - `apps/planning/tests/test_weekend_planning.py`
  - **Priority:** 🔴 **CRITICAL** - Core business logic requirement
  - **Complexity:** HIGH - Major architectural change
  - **Impact:** Planning engine, Gantt chart, database schema, UI
  - **Time Spent:** 1 day (November 20, 2025)
  - **Estimated Remaining:** 1-2 days for shift team implementation

- [x] 5.6.6.1. **Overnight/Cross-Midnight Shift Support** ✅ **COMPLETE - November 20, 2025**
  - **Status:** ✅ IMPLEMENTED & VERIFIED (Browser Testing)
  - **Implementation Details:**
    - [x] **Time Calculation:**
      - Detects when `end_time <= start_time` (indicates overnight shift)
      - Calculates duration correctly: 22:00-06:00 = 8 hours ✅
      - Adjusts end date to next day for overnight shifts
    - [x] **Gantt Chart Display:**
      - Overnight shifts display correctly across day boundaries
      - Time labels handle day wrap (22:00, 23:00, 00:00, 01:00...)
      - `addMinutesWithWrap()` utility function implemented
    - [x] **Planning Engine:**
      - `ShiftDefinition` dataclass includes `is_overnight` flag
      - Task start/end times calculated correctly for overnight shifts
      - Shift intersection logic handles overnight shifts properly
    - [x] **Configuration:**
      - Supported in `config.json` shift definitions
      - Overnight shifts defined with `end_time < start_time`
      - Example: `{"name": "late", "start_time": "18:00", "end_time": "06:00"}`
  - **Verification:** ✅ Browser tested
    - Friday "Maint Late" (22:00-06:00) displays correctly across midnight
    - Saturday "Maint Late" (18:00-06:00) displays correctly
    - Duration calculations verified (8h and 12h shifts)
  - **Code Reused from Legacy:** ✅ `addMinutesWithWrap()` function adapted
  - **Files Modified:** Same as 5.6.6
  - **Priority:** 🔴 **CRITICAL** - Required for real-world shift patterns
  - **Complexity:** MEDIUM - Datetime handling complexity
  - **Actual Time:** Included in 5.6.6 (1 day total)

- [ ] 5.6.7. **Enhanced Dummy Data Generation** 🆕 **USER REQUEST - November 20, 2025**
  - **Current State:** 20 MOs in dummy_data.json, hardcoded values
  - **Problems:**
    - File too long, hard to maintain
    - Same data every time
    - Limited testing scenarios
  - **Requirements:**
    - [ ] **Quantity:** 100-200 MOs instead of 20
    - [ ] **Randomization:**
      - Random task names/descriptions (realistic, not gibberish)
      - Random order types (PM, REP, Corrective, Project)
      - Random priorities (Critical, High, Medium, Low)
      - Random frequencies (Daily, Weekly, Monthly, etc.)
      - Random durations (realistic range: 15-480 minutes)
      - Random technician counts (1-5)
      - Random skill requirements (1-3 skills per task)
      - Empty/null fields where allowed (test validation)
    - [ ] **Implementation Options:**
      - Option 1: Python script to generate JSON (run before seeding)
      - Option 2: Faker library for realistic names/descriptions
      - Option 3: Seed script generates data programmatically (not from JSON)
    - [ ] **Benefits:**
      - Better testing (edge cases, large datasets)
      - More realistic demonstrations
      - Performance testing
      - Different data each run (random seed)
  - **Priority:** 🟡 Medium - Development quality of life
  - **Recommended Approach:** Use Faker + programmatic generation in seed script

- [✅] 5.7. **Planning Algorithm Enhancements** (USER FEEDBACK - HIGH PRIORITY) 🆕 **COMPLETE - November 19, 2025**
  - [x] 5.7.1. **Team Formation Logic:** Enhance planning engine to properly form multi-technician teams ✅ **COMPLETE**
    - ✅ Implemented `_select_best_team()` with multi-factor scoring (workload, skill diversity, proficiency)
    - ✅ Implemented `_balance_team_experience()` to mix senior and junior technicians
    - ✅ Added team compatibility checks and skill coverage validation
    - ✅ Technicians grouped into teams with complementary skills
    - **Algorithm Features:**
      - 40% weight on workload balancing (fair distribution)
      - 30% weight on skill diversity (number of unique skills)
      - 30% weight on skill level (average proficiency)
      - Automatic experience balancing (mix of senior/junior for teams of 2+)
      - Ensures at least one highly skilled tech (level >= 4) on multi-person teams
  - [x] 5.7.2. **Complex Grouping Logic:** Implement advanced team optimization ✅ **COMPLETE**
    - ✅ `_find_team_with_skill_coverage()` - Finds teams where members collectively have all required skills
    - ✅ `_team_has_all_skills()` - Validates team has complete skill coverage
    - ✅ Greedy algorithm to maximize skill coverage across team members
    - ✅ Fallback to individual matching if team formation fails
    - **Implemented Strategy:**
      - For multi-skill tasks: Team members don't each need ALL skills, but collectively must cover them
      - Iteratively selects technicians to maximize uncovered skill coverage
      - Balances experienced vs. junior technicians
      - Considers skill level proficiency in team selection
  - [ ] 5.7.3. **Duration Calculation Refinement:** Improve task duration estimates ⏳ **NEXT PRIORITY**
    - Current: Basic efficiency gain model (10% per extra tech, max 30%)
    - Needed: Factor in team composition (experienced teams = faster completion)
    - Needed: Consider task complexity and asset location
    - Needed: Historical data analysis for better estimates
  - [ ] 5.7.4. **Workload Balancing:** Enhance fairness in task distribution ⏳ **NEXT PRIORITY**
    - Current: Considers available time (40% weight in scoring)
    - Needed: Consider task difficulty based on technician expertise
    - Needed: Track recent workload history to avoid overloading same technicians
  - [ ] 5.7.5. **Testing:** Add comprehensive tests for team assignment scenarios ⏳ **NEXT**
    - [ ] Test multi-technician team formation
    - [ ] Test skill coverage validation
    - [ ] Test experience balancing
    - [ ] Test team optimization scoring

- [ ] 5.8. **Testing & Validation**
  - [ ] 5.8.1. **API Endpoint Testing:** Write tests for all new API endpoints that serve data to the UI (e.g., fetching plan data, Gantt chart data) to ensure they are secure and return the correct data shape.
  - [ ] 5.8.2. **Component-Level UI Testing:** For complex UI components like the Gantt chart, use a framework (like Playwright or Selenium) to test interactions (e.g., filtering, hovering) in isolation.
  - [ ] 5.8.3. **End-to-End (E2E) User Flow Testing:** Create E2E tests that simulate user journeys:
    - A Planner logs in, generates a weekend plan, and verifies the result.
    - A Technician logs in and views their assigned tasks on the Gantt chart.
    - A Supervisor logs in and adds an ad-hoc task to the current shift plan.
  - [ ] 5.8.4. **User Acceptance Testing (UAT):** Conduct manual UAT sessions with stakeholders representing each role (Planner, Supervisor, Technician) to gather feedback on usability and correctness.
  - [ ] 5.8.5. **Regression Testing:** Verify that all Phase 1 and Phase 2 tests still pass after UI changes

- [ ] 5.9. **UI Refinement & Bug Fixes** 🆕 ⏳ **IN PROGRESS - November 19-20, 2025**
  - [x] 5.9.1. **Weekend Planning Investigation** ✅ **COMPLETE - November 20, 2025**
    - **Issue:** Single-day weekend schedule assigns no tasks + Warning messages not visible
    - **Status:** ✅ **RESOLVED** - Root cause found and fixed
    - **Root Cause Identified:**
      - Daily PMs were being filtered out by weekend mode
      - User had 3 PM tasks with frequency="Daily"
      - Weekend filter only allowed Weekly/Monthly/Bi-weekly/Quarterly
      - Result: Only 5/8 tasks were eligible for planning
    - **Fixes Applied (November 20, 2025):**
      - [x] ✅ **Fixed Daily PM filtering** - Now includes 'daily' in allowed frequencies (Option 1)
      - [x] ✅ **Fixed toast position** - Centered at top of window, above navbar (user request)
      - [x] ✅ **Fixed warning message disappearing** - Messages persist after page reload
      - [x] ✅ **Removed confirmation dialog** - No more "Are you sure?" popup
      - [x] ✅ **Removed success alert** - No more popup with stats
      - [x] ✅ **Added success toast** - Brief message at top-center of screen
      - [x] ✅ **Added loading state** - Button shows spinner while planning runs
      - [x] ✅ **Improved error handling** - Errors display on page, not in popups
    - **Code Changes:**
      - File: `planning_engine.py` line ~250
      - Before: `if mo.frequency.lower() in ['weekly', 'monthly', 'bi-weekly', 'quarterly']:`
      - After: `if mo.frequency.lower() in ['daily', 'weekly', 'monthly', 'bi-weekly', 'quarterly']:`
      - Impact: Daily PMs now included in weekend planning
    - **User Experience Improvements:**
      - Before: Click → Confirm → Run → Alert → Reload → Warnings lost
      - After: Click → Loading state → Reload → Warnings visible + Toast at top
      - Toast: Top-center of window (20px from top, above navbar, z-index 10000)
      - No interrupting popups, clean modern UX
    - **Result:** Weekend planning now works for single-day and multi-day schedules
    - **Investigation Doc:** `docs/WEEKEND_PLANNING_BUG_INVESTIGATION.md`

  - [ ] 5.9.2. **Advanced Table Height Issues** 🟡 **MEDIUM PRIORITY - November 20, 2025**
    - **Issue:** Table height works correctly in schedules page, but still has problems in Assets, MOs, Users, Spare Parts pages
    - **Current State:**
      - ✅ Planning table in schedules: Sizes naturally based on content
      - ⚠️ Other pages: Still not filling to bottom properly
    - **Attempted Fix (November 19):**
      ```css
      .page-full-height .advanced-table-wrapper {
        min-height: calc(100vh - 280px);
      }
      ```
    - **Status:** Partial fix - needs refinement
    - **Action Items:**
      - [ ] Investigate viewport height calculation on different pages
      - [ ] Check if header/navigation heights are consistent across pages
      - [ ] Consider different approaches:
        - Option 1: Adjust `calc()` formula per page type
        - Option 2: Use flexbox layout for main content area
        - Option 3: Use CSS Grid for better height control
      - [ ] Test across different screen sizes and browsers
    - **Affected Files:**
      - `src/static/css/advanced-table.css`
      - `src/templates/assets.html`
      - `src/templates/maintenance_orders.html`
      - `src/templates/spare_parts.html`
      - `src/templates/users.html`

  - [ ] 5.9.3. **Gantt Chart Column Hover Highlighting** 🔴 **HIGH PRIORITY - November 20, 2025**
    - **Issue:** Hover over time columns in Gantt chart does not highlight entire column
    - **Expected Behavior:** When hovering over any cell in a time column (e.g., 09:00), entire column should highlight in blue
    - **Current State:** Not working - column highlighting does not occur
    - **Location:** `apps/planning/src/static/js/planning-gantt-custom.js` - `addInteractivity()` method
    - **Attempted Fix (November 19):**
      ```javascript
      // Added data-col-index attribute approach
      const colIndex = cell.getAttribute("data-col-index");
      const allCells = this.container.querySelectorAll(
        `[data-col-index="${colIndex}"]`,
      );
      allCells.forEach((c) => {
        c.style.background = "#e3f2fd";
      });
      ```
    - **Status:** Not working as expected
    - **Possible Issues:**
      - Data attributes not being added correctly
      - CSS selector not matching cells
      - Event listeners not attaching properly
      - Grid structure preventing proper highlighting
    - **Action Items:**
      - [ ] Debug data-col-index attribute assignment
      - [ ] Verify event listeners are being attached to grid cells
      - [ ] Check if grid structure allows for column highlighting
      - [ ] Test hover behavior in browser developer tools
      - [ ] Consider alternative approaches:
        - Option 1: Use CSS classes instead of inline styles
        - Option 2: Use CSS `:hover` pseudo-class with adjacent sibling selectors
        - Option 3: Pre-calculate column cells and store references
      - [ ] Verify row highlighting works (should already be working)
    - **Testing:**
      - [ ] Hover over time column cell → entire column highlights
      - [ ] Move mouse away → column returns to normal background
      - [ ] Hover over row → row highlights (should already work)
      - [ ] Verify alternating column backgrounds are preserved

  - [ ] 5.9.4. **CSS/JS Consolidation Audit** 🔴 **HIGH PRIORITY - CODE QUALITY**
    - **Goal:** Ensure ALL styling in CSS files, ALL scripts in JS files - NO inline styles or scripts
    - **Rationale:**
      - Maintainability: One place to look for styles/scripts
      - Debugging: Clear separation of concerns
      - Performance: Browser can cache CSS/JS files
      - Standards: Professional coding practices
    - **Scope:** Check ENTIRE codebase (not just planning)
    - **Action Items:**
      - [ ] **HTML Audit:** Scan all `.html` files for inline `style=""` attributes
        - Location: `src/templates/*.html`
        - Location: `apps/planning/src/templates/**/*.html`
        - Location: `apps/reporting/src/templates/**/*.html`
        - Tool: Use grep/search for `style="`
        - **Fix:** Move all inline styles to appropriate CSS files
      - [ ] **JavaScript Audit:** Scan all `.html` files for inline `<script>` tags (except template data injection)
        - Allowed exceptions:
          - `<script>const data = {{ json_data|safe }};</script>` (template data injection)
          - Minimal initialization code that requires template variables
        - **Fix:** Extract all logic to `.js` files
        - **Fix:** Use data attributes for passing data to JS instead of inline scripts
      - [ ] **CSS Organization:** Ensure logical file structure
        - Main app: `src/static/css/`
        - planning: `apps/planning/src/static/css/`
        - Reporting: `apps/reporting/src/static/css/`
        - **Fix:** Create component-specific CSS files if needed
        - **Fix:** Add CSS comments documenting purpose of each file
      - [ ] **JS Organization:** Ensure logical file structure
        - Main app: `src/static/js/`
        - planning: `apps/planning/src/static/js/`
        - Reporting: `apps/reporting/src/static/js/`
        - **Fix:** Split monolithic JS files into modules
        - **Fix:** Use ES6 modules for better organization
      - [ ] **Documentation:** Create style guide documenting conventions
        - CSS naming conventions (BEM, or chosen methodology)
        - JS module structure
        - When inline code is acceptable vs. not
        - How to pass data from templates to JavaScript
    - **Testing:**
      - [ ] Verify all pages render correctly after consolidation
      - [ ] Check browser console for errors
      - [ ] Test all interactive features still work
      - [ ] Validate CSS loads correctly (check Network tab)
      - [ ] Validate JS loads correctly (check Network tab)
    - **Priority Files to Check:**
      - 🔴 High: `schedule_view.html`, `technician_dashboard.html`
      - 🟡 Medium: All planning templates, all main app templates
      - 🟢 Low: Admin/utility templates
    - **Success Criteria:**
      - Zero inline `style=""` attributes (except dynamic values set by JS)
      - Zero inline `<script>` blocks (except template data injection)
      - All CSS in `.css` files
      - All JS logic in `.js` files
      - Clear documentation of organization

- [ ] 5.10. **Gantt Chart Advanced Features** 🔴 **CRITICAL - BEFORE PHASE 4** (Based on Original Technician Dashboard)
  - **⚠️ IMPORTANT:** These features must be implemented BEFORE Phase 4 (Cleanup) because Phase 4 will delete the legacy technician dashboard code that serves as the reference implementation.
  - **Priority:** 🔴 **HIGH - NOT A FUTURE FEATURE** - Critical to implement while original dashboard is still available for reference
  - **Timeline:** Must complete before starting Phase 4 cleanup

  - [ ] 5.10.1. **Break Time Shading**
    - **Feature:** Gray-shaded columns for scheduled break times (e.g., lunch breaks, shift change)
    - **Benefits:** Visual clarity of available work time vs. break time
    - **Reference:** Original technician dashboard has break time visualization
    - **Implementation:**
      - Add break time configuration (start time, duration)
      - Calculate which time columns fall within break periods
      - Apply gray background CSS class to break columns
      - Add legend indicating break time shading
    - **Priority:** 🟡 Medium - Nice to have, improves readability

  - [ ] 5.10.2. **Current Time Indicator**
    - **Feature:** Red vertical line showing current time on Gantt chart
    - **Benefits:** Real-time awareness of schedule progress
    - **Reference:** Original dashboard shows current time marker
    - **Implementation:**
      - Calculate current time position as percentage of timeline
      - Render vertical red line at calculated position
      - Update position every minute (or on refresh)
      - Only show if current time falls within schedule date range
    - **Priority:** 🟡 Medium - Useful for active shift planning

  - [ ] 5.10.3. **Drag & Drop Task Reschedule** 🔴 **HIGH PRIORITY**
    - **Feature:** Drag task bars to different times or technicians to reschedule
    - **Benefits:** Quick manual adjustments to auto-generated plans
    - **Reference:** Original technician dashboard has drag & drop functionality
    - **Implementation:**
      - Make task bars draggable (HTML5 Drag & Drop API)
      - Implement drop zones (time slots and technician rows)
      - Validate drop target (technician skills, time availability)
      - Update task start/end times and assignment on drop
      - Show preview while dragging
      - Persist changes to database
    - **Priority:** 🔴 High - Matches original dashboard functionality, very useful
    - **Testing:**
      - [ ] Test drag within same technician (time change only)
      - [ ] Test drag to different technician (reassignment)
      - [ ] Test validation (prevent invalid drops)
      - [ ] Test conflict detection (overlapping tasks)

  - [ ] 5.10.4. **Enhanced Tooltip Popups**
    - **Feature:** Detailed task information on hover (similar to original dashboard)
    - **Benefits:** Quick access to task details without navigating away
    - **Current State:** Basic tooltip with task description and MO ID
    - **Reference:** Original dashboard has rich tooltips
    - **Enhanced Content:**
      - Task description and MO ID
      - Asset name and location
      - Required skills and assigned technicians
      - Estimated vs. actual duration
      - Priority and status
      - Required spare parts and availability
      - Any special notes or warnings
    - **Implementation:**
      - Create rich HTML tooltip component
      - Position tooltip near mouse cursor
      - Add smooth fade-in/fade-out transitions
      - Ensure tooltip stays within viewport bounds
    - **Priority:** 🟡 Medium - Improves user experience

  - [ ] 5.10.5. **Table-Gantt Synchronization** 🔴 **HIGH PRIORITY**
    - **Feature:** Bidirectional highlighting between table rows and Gantt bars
    - **Current State:** ✅ Click Gantt bar → highlights table row (implemented)
    - **Reference:** Original dashboard has full bidirectional sync
    - **Missing Functionality:**
      - Hover over table row → highlight corresponding Gantt bar(s)
      - Click table row → scroll Gantt to show task and highlight it
      - Maintain highlight sync during filtering/sorting
    - **Implementation:**
      - Add hover listeners to table rows
      - Add data-mo-id attributes to both table rows and Gantt bars
      - Implement highlight functions in both directions
      - Handle cases where multiple technicians assigned to same task
    - **Priority:** 🔴 High - Critical for usability, matches original dashboard
    - **Testing:**
      - [ ] Test table row hover → Gantt bar highlights
      - [ ] Test table row click → scrolls to Gantt bar
      - [ ] Test Gantt bar click → table row highlights (already works)
      - [ ] Test with multi-technician tasks
      - [ ] Test with filtered/sorted tables

  - [ ] 5.10.6. **View Mode Enhancements**
    - **Feature:** Additional view modes beyond current Day view
    - **Reference:** Original dashboard supports multiple time scales
    - **Modes to Add:**
      - Quarter Day (6 hours) - Good for shift-break planning
      - Half Day (12 hours) - Current default
      - Full Day (24 hours) - For weekend planning
      - Week View - Overview of entire week
    - **Implementation:**
      - Add view mode selector buttons
      - Adjust time column width based on selected mode
      - Dynamically generate time labels (15min, 30min, 1hr intervals)
      - Maintain user's view preference in session storage
    - **Priority:** 🟢 Low - Current day view is sufficient for now

  - [ ] 5.10.7. **Print & Export Gantt**
    - **Feature:** Print-friendly Gantt chart and export to PDF/PNG
    - **Benefits:** Share plans with stakeholders, archive completed plans
    - **Reference:** Original dashboard has print functionality
    - **Implementation:**
      - Add print CSS to hide controls and optimize layout
      - Implement "Print Gantt" button
      - Consider PDF export using library like jsPDF or html2canvas
      - Include schedule metadata (date, mode, statistics)
    - **Priority:** 🟡 Medium - Useful for documentation

  - [ ] 5.10.8. **Testing & Validation for Advanced Features**
    - [ ] Unit tests for each new feature component
    - [ ] Integration tests for drag & drop workflow
    - [ ] Visual regression tests for UI consistency
    - [ ] Performance tests (ensure large schedules render smoothly)
    - [ ] Accessibility tests (keyboard navigation, screen readers)
    - [ ] Cross-browser testing (Chrome, Firefox, Edge, Safari)
    - [ ] Compare with original dashboard to ensure feature parity
