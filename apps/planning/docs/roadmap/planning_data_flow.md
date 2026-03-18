# Planning Module Data Flow Architecture

_Created: November 18, 2025_

This document describes the data flow architecture for the Planning module integration into mockCMMS.

---

## High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        mockCMMS Database (SQLAlchemy)                   │
│  ┌──────────────┐  ┌──────────┐  ┌───────┐  ┌──────────┐  ┌────────┐  │
│  │MaintenanceOrder│  │Technician│  │ Skill │  │SparePart │  │  Asset │  │
│  └──────┬───────┘  └─────┬────┘  └───┬───┘  └────┬─────┘  └───┬────┘  │
└─────────┼────────────────┼───────────┼───────────┼─────────────┼───────┘
          │                │           │           │             │
          ▼                ▼           ▼           ▼             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   Data Transformation Layer                              │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  data_transformation.py                                          │  │
│  │  • transform_mo_to_planning_task()                               │  │
│  │  • validate_task_data()                                          │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  inventory_service.py                                            │  │
│  │  • check_spare_parts_availability()                              │  │
│  │  • get_tasks_with_insufficient_parts()                           │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     Planning Domain Models                               │
│  ┌───────────────┐  ┌──────────┐  ┌─────────────────┐  ┌────────────┐ │
│  │ PlanningTask  │  │ Schedule │  │ TechnicianSkill │  │   Shift    │ │
│  │ • mo_id       │  │ • name   │  │ • tech_id       │  │ • name     │ │
│  │ • schedule_id │  │ • dates  │  │ • skill_id      │  │ • times    │ │
│  │ • status      │  │ • status │  │ • skill_level   │  │            │ │
│  │ • assigned_to │  │          │  │                 │  │            │ │
│  └───────────────┘  └──────────┘  └─────────────────┘  └────────────┘ │
└────────────────────────────────────────��────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Planning Engine (Phase 2)                           │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  task_assigner.py                                                │  │
│  │  • Skill-based matching                                          │  │
│  │  • Team size optimization                                        │  │
│  │  • Workload balancing                                            │  │
│  │  • Constraint validation (parts, skills, availability)           │  │
│  └────────────────────────────────────────────��─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Planning Results                                 │
│  ┌─���──────────────────────────────────���─────────────────────────────┐  │
│  │  PlanningResult Structure                                        │  │
│  │  • Assigned tasks (with technician, timing)                      │  │
│  │  • Unassigned tasks (with reasons)                               │  │
│  │  • Workload summary per technician                               │  │
│  │  • Constraint violations                                         │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          Planning UI (Phase 3)                           │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────────────┐  │
│  │  Table View    │  │  Gantt Chart   │  │  Role-Based Controls    │  │
│  │  • Filter      │  │  • Timeline    │  │  • Planner: Run/Lock    │  │
│  │  • Sort        │  │  • Drag/Drop   │  │  • Supervisor: Adjust   │  │
│  │  • Search      │  │  • Hover Info  │  │  • Technician: View     │  │
│  └────────────────┘  └────────────────┘  └─────────────────────────┘  │
└──────────────────────────────────────────────���──────────────────────────┘
```

---

## Detailed Flow Descriptions

### 1. Data Ingestion (Phase 1 - Complete)

**Source:** mockCMMS Database

- `MaintenanceOrder` table contains all PM, REP, and corrective tasks
- `Technician` table contains planning information
- `Skill` table defines available competencies
- `SparePart` table tracks inventory
- `Asset` table defines equipment

**Process:**

1. Planning module queries MaintenanceOrder records based on criteria:
   - Schedule date ranges
   - Order types (PM/REP/Corrective)
   - Status (Open, In Progress)
   - Priority levels

2. For each MaintenanceOrder, the transformation layer:
   - Validates required fields (completion time, labour count)
   - Checks spare parts availability
   - Creates PlanningTask domain object

**Output:** List of validated PlanningTask objects ready for assignment

---

### 2. Constraint Checking (Phase 1 - Complete)

**Spare Parts Constraint:**

```python
# For each MaintenanceOrder
is_available, details = check_spare_parts_availability(mo)
# Returns:
# - is_available: True/False
# - details: {part_id: {required, available, sufficient}}
```

**Technician Availability:**

```python
# Check technician status
technician.availability_status  # "Available", "On Leave", "Sick", "Vacation"
technician.shift  # Shift assignment with times
```

**Skill Requirements:**

```python
# Task requirements
task.required_skills  # List of Skill objects
# Technician capabilities
technician.skills  # List of TechnicianSkill with skill_level
```

---

### 3. Planning Engine (Phase 2 - To Be Implemented)

**Input:**

- List of PlanningTask objects (filtered for parts availability)
- List of available Technician objects (filtered by availability_status)
- Schedule parameters (shift times, date range, mode)

**Algorithm Flow:**

```
1. Filter plannable tasks
   ├─ Exclude tasks with insufficient parts
   ├─ Exclude tasks with incomplete data
   └─ Prioritize by:
      ├─ Critical (production impact)
      ├─ REP/Corrective
      └─ PM/Project

2. For each task (in priority order):
   ├─ Find technicians with matching skills
   ├─ Check technician availability and workload
   ���─ Optimize team size (balance efficiency vs. resources)
   ├─ Calculate duration based on team composition
   ├─ Assign time slot considering:
   │  ├─ Shift constraints
   │  ├─ Break times
   │  └─ Existing assignments
   └─ Create assignment or flag as unassignable

