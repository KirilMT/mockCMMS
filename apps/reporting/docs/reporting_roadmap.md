# Reporting App Roadmap

_Updated March 10, 2026_

---

## 🎯 Active Work

### Team-Scoped Report Filtering (Priority: High)

**Status:** 🚀 **IN PROGRESS**

**Goal:** Show only MOs assigned to the selected report team in Shift/Weekend reporting.

**Rules:**

- Handover sections: In Progress Reactive/Corrective MOs assigned to selected team
- Breakdowns: Completed Reactive MOs assigned to selected team
- Break Activities (FLUX Tickets/MOs): Completed Corrective MOs assigned to selected team
- Engineering Support: Engineering MOs assigned to selected team

**Implementation Notes:**

- Team matching reads assignees from both `maintenance_order_assignees` and legacy `assignees_json`
- If a report team is selected, unassigned MOs are excluded
- If no team is selected, legacy behavior remains

**Current Validation Finding (March 6, 2026):**

- User-created MOs `29`, `30`, `31` are not shown because `assignees_count = 0` in DB
- Team A users exist (`3`, `11`, `12`, `13`), but no assignee link rows exist for these MOs

**Remaining Tasks:**

- [ ] Verify assignee persistence from MO edit form to `maintenance_order_assignees`
- [ ] Add backend test for team-scoped weekend aggregation
- [ ] Add integration test covering Shift + Weekend team scoping

### 2.2 Link Reporting to Core CMMS Data (Priority: High)

**Status:** 🚀 **IN PROGRESS** - Handover sections tested and working!

**Goal:** Ensure report sections are fully linked to live CMMS data (MOs, Assets, Spare Parts).

**Background:**

- Reporting currently use some dummy/hardcoded data
- Need to ensure all data comes from the actual database
- All asset codes, MO numbers, and spare part references must resolve to real entities

**Completed Tasks:**

- [x] **Shift Report - Breakdowns Section:**
  - ✅ Links to Reactive MOs from the MOs database
  - ✅ Verified asset codes use Assets DB
  - ✅ All breakdown data (fault, root cause, recovery) is DB-backed
- [x] **Shift Report - Handover from Previous Shift:**
  - ✅ Links to In Progress Reactive MOs before shift start
  - ✅ Includes MO ID for linking to detail pages
  - ✅ **USER TESTED (March 6, 2026)**: Confirmed working with MO-33
- [x] **Shift Report - Handover to Next Shift:**
  - ✅ Links to In Progress Reactive MOs created during shift
  - ✅ Includes MO ID for linking to detail pages
  - ✅ **USER TESTED (March 6, 2026)**: Confirmed working with MO-33 and MO-35
  - ✅ **Verified**: `due_date` is NOT required (nullable field)
- [x] **Shift Report - Engineering Support Section:**
  - ✅ Links to Engineering-type MOs
  - ✅ Validates MO numbers resolve to correct detail pages
- [x] **Weekend Report - All Sections:**
  - ✅ Applied same linking logic as Shift Reporting
  - ✅ PMs link to correct Maintenance Orders
  - ✅ All data uses asset_code (not asset_name)

**Remaining Tasks:**

- [ ] **Manual Testing:**
  - [x] Test handover sections (both "from previous" and "to next") ✓
  - [ ] Verify all MO links navigate to correct detail pages
  - [ ] Verify all asset code links navigate to asset details
  - [ ] Test Breakdowns section with live Reactive MOs
  - [ ] Test Engineering Support section with live Engineering MOs
  - [ ] Test with freshly seeded database
- [ ] **Backend Tests:**
  - Add unit tests for new DataAggregator methods
  - Add integration tests for report generation
  - Verify coverage meets 92% diff threshold

**Files Modified:**

- ✅ `apps/reporting/src/services/data_aggregator.py` - Added MO linking methods
  - `_get_handover_from_previous()` - Get In Progress MOs before shift
  - `_get_handover_to_next()` - Get In Progress MOs during shift
  - `_get_engineering_support()` - Get Engineering MOs
  - Updated `get_aggregated_shift_data()` - Include all new data
  - Updated `get_aggregated_weekend_data()` - Use asset_code, add handovers

**Validation Results:**

```
✅ Database Status: 28 MOs, 3 Reactive, 4 In Progress, 0 Engineering
✅ Shift Report: Handovers linked to MO ID 9
✅ Asset Code Validation: All codes resolve to real assets
✅ Data Structure: All required fields present
```

---

## 📋 Planned Work

