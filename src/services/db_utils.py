"""Database models and utilities for mockCMMS."""
import os
import json
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy import Table, Column, Integer, String, ForeignKey, Text, DateTime, Boolean
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# Task model and task_skills table REMOVED - use MaintenanceOrder instead

# Association table for MaintenanceOrder-Skill many-to-many relationship
maintenance_order_skills = Table(
    'maintenance_order_skills',
    db.Model.metadata,
    Column(
        'maintenance_order_id',
        Integer,
        ForeignKey('maintenance_order.id'),
        primary_key=True),
    Column(
        'skill_id',
        Integer,
        ForeignKey('skill.id'),
        primary_key=True))

# Association table for User-Role many-to-many relationship
user_roles = Table('user_roles', db.Model.metadata,
                   Column('user_id', Integer, ForeignKey('user.id'), primary_key=True),
                   Column('role_id', Integer, ForeignKey('role.id'), primary_key=True)
                   )

# Association table for MaintenanceOrder to SparePart
maintenance_order_spare_parts = Table(
    'maintenance_order_spare_parts', db.Model.metadata,
    Column('maintenance_order_id', Integer,
           ForeignKey('maintenance_order.id'), primary_key=True),
    Column('spare_part_id', Integer,
           ForeignKey('spare_part.id'), primary_key=True),
    Column('quantity_required', Integer, nullable=False, default=1))

# Association table for MaintenanceOrder to User (assignees)
maintenance_order_assignees = Table(
    'maintenance_order_assignees',
    db.Model.metadata,
    Column(
        'maintenance_order_id',
        Integer,
        ForeignKey('maintenance_order.id'),
        primary_key=True),
    Column(
        'user_id',
        Integer,
        ForeignKey('user.id'),
        primary_key=True))

# Association table for MaintenanceOrder self-referential relationships (associated MOs)
maintenance_order_associations = Table(
    'maintenance_order_associations', db.Model.metadata, Column(
        'parent_mo_id', Integer, ForeignKey('maintenance_order.id'), primary_key=True), Column(
            'child_mo_id', Integer, ForeignKey('maintenance_order.id'), primary_key=True))

# Task model REMOVED - use MaintenanceOrder instead
# Legacy Task data should be migrated to MaintenanceOrder

# Association model for Technician to Skill (must be defined before Technician and Skill)


class UserSkill(db.Model):
    """Association model for User-Skill many-to-many relationship."""
    __tablename__ = 'user_skill'
    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    skill_id = Column(Integer, ForeignKey('skill.id'), primary_key=True)
    skill_level = Column(Integer, default=1)  # e.g., 1-5 rating

    user = relationship("User", back_populates="skills")
    skill = relationship("Skill", back_populates="users")

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "skill_id": self.skill_id,
            "skill_level": self.skill_level,
            "user_name": self.user.username if self.user else None,
            "skill_name": self.skill.name if self.skill else None
        }

# Technician model REMOVED - merged into User
# Legacy data migrated to User table


class Skill(db.Model):
    """Skill model for technician capabilities."""
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    users = relationship('UserSkill', back_populates='skill')
    maintenance_orders = relationship(
        'MaintenanceOrder',
        secondary=maintenance_order_skills,
        back_populates='required_skills')

    def to_dict(self):
        """Convert to dictionary."""
        return {"id": self.id, "name": self.name}


class Asset(db.Model):
    """Asset model for equipment and machinery."""
    id = Column(Integer, primary_key=True)
    asset_code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    # department/location/line/station/tooling/robot
    asset_type = Column(String(100), nullable=True)
    cost_center = Column(String(100), nullable=True)  # paint/assembly/biw
    status = Column(String(50), default='Operational')
    maintenance_orders = db.relationship(
        'MaintenanceOrder',
        back_populates='asset',
        lazy=True,
        cascade="all, delete-orphan")

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "asset_code": self.asset_code,
            "name": self.name,
            "description": self.description,
            "asset_type": self.asset_type,
            "cost_center": self.cost_center,
            "status": self.status
        }


