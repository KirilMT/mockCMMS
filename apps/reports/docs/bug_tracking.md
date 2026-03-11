# Reports App Bug Tracking Document

_Created: March 10, 2026_
_Last Updated: March 10, 2026_

---

## 📋 DOCUMENT PURPOSE

This document tracks all identified bugs in the **Reports** application (`apps/reports`).
Each bug includes:

- **Description**: What the bug is and how it manifests
- **Priority**: Critical, High, Medium, or Low
- **Status**: Open, In Progress, Fixed, or Resolved
- **Affected Files**: Files that need to be modified

> [!NOTE]
> **Document Relationship:** This document tracks bugs specific to the Reports app.
> For bugs in the core mockCMMS application, see `docs/bug_tracking.md`.
> For Reports feature planning, see `apps/reports/docs/reports_roadmap.md`.

---

## 🤖 AI AGENT INSTRUCTIONS

### Status Definitions

| Icon   | Status      | Meaning                           |
| ------ | ----------- | --------------------------------- |
| (none) | Open        | Bug identified, not yet addressed |
| ����   | In Progress | Currently being worked on         |
| ✅     | Resolved    | Code applied, user confirmed      |

### Document Quality Rules

> [!CAUTION]
> **MANDATORY:** Follow these rules to maintain document quality for AI interaction.

| Rule                        | Action                                                                                             |
| --------------------------- | -------------------------------------------------------------------------------------------------- |
| **Update Summary Counts**   | After EVERY status change, update the Summary table                                                |
| **Apply 5-Day Rule**        | After bug is FIXED for 5+ days, simplify entry (keep: status, date, 1-2 sentence summary, files)   |
| **Avoid Duplicates**        | ALWAYS search document before adding new bug                                                       |
| **Keep Open Bugs Detailed** | New/Open bugs MUST have: Description, Current/Expected Behavior, Possible Solution, Affected Files |

---

## 🚨 HIGH PRIORITY BUGS

### Bug #R-1: Back Button Incorrect Navigation from Report-Linked Detail Pages

**Priority:** High
**Status:** Open
**Identified:** March 10, 2026

**Description:**
When navigating from a Report details page to a linked entity (e.g., clicking an `MO_ID`, `ASSET_CODE`,
or a Spare Part link), the back button on those entity detail pages does **not** redirect back to the
Report. Instead, it shows the generic label (e.g., "Back to Maintenance Orders") and navigates to the
entity list page — not to the Report the user came from.

This is a **critical UX regression risk**: the back-navigation system was built carefully and works
correctly for core flows (e.g., navigating to MO details from Assets). Any fix here must not break
those existing, working flows.

**Current Behavior:**

- User is on a Report detail page (e.g., `/reports/shift/5`).
- User clicks a linked `MO_ID` (e.g., MO-33) in the report table.
- User lands on `/maintenance-orders/33` detail page.
- Back button label reads **"Back to Maintenance Orders"** and navigates to `/maintenance-orders`.
- Expected: button should read **"Back to Report"** and navigate back to `/reports/shift/5`.

**The same issue applies to:**

- Clicking `ASSET_CODE` → navigates to Asset detail → back button says "Back to Assets".
- Clicking a Spare Part link → navigates to Spare Part detail → back button says "Back to Spare Parts".
- Clicking "Edit" on an MO element in the shift report that is linked to the MOs DB → back button incorrect.

**Expected Behavior:**

- When arriving at any entity detail page **from a Report**, the back button should:
  - Show a label reflecting the origin (e.g., **"Back to Report"**).
  - Navigate back to the exact Report page the user came from (e.g., `/reports/shift/5`).
- This must work **dynamically** — any new page added in the future that links to MOs, Assets, or
  Spare Parts should automatically inherit the correct back-button behavior without manual wiring.

**⚠️ Critical Constraint:**
The existing back-navigation logic (e.g., from Asset detail to MO detail and back) is working very
well and must **not be broken**. The fix must be additive and compatible with the current `return_to`
/ `referrer` mechanism already in place.

**Proposed Solution (Robust & Future-Proof):**

Use a `?return_to=<encoded_url>` query parameter pattern (already partially implemented in the core
app via `Bug #R1` / `Bug #3`). Extend this pattern to all links generated from Report templates:

1. **Report templates:** When rendering clickable `MO_ID`, `ASSET_CODE`, or Spare Part links,
   append `?return_to=<current_report_url>` to each link's `href`.
2. **Entity detail templates:** Read `return_to` from query params and use it to override the
   default back-button `href` and label (e.g., "Back to Report" instead of "Back to Maintenance Orders").
3. **Fallback:** If `return_to` is absent or invalid, retain the current default behavior (e.g.,
   "Back to Maintenance Orders"), so no existing flows are broken.
4. **Label logic:** Detect the origin type from the `return_to` URL to set a meaningful button label
   (e.g., URL contains `/reports/` → label = "Back to Report").
5. **Security:** URL-encode and validate `return_to` to prevent open redirect vulnerabilities.
   Only allow internal relative paths.

**Affected Files (Likely):**

- `apps/reports/src/templates/report_detail.html` — Add `?return_to=` to all entity links
- `src/templates/maintenance_order_detail.html` — Read `return_to` param for back button
- `src/templates/asset_detail.html` — Read `return_to` param for back button
- `src/templates/spare_part_detail.html` — Read `return_to` param for back button
- `src/routes/main.py` — Pass/validate `return_to` through routes as needed

**Reference:**
See core app `Bug #R1` (resolved) and `Bug #3` (resolved) for the existing `return_to` pattern
implementation as a baseline.

---

## 📊 BUG SUMMARY BY PRIORITY

> [!NOTE]
> Last updated: March 10, 2026

### Summary Counts

| Category  | Open  | Partial | In Progress | Fixed | Total |
| --------- | ----- | ------- | ----------- | ----- | ----- |
| Critical  | 0     | 0       | 0           | 0     | 0     |
| High      | 1     | 0       | 0           | 0     | 1     |
| Medium    | 0     | 0       | 0           | 0     | 0     |
| Low       | 0     | 0       | 0           | 0     | 0     |
| **Total** | **1** | **0**   | **0**       | **0** | **1** |

### Open Bugs

- **High:** #R-1 Back Button Incorrect Navigation from Report-Linked Detail Pages

---

## 📅 MAINTENANCE GUIDELINES

**When a bug is fixed:**

1. Change status to "✅ FIXED" with date
2. Add 1-2 sentence resolution summary
3. List affected files
4. Update summary counts

**After 5+ days resolved:**

1. Simplify entry per the "5-Day Rule" above
2. Remove verbose details (behavior, solution steps, code snippets)

**When adding new bugs:**

1. Use next available ID (`#R-2`, `#R-3`, etc.)
2. Set priority (Critical, High, Medium, Low)
3. Add full details: Description, Current/Expected Behavior, Possible Solution, Affected Files
4. Add to appropriate section
5. Update summary counts

---

_This document tracks bugs for the Reports (`apps/reports`) application._
