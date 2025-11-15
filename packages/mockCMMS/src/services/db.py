from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy import Table, Column, Integer, String, ForeignKey, Text, DateTime, Boolean
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# Association table for Task-Skill many-to-many relationship
task_skills = Table('task_skills', db.Model.metadata,
    Column('task_id', Integer, ForeignKey('task.id'), primary_key=True),
    Column('skill_id', Integer, ForeignKey('skill.id'), primary_key=True)
)

# Association table for User-Role many-to-many relationship
user_roles = Table('user_roles', db.Model.metadata,
    Column('user_id', Integer, ForeignKey('user.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('role.id'), primary_key=True)
)

class Task(db.Model):
    id = Column(Integer, primary_key=True)
    scheduler_group_task = Column(String(255), nullable=False)
    planning_notes = Column(Text, nullable=True)
    lines = Column(String(255), nullable=True)
    mitarbeiter_pro_aufgabe = Column(Integer, nullable=False)
    planned_worktime_min = Column(Integer, nullable=False)
    priority = Column(String(10), nullable=False) # e.g., 'A', 'B', 'C'
    quantity = Column(Integer, nullable=False)
    task_type = Column(String(10), nullable=False) # 'PM' or 'Rep'
    ticket_mo = Column(String(255), nullable=True)
    ticket_url = Column(String(255), nullable=True)

    # Many-to-many relationship with Skill
    required_skills = relationship('Skill', secondary=task_skills, back_populates='tasks')

    def __repr__(self):
        return f"<Task {self.id}: {self.scheduler_group_task}>"

    def to_dict(self):
        return {
            "id": self.id,
            "scheduler_group_task": self.scheduler_group_task,
            "planning_notes": self.planning_notes,
            "lines": self.lines,
            "mitarbeiter_pro_aufgabe": self.mitarbeiter_pro_aufgabe,
            "planned_worktime_min": self.planned_worktime_min,
            "priority": self.priority,
            "quantity": self.quantity,
            "task_type": self.task_type,
            "ticket_mo": self.ticket_mo,
            "ticket_url": self.ticket_url,
            "required_skills": [skill.name for skill in self.required_skills]
        }

class Technician(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    # Add other technician-specific fields as needed, e.g., skills, availability

    def __repr__(self):
        return f"<Technician {self.id}: {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name
        }

class Skill(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)

    # Many-to-many relationship with Task
    tasks = relationship('Task', secondary=task_skills, back_populates='required_skills')

    def __repr__(self):
        return f"<Skill {self.id}: {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name
        }

class Asset(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    status = Column(String(50), default='Operational') # e.g., Operational, Under Maintenance, Decommissioned

    maintenance_orders = relationship('MaintenanceOrder', back_populates='asset', lazy=True)

    def __repr__(self):
        return f"<Asset {self.id}: {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "location": self.location,
            "status": self.status
        }

class MaintenanceOrder(db.Model):
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('asset.id'), nullable=False)
    description = Column(Text, nullable=False)
    order_type = Column(String(50), nullable=False) # e.g., PM, Corrective, Inspection
    status = Column(String(50), default='Open') # e.g., Open, In Progress, Completed, Cancelled
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    asset = relationship('Asset', back_populates='maintenance_orders')

    def __repr__(self):
        return f"<MaintenanceOrder {self.id}: {self.description}>"

    def to_dict(self):
        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "description": self.description,
            "order_type": self.order_type,
            "status": self.status,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "created_at": self.created_at.isoformat()
        }

class SparePart(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    quantity = Column(Integer, nullable=False, default=0)
    location = Column(String(255), nullable=True)
    min_quantity = Column(Integer, default=0)

    def __repr__(self):
        return f"<SparePart {self.id}: {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "quantity": self.quantity,
            "location": self.location,
            "min_quantity": self.min_quantity
        }

class User(db.Model):
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    roles = relationship('Role', secondary=user_roles, back_populates='users', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.id}: {self.username}>"

    def to_dict(self, include_roles=False):
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat()
        }
        if include_roles:
            data['roles'] = [role.name for role in self.roles]
        return data

class Role(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    users = relationship('User', secondary=user_roles, back_populates='roles', lazy=True)

    def __repr__(self):
        return f"<Role {self.id}: {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description
        }

