# Planning App Roadmap

_Updated June 1, 2026_

---

## ⚠️ INSTRUCTIONS FOR AI ASSISTANTS

**When working on this project:**

1. **Update "ACTIVE WORK" section** when sprint phases change or complete
2. **Update status** as work progresses
3. **Move completed items** to "Recently Completed" section
4. **Update "Last Updated" date** at the top when making changes

---

## 🔥 ACTIVE WORK

**Current Focus:** Legacy Code Analysis & Line Conditions
**Implementation Plan:** See [Detailed Phase Docs](roadmap/)

---

## 🚀 FUTURE FEATURES

This application handles skill-based task assignment. The next logical steps involve deeper integration and more advanced planning management features.

- **[IN PROGRESS] Line Conditions for Planning** _(Priority: High)_
  - **Goal:** Standardize the line conditions needed for task planning to ensure proper execution prerequisites.
  - **Implemented So Far:**
    - ✅ **Database Schema:** `line_conditions` and `task_line_conditions` tables created.
    - ✅ **Backend Logic:** `LineConditionManager` implemented.
    - ✅ **API Endpoints:** `get_line_conditions_api` and `manage_task_conditions_api` added.
    - ✅ **Dummy Data:** Population of default conditions and assignment to tasks.
    - ✅ **Manage Line Conditions UI:** Create/Modify/Delete global conditions via Planning Settings.
  - **Features to Implement:**
    - **Task Condition Assignment:** Implement a UI (initially manual) to assign Line Conditions to Maintenance Orders (MOs).
      - **Mechanism:** Multiple selection dropdown in the task/MO detail or edit view.
    - **Planning Table Integration:** Display the assigned Line Conditions in a dedicated column in the planning table.
    - **Visibility:** Make conditions visible to users with operations roles.
    - **Future Enhancement:** Automate condition assignment based on predefined logic or criteria.

- **[ ] Legacy Code Analysis & Cleanup Decision** _(Priority: **CRITICAL**)_ 🔴 **SUPER CRITICAL**
  - **Status:** Not Started
  - **Goal:** Comprehensive analysis of legacy WorkforceManager code.
  - **Reference:** [Phase 4 Cleanup Plan](roadmap/05_PHASE_4_CLEANUP.md)
  - **Background:** Current Planning App contains active legacy code (1500+ lines) from the original WorkforceManager repository alongside the new architecture.
  - **Criticality:** High risk of breaking working UI (Dashboard, Excel imports) if removed without analysis.
  - **Action:** Execute the "Deep Code Analysis" phase defined in the reference plan.

- **[ ] Advanced Planning Algorithms** _(Priority: Medium)_
  - **Goal:** Evolve beyond simple task assignment to holistic planning.
  - **Features:**
    - Develop logic for complex scheduling scenarios like multi-day shutdowns or holidays, factoring in technician availability.
    - Create a simulation feature that can optimize schedules before finalizing them.

---

## 📅 DETAILED PHASES

The Planning implementation is divided into detailed phases. Please refer to the specific documents for in-depth plans:

- **Phase 0:** [Discovery & Requirements](roadmap/01_PHASE_0_DISCOVERY.md)
- **Phase 1:** [Domain Model Implementation](roadmap/02_PHASE_1_DOMAIN_MODEL.md)
- **Phase 2:** [Planning Engine](roadmap/03_PHASE_2_PLANNING_ENGINE.md)
- **Phase 3:** [UI Integration](roadmap/04_PHASE_3_UI_INTEGRATION.md)
- **Phase 4:** [Cleanup & Legacy Removal](roadmap/05_PHASE_4_CLEANUP.md)
- **Phase 5:** [Future Features](roadmap/06_PHASE_5_FUTURE.md)
