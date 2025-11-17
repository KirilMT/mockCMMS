# Planning Module Integration Action Plan

_Last Updated: 2025-11-17_

This document is a living, step-by-step action plan for integrating the legacy `workforceManager` application into the main `mockCMMS` project as the **Planning** module. It focuses on backend planning logic and clean, technician-friendly UI.

The plan is organized by phases, each including specific testing points to ensure quality at every stage. Each task should be updated with status as work progresses.

---

## 1. Objectives & Scope

**Primary goals:**

- Integrate `workforceManager` into `mockCMMS` as a **Planning** page/module.
- Remove the legacy Excel-based workflow and mappings.
- Preserve and improve the **skill-based automatic task assignment** logic.
- Provide a **Planning UI** with:
  - Table view and **Gantt chart view** (critical requirement).
  - Shift break planning and weekend planning modes.
  - Role-based capabilities for technicians, supervisors, and planners.
- Enforce planning constraints based on **spare parts availability** and **technician skills/availability**.
- Keep the architecture **modular**, testable, and easy to extend.

Out of scope for the initial phases: full SCADA integration, fully automated REP task assignment, and automatic spare parts ordering. These are captured later as future phases.

---

## 2. Phase 0 – Discovery & Architecture Alignment

**Goal:** Ensure a clear understanding of current code, data model, and integration points before implementing changes.

- [ ] 2.1. Document the current `workforceManager` internals
  - [ ] 2.1.1. Identify where the skill-based assignment algorithm lives (e.g., `apps/workforceManager/src/services/task_assigner.py`).
  - [ ] 2.1.2. Map all inputs/outputs of the assignment logic (tasks, technicians, constraints, schedules).
  - [ ] 2.1.3. List Excel-specific components to be deprecated (data extraction, mapping UI, related services).

- [ ] 2.2. Document current `mockCMMS` planning-related data
  - [ ] 2.2.1. Confirm how MOs, PMs, and REP tickets are represented in the main database.
  - [ ] 2.2.2. Identify fields relevant for planning (e.g., `schedule_name`, `justification`, `asset_id`, `labour_count`, `estimated_completion_time`, `order_type`).
  - [ ] 2.2.3. Identify how spare parts are linked to MOs and how stock levels are stored.

- [ ] 2.3. Define integration boundaries
  - [ ] 2.3.1. Decide how the Planning module will obtain tasks: via existing API routes (`src/routes/api.py`) or direct DB access.
  - [ ] 2.3.2. Decide how technician data and skills are sourced (shared DB tables vs. module-specific tables).
  - [ ] 2.3.3. Define how Planning results will be stored: new tables vs. extending existing MOs with planning/assignment metadata.

- [ ] 2.4. Update architecture documentation
  - [ ] 2.4.1. Add a high-level diagram in `docs/` describing data flow: CMMS tasks → Planning engine → Technician assignments → UI.
  - [ ] 2.4.2. Link this plan from `docs/mockCMMS_roadmap.md` under the `workforceManager` section.

- [ ] 2.5. **Testing & Validation**
  - [ ] 2.5.1. **Peer Review:** Conduct a formal peer review of all architectural documents and data flow diagrams to ensure consensus and identify potential flaws before implementation begins.
  - [ ] 2.5.2. **Data Mapping Validation:** Create a script to pull sample data from the `mockCMMS` database and manually verify it against the proposed planning data model to catch discrepancies early.

---

## 3. Phase 1 – Core Data & Domain Model

**Goal:** Define a clean domain model for planning that no longer depends on Excel and is reusable by the assignment algorithm.

- [ ] 3.1. Define Planning domain entities
  - [ ] 3.1.1. Design models for **PlanningTask**, **Technician**, **TechnicianSkill**, **Shift**, and **Schedule**.
  - [ ] 3.1.2. Ensure tasks can support **multiple required skills** and associated effort per skill if needed.
  - [ ] 3.1.3. Ensure technician models capture availability (e.g., shift, hours, status).