### Automatic Report Generation at End of Shift (Priority: High)

**Goal:** Generate reporting automatically when a shift ends, with the option to trigger generation
manually at any time — while enforcing a strict one-report-per-shift constraint.

**Rules:**

- One report per shift: if a report already exists for a given shift, it must not be duplicated.
- Auto-generation triggers at shift end (based on the shift calendar already in the core app).
- Manual trigger button available at any time within the shift window (e.g., for early previews or ad-hoc needs).
- If a report for that shift already exists, the manual trigger should offer an **update** flow instead (see "Update Report" item below).

**Proposed Tasks:**

- [ ] Add a shift-end trigger mechanism (cron job, shift calendar event hook, or background task).
- [ ] Enforce uniqueness: validate that no report exists for the shift before creating a new one.
- [ ] Add a "Generate Report" button on the Reporting list page, disabled if a report already exists for the current shift.
- [ ] Handle edge cases: shift not started, shift already has a report, data not yet available.

---

### Reactive MO Workflow for Breakdowns — HMI Integration (Priority: Medium)

**Goal:** Streamline the breakdown workflow so that when operations press the MNTC (Maintenance)
button on the HMI, a Reactive Maintenance Order is automatically opened in the system.

**Background:**
Since the system relies on Reactive MOs to track breakdowns, the manual creation step creates a gap
between the physical event (machine stops) and the digital record (MO created). Automating this link
would improve data accuracy and response time tracking.

**Proposed Approach:**

- When an operator presses the MNTC button on the HMI, trigger creation of a generic Reactive MO
  with pre-filled context (asset code, timestamp, shift).
- The MO should be editable: operators/technicians can add fault details, root cause, and recovery
  time after the fact.
- This change touches the core mockCMMS MO workflow — see `docs/mockCMMS_roadmap.md` for the
  related core-app item.

**Proposed Tasks:**

- [ ] Define HMI → CMMS integration API contract (webhook or polling endpoint).
- [ ] Auto-populate Reactive MO with: Asset, Shift, Timestamp, Status = "Open".
- [ ] Provide an edit flow for technicians to complete the MO after the breakdown is resolved.
- [ ] Ensure Breakdowns section in Shift Reporting picks up these auto-created MOs correctly.

> **Note:** The broader HMI integration design and core MO workflow changes are tracked in
> `docs/mockCMMS_roadmap.md`.

---

### Update Report Button (Priority: High)

**Goal:** Allow a report to be refreshed/updated with new data (e.g., newly created Reactive MOs)
**during the shift the report belongs to**. Once the shift ends, the report becomes read-only.

**Rules:**

- The "Update Report" button is only visible/enabled if the report belongs to the **current active shift**.
- Clicking it re-runs the data aggregation and updates the report in place (no new report created).
- After the shift ends, the report is locked — no further updates allowed.
- This prevents accidental modification of historical records.

**Proposed Tasks:**

- [ ] Add "Update Report" button to the Report detail page (conditionally shown based on shift status).
- [ ] Add backend endpoint to re-aggregate data for an existing report and persist updated results.
- [ ] Add shift-status check: reject update requests if the report's shift has ended.
- [ ] Show a clear indicator (e.g., "Last updated: HH:MM") so users know when data was last refreshed.
- [ ] Ensure idempotency: updating twice with the same data produces the same result.

---

### Asset Dropdown Population (Priority: Medium)

**Goal:** Replace free-text asset entries with DB-backed asset selection.

**Current State:**

- Asset dropdowns use Select2 with `tags: true` (allows free text)
- Users can enter any text, not limited to existing assets
- No validation against Assets DB

**Proposed Solution:**

- [ ] Create backend API endpoint `/api/assets`
  - Returns all assets from Assets DB
  - Format: `[{id, asset_code, name, location}, ...]`
  - Add filtering/search capability
- [ ] Configure Select2 with AJAX loading
  - Remove `tags: true` to disable free text
  - Add `ajax` configuration pointing to `/api/assets`
  - Implement search/filtering on backend
- [ ] Update all report modals
  - Apply to Add/Edit modals in Shift Reporting
  - Apply to Add/Edit modals in Weekend Reporting
  - Ensure selected assets are validated server-side

**Note:** This is a larger enhancement beyond the current immediate scope.

---

## 📝 Notes

- **Frontend tests:** Deferred per current guidance - focus on backend data linking first
- **Testing strategy:** Focus on backend tests to verify data linkage correctness
- **No rework principle:** Get data contracts right before updating frontend tests
