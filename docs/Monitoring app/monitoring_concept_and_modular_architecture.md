# Monitoring App — Concept & Modular Architecture

_Updated March 12, 2026_

---

## ⚠️ INSTRUCTIONS FOR AI ASSISTANTS

**This document defines the architectural foundation for the Monitoring app. Treat it as a design specification, not a task list.**

- **Do NOT modify design decisions** without discussing them first — they have dependencies
- **Update the "Domain Model" section** if the schema changes during Phase 0 review
- **Keep integration patterns in sync** with `src/app.py` as the core app evolves
- **Update "Last Updated" date** at the top when making any changes

> [!NOTE]
> For the phased implementation plan, see [`monitoring_roadmap.md`](monitoring_roadmap.md). This document focuses on **what** is being built and **how** it integrates — the roadmap tracks **when** and **who**.

---

## 🎯 Objective

Create a real-time **Production Re-Start Status Monitoring** application that provides visual oversight of plant floor readiness after Break Activities periods or weekend maintenance tasks. The application displays a spatial layout of the plant floor with live status indicators for each production station, enabling operations teams to quickly identify which lines are ready for production and which still have pending tasks.

### Primary Use Cases

1. **Post-Weekend Readiness Check:** After weekend maintenance, operations managers need to see which production lines are ready to restart.
2. **Break Period Status:** During extended breaks (holidays, shutdowns), track progress of maintenance activities across all stations.
3. **Production Planning:** Identify bottlenecks and prioritize resources based on real-time status across the plant floor.
4. **Cross-Team Coordination:** Provide a shared visual reference for maintenance, operations, and production teams.

---

## 📖 Source Concept: Production Status Board

The reference image shows a production re-start status board with:

- **Spatial Layout:** Stations arranged to match physical plant floor (e.g., STATION-01, STATION-02, CELL-A, CELL-B, etc.)
- **Task Categories:** Multiple task types per station (Line filled, Q-Checks, TPM, Line Validation, MNT Task, Integration Task)
- **Color-Coded Status:**
  - 🟢 **Green:** Completed
  - 🟡 **Yellow:** Started / In Progress
  - 🔴 **Red:** Not Started / Critical
  - 🔵 **Light Blue:** No Status / Not Applicable
- **Visual Hierarchy:** Grouped stations (e.g., adjacent stations, separate work areas)
- **Calendar Reference:** Week number indicator

### Key Design Principles to Adopt

| Principle                 | Implementation in mockCMMS                                     |
| ------------------------- | -------------------------------------------------------------- |
| **Spatial Accuracy**      | Layout configuration must match actual plant floor arrangement |
| **At-a-Glance Status**    | Color coding visible without zooming or scrolling              |
| **Task Granularity**      | Show individual task types, not just overall station status    |
| **Real-Time Updates**     | Status changes reflect immediately (or within seconds)         |
| **Drill-Down Navigation** | Click on station → See task details → Link to MO/Asset         |

---

## 🏗️ Proposed App Structure

The module follows the same conventions as `apps/planning` and `apps/reporting`. Every directory has a specific responsibility and must not be mixed.

```text
apps/monitoring/
├── src/                              # All application source code
│   ├── app.py                        # ⭐ Flask app factory (create_app)
│   ├── config.py                     # Configuration classes (Dev, Prod, Test)
│   ├── extensions.py                 # Flask extensions init (SQLAlchemy, etc.)
│   ├── routes/
│   │   └── monitoring.py             # ⭐ Blueprint — all routes defined here
│   ├── services/
│   │   ├── status_service.py         # Status tracking and aggregation logic
│   │   ├── layout_service.py         # Plant layout management
│   │   ├── integration_service.py    # MO/Asset integration layer
│   │   └── db_seeding.py             # Idempotent seed data population
│   ├── models/
│   │   └── monitoring_models.py      # SQLAlchemy model definitions
│   ├── static/
│   │   ├── css/
│   │   │   └── monitoring.css        # App-specific styles
│   │   └── js/
│   │       ├── monitoring.js         # Main monitoring board logic
│   │       └── realtime_updates.js   # WebSocket/SSE client
│   ├── templates/
│   │   ├── monitoring.html           # Main monitoring board view
│   │   ├── station_detail.html       # Station drill-down modal/page
│   │   └── layout_admin.html         # Layout configuration UI (admin)
│   └── __init__.py
├── tests/                            # Isolated test suite
│   ├── conftest.py                   # Pytest fixtures
│   ├── test_status_service.py        # Business logic tests
│   ├── test_layout_service.py        # Layout management tests
│   ├── test_integration.py           # Integration with MOs/Assets
│   └── test_routes.py                # API endpoint tests
├── docs/
│   ├── monitoring_roadmap.md         # ⭐ Canonical roadmap (copy from root docs/)
│   ├── monitoring_bug_tracking.md    # App-specific bug tracker
│   └── assets/                       # Screenshots, diagrams
├── config/
│   └── default_layout.json           # Default plant floor layout configuration
├── instance/
│   └── monitoring.db                 # SQLite database (dev/test only)
├── setup.py                          # Package setup for pip install -e
└── README.md                         # App-specific documentation
```

