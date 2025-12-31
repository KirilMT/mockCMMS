# src/services/db_utils.py
"""Database models and utilities for mockCMMS."""

from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import relationship
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()

# --- Association Tables ---

user_roles = Table(
    "user_roles",
    db.Model.metadata,  # type: ignore
    Column("user_id", Integer, ForeignKey("user.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("role.id"), primary_key=True),
)

maintenance_order_skills = Table(
    "maintenance_order_skills",
    db.Model.metadata,  # type: ignore
    Column(
        "maintenance_order_id",
        Integer,
        ForeignKey("maintenance_order.id"),
        primary_key=True,
    ),
    Column("skill_id", Integer, ForeignKey("skill.id"), primary_key=True),
)

maintenance_order_spare_parts = Table(
    "maintenance_order_spare_parts",
    db.Model.metadata,  # type: ignore
    Column(
        "maintenance_order_id",
        Integer,
        ForeignKey("maintenance_order.id"),
        primary_key=True,
    ),
    Column("spare_part_id", Integer, ForeignKey("spare_part.id"), primary_key=True),
    Column("quantity_required", Integer, nullable=False, default=1),
)

maintenance_order_assignees = Table(
    "maintenance_order_assignees",
    db.Model.metadata,  # type: ignore
    Column(
        "maintenance_order_id",
        Integer,
        ForeignKey("maintenance_order.id"),
        primary_key=True,
    ),
    Column("user_id", Integer, ForeignKey("user.id"), primary_key=True),
)

# --- Models ---


class SatellitePoint(db.Model):  # type: ignore
    """Satellite Point model for technicians."""

    # pylint: disable=too-few-public-methods

    __tablename__ = "satellite_points"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)

    def to_dict(self):
        """Serialize SatellitePoint to dictionary."""
        return {"id": self.id, "name": self.name}


class User(db.Model):  # type: ignore
    """User model with integrated technician capabilities."""

    # pylint: disable=too-few-public-methods

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    availability_status = Column(String(20), default="Available")
    team_id = Column(Integer, ForeignKey("team.id"), nullable=True)
    satellite_point_id = Column(
        Integer, ForeignKey("satellite_points.id"), nullable=True
    )

    roles = relationship("Role", secondary=user_roles, back_populates="users")
    team = relationship("Team", backref="users")
    satellite_point = relationship("SatellitePoint", backref="users")
    skills = relationship(
        "UserSkill", back_populates="user", cascade="all, delete-orphan"
    )

    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check against password hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_roles=False):
        """Serialize User to dictionary."""
        roles_list = [role.name for role in self.roles]
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "availability_status": self.availability_status,
            "team_id": self.team_id,
            "satellite_point_id": self.satellite_point_id,
            "team_name": self.team.name if self.team else None,
            "satellite_point_name": (
                self.satellite_point.name if self.satellite_point else None
            ),
            "is_technician": "Technician" in roles_list,
        }
        if include_roles:
            data["roles_display"] = ", ".join(roles_list) if roles_list else "N/A"
        return data


class Role(db.Model):  # type: ignore
    """Role model for user permissions."""

    # pylint: disable=too-few-public-methods

    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    users = relationship("User", secondary=user_roles, back_populates="roles")

    def to_dict(self):
        """Serialize Role to dictionary."""
        return {"id": self.id, "name": self.name, "description": self.description}


class Team(db.Model):  # type: ignore
    """Team model for shift-based scheduling."""

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name}


class Skill(db.Model):  # type: ignore
    """Skill model for technician capabilities."""

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    users = relationship("UserSkill", back_populates="skill")

    def to_dict(self):
        return {"id": self.id, "name": self.name}


class UserSkill(db.Model):  # type: ignore
    """Association model for the User-Skill many-to-many relationship."""

    user_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skill.id"), primary_key=True)
    skill_level = Column(Integer, default=1)
    user = relationship("User", back_populates="skills")
    skill = relationship("Skill", back_populates="users")

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "skill_id": self.skill_id,
            "skill_level": self.skill_level,
            "user_name": self.user.username if self.user else None,
            "skill_name": self.skill.name if self.skill else None,
        }


