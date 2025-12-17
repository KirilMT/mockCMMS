# apps/planning/src/services/planning_models.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from src.services.db_utils import db

# Association table for PlanningTask to User (many-to-many)
# Commented out: Cross-DB M2M relationships are complex in SQLite
# planning_task_users = Table('planning_task_users', db.Model.metadata,
#     Column('planning_task_id', Integer, ForeignKey('planning_task.id'), primary_key=True),
#     Column('user_id', Integer, ForeignKey('user.id'), primary_key=True)
# )


class Schedule(db.Model):
    __bind_key__ = 'planning'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    planning_status = Column(String(50), default='Draft') # Draft, Published, Locked
    created_at = Column(DateTime, server_default=db.func.now())

    # Relationship to assigned tasks
    planned_tasks = relationship('PlanningTask', back_populates='schedule')

class PlanningTask(db.Model):
    __bind_key__ = 'planning'
    __tablename__ = 'planning_task'
    id = Column(Integer, primary_key=True)
    # Cross-DB ForeignKey to core MaintenanceOrder (logical link only)
    maintenance_order_id = Column(Integer, nullable=False)
    schedule_id = Column(Integer, ForeignKey('schedule.id'), nullable=True)

    # Planning-specific fields
    planned_start_time = Column(DateTime, nullable=True)
    planned_end_time = Column(DateTime, nullable=True)
    actual_duration_minutes = Column(Integer, nullable=True)  # Calculated duration after planning (may differ from MO estimate)
    status = Column(String(50), default='Unplanned') # Unplanned, Planned, In-Progress, Completed, Cancelled
    assigned_user_id = Column(Integer, nullable=True)  # DEPRECATED: Keep for backward compatibility

    # Relationships
    # Note: Cross-DB relationships require explicit primaryjoin and foreign_keys
    maintenance_order = relationship('MaintenanceOrder', primaryjoin="foreign(PlanningTask.maintenance_order_id) == MaintenanceOrder.id")
    schedule = relationship('Schedule', back_populates='planned_tasks')
    assigned_user = relationship('User', primaryjoin="foreign(PlanningTask.assigned_user_id) == User.id")  # Single user (deprecated)
    # assigned_users = relationship('User', secondary=planning_task_users, backref='planning_tasks')  # Multiple users (NEW) - Commented out as M2M across DBs is complex