---

## 🗄️ Domain Model (Draft)

### Data Sourcing Strategy

**🔑 CRITICAL ARCHITECTURAL DECISION:**

This app is a **READ-ONLY DASHBOARD** that aggregates and visualizes data from existing mockCMMS tables. It does NOT duplicate or store business data.

| Data Type            | Source                       | Storage Location              | Rationale                                     |
| -------------------- | ---------------------------- | ----------------------------- | --------------------------------------------- |
| **Stations**         | `assets` table               | Existing DB                   | Assets already define production stations     |
| **Tasks**            | `maintenance_orders` table   | Existing DB                   | MOs already define maintenance tasks          |
| **Status**           | Calculated on-the-fly        | Cached temporarily only       | Real-time status must reflect current MO data |
| **Technicians**      | `technicians` table          | Existing DB                   | Already linked via MO foreign keys            |
| **Layout Positions** | JSON config or minimal table | Config file or small DB table | UI preference only, not business data         |

### Minimal Database Tables (UI Preferences Only)

**Option 1: No Database Tables (Recommended for MVP)**

Store layout preferences in a JSON configuration file. This keeps the app truly stateless and avoids data duplication.

**Option 2: Minimal Layout Table (If Dynamic UI Configuration Needed)**

If admins need to configure layout via UI (not editing JSON files), add ONE minimal table:

#### `monitoring_layout_preferences` (Optional)

Stores ONLY visual layout preferences, NOT business data.

| Column             | Type       | Description                                  |
| ------------------ | ---------- | -------------------------------------------- |
| `id`               | Integer    | Primary key                                  |
| `asset_id`         | Integer    | FK to `assets` (the station being displayed) |
| `grid_row`         | Integer    | CSS grid row position                        |
| `grid_column`      | Integer    | CSS grid column position                     |
| `grid_row_span`    | Integer    | Vertical span (default 1)                    |
| `grid_column_span` | Integer    | Horizontal span (default 1)                  |
| `display_label`    | String(50) | Optional custom label override               |
| `is_visible`       | Boolean    | Show/hide this station on the board          |
| `display_order`    | Integer    | Sort order for grouped stations              |
| `created_at`       | DateTime   | Timestamp                                    |
| `updated_at`       | DateTime   | Timestamp                                    |

**Unique Constraint:** (`asset_id`) — One layout config per asset

### ❌ TABLES WE DO NOT NEED (Data Already Exists)

The following tables from the original draft are **NOT NEEDED** because the data already exists:

~~`monitoring_plant_layout`~~ → Use `assets` table (filter by `asset_type`)
~~`monitoring_task_types`~~ → Use `maintenance_orders.mo_type` or `maintenance_orders.category`
~~`monitoring_station_status`~~ → Calculate on-the-fly from `maintenance_orders.status`
~~`monitoring_status_history`~~ → Already tracked in `maintenance_orders` audit logs (if implemented)

### Data Retrieval Examples

**Get All Stations:**

```python
# Query existing Assets table
stations = db.session.query(Asset).filter(
    Asset.asset_type.in_(['Production Line', 'Station', 'Cell', 'Workstation'])
).all()
```

**Get Tasks for a Station:**

```python
# Query existing Maintenance Orders table
tasks = db.session.query(MaintenanceOrder).filter(
    MaintenanceOrder.asset_id == station_id,
    MaintenanceOrder.scheduled_date >= weekend_start,  # Filter to relevant timeframe
    MaintenanceOrder.scheduled_date <= weekend_end
).all()
```

**Calculate Station Status:**

```python
def calculate_station_status(station_id, date_range):
    """Calculate color-coded status from MO completion."""
    mos = MaintenanceOrder.query.filter_by(asset_id=station_id).filter(
        MaintenanceOrder.scheduled_date.between(*date_range)
    ).all()

    if not mos:
        return 'no_status'  # Blue

    completed = sum(1 for mo in mos if mo.status == 'Completed')
    in_progress = sum(1 for mo in mos if mo.status == 'In Progress')

    if completed == len(mos):
        return 'completed'  # Green
    elif in_progress > 0 or completed > 0:
        return 'in_progress'  # Yellow
    else:
        return 'not_started'  # Red
```

