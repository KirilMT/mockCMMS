# Monitoring App Roadmap

_Updated March 12, 2026_

---

## ⚠️ INSTRUCTIONS FOR AI ASSISTANTS

**When working on this project:**

1. **Update "ACTIVE WORK" section** when sprint phases change or complete
2. **Update status** as work progresses (e.g., "Phase 0" → "Phase 1" → "Completed")
3. **Move completed items** to "Recently Completed" section (don't delete immediately)
4. **Update "Last Updated" date** at the top when making changes
5. **Keep this file synchronized** with `docs/mockCMMS_roadmap.md` (high-level summary only there, full detail here)

> [!NOTE]
> This is a **pre-implementation planning roadmap**. The `apps/monitoring/` directory does not yet exist. The first implementation task is Phase 1 (Scaffolding). Once the app directory is created, a **canonical copy** of this roadmap must also live at `apps/monitoring/docs/monitoring_roadmap.md` and a bug tracker must be created at `apps/monitoring/docs/monitoring_bug_tracking.md`.

> [!TIP]
> **Document Relationship:** This roadmap plans new work for the Monitoring module. For bugs (once they exist), use the app-level bug tracker. For the core mockCMMS project overview, see [`docs/mockCMMS_roadmap.md`](../mockCMMS_roadmap.md).

---

## 🔥 ACTIVE WORK

**Current Sprint:** Phase 0 — Discovery and Architecture
**Status:** In Progress — Defining scope, data model, and UI/UX design
**Started:** March 12, 2026
**Target Completion:** TBD (depends on design decisions)

> [!IMPORTANT]
> **Phase 0 must be completed before any code is written.** The key deliverables are a finalized data model, plant layout configuration structure, and documented integration points with Assets and Maintenance Orders. See [Concept & Architecture Doc](monitoring_concept_and_modular_architecture.md).

---

## 📋 PLANNED WORK

### Phase 0 — Discovery and Architecture

- **[ ] Finalize MVP Feature Scope** _(Priority: Critical)_
  - **Goal:** Lock the boundaries of the first release to avoid scope creep before scaffolding begins.
  - **Deliverables:**
    - Written MVP scope decision: what IS and IS NOT in v1.0
    - Confirmed data model (see architecture doc for draft)
    - Plant layout configuration structure (stations, lines, production cells)
    - Status indicator definitions and color coding rules
    - Defined integration points with Assets and Maintenance Orders
    - Real-time update strategy (polling vs. WebSocket vs. SSE)
  - **Status:** Not Started

- **[ ] Data Model Approval** _(Priority: Critical)_
  - **Goal:** Approve the data sourcing strategy before implementation begins.
  - **Key Decisions:**
    - Confirm that stations are sourced from `assets` table dynamically
    - Confirm that tasks are sourced from `maintenance_orders` table
    - Confirm that status is calculated on-the-fly from MO completion status
    - Approve minimal layout configuration approach (JSON file or simple table for grid positions only)
    - Confirm NO duplication of business data in monitoring-specific tables
  - **Reference:** [Architecture Document](monitoring_concept_and_modular_architecture.md) - See "Data Sourcing Strategy" section
  - **Status:** Draft in architecture doc — pending review

- **[ ] UI/UX Design Approval** _(Priority: Critical)_
  - **Goal:** Finalize the visual design and interaction model before implementation.
  - **Key Design Decisions:**
    - Responsive grid layout strategy for plant floor visualization
    - Color palette for status indicators (green/yellow/red/blue)
    - Interactive elements (click for details, drill-down to MO/Asset)
    - Real-time update visual feedback (animations, transitions)
    - Mobile responsiveness requirements
  - **Reference:** User-provided screenshot showing production re-start status board layout
  - **Status:** Reference design available — needs translation to mockCMMS design system

---

### Phase 1 — App Scaffolding

- **[ ] Create `apps/monitoring/` Package** _(Priority: Critical)_
  - **Goal:** Scaffold the full modular app structure, mirroring the conventions used by `apps/planning` and `apps/reporting`.
  - **Tasks:**
    - Create full directory structure (`src/`, `tests/`, `docs/`, `config/`, `instance/`)
    - Add `setup.py` (package setup) and `requirements.txt` (app-local dependencies)
    - Create `src/app.py` with Flask app factory
    - Create `src/config.py` with configuration classes
    - Create `src/extensions.py` for Flask extensions
    - Set up initial test structure with pytest fixtures
  - **Dependencies:** Phase 0 must be complete
  - **Status:** Not Started

- **[ ] Environment Variable Integration** _(Priority: Critical)_
  - **Goal:** Add `MONITORING_ENABLED` environment variable to control app activation.
  - **Tasks:**
    - Add `MONITORING_ENABLED` to `.env.example`
    - Update core `src/app.py` to conditionally register monitoring blueprint
    - Document environment variable in README
  - **Dependencies:** Phase 1 scaffolding must be complete
  - **Status:** Not Started

---

### Phase 2 — Data Integration & Query Layer

- **[ ] Dynamic Data Sourcing Implementation** _(Priority: Critical)_
  - **Goal:** Implement query services that fetch station and task data from existing mockCMMS tables.
  - **Tasks:**
    - Create `station_service.py` to query Assets table for stations
    - Create `task_service.py` to query Maintenance Orders for tasks
    - Implement status calculation logic (MO status → color codes)
    - Create caching layer for performance optimization
    - Write unit tests for all query and calculation logic
  - **Dependencies:** Phase 0 data model approval, Phase 1 scaffolding
  - **Status:** Not Started

- **[ ] Layout Configuration System** _(Priority: High)_
  - **Goal:** Implement the system for defining spatial layout (UI preferences only).
  - **Tasks:**
    - Decide: JSON file vs. minimal database table for layout preferences
    - Create configuration file format (JSON) for layout definition
    - Implement layout validation logic
    - Create admin interface for layout management (Phase 3 enhancement)
    - Support hierarchical station grouping (lines, cells, areas)
  - **Dependencies:** Phase 2 dynamic data sourcing
  - **Status:** Not Started

- **[ ] Performance Optimization** _(Priority: High)_
  - **Goal:** Ensure monitoring board loads quickly with efficient queries.
  - **Tasks:**
    - Implement database query optimization (eager loading, indexing)
    - Add caching layer (Redis or in-memory) for frequently accessed data
    - Implement pagination or lazy loading for large plant floors (100+ stations)
    - Profile query performance and optimize slow queries
  - **Dependencies:** Phase 2 data integration
  - **Status:** Not Started

---

### Phase 3 — Status Tracking & Integration

- **[ ] MO-to-Status Integration** _(Priority: High)_
  - **Goal:** Link Maintenance Orders to station status updates.
  - **Tasks:**
    - Create service to map MO completion to status changes
    - Implement business logic for status transitions (not started → started → completed)
    - Handle multi-station MOs (one MO affects multiple stations)
    - Create API endpoints for status updates
  - **Dependencies:** Core data model (Phase 2)
  - **Status:** Not Started

- **[ ] Real-Time Status Updates** _(Priority: High)_
  - **Goal:** Implement mechanism for live status updates without page refresh.
  - **Tasks:**
    - Evaluate technology options (polling, WebSocket, Server-Sent Events)
    - Implement chosen real-time update mechanism
    - Add frontend JavaScript for receiving and displaying updates
    - Optimize update frequency to balance responsiveness and server load
  - **Dependencies:** MO-to-Status integration
  - **Status:** Not Started

- **[ ] Asset Status Aggregation** _(Priority: Medium)_
  - **Goal:** Aggregate asset readiness based on all associated MO statuses.
  - **Tasks:**
    - Define asset readiness calculation rules
    - Implement aggregation service
    - Create visual indicators for overall asset/line readiness
    - Support drill-down from asset to individual task statuses
  - **Dependencies:** MO-to-Status integration
  - **Status:** Not Started

---

### Phase 4 — UI Development

- **[ ] Plant Layout Visualization** _(Priority: High)_
  - **Goal:** Create the visual plant floor layout interface.
  - **Tasks:**
    - Implement responsive grid layout system
    - Create station card components with status indicators
    - Implement color-coded status visualization (green/yellow/red/blue)
    - Add station labels and identifiers (STATION-01, STATION-02, CELL-A, etc.)
    - Ensure layout matches physical plant floor arrangement
  - **Dependencies:** Plant layout configuration system (Phase 2)
  - **Status:** Not Started

- **[ ] Interactive Status Details** _(Priority: High)_
  - **Goal:** Enable users to view detailed information by clicking on stations.
  - **Tasks:**
    - Create modal/sidebar for detailed station status
    - Display all tasks for selected station with individual statuses
    - Link to associated MOs and Assets
    - Show technician assignments and estimated completion times
    - Add navigation to MO detail pages
  - **Dependencies:** Plant layout visualization
  - **Status:** Not Started

- **[ ] Status Legend and Key** _(Priority: Medium)_
  - **Goal:** Provide clear explanation of color codes and status meanings.
  - **Tasks:**
    - Create visual legend component
    - Document status definitions (completed, started, not started, no status)
    - Add contextual help and tooltips
  - **Dependencies:** Plant layout visualization
  - **Status:** Not Started

---

### Phase 5 — Advanced Features

- **[ ] Historical Status Playback** _(Priority: Medium)_
  - **Goal:** Allow users to view status changes over time.
  - **Tasks:**
    - Implement status history tracking
    - Create timeline visualization
    - Add date/time selector for historical views
    - Generate status reports for specific time periods
  - **Dependencies:** Status tracking implementation (Phase 3)
  - **Status:** Not Started

- **[ ] Production Readiness Dashboard** _(Priority: Medium)_
  - **Goal:** Provide high-level overview of production readiness.
  - **Tasks:**
    - Calculate overall plant readiness percentage
    - Identify critical path blockers
    - Show estimated time to full production readiness
    - Create executive summary view
  - **Dependencies:** Asset status aggregation (Phase 3)
  - **Status:** Not Started

- **[ ] Mobile-Optimized View** _(Priority: Low)_
  - **Goal:** Ensure monitoring board is usable on mobile devices.
  - **Tasks:**
    - Implement responsive design for small screens
    - Optimize touch interactions
    - Create simplified mobile view with most critical information
  - **Dependencies:** UI development (Phase 4)
  - **Status:** Not Started

---

## ✅ RECENTLY COMPLETED

_No completed items yet — app is in planning phase._

---

## 🎯 Success Criteria

### MVP (v1.0) Acceptance Criteria

1. **Plant Layout Visualization:**
   - ✅ Visual representation of actual plant floor layout
   - ✅ All production stations/cells displayed with correct positioning
   - ✅ Color-coded status indicators visible at a glance

2. **Status Tracking:**
   - ✅ Real-time status updates without page refresh
   - ✅ Accurate reflection of MO completion status
   - ✅ Support for multiple task types per station

3. **Integration:**
   - ✅ Seamless linking to existing Assets and MOs
   - ✅ Click-through navigation to detail pages
   - ✅ Consistent with mockCMMS authentication and permissions

4. **Performance:**
   - ✅ Page load time < 2 seconds
   - ✅ Status updates appear within 5 seconds of MO change
   - ✅ Supports monitoring of at least 50 stations simultaneously

5. **Usability:**
   - ✅ Intuitive color coding (matches industry standards)
   - ✅ Clear labeling of all stations and task types
   - ✅ Responsive design works on desktop and tablet

---

## 📊 Technical Requirements

- **Environment Toggle:** `MONITORING_ENABLED=True|False` in `.env`
- **Database:** Extend existing SQLite/PostgreSQL schema
- **Frontend:** Vanilla JavaScript (ES6+), CSS3, HTML5
- **Backend:** Python 3.12+, Flask, SQLAlchemy
- **Real-Time:** Server-Sent Events (SSE) recommended for simplicity
- **Testing:** 80%+ coverage (pytest backend, Jest frontend, Playwright E2E)

---

## 🔗 Related Documentation

- [Monitoring App Concept & Architecture](monitoring_concept_and_modular_architecture.md)
- [Main mockCMMS Roadmap](../mockCMMS_roadmap.md)
- [Planning App Roadmap](../../apps/planning/docs/planning_roadmap.md)
- [Reporting App Roadmap](../../apps/reporting/docs/reporting_roadmap.md)

---

_Last Updated: March 12, 2026_