class Asset(db.Model):  # type: ignore
    """Asset model for equipment and machinery."""

    id = Column(Integer, primary_key=True)
    asset_code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    asset_type = Column(String(100), nullable=True)
    cost_center = Column(String(100), nullable=True)
    status = Column(String(50), default="Operational")
    maintenance_orders = relationship(
        "MaintenanceOrder",
        back_populates="asset",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "asset_code": self.asset_code,
            "name": self.name,
            "description": self.description,
            "asset_type": self.asset_type,
            "cost_center": self.cost_center,
            "status": self.status,
        }


class MaintenanceOrder(db.Model):  # type: ignore
    """Maintenance order model for work orders."""

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("asset.id"), nullable=False)
    description = Column(Text, nullable=False)
    order_type = Column(String(50), nullable=False)
    status = Column(String(50), default="Open")
    due_date = Column(DateTime, nullable=True)
    priority = Column(String(20), default="Undefined")
    schedule_name = Column(String(255), nullable=True)
    frequency = Column(String(50), nullable=True)
    estimated_completion_time = Column(Integer, nullable=True)
    labour_count = Column(Integer, default=1)
    justification = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("user.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    modified_by = Column(Integer, ForeignKey("user.id"), nullable=True)
    modified_on = Column(DateTime, nullable=True)
    assignees_json = Column(Text, nullable=True)  # Retained for backward compatibility

    asset = relationship("Asset", back_populates="maintenance_orders")
    creator = relationship("User", foreign_keys=[created_by], backref="created_mos")

    required_skills = relationship(
        "Skill", secondary=maintenance_order_skills, backref="maintenance_orders"
    )
    assignees = relationship(
        "User",
        secondary=maintenance_order_assignees,
        backref="assigned_maintenance_orders",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "asset_name": self.asset.name if self.asset else "N/A",
            "description": self.description,
            "order_type": self.order_type,
            "status": self.status,
            "due_date": self.due_date.strftime("%Y-%m-%d") if self.due_date else None,
            "priority": self.priority,
            "schedule_name": self.schedule_name,
            "frequency": self.frequency,
            "estimated_completion_time": self.estimated_completion_time,
            "assignees": ", ".join(u.username for u in self.assignees),
            "labour_count": self.labour_count,
            "created_by": self.creator.username if self.creator else "N/A",
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M"),
        }


class SparePart(db.Model):  # type: ignore
    """Spare part model for inventory management."""

    id = Column(Integer, primary_key=True)
    description = Column(Text, nullable=False)
    manufacturer = Column(String(255), nullable=True)
    manufacturer_part_id = Column(String(255), nullable=True)
    stock_quantity = Column(Integer, nullable=False, default=0)
    location = Column(String(255), nullable=True)
    min_quantity = Column(Integer, default=0)

    maintenance_orders = relationship(
        "MaintenanceOrder",
        secondary=maintenance_order_spare_parts,
        backref="required_spare_parts",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "manufacturer": self.manufacturer,
            "manufacturer_part_id": self.manufacturer_part_id,
            "stock_quantity": self.stock_quantity,
            "location": self.location,
            "min_quantity": self.min_quantity,
        }


class TableConfiguration(db.Model):  # type: ignore
    """Table configuration model for user preferences."""

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    page_name = Column(String(50), nullable=False)
    config_name = Column(String(255), nullable=False)
    column_order = Column(Text)
    hidden_columns = Column(Text)
    filters = Column(Text)
    sort_config = Column(Text)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", backref="table_configurations")

    def to_dict(self):
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
            "created_at": self.created_at.isoformat(),
        }


def populate_dummy_data(logger):
    """Populates the database with initial dummy data.

    This function delegates to db_seeding.populate_dummy_data to avoid code duplication
    (R0801) and cyclic imports (R0401).
    """
    # pylint: disable=import-outside-toplevel
    from .db_seeding import populate_dummy_data as _populate

    _populate(logger)
