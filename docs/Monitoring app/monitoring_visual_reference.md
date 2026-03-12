# Monitoring App — Visual Layout Reference

_Updated March 12, 2026_

---

> [!IMPORTANT]
> **All examples in this document use dummy data for illustration purposes only.**
> The actual Monitoring app will fetch data **dynamically** from existing mockCMMS database tables:
>
> - **Stations** → Queried from `assets` table (filtered by asset type)
> - **Tasks** → Queried from `maintenance_orders` table (filtered by asset and date range)
> - **Status** → Calculated on-the-fly from MO completion status
> - **Layout** → Only grid positions are configured; station names/codes come from database
>
> This document shows the **visual design concept**, not the data structure.

---

## Reference Design: Production Re-Start Status Board

This document captures the key visual design elements from the reference image that should be implemented in the Monitoring app.

### Layout Structure

**Grid-Based Spatial Arrangement:**

- Stations arranged to match physical plant floor layout
- Grouped stations (e.g., STATION-01/STATION-02 side-by-side)
- Hierarchical areas (e.g., Paint Conveyor as separate region)
- Flow indicators showing production line progression (arrows between stations)

**Station Card Components:**

```
┌─────────────────────┐
│  Station Code/Name  │
├─────────────────────┤
│ ⬜ Line filled      │ ← Task row 1
│ ⬜ Q-Checks         │ ← Task row 2
│ ⬜ TPM              │ ← Task row 3
│ ⬜ Line Validation  │ ← Task row 4
│ ⬜ MNT Task         │ ← Task row 5
│ ⬜ Integration Task │ ← Task row 6
└─────────────────────┘
```

### Color Coding System

| Status                         | Color         | Hex Code  | Use Case                                   |
| ------------------------------ | ------------- | --------- | ------------------------------------------ |
| **Completed**                  | 🟢 Green      | `#4CAF50` | Task finished, verified, signed off        |
| **Started / In Progress**      | 🟡 Yellow     | `#FFEB3B` | Work actively ongoing, technician assigned |
| **Not Started / Critical**     | 🔴 Red        | `#F44336` | Task pending, blocking production restart  |
| **No Status / Not Applicable** | 🔵 Light Blue | `#B3E5FC` | Task not required for this station/shift   |

**Color Contrast Requirements:**

- All colors must meet WCAG 2.1 AA contrast ratio (4.5:1 minimum)
- Text on colored backgrounds should be black or white based on luminosity
- Border colors should provide additional visual distinction

### Task Types (Reference Image)

From the reference board, the following task types are visible:

1. **Line filled** — Production line has parts/materials loaded
2. **Q-Checks** — Quality checks completed and passed
3. **TPM** — Total Productive Maintenance tasks completed
4. **Line Validation** — Line validation procedures executed
5. **MNT Task** — General maintenance tasks completed
6. **Integration Task** — Integration/commissioning tasks completed

**Implementation Note:** These should be configurable in the database (`monitoring_task_types` table) rather than hardcoded, allowing plants to customize task types based on their specific processes.

### Header Elements

**Calendar/Time Reference:**

- Week indicator (e.g., "08" for Week 8)
- Year (e.g., "2026")
- Plant/Line identifier (e.g., "Plant A - Assembly")
- Purpose label (e.g., "Production Re-Start Status")

**Suggested Implementation:**

```html
<header class="monitoring-header">
  <div class="header-logo">
    <img src="company_logo.png" alt="Company Logo" />
  </div>
  <div class="header-info">
    <h1>Plant A - Assembly</h1>
    <h2>Production Re-Start Status</h2>
  </div>
  <div class="header-calendar">
    <div class="calendar-week">08</div>
    <div class="calendar-label">Calendar<br />Week<br />2026</div>
  </div>
</header>
```

### Status Legend

**Key / Legend Component:**
Located in top-left or top-right corner:

```
KEY
┌──────────────────┐
│ 🟢 completed     │
│ 🟡 started       │
│ 🔴 not started   │
│ 🔵 no status     │
└──────────────────┘
```

### Interactive Behaviors

**Click Behaviors:**

- **Click station card:** Open modal/sidebar with detailed task list
- **Click individual task row:** Navigate to linked MO or Asset detail page
- **Hover station card:** Highlight and show tooltip with summary (e.g., "3/6 tasks completed")
- **Hover task row:** Show tooltip with assigned technician, estimated completion time

**Real-Time Updates:**

- Smooth color transitions when status changes (CSS animation)
- Visual pulse/flash when status updates (draw attention without being distracting)
- Timestamp of last update displayed in footer or header

### Responsive Design Considerations

**Desktop (1920×1080 and above):**

- Full grid layout with all stations visible
- No scrolling required for main view
- Sidebar/modal for drill-down details

**Tablet (iPad Landscape, 1024×768):**