class MaintenanceOrder(db.Model):
    """Maintenance order model for work orders."""
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('asset.id'), nullable=False)
    description = Column(Text, nullable=False)
    order_type = Column(String(50), nullable=False)  # PM/reactive/corrective
    status = Column(String(50), default='Open')
    due_date = Column(DateTime, nullable=True)
    priority = Column(String(20), default='Undefined')  # Critical/High/Medium/Low/Undefined
    schedule_name = Column(String(255), nullable=True)  # PM scheduler
    schedule_date = Column(DateTime, nullable=True)
    frequency = Column(String(50), nullable=True)  # daily/weekly/monthly
    completion_date = Column(DateTime, nullable=True)
    estimated_completion_time = Column(Integer, nullable=True)  # minutes
    # DEPRECATED - use assignees_users relationship
    assignees_json = Column('assignees', Text, nullable=True)
    created_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    modified_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    modified_on = Column(DateTime, nullable=True)
    labour_count = Column(Integer, default=1)
    # DEPRECATED - use associated_orders relationship
    associated_mos_json = Column('associated_mos', Text, nullable=True)
    total_time_on_job = Column(Integer, default=0)  # minutes
    completed_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    completed_on = Column(DateTime, nullable=True)
    justification = Column(Text, nullable=True)
    url = Column(String(500), nullable=True)

    asset = relationship('Asset', back_populates='maintenance_orders')
    creator = relationship('User', foreign_keys=[created_by], backref='created_mos')
    modifier = relationship('User', foreign_keys=[modified_by], backref='modified_mos')
    completer = relationship('User', foreign_keys=[completed_by], backref='completed_mos')
    required_spare_parts = relationship(
        'SparePart',
        secondary=maintenance_order_spare_parts,
        back_populates='maintenance_orders')
    required_skills = relationship('Skill',
                                   secondary=maintenance_order_skills,
                                   back_populates='maintenance_orders')

    # NEW: Proper relationships replacing JSON fields
    assignees_users = relationship('User',
                                   secondary=maintenance_order_assignees,
                                   backref='assigned_maintenance_orders')
    associated_orders = relationship(
        'MaintenanceOrder',
        secondary=maintenance_order_associations,
        primaryjoin='MaintenanceOrder.id==maintenance_order_associations.c.parent_mo_id',
        secondaryjoin='MaintenanceOrder.id==maintenance_order_associations.c.child_mo_id',
        backref='parent_orders'
    )

    def to_dict(self):
        """Convert to dictionary."""
        # Bug #5: Create a user-friendly display string for assignees
        assignees_list = []
        if self.assignees_json:
            try:
                raw_list = json.loads(self.assignees_json)
                # Clean up the prefixes for display
                assignees_list = [
                    item.replace(
                        'user:',
                        '').replace(
                        'team:',
                        '') for item in raw_list]
            except json.JSONDecodeError:
                assignees_list = [self.assignees_json]  # Fallback for old plain text

        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "asset_name": self.asset.name if self.asset else "N/A",  # Add asset name
            "description": self.description,
            "order_type": self.order_type,
            "status": self.status,
            "due_date": self.due_date.strftime('%Y-%m-%d') if self.due_date else None,
            "priority": self.priority,
            "schedule_name": self.schedule_name,
            "frequency": self.frequency,
            "estimated_completion_time": self.estimated_completion_time,
            "assignees": ", ".join(assignees_list),  # Use the new display string
            "labour_count": self.labour_count,
            "created_by": self.creator.username if self.creator else "N/A",
            "created_at": self.created_at.strftime('%Y-%m-%d %H:%M'),
        }


class SparePart(db.Model):
    """Spare part model for inventory management."""
    id = Column(Integer, primary_key=True)
    description = Column(Text, nullable=False)
    manufacturer = Column(String(255), nullable=True)
    manufacturer_part_id = Column(String(255), nullable=True)
    stock_quantity = Column(Integer, nullable=False, default=0)
    location = Column(String(255), nullable=True)
    min_quantity = Column(Integer, default=0)
    maintenance_orders = relationship(
        'MaintenanceOrder',
        secondary=maintenance_order_spare_parts,
        back_populates='required_spare_parts')

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "description": self.description,
            "manufacturer": self.manufacturer,
            "manufacturer_part_id": self.manufacturer_part_id,
            "stock_quantity": self.stock_quantity,
            "location": self.location,
            "min_quantity": self.min_quantity
        }