---

## 🔗 Integration Points

### With Core mockCMMS

1. **Assets:**
   - Link station status to specific assets
   - Query asset hierarchy to determine station assignments
   - Display asset details in station drill-down

2. **Maintenance Orders (MOs):**
   - Auto-update station status when MO status changes
   - Map MO task types to monitoring task types
   - Link directly to MO detail pages

3. **Technicians:**
   - Show assigned technician for in-progress tasks
   - Link to technician dashboard (if Planning app is enabled)

4. **Authentication:**
   - Use shared Flask-Login session
   - Respect user roles and permissions
   - Admin-only access for layout configuration

### Real-Time Update Strategy

**Recommended: Server-Sent Events (SSE)**

```python
# src/routes/monitoring.py
from flask import Response, stream_with_context
import json
import time

@monitoring_bp.route('/api/status-stream')
@login_required
def status_stream():
    """
    SSE endpoint for real-time status updates.
    """
    def generate():
        while True:
            # Query for recent status changes
            changes = get_recent_status_changes(last_check=time.time() - 5)
            if changes:
                yield f"data: {json.dumps(changes)}\n\n"
            time.sleep(5)  # Poll every 5 seconds

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )
```

**Alternative: Polling (Simpler, Less Efficient)**

- Frontend polls `/api/station-status` every 10-30 seconds
- Easier to implement, no persistent connections
- Higher server load with many concurrent users

**Not Recommended: WebSocket**

- Adds complexity (requires Flask-SocketIO or separate process)
- Overkill for this use case (status changes are infrequent)

---

## 🎨 UI/UX Design Guidelines

### Layout System

**CSS Grid Approach:**

```css
.monitoring-board {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  grid-template-rows: auto;
  gap: 10px;
  padding: 20px;
}

.station-card {
  grid-row: var(--station-row);
  grid-column: var(--station-col) / span var(--station-col-span);
  border: 2px solid #ccc;
  border-radius: 8px;
  padding: 10px;
}

.station-card.critical {
  border-color: #f44336;
  box-shadow: 0 0 10px rgba(244, 67, 54, 0.3);
}
```

### Status Indicators

Each station card displays task rows with color-coded backgrounds:

```html
<div class="station-card" data-station-id="12">
  <h3 class="station-name">STATION-01</h3>
  <div class="task-list">
    <div class="task-row status-completed">
      <span class="task-name">Line filled</span>
    </div>
    <div class="task-row status-in-progress">
      <span class="task-name">Q-Checks</span>
    </div>
    <div class="task-row status-not-started">
      <span class="task-name">TPM</span>
    </div>
    <!-- ... -->
  </div>
</div>
```

### Interaction Patterns

1. **Click Station Card:** Open modal with detailed task list and links to MOs
2. **Hover Task Row:** Show tooltip with assigned technician and ETA
3. **Legend Toggle:** Expandable/collapsible legend explaining color codes
4. **Filter Controls:** Hide/show stations by status or department

---

## 🔒 Security & Permissions

### Role-Based Access

| Role                   | Permissions                                            |
| ---------------------- | ------------------------------------------------------ |
| **Admin**              | Full access: configure layout, edit statuses, view all |
| **Operations Manager** | View all, update statuses, no layout config            |
| **Technician**         | View all, update own assigned tasks only               |
| **Viewer**             | Read-only access to monitoring board                   |

### Data Validation

- Status transitions must follow valid state machine (not_started → in_progress → completed)
- Only assigned technician or admin can update task status
- Layout configuration changes require admin role and audit logging

---

## 📏 Non-Functional Requirements

### Performance

- **Target Load Time:** < 2 seconds for initial page load
- **Status Update Latency:** < 5 seconds from MO change to board update
- **Concurrent Users:** Support 50+ simultaneous viewers without degradation
- **Database Queries:** Use eager loading and caching to minimize N+1 queries

### Scalability

- **Station Limit (MVP):** 100 stations
- **Task Types (MVP):** 10 task types per station
- **Historical Data:** Retain status history for 90 days (configurable)

### Accessibility

- **WCAG 2.1 AA Compliance:** Color contrast ratios, keyboard navigation
- **Screen Reader Support:** ARIA labels for status indicators
- **Responsive Design:** Usable on tablets (iPad landscape orientation minimum)

---

## 🧪 Testing Strategy

### Unit Tests (pytest)

- Status service business logic
- Layout validation
- Status aggregation calculations

### Integration Tests (pytest)

- MO status change triggers station status update
- Asset hierarchy correctly maps to stations
- Real-time update mechanism delivers changes