3. Balance workload
   ├─ Distribute tasks evenly across technicians
   ├─ Avoid overloading individuals
   └─ Consider skill development opportunities
```

**Output:** PlanningResult object

---

### 4. Result Persistence (Phase 2)

**Storage Strategy:**

- Update `PlanningTask` records with:
  - `schedule_id` → Links to Schedule
  - `assigned_technician_id` → Links to Technician
  - `planned_start_time` and `planned_end_time`
  - `status` → "Planned"

- Create/Update `Schedule` record:
  - `planning_status` → "Draft" or "Published"
  - Tracks all PlanningTasks for a planning period

**Query Pattern:**

```python
# Retrieve a complete plan
schedule = Schedule.query.get(schedule_id)
tasks = schedule.planned_tasks  # All PlanningTask objects
for task in tasks:
    mo = task.maintenance_order  # Original MO
    tech = task.assigned_technician  # Assigned worker
```

---

### 5. UI Presentation (Phase 3 - To Be Implemented)

**Table View Data:**

```json
{
  "task_id": 123,
  "description": "Monthly PM - Asset XYZ",
  "asset": "Paint Line 1 - Robot A",
  "assigned_to": "John Doe",
  "shift": "Day Shift (07:00-19:00)",
  "start_time": "2025-11-18 08:00",
  "end_time": "2025-11-18 10:00",
  "status": "Planned",
  "priority": "High",
  "parts_available": true,
  "skills_required": ["Electrical", "Mechanical"]
}
```

**Gantt Chart Data:**

```json
{
  "tasks": [
    {
      "id": 123,
      "name": "Monthly PM - Asset XYZ",
      "start": "2025-11-18T08:00:00",
      "end": "2025-11-18T10:00:00",
      "resource": "John Doe",
      "progress": 0,
      "dependencies": []
    }
  ],
  "resources": [
    {
      "id": 1,
      "name": "John Doe",
      "shift": "Day",
      "skills": ["Electrical", "Mechanical"]
    }
  ]
}
```

---

## Data Flow by Planning Mode

### Shift-Break Planning Mode

**Characteristics:**

- 30-minute planning window per shift
- Focus on urgent/critical tasks
- Limited time for execution

**Priority Order:**

1. Critical tasks affecting production
2. REP/corrective tasks (high occurrence/downtime)
3. Quick PMs that fit the window
4. Project tasks (if time permits)

**Flow:**

```
CMMS Tasks → Filter by urgency → Check parts →
→ Assign to available shift techs → 30-min windows → UI
```

### Weekend Planning Mode

**Characteristics:**

- Multi-day planning window (Saturday-Sunday)
- Focus on scheduled maintenance
- More technician availability

**Priority Order:**

1. Frequency-based PMs due this period
2. Outstanding REP tasks
3. Deferred maintenance
4. Project work

**Flow:**

```
CMMS Tasks → Filter by schedule/frequency → Check parts →
→ Assign to weekend crew → Multi-hour blocks → UI
```

---

## Integration Points

### 1. API Routes (Phase 3)

```
GET  /planning/schedules          # List all schedules
POST /planning/schedules          # Create new schedule
GET  /planning/schedules/{id}     # Get plan details
PUT  /planning/schedules/{id}     # Update/lock schedule
GET  /planning/gantt/{id}         # Gantt chart data
POST /planning/assign             # Run planning algorithm
```

### 2. Report Integration

```
Planning Results → reporting module → PDF/Excel export
```

### 3. Future: SCADA Integration

```
SCADA Data → Asset downtime/occurrence → REP task prioritization
```

---

## Security & Access Control

**Role-Based Access:**

- **Technician:** Read-only access to assigned tasks
- **Supervisor:** View all plans, adjust assignments, add ad-hoc tasks
- **Planner:** Full access, can run planning algorithm, lock schedules

**Data Flow:**

```
User Login → Role Check → UI Permissions → API Access Control
```

---

## Performance Considerations

**Expected Load:**

- ~100-200 tasks per planning run
- ~20-30 technicians
- Response time target: <5 seconds for assignment algorithm

**Optimization Strategies:**

- Cache technician skill data
- Index on schedule_id, assigned_technician_id
- Batch database updates
- Async processing for large plans

---

## Monitoring & Observability

**Key Metrics:**

- Planning algorithm execution time
- Assignment success rate (% of tasks assigned)
- Constraint violation frequency
- User engagement (views per role)

**Logging Points:**

- Data transformation errors
- Constraint check failures
- Assignment algorithm decisions
- UI interactions (plan generation, adjustments)

---

## Future Enhancements

**Phase 5 and Beyond:**

1. **Real-time SCADA integration** - Dynamic task reprioritization
2. **Predictive maintenance** - ML-based task suggestion
3. **Automatic spare parts ordering** - Trigger orders for upcoming tasks
4. **Mobile app** - Technician task view on tablets/phones
5. **Simulation mode** - Test planning scenarios without committing

---

## References

- Main Action Plan: `00_OVERVIEW_AND_STATUS.md`
- Database Schema: `src/services/db_utils.py`
- Planning Models: `apps/planning/src/services/planning_models.py`
- Transformation Layer: `apps/planning/src/services/data_transformation.py`