class User(db.Model):
    """User model with authentication and technician capabilities."""
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Technician fields (merged)
    availability_status = db.Column(db.String(20),
                                    default='Available')  # 'Available', 'On Leave', 'Sick'
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)

    # Relationships
    roles = db.relationship('Role', secondary=user_roles, back_populates='users')
    team = db.relationship('Team', backref='users')
    skills = relationship('UserSkill', back_populates='user', cascade="all, delete-orphan")

    def set_password(self, password):
        """Hash and set password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_roles=False):
        """Convert to dictionary."""
        roles_list = [role.name for role in self.roles]
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "availability_status": self.availability_status,
            "team_id": self.team_id,
            "team_name": self.team.name if self.team else None,
            "is_technician": "Technician" in roles_list
        }
        if include_roles:
            data['roles_display'] = ", ".join(roles_list) if roles_list else "N/A"
        return data


class Role(db.Model):
    """Role model for user permissions."""
    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    users = relationship('User', secondary=user_roles, back_populates='roles')

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description
        }

# Shift model REMOVED - unused/orphaned table
# Use Team for rotation-based scheduling


class Team(db.Model):
    """Team model for shift-based scheduling."""
    __tablename__ = 'team'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    shift_type = db.Column(db.String(20), nullable=False)  # 'Early', 'Late', 'Night'
    rotation_pattern = db.Column(db.String(50), nullable=False)  # 'Pattern 1', 'Pattern 2'

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'shift_type': self.shift_type,
            'rotation_pattern': self.rotation_pattern
        }


class Report(db.Model):
    """Report model for generated reports."""
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    report_type = Column(String(50), nullable=False)  # reactive_production/completed_weekend
    generated_by = Column(Integer, ForeignKey('user.id'), nullable=False)
    generated_on = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    parameters = Column(Text, nullable=True)  # JSON of filter parameters
    file_path = Column(String(500), nullable=True)
    format = Column(String(20), nullable=False)  # PDF/Markdown

    generated_by_user = relationship('User', backref='generated_reports')

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "report_type": self.report_type,
            "generated_by": self.generated_by,
            "generated_on": self.generated_on.isoformat(),
            "parameters": self.parameters,
            "file_path": self.file_path,
            "format": self.format
        }


class TableConfiguration(db.Model):
    """Table configuration model for user preferences."""
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    page_name = Column(String(50), nullable=False)  # assets/mos/spare_parts/users
    config_name = Column(String(255), nullable=False)
    column_order = Column(Text, nullable=True)  # JSON array
    hidden_columns = Column(Text, nullable=True)  # JSON array
    filters = Column(Text, nullable=True)  # JSON object
    sort_config = Column(Text, nullable=True)  # JSON object
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship('User', backref='table_configurations')

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "page_name": self.page_name,
            "config_name": self.config_name,
            "column_order": self.column_order,
            "hidden_columns": self.hidden_columns,
            "filters": self.filters,
            "sort_config": self.sort_config,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat()
        }


def populate_dummy_data(logger):
    """Populates the database with dummy data from dummy_data.json."""
    from .db_seeding import (
        _load_dummy_data, _create_roles, _create_teams, _create_users,
        _create_skills, _create_technicians, _create_assets,
        _create_maintenance_orders, _create_spare_parts, _create_schedules
    )

    logger.info("Populating database with dummy data.")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dummy_data_path = os.path.join(current_dir, '..', '..', 'test_data', 'dummy_data.json')

    data = _load_dummy_data(dummy_data_path, logger)
    if not data:
        return

    roles = _create_roles(data, logger)
    teams = _create_teams(logger)
    _create_users(data, roles, logger)
    skills = _create_skills(data, logger)
    _create_technicians(data, teams, skills, logger)
    assets = _create_assets(data, logger)
    maintenance_orders = _create_maintenance_orders(data, assets, skills, logger)
    _create_spare_parts(data, logger)
    _create_schedules(data, maintenance_orders, logger)

    logger.info("Dummy data population complete.")
