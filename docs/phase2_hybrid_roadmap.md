# Phase 2 Hybrid Implementation Roadmap

_Created: November 18, 2025_  
_Strategy: Option 3 - Hybrid Approach_

---

## Overview

This document outlines the specific implementation tasks for completing Phase 2 using the Hybrid Approach (Option 3). This approach focuses on implementing essential mode-specific planning constraints while deferring SCADA integration and advanced testing.

---

## Implementation Priorities

### 🎯 PRIORITY 1: Shift-Break Planning Mode (4.2.1, 4.2.2)

**Goal:** Enable 30-minute planning windows with strict priority enforcement for production shift breaks.

**Tasks:**

1. **Add 30-minute window constraint to planning engine**
   - Modify `PlanningEngine._assign_single_task()` to check if task duration fits within shift-break window
   - Add `max_task_duration` parameter for shift-break mode
   - Default: 30 minutes for shift-break mode, unlimited for weekend mode

2. **Enhance priority enforcement for shift-break mode**
   - Current: Sorts by priority but doesn't enforce strict rules
   - Needed: Reject low-priority tasks if higher-priority tasks are unassigned
   - Add validation: Critical/REP tasks must be attempted before PM/Project tasks

3. **Update test coverage**
   - Add test: `test_shift_break_30_minute_window()`
   - Add test: `test_shift_break_priority_enforcement()`

**Estimated Effort:** 2-3 hours

---

### 🎯 PRIORITY 2: Weekend Planning Mode (4.3.1, 4.3.2)

**Goal:** Implement frequency-based PM selection and weekend-specific constraints.

**Tasks:**

1. **Add PM frequency filtering**
   - Create helper function to filter tasks by `frequency` field
   - Weekend mode should select:
     - Weekly PMs
     - Monthly PMs (if scheduled this weekend)
     - Outstanding REP tasks
     - Deferred maintenance

2. **Implement weekend constraints**
   - Filter technicians by weekend shift availability
   - Allow longer task durations (no 30-minute limit)
   - Different priority ordering: PM-first instead of Critical-first

3. **Update test coverage**
   - Add test: `test_weekend_pm_frequency_selection()`
   - Add test: `test_weekend_shift_constraints()`

**Estimated Effort:** 2-3 hours

---

### ⏭️ DEFERRED: SCADA Integration (4.2.3, 4.2.4)

**Reason for Deferral:**
- Requires external data source setup
- Not blocking for UI development
- Can be added as Phase 5 enhancement

**Future Implementation:**
- Will be part of Phase 5 (Section 7.2 - Advanced REP task assignment)
- Will integrate with `CMMS-SCADA-Excel-DataProcessor` repository
- Will add JSON-backed SCADA data service

---

### ⏭️ DEFERRED: Advanced Testing (4.5.2, 4.5.3)

**Reason for Deferral:**
- Integration tests more valuable with UI in place
- Performance testing can happen alongside Phase 3
- Core algorithm already has 13 passing unit tests

**Future Implementation:**
- Integration tests during Phase 3 development
- Performance benchmarks before production deployment

---

## Implementation Details

### Shift-Break Mode Implementation

**File:** `apps/workforceManager/src/services/planning_engine.py`

**Changes Needed:**

```python
class PlanningEngine:
    def generate_plan(
        self,
        schedule: Schedule,
        planning_mode: str = "weekend",
        shift_duration_minutes: int = 720,
        check_parts: bool = True,
        max_task_duration: int = None  # NEW: Add time constraint
    ) -> PlanningResult:
        # ...existing code...
        
        # Set mode-specific constraints
        if planning_mode == "shift_break":
            max_task_duration = max_task_duration or 30  # 30-minute default
        else:
            max_task_duration = max_task_duration or shift_duration_minutes
        
        # Pass to assignment logic
        # ...
```

**New Helper Method:**

```python
def _fits_time_window(
    self,
    task_duration: int,
    max_allowed: int,
    mode: str
) -> bool:
    """Check if task fits within time window for mode."""
    if mode == "shift_break":
        return task_duration <= max_allowed
    return True  # No limit for weekend mode
```

---

### Weekend Mode Implementation

**File:** `apps/workforceManager/src/services/planning_engine.py`

**Changes Needed:**