### End-to-End Tests (Playwright)

- Load monitoring board and verify station rendering
- Click station card and verify modal appears
- Simulate status change and verify color update

### Visual Regression Tests (Playwright)

- Screenshot comparison for layout consistency
- Verify color codes match specification

---

## 📦 Deployment & Configuration

### Environment Variables

```env
# .env
MONITORING_ENABLED=True
MONITORING_UPDATE_INTERVAL=5  # Seconds between status checks
```

### Data Source Philosophy

**🔑 CRITICAL: This app is a DYNAMIC VIEW of existing data, NOT a separate data source.**

All monitoring data is derived from existing mockCMMS database tables:

| Monitoring Display   | Data Source                                     | How It's Derived                                                   |
| -------------------- | ----------------------------------------------- | ------------------------------------------------------------------ |
| **Stations**         | `assets` table                                  | Filter assets by type (e.g., "Production Line", "Station", "Cell") |
| **Task Types**       | `maintenance_orders` table                      | MO types/categories (Preventive, Corrective, Integration, etc.)    |
| **Station Status**   | Calculated from `maintenance_orders` + `assets` | Aggregate MO completion status for each asset                      |
| **Assigned Techs**   | `maintenance_orders.assigned_technician_id`     | Direct FK relationship                                             |
| **Completion Times** | `maintenance_orders.completion_date`            | Direct field                                                       |
| **Plant Layout**     | UI configuration only (not business data)       | Stores grid positions for spatial representation                   |

### Layout Configuration File (UI Only)

**This configuration ONLY controls visual layout, NOT the data itself.**

```json
{
  "plant_name": "Plant A - Assembly Line",
  "grid_columns": 12,
  "layout_preferences": {
    "description": "Maps asset IDs to grid positions for spatial visualization",
    "note": "Station data itself comes from Assets table dynamically"
  },
  "station_positions": [
    {
      "asset_id": 101,
      "grid_row": 2,
      "grid_column": 5,
      "grid_column_span": 1,
      "display_label": "STATION-01"
    },
    {
      "asset_id": 205,
      "grid_row": 8,
      "grid_column": 3,
      "grid_column_span": 3,
      "display_label": "CONVEYOR-A"
    }
  ],
  "task_type_filters": {
    "description": "Optional: Filter which MO types to display as task rows",
    "enabled_mo_types": ["Preventive", "Corrective", "Integration"],
    "custom_display_names": {
      "Preventive": "TPM",
      "Corrective": "MNT Task",
      "Integration": "Integration Task"
    }
  }
}
```

**Key Principles:**

1. **Assets = Stations:** Query `assets` table filtered by `asset_type IN ('Station', 'Line', 'Cell')`
2. **MOs = Tasks:** Query `maintenance_orders` filtered by `asset_id` to get tasks per station
3. **Status = Calculated:** Aggregate MO statuses (Open, In Progress, Completed) → Map to color codes
4. **No Data Duplication:** Configuration only stores visual preferences (grid positions), never business data
5. **Single Source of Truth:** mockCMMS database is the authoritative source

**Example Query Flow:**

```python
# Fetch all production stations (Assets)
stations = Asset.query.filter(Asset.asset_type.in_(['Station', 'Line', 'Cell'])).all()

# For each station, get associated MOs
for station in stations:
    mos = MaintenanceOrder.query.filter_by(asset_id=station.id).all()

    # Calculate status based on MO completion
    status = calculate_status(mos)  # Open → Red, In Progress → Yellow, Completed → Green

    # Get grid position from layout config (UI only)
    position = layout_config.get_position(station.id)

    # Render station card with dynamic data
    render_station(station, mos, status, position)
```

---

## 🚀 Future Enhancements (Post-MVP)

- **[ ] Mobile App:** Native iOS/Android app for on-the-go monitoring
- **[ ] Predictive Analytics:** ML model to predict completion times based on historical data
- **[ ] Automated Notifications:** Slack/Teams alerts when critical tasks are delayed
- **[ ] 3D Plant Visualization:** Interactive 3D model of plant floor (using Three.js)
- **[ ] Multi-Plant Support:** Switch between different plant locations
- **[ ] Shift Handoff Reports:** Auto-generate summary of status at shift change

---

## 🔗 Related Documentation

- [Monitoring App Roadmap](monitoring_roadmap.md)
- [Main mockCMMS Roadmap](../mockCMMS_roadmap.md)
- [Planning App Concept](../../apps/planning/docs/README.md)
- [Reporting App Concept](../../apps/reporting/README.md)

---

_Last Updated: March 12, 2026_