- [ ] 3.2. Map CMMS data to Planning entities
  - [ ] 3.2.1. Create a transformation layer that converts MOs/PMs/tickets into `PlanningTask` objects.
  - [ ] 3.2.2. Ensure mapping covers fields equivalent to the old Excel columns:
    - ID, schedule name, planning notes, line/asset, required technicians, estimated completion time, type, day/shift.
  - [ ] 3.2.3. Add validation to reject or flag tasks with incomplete critical data.

- [ ] 3.3. Integrate spare parts constraints
  - [ ] 3.3.1. Define how required spare parts per task are represented in the domain model.
  - [ ] 3.3.2. Implement a service that checks stock levels for all parts linked to planned tasks.
  - [ ] 3.3.3. Define logic: tasks requiring non-stocked parts must be excluded from the plan or flagged as "cannot plan" with reason.

- [ ] 3.4. Prepare for manpower status integration
  - [ ] 3.4.1. Reserve fields in technician domain model for status (onsite, off, sick, vacation).
  - [ ] 3.4.2. Define an interface for a future "manpower status API" (backed by JSON for now).

- [ ] 3.5. **Testing & Validation**
  - [ ] 3.5.1. **Unit Tests (Domain Models):** Write comprehensive unit tests for all new domain models (`PlanningTask`, `Technician`, etc.) to validate data types, constraints, and default values.
  - [ ] 3.5.2. **Unit Tests (Transformation Layer):** Test the CMMS-to-Planning data transformation layer with various inputs, including malformed data, to ensure it is robust.
  - [ ] 3.5.3. **Integration Tests (Spare Parts):** Create integration tests for the spare parts constraint service. These tests should use a test database to confirm that tasks are correctly filtered based on mock inventory levels.

---

## 4. Phase 2 – Planning Engine & Skill-Based Assignment

**Goal:** Reuse and adapt the legacy `workforceManager` logic to work on the new Planning domain, without Excel.

- [ ] 4.1. Isolate and refactor the assignment algorithm
  - [ ] 4.1.1. Extract the core skill-based assignment functions into a reusable service (if not already isolated).
  - [ ] 4.1.2. Replace Excel-specific inputs with the new `PlanningTask` and `Technician` objects.
  - [ ] 4.1.3. Add unit tests to cover:
    - Matching tasks to technicians based on skills.
    - Multi-skill tasks.
    - Team size optimization.
    - Duration adjustments by team composition.
    - Fair workload distribution.

- [ ] 4.2. Implement shift-break planning logic
  - [ ] 4.2.1. Define a "shift-break planning" mode with a 30-minute window per shift.
  - [ ] 4.2.2. Encode prioritization rules:
    - Critical tasks affecting production first.
    - REP/corrective tasks next.
    - PM and project tasks last.
  - [ ] 4.2.3. Integrate SCADA-like data (initially via JSON) to identify assets with long downtime or frequent occurrences.
  - [ ] 4.2.4. Use logic from the external repo (`CMMS-SCADA-Excel-DataProcessor`) as a reference for REP task prioritization.

- [ ] 4.3. Implement weekend planning logic
  - [ ] 4.3.1. Define rules for selecting weekend tasks (frequency-based PMs, outstanding REP tasks, etc.).
  - [ ] 4.3.2. Apply the same skill-based assignment engine with weekend-specific constraints (e.g., fewer technicians, special shifts).
  - [ ] 4.3.3. Ensure bidirectional consistency: planning must consider available technicians and skills for the target dates.

- [ ] 4.4. Expose planning results in a structured format
  - [ ] 4.4.1. Define a `PlanningResult` structure capturing assignments, unassigned tasks, and reasons.
  - [ ] 4.4.2. Persist results so they can be reloaded by the UI and referenced by reports.

- [ ] 4.5. **Testing & Validation**
  - [ ] 4.5.1. **Unit Tests (Assignment Algorithm):** Write extensive unit tests for the core assignment logic, covering:
    - Correctly matching tasks to technicians based on single and multiple skills.
    - Optimizing team size based on task requirements.
    - Adjusting task duration based on team composition.
    - Ensuring fair workload distribution among technicians.
    - Handling cases where no suitable technician is available.
  - [ ] 4.5.2. **Integration Tests (Planning Modes):** Create integration tests for both "shift-break" and "weekend" planning modes. These tests should simulate a full run with a set of tasks and technicians, then validate the generated `PlanningResult` for correctness.
  - [ ] 4.5.3. **Performance Testing:** Establish baseline performance tests to measure the time taken to generate a plan for a representative number of tasks (e.g., 100 tasks, 20 technicians). This helps identify bottlenecks early.

