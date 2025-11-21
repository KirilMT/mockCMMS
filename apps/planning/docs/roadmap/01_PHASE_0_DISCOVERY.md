# Phase 0 – Discovery & Architecture Alignment

**Goal:** Ensure a clear understanding of current code, data model, and integration points before implementing changes.

**Status:** ✅ **COMPLETE** (November 18, 2025)

**Key Decisions Made:**
- ✅ Direct database access for efficiency (not API-based)
- ✅ Shared Technician/Skill tables as single source of truth
- ✅ Planning results stored by extending MaintenanceOrder model
- ✅ Assignment algorithm located in `apps/planning/src/services/task_assigner.py`

**Documentation Created:**
- ✅ Data flow diagram: `docs/planning_data_flow.md`
- ✅ Peer review: `docs/phase0_peer_review.md`
- ✅ Data validation script: `validate_data_mapping.py`

- [x] 2.1. Document the current `planning` internals
  - [x] 2.1.1. Identify where the skill-based assignment algorithm lives (e.g., `apps/planning/src/services/task_assigner.py`).
  - [x] 2.1.2. Map all inputs/outputs of the assignment logic (tasks, technicians, constraints, schedules).
  - [x] 2.1.3. List Excel-specific components to be deprecated (data extraction, mapping UI, related services).

- [x] 2.2. Document current `mockCMMS` planning-related data
  - [x] 2.2.1. Confirm how MOs, PMs, and REP tickets are represented in the main database.
  - [x] 2.2.2. Identify fields relevant for planning (e.g., `schedule_name`, `justification`, `asset_id`, `labour_count`, `estimated_completion_time`, `order_type`).
  - [x] 2.2.3. Identify how spare parts are linked to MOs and how stock levels are stored. **Note:** A `SparePart` model with `stock_quantity` exists, but there is no direct relationship defined between `MaintenanceOrder` and `SparePart` in the database schema. This link will need to be established.

- [x] 2.3. Define integration boundaries
  - [x] 2.3.1. Decide how the Planning module will obtain tasks: via existing API routes (`src/routes/api.py`) or direct DB access. **Decision:** Direct database access will be used for efficiency, as the module will be integrated into the main application.
  - [x] 2.3.2. Decide how technician data and skills are sourced (shared DB tables vs. module-specific tables). **Decision:** Shared `Technician` and `Skill` tables in the main `mockCMMS` database will be the single source of truth.
  - [x] 2.3.3. Define how Planning results will be stored: new tables vs. extending existing MOs with planning/assignment metadata. **Decision:** Planning results will be stored by extending the existing `MaintenanceOrder` model to include assignment and schedule details.

- [x] 2.4. Update architecture documentation
  - [x] 2.4.1. Add a high-level diagram in `docs/` describing data flow: CMMS tasks → Planning engine → Technician assignments → UI. ✅ **Created:** `docs/planning_data_flow.md`
  - [x] 2.4.2. Link this plan from `docs/mockCMMS_roadmap.md` under the `planning` section.

- [x] 2.5. **Testing & Validation**
  - [x] 2.5.1. **Peer Review:** Conduct a formal peer review of all architectural documents and data flow diagrams to ensure consensus and identify potential flaws before implementation begins. ✅ **Created:** `docs/phase0_peer_review.md`
  - [x] 2.5.2. **Data Mapping Validation:** Create a script to pull sample data from the `mockCMMS` database and manually verify it against the proposed planning data model to catch discrepancies early. ✅ **Created:** `validate_data_mapping.py`
