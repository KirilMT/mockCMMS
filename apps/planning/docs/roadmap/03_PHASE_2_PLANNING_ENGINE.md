# Phase 2 – Planning Engine & Skill-Based Assignment

**Goal:** Reuse and adapt the legacy `planning` logic to work on the new Planning domain, without Excel.

**Status:** ✅ **COMPLETE - Hybrid Approach** (November 18, 2025)

**📋 Implementation Roadmap:** See `docs/phase2_hybrid_roadmap.md` for detailed implementation plan

**✅ Hybrid Approach Completed:**

- ✅ **Priority 1: Shift-break mode** - 30-minute window + REP-first priority (4.2.1, 4.2.2)
- ✅ **Priority 2: Weekend mode** - PM frequency filtering + PM-first priority (4.3.1, 4.3.2)
- ⏭️ **Deferred: SCADA integration** - Phase 5 enhancement (4.2.3, 4.2.4)
- ⏭️ **Deferred: Advanced testing** - Alongside Phase 3 (4.5.2, 4.5.3)

**Implementation Summary:**

**Core Components Created:**

1. **`planning_result.py`** - Comprehensive result data structures
   - `PlanningResult` - Main container for all planning outcomes
   - `TaskAssignment` - Successfully assigned tasks with details
   - `UnassignedTask` - Failed assignments with reasons
   - `TechnicianWorkload` - Workload tracking per technician
   - `PlanningStatistics` - Overall metrics and success rates
   - `UnassignedReason` enum - Structured failure reasons

2. **`planning_engine.py`** - Clean, SQLAlchemy-based assignment engine
   - `PlanningEngine` class - Main algorithm implementation
   - Skill-based matching (single and multi-skill)
   - Team size optimization
   - Duration adjustment based on team composition
   - Workload balancing across technicians
   - Priority-based task ordering
   - Constraint validation (spare parts, skills, availability)
   - Comprehensive logging and error handling

**Algorithm Features:**

- ✅ Filters tasks by spare parts availability
- ✅ Validates task data completeness
- ✅ Matches technicians based on required skills
- ✅ Handles multi-skill requirements
- ✅ Optimizes team size (can assign more techs than required if beneficial)
- ✅ Adjusts duration based on team efficiency
- ✅ Balances workload fairly (selects techs with most available time)
- ✅ Supports different planning modes (shift-break vs weekend)
- ✅ Provides detailed reasons for unassigned tasks
- ✅ Persists assignments to PlanningTask records

**Test Coverage (13 tests - all passing ✅):**

- Skill-based matching (single skill)
- Multi-skill task matching
- No matching skills → unassigned
- Team size optimization
- Insufficient team size → unassigned
- Duration adjustment by team composition
- Workload distribution across technicians
- Spare parts constraint enforcement
- Invalid task data → unassigned
- Priority ordering (shift-break mode)
- Planning result statistics calculation

**Key Differences from Legacy:**

- ❌ NO Excel dependencies
- ❌ NO raw SQLite queries
- ✅ Uses SQLAlchemy ORM throughout
- ✅ Clean separation of concerns
- ✅ Testable, modular design
- ✅ Structured error handling
- ✅ Comprehensive result objects

**Implementation Strategy:**

- Create NEW planning engine service (`planning_engine.py`) using domain models
- Extract reusable algorithms from legacy `task_assigner.py`
- Replace Excel/SQLite data structures with SQLAlchemy models
- Implement test-driven development for each component

**Key Files:**

- `apps/planning/src/services/planning_engine.py` - NEW assignment engine ✅
- `apps/planning/src/services/planning_result.py` - NEW result structure ✅
- `apps/planning/tests/test_planning_engine.py` - NEW comprehensive tests ✅
- Legacy reference: `apps/planning/src/services/task_assigner.py` (to be deprecated in Phase 5)

- [x] 4.1. Isolate and refactor the assignment algorithm
  - [x] 4.1.1. Extract the core skill-based assignment functions into a reusable service (if not already isolated). ✅ **Created** `planning_engine.py` with clean PlanningEngine class
  - [x] 4.1.2. Replace Excel-specific inputs with the new `PlanningTask` and `Technician` objects. ✅ Uses SQLAlchemy models throughout
  - [x] 4.1.3. Add unit tests to cover: ✅ **Created** `test_planning_engine.py` with 13 comprehensive tests
    - Matching tasks to technicians based on skills. ✅
    - Multi-skill tasks. ✅
    - Team size optimization. ✅
    - Duration adjustments by team composition. ✅
    - Fair workload distribution. ✅

- [ ] 4.2. Implement shift-break planning logic
  - [x] 4.2.1. Define a "shift-break planning" mode with a 30-minute window per shift. ✅ **COMPLETE** - Implemented in `planning_engine.py`
  - [x] 4.2.2. Encode prioritization rules: ✅ **COMPLETE** - REP/Corrective prioritized over PM/Project in shift-break mode
    - Critical tasks affecting production first. ✅
    - REP/corrective tasks next. ✅
    - PM and project tasks last. ✅
  - [ ] 4.2.3. Integrate SCADA-like data (initially via JSON) to identify assets with long downtime or frequent occurrences. ⏭️ **DEFERRED to Phase 5**
  - [ ] 4.2.4. Use logic from the external repo (`CMMS-SCADA-Excel-DataProcessor`) as a reference for REP task prioritization. ⏭️ **DEFERRED to Phase 5**

- [x] 4.3. Implement weekend planning logic
  - [x] 4.3.1. Define rules for selecting weekend tasks (frequency-based PMs, outstanding REP tasks, etc.). ✅ **COMPLETE** - `_filter_weekend_tasks()` filters by PM frequency
  - [x] 4.3.2. Apply the same skill-based assignment engine with weekend-specific constraints (e.g., fewer technicians, special shifts). ✅ **COMPLETE** - PM-first priority, no time limits
  - [x] 4.3.3. Ensure bidirectional consistency: planning must consider available technicians and skills for the target dates. ✅ **Already implemented** via technician availability filtering

- [x] 4.4. Expose planning results in a structured format
  - [x] 4.4.1. Define a `PlanningResult` structure capturing assignments, unassigned tasks, and reasons. ✅ **Created** `planning_result.py` with comprehensive data structures
  - [x] 4.4.2. Persist results so they can be reloaded by the UI and referenced by reports. ✅ PlanningTask records updated with assignments in `planning_engine.py`

- [x] 4.5. **Testing & Validation**
  - [x] 4.5.1. **Unit Tests (Assignment Algorithm):** Write extensive unit tests for the core assignment logic, covering: ✅ **COMPLETE** - All 13 tests passing
    - Correctly matching tasks to technicians based on single and multiple skills. ✅
    - Optimizing team size based on task requirements. ✅
    - Adjusting task duration based on team composition. ✅
    - Ensuring fair workload distribution among technicians. ✅
    - Handling cases where no suitable technician is available. ✅
  - [ ] 4.5.2. **Integration Tests (Planning Modes):** Create integration tests for both "shift-break" and "weekend" planning modes. These tests should simulate a full run with a set of tasks and technicians, then validate the generated `PlanningResult` for correctness. ⏭️ **DEFERRED** - Can be developed alongside Phase 3 UI
  - [ ] 4.5.3. **Performance Testing:** Establish baseline performance tests to measure the time taken to generate a plan for a representative number of tasks (e.g., 100 tasks, 20 technicians). This helps identify bottlenecks early. ⏭️ **DEFERRED** - Can be added during Phase 3 development