```python
def _filter_weekend_tasks(
    self,
    tasks: List[Tuple[PlanningTask, MaintenanceOrder]]
) -> List[Tuple[PlanningTask, MaintenanceOrder]]:
    """Filter tasks suitable for weekend planning."""
    weekend_tasks = []
    
    for task, mo in tasks:
        # Include based on frequency
        if mo.frequency in ['Weekly', 'Monthly']:
            weekend_tasks.append((task, mo))
        # Include outstanding REP tasks
        elif mo.order_type == 'REP' and mo.status == 'Open':
            weekend_tasks.append((task, mo))
        # Include deferred maintenance
        elif mo.status == 'Deferred':
            weekend_tasks.append((task, mo))
    
    return weekend_tasks
```

**Priority Ordering Update:**

```python
def _prioritize_tasks(
    self,
    tasks: List[Tuple[PlanningTask, MaintenanceOrder]],
    planning_mode: str
) -> List[Tuple[PlanningTask, MaintenanceOrder]]:
    # ...existing priority maps...
    
    if planning_mode == "weekend":
        # Weekend: PM-first approach
        type_priority_weekend = {
            'PM': 1,
            'REP': 2,
            'Corrective': 3,
            'Project': 4
        }
    else:  # shift_break
        # Shift-break: Critical-first approach
        type_priority_shift_break = {
            'REP': 1,
            'Corrective': 2,
            'PM': 3,
            'Project': 4
        }
    # ...
```

---

## Test Plan

### New Tests to Add

**File:** `apps/workforceManager/tests/test_planning_modes.py` (NEW)

```python
# Test shift-break 30-minute window
def test_shift_break_30_minute_window():
    """Tasks over 30 minutes should be unassigned in shift-break mode."""
    # Create 45-minute task
    # Run in shift-break mode
    # Assert: task unassigned with reason "exceeds time window"

# Test shift-break priority enforcement
def test_shift_break_priority_enforcement():
    """Low-priority tasks should not block high-priority tasks."""
    # Create mix of Critical, High, Low tasks
    # Run in shift-break mode
    # Assert: Critical assigned first, even if Low is easier

# Test weekend PM frequency selection
def test_weekend_pm_frequency_selection():
    """Weekend mode should select weekly/monthly PMs."""
    # Create tasks with different frequencies
    # Run in weekend mode
    # Assert: Only appropriate frequency tasks selected

# Test weekend no time limit
def test_weekend_no_time_limit():
    """Weekend mode should accept long-duration tasks."""
    # Create 4-hour task
    # Run in weekend mode
    # Assert: task successfully assigned
```

---

## Success Criteria

Phase 2 Hybrid Implementation is complete when:

- ✅ Shift-break mode enforces 30-minute window
- ✅ Shift-break mode has strict Critical > REP > PM > Project ordering
- ✅ Weekend mode filters by PM frequency
- ✅ Weekend mode allows longer tasks
- ✅ Weekend mode prioritizes PMs over REP tasks
- ✅ All existing 13 tests still pass
- ✅ 4+ new mode-specific tests added and passing
- ✅ Documentation updated with mode differences

---

## Timeline Estimate

**Total Estimated Effort:** 4-6 hours

- Shift-break mode: 2-3 hours
- Weekend mode: 2-3 hours
- Testing & validation: Included above
- Documentation updates: 30 minutes

**Recommended Approach:**
1. Implement shift-break mode first (smaller scope)
2. Test thoroughly
3. Implement weekend mode
4. Test interaction between modes
5. Update documentation

---

## Next Steps After Hybrid Completion

Once Priority 1 & 2 are complete:

1. Mark tasks 4.2.1, 4.2.2, 4.3.1, 4.3.2 as complete
2. Update Phase 2 status to "COMPLETE (Hybrid)"
3. Proceed to Phase 3 - Planning Page UI & Integration
4. Return to deferred items (4.2.3, 4.2.4, 4.5.2, 4.5.3) in Phase 5 or alongside Phase 3

---

## References

- Main Action Plan: `docs/PLANNING_MODULE_ACTION_PLAN.md`
- Data Flow: `docs/planning_data_flow.md`
- Core Engine: `apps/workforceManager/src/services/planning_engine.py`
- Current Tests: `apps/workforceManager/tests/test_planning_engine.py`