---

## 5. Phase 3 – Planning Page UI & Integration

**Goal:** Create the Planning page within `mockCMMS` that embeds `workforceManager` functionality and presents results clearly.

- [ ] 5.1. Planning page routing & layout
  - [ ] 5.1.1. Add a **Planning** route to the main app (e.g., `src/routes/main.py` or a dedicated blueprint).
  - [ ] 5.1.2. Integrate `workforceManager` blueprint/routes into the main app under `/planning` (renamed appropriately).
  - [ ] 5.1.3. Create a main Planning template that adheres to the existing `base.html` structure (navigation, styling).

- [ ] 5.2. Planning page modes (Shift Break vs Weekend)
  - [ ] 5.2.1. Add UI controls (e.g., two buttons or tabs) for **Shift Break Planning** and **Weekend Planning** modes.
  - [ ] 5.2.2. Ensure mode selection triggers the correct backend planning logic and refreshes the views.

- [ ] 5.3. Table view implementation
  - [ ] 5.3.1. Build a table view for planned assignments using the same advanced table patterns as Assets/MOs/Spare Parts.
  - [ ] 5.3.2. Support filtering, sorting, and search on key fields (asset, technician, shift, status, priority, etc.).
  - [ ] 5.3.3. Add visual indicators for tasks that could not be planned (e.g., missing parts, no matching skills).

- [ ] 5.4. Gantt chart view (critical)
  - [ ] 5.4.1. Choose a Gantt visualization strategy (e.g., client-side JS library or custom timeline implementation).
  - [ ] 5.4.2. Design JSON/API data shape for Gantt data (tasks, start/end times, assigned technicians, status).
  - [ ] 5.4.3. Implement the Gantt chart view side-by-side or as a separate tab from the table view.
  - [ ] 5.4.4. Ensure interactions (hover, click, filtering) stay consistent with the table view.

- [ ] 5.5. Role-based capabilities
  - [ ] 5.5.1. Define roles: Technician, Supervisor, Maintenance Planner (reusing existing auth/roles where possible).
  - [ ] 5.5.2. For Technicians: read-only access with filters and search to see assigned tasks.
  - [ ] 5.5.3. For Supervisors: ability to adjust assignments on the fly, including adding tasks similar to the old "Additional Task Creation" modal.
  - [ ] 5.5.4. For Maintenance Planners: ability to trigger planning runs, lock/unlock schedules, and manage planning parameters.

- [ ] 5.6. Export options
  - [ ] 5.6.1. Design export formats (e.g., PDF and Excel) for the current plan.
  - [ ] 5.6.2. Implement export endpoints that generate downloads from the current `PlanningResult`.
  - [ ] 5.6.3. Ensure exports integrate with or reuse patterns from the `reports` app where appropriate.

- [ ] 5.7. **Testing & Validation**
  - [ ] 5.7.1. **API Endpoint Testing:** Write tests for all new API endpoints that serve data to the UI (e.g., fetching plan data, Gantt chart data) to ensure they are secure and return the correct data shape.
  - [ ] 5.7.2. **Component-Level UI Testing:** For complex UI components like the Gantt chart, use a framework (like Playwright or Selenium) to test interactions (e.g., filtering, hovering) in isolation.
  - [ ] 5.7.3. **End-to-End (E2E) User Flow Testing:** Create E2E tests that simulate user journeys:
    - A Planner logs in, generates a weekend plan, and verifies the result.
    - A Technician logs in and views their assigned tasks on the Gantt chart.
    - A Supervisor logs in and adds an ad-hoc task to the current shift plan.
  - [ ] 5.7.4. **User Acceptance Testing (UAT):** Conduct manual UAT sessions with stakeholders representing each role (Planner, Supervisor, Technician) to gather feedback on usability and correctness.