- Responsive grid with 2-3 columns per row
- Horizontal scroll for wide plant layouts
- Smaller station cards with slightly condensed task lists

**Mobile (Not MVP, Future Enhancement):**

- Vertical list view instead of grid
- Expandable accordion for task details
- Swipe gestures for navigation

### Accessibility Features

**Screen Reader Support:**

- ARIA labels for status indicators: `<div role="status" aria-label="Line filled: Completed">`
- Keyboard navigation: Tab through stations, Enter to open details
- Focus indicators clearly visible

**High Contrast Mode:**

- Ensure colors work in Windows High Contrast mode
- Use border and icon patterns in addition to color
- Test with color blindness simulators (protanopia, deuteranopia)

### Performance Considerations

**Rendering Optimization:**

- Use CSS Grid for layout (better performance than flexbox for this use case)
- Minimize DOM reflows by batching status updates
- Use `will-change` CSS property for animated elements
- Lazy load off-screen station cards if plant has 100+ stations

**Update Strategy:**

- Server-Sent Events (SSE) for real-time updates (preferred)
- Polling fallback every 10-30 seconds if SSE unavailable
- Delta updates only (send changed stations, not full dataset)
- Client-side caching of layout configuration

---

## Example Stations from Reference Image

### Station Codes Visible:

- **STATION-01, STATION-02** — Assembly/Production stations
- **CELL-A, CELL-B** — Manufacturing cells
- **WELD-01, WELD-02** — Welding stations
- **PAINT-01** — Paint application station
- **CONVEYOR-A** — Conveyor system
- **QA-01, QA-02** — Quality assurance checkpoints
- **FINAL-01** — Final assembly station

**Implementation Note:** Station codes should be dynamically queried from the `assets` table in the mockCMMS database. The codes shown here (STATION-01, CELL-A, etc.) are examples only.

**Data Flow:**

```python
# Real implementation - query Assets dynamically
stations = Asset.query.filter(
    Asset.asset_type.in_(['Station', 'Line', 'Cell'])
).order_by(Asset.name).all()

# Station codes come from Asset.code or Asset.name
# NOT from hardcoded configuration files
```

---

## UI/UX Mockup (Text-Based)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  [Logo]    Plant A - Assembly Production Re-Start Status    Calendar Week 08  │
│                                                                        2026    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│  KEY                                                                           │
│  🟢 completed  🟡 started  🔴 not started  🔵 no status                        │
│                                                                                │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐           │
│  │ STN-01  │  │ STN-02  │  │ STN-03  │  │ STN-04  │  │ STN-05  │           │
│  ├─────────┤  ├─────────┤  ├─────────┤  ├─────────┤  ├─────────┤           │
│  │🔵 Line  │  │🔵 Line  │  │🔵 Line  │  │🔵 Line  │  │🔵 Line  │           │
│  │🔵 Q-Chk │  │🔵 Q-Chk │  │🔴 Q-Chk │  │🔵 Q-Chk │  │🔵 Q-Chk │           │
│  │🟡 TPM   │  │🟢 TPM   │  │🟡 TPM   │  │🔵 TPM   │  │🔵 TPM   │           │
│  │🔴 Line V│  │🟢 Line V│  │🟡 Line V│  │🔵 Line V│  │🔵 Line V│           │
│  │🔴 MNT   │  │🟢 MNT   │  │🟢 MNT   │  │🔵 MNT   │  │🔵 MNT   │           │
│  │🔴 Integ │  │🟢 Integ │  │🟢 Integ │  │🔵 Integ │  │🔵 Integ │           │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘           │
│                                                                                │
│  ┌─────────────────┐  ┌─────────┐  ┌─────────┐                              │
│  │  Conveyor-A     │  │ FINAL-L │  │ FINAL-R │                              │
│  ├─────────────────┤  ├─────────┤  ├─────────┤                              │
│  │🔴 Line filled   │  │🟢 Line  │  │🟢 Line  │                              │
│  │🔴 TPM           │  │🟢 Q-Chk │  │🔴 Q-Chk │                              │
│  │🟡 Line Valid.   │  │🟢 TPM   │  │🔴 TPM   │                              │
│  │🟢 MNT Task      │  │🟢 Line V│  │🟡 Line V│                              │
│  │🟢 Integration   │  │🟢 MNT   │  │🔴 MNT   │                              │
│  └─────────────────┘  │🟢 Integ │  │🔴 Integ │                              │
│                        └─────────┘  └─────────┘                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Next Steps

1. **Phase 0:** User to approve this visual design concept
2. **Phase 1:** Translate design to HTML/CSS/JS mockup
3. **Phase 2:** Implement database schema for station configuration
4. **Phase 3:** Connect to live MO data for real-time updates
5. **Phase 4:** User acceptance testing with real plant data

---

_Last Updated: March 12, 2026_