---

## 6. Phase 4 – Cleanup & Legacy Removal

**Goal:** Retire legacy `workforceManager` pieces that are no longer needed after integration.

- [ ] 6.1. Remove Excel-based workflow components
  - [ ] 6.1.1. Delete or archive Excel extraction scripts and services in `apps/workforceManager`.
  - [ ] 6.1.2. Remove the Manage Mappings page and its logic.

- [ ] 6.2. Remove or replace obsolete UI components
  - [ ] 6.2.1. Remove the standalone output HTML export for the old dashboard; ensure Planning UI replaces it.
  - [ ] 6.2.2. Remove the "Absent Technicians" modal once manpower status API simulation is in place.
  - [ ] 6.2.3. Mark legacy "REP Task Assignment" flows as deprecated in the codebase, preparing for full automation.

- [ ] 6.3. Update documentation
  - [ ] 6.3.1. Update `apps/workforceManager/README.md` to reflect integrated role and new architecture.
  - [ ] 6.3.2. Update the root `README.md` and `docs/mockCMMS_roadmap.md` to reference the Planning module and its status.

- [ ] 6.4. **Testing & Validation**
  - [ ] 6.4.1. **Regression Testing:** After removing legacy code, run the complete test suite (unit, integration, and E2E) to ensure that no existing functionality has been broken.
  - [ ] 6.4.2. **Code Quality Scan:** Run static analysis and code quality tools to identify and remove any dead or unreachable code that was left behind.

---

## 7. Phase 5 – Future Enhancements

These items are intentionally out of scope for the initial Planning integration but should be considered in future sprints.

- [ ] 7.1. Manpower status API (JSON-backed)
  - [ ] 7.1.1. Implement a service (initially using JSON) that exposes technician status: onsite, off, sick, vacation.
  - [ ] 7.1.2. Integrate this service into the planning engine so unavailable technicians are automatically excluded.
  - [ ] 7.1.3. **Testing:** Write integration tests to verify that the planning engine correctly excludes unavailable technicians based on the API's output.

- [ ] 7.2. Advanced REP task assignment
  - [ ] 7.2.1. Design a text-analysis-based approach for REP MOs (title/description based classification and prioritization).
  - [ ] 7.2.2. Reuse or adapt logic from `CMMS-SCADA-Excel-DataProcessor` to inform REP planning.
  - [ ] 7.2.3. Integrate REP auto-assignment into the main planning engine and UI.
  - [ ] 7.2.4. **Testing:** Develop unit tests for the text analysis logic and E2E tests to validate that REP tasks are correctly prioritized and assigned.

- [ ] 7.3. Automatic spare parts ordering
  - [ ] 7.3.1. Define a rule set for when to automatically generate spare parts orders ahead of planned tasks (e.g., previous shift).
  - [ ] 7.3.2. Implement a background job or service that checks upcoming tasks and triggers orders based on inventory and lead time.
  - [ ] 7.3.3. Integrate these orders with the core CMMS spares management module.
  - [ ] 7.3.4. **Testing:** Create tests for the background job to ensure orders are triggered correctly based on various inventory and timing scenarios.

- [ ] 7.4. Planning simulations and optimization
  - [ ] 7.4.1. Add a "simulation" mode that allows planners to test different scenarios without committing changes.
  - [ ] 7.4.2. Explore algorithmic or heuristic optimization (e.g., load balancing, minimizing technician travel, respecting preferences).
  - [ ] 7.4.3. **Testing:** Test the simulation mode to ensure it accurately reflects planning outcomes without altering the live plan. Validate that optimization algorithms produce measurably better results against a baseline.

---

## 8. Working Agreements

- This file is the **canonical action plan** for the Planning module.
- As tasks are completed, mark them as `[x]` and, if useful, add short notes or links to PRs.
- New ideas or changes discovered during implementation should be added as new checklist items under the relevant phase.
- High-level priorities and cross-app impacts should continue to be tracked in `docs/mockCMMS_roadmap.md`.

