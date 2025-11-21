import os
import json
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy import Table, Column, Integer, String, ForeignKey, Text, DateTime, Boolean
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# Task model and task_skills table REMOVED - use MaintenanceOrder instead

# Association table for MaintenanceOrder-Skill many-to-many relationship
maintenance_order_skills = Table('maintenance_order_skills', db.Model.metadata,
    Column('maintenance_order_id', Integer, ForeignKey('maintenance_order.id'), primary_key=True),
    Column('skill_id', Integer, ForeignKey('skill.id'), primary_key=True)
)

# Association table for User-Role many-to-many relationship
user_roles = Table('user_roles', db.Model.metadata,
    Column('user_id', Integer, ForeignKey('user.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('role.id'), primary_key=True)
)

# Association table for MaintenanceOrder to SparePart
maintenance_order_spare_parts = Table('maintenance_order_spare_parts', db.Model.metadata,
    Column('maintenance_order_id', Integer, ForeignKey('maintenance_order.id'), primary_key=True),
    Column('spare_part_id', Integer, ForeignKey('spare_part.id'), primary_key=True),
    Column('quantity_required', Integer, nullable=False, default=1)
)

# Association table for MaintenanceOrder to User (assignees)
maintenance_order_assignees = Table('maintenance_order_assignees', db.Model.metadata,
    Column('maintenance_order_id', Integer, ForeignKey('maintenance_order.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('user.id'), primary_key=True)
)

# Association table for MaintenanceOrder self-referential relationships (associated MOs)
maintenance_order_associations = Table('maintenance_order_associations', db.Model.metadata,
    Column('parent_mo_id', Integer, ForeignKey('maintenance_order.id'), primary_key=True),
    Column('child_mo_id', Integer, ForeignKey('maintenance_order.id'), primary_key=True)
)

# Task model REMOVED - use MaintenanceOrder instead
# Legacy Task data should be migrated to MaintenanceOrder

# Association model for Technician to Skill (must be defined before Technician and Skill)
class UserSkill(db.Model):
    __tablename__ = 'user_skill'
    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    skill_id = Column(Integer, ForeignKey('skill.id'), primary_key=True)
    skill_level = Column(Integer, default=1)  # e.g., 1-5 rating

    user = relationship("User", back_populates="skills")
    skill = relationship("Skill", back_populates="users")

    def to_dict(self):
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
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    users = relationship('UserSkill', back_populates='skill')
    maintenance_orders = relationship('MaintenanceOrder', secondary=maintenance_order_skills, back_populates='required_skills')

    def to_dict(self):
        return {"id": self.id, "name": self.name}

class Asset(db.Model):
    id = Column(Integer, primary_key=True)
    asset_code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    asset_type = Column(String(100), nullable=True)  # department/location/line/station/tooling/robot
    cost_center = Column(String(100), nullable=True)  # paint/assembly/biw
    status = Column(String(50), default='Operational')
    maintenance_orders = relationship('MaintenanceOrder', back_populates='asset', lazy=True)

    def to_dict(self):
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
    assignees_json = Column('assignees', Text, nullable=True)  # DEPRECATED - use assignees_users relationship
    created_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    modified_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    modified_on = Column(DateTime, nullable=True)
    labour_count = Column(Integer, default=1)
    associated_mos_json = Column('associated_mos', Text, nullable=True)  # DEPRECATED - use associated_orders relationship
    total_time_on_job = Column(Integer, default=0)  # minutes
    completed_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    completed_on = Column(DateTime, nullable=True)
    justification = Column(Text, nullable=True)
    url = Column(String(500), nullable=True)
    
    asset = relationship('Asset', back_populates='maintenance_orders')
    creator = relationship('User', foreign_keys=[created_by], backref='created_mos')
    modifier = relationship('User', foreign_keys=[modified_by], backref='modified_mos')
    completer = relationship('User', foreign_keys=[completed_by], backref='completed_mos')
    required_spare_parts = relationship('SparePart', secondary=maintenance_order_spare_parts, back_populates='maintenance_orders')
    required_skills = relationship('Skill', secondary=maintenance_order_skills, back_populates='maintenance_orders')
    
    # NEW: Proper relationships replacing JSON fields
    assignees_users = relationship('User', secondary=maintenance_order_assignees, backref='assigned_maintenance_orders')
    associated_orders = relationship(
        'MaintenanceOrder',
        secondary=maintenance_order_associations,
        primaryjoin='MaintenanceOrder.id==maintenance_order_associations.c.parent_mo_id',
        secondaryjoin='MaintenanceOrder.id==maintenance_order_associations.c.child_mo_id',
        backref='parent_orders'
    )

    def to_dict(self):
        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "description": self.description,
            "order_type": self.order_type,
            "status": self.status,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "priority": self.priority,
            "schedule_name": self.schedule_name,
            "schedule_date": self.schedule_date.isoformat() if self.schedule_date else None,
            "frequency": self.frequency,
            "completion_date": self.completion_date.isoformat() if self.completion_date else None,
            "estimated_completion_time": self.estimated_completion_time,
            "assignees": self.assignees_json,  # Legacy JSON field
            "assignees_users": [user.id for user in self.assignees_users],  # NEW: Proper relationship
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "modified_by": self.modified_by,
            "modified_on": self.modified_on.isoformat() if self.modified_on else None,
            "labour_count": self.labour_count,
            "associated_mos": self.associated_mos_json,  # Legacy JSON field
            "associated_orders": [mo.id for mo in self.associated_orders],  # NEW: Proper relationship
            "total_time_on_job": self.total_time_on_job,
            "completed_by": self.completed_by,
            "completed_on": self.completed_on.isoformat() if self.completed_on else None,
            "justification": self.justification,
            "url": self.url,
            "required_spare_parts": [{"part_id": part.id, "description": part.description} for part in self.required_spare_parts]
        }

class SparePart(db.Model):
    id = Column(Integer, primary_key=True)
    description = Column(Text, nullable=False)
    manufacturer = Column(String(255), nullable=True)
    manufacturer_part_id = Column(String(255), nullable=True)
    stock_quantity = Column(Integer, nullable=False, default=0)
    location = Column(String(255), nullable=True)
    min_quantity = Column(Integer, default=0)
    maintenance_orders = relationship('MaintenanceOrder', secondary=maintenance_order_spare_parts, back_populates='required_spare_parts')

    def to_dict(self):
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
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Technician fields (merged)
    availability_status = db.Column(db.String(20), default='Available') # 'Available', 'On Leave', 'Sick'
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)
    
    # Relationships
    roles = db.relationship('Role', secondary=user_roles, back_populates='users')
    team = db.relationship('Team', backref='users')
    skills = relationship('UserSkill', back_populates='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_roles=False):
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "availability_status": self.availability_status,
            "team_id": self.team_id,
            "team_name": self.team.name if self.team else None
        }
        if include_roles:
            data['roles'] = [role.name for role in self.roles]
        return data

class Role(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    users = relationship('User', secondary=user_roles, back_populates='roles')

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description
        }

# Shift model REMOVED - unused/orphaned table
# Use Team for rotation-based scheduling

class Team(db.Model):
    __tablename__ = 'team'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    shift_type = db.Column(db.String(20), nullable=False)  # 'Early', 'Late', 'Night'
    rotation_pattern = db.Column(db.String(50), nullable=False) # 'Pattern 1', 'Pattern 2'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'shift_type': self.shift_type,
            'rotation_pattern': self.rotation_pattern
        }

class Report(db.Model):
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    report_type = Column(String(50), nullable=False)  # reactive_production/completed_weekend
    generated_by = Column(Integer, ForeignKey('user.id'), nullable=False)
    generated_on = Column(DateTime, default=datetime.utcnow)
    parameters = Column(Text, nullable=True)  # JSON of filter parameters
    file_path = Column(String(500), nullable=True)
    format = Column(String(20), nullable=False)  # PDF/Markdown
    
    generated_by_user = relationship('User', backref='generated_reports')

    def to_dict(self):
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
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    page_name = Column(String(50), nullable=False)  # assets/mos/spare_parts/users
    config_name = Column(String(255), nullable=False)
    column_order = Column(Text, nullable=True)  # JSON array
    hidden_columns = Column(Text, nullable=True)  # JSON array
    filters = Column(Text, nullable=True)  # JSON object
    sort_config = Column(Text, nullable=True)  # JSON object
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship('User', backref='table_configurations')

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
            "created_at": self.created_at.isoformat()
        }

def populate_dummy_data(logger):
    """Populates the database with dummy data from dummy_data.json."""
    logger.info("Populating database with dummy data.")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dummy_data_path = os.path.join(current_dir, '..', '..', 'test_data', 'dummy_data.json')

    try:
        with open(dummy_data_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"Dummy data file not found at {dummy_data_path}")
        return
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from {dummy_data_path}")
        return

    # Create Roles
    roles = {}
    for role_data in data.get("roles", []):
        role = Role(name=role_data["name"], description=role_data.get("description", ""))
        db.session.add(role)
        roles[role_data["name"]] = role
    db.session.commit()
    logger.info(f"Populated {len(roles)} roles.")

    # Create Shift Teams
    shift_teams = {}
    teams_config = [
        {"name": "Team A", "shift_type": "Early", "rotation_pattern": "Pattern 1"},
        {"name": "Team B", "shift_type": "Late", "rotation_pattern": "Pattern 1"},
        {"name": "Team C", "shift_type": "Early", "rotation_pattern": "Pattern 2"},
        {"name": "Team D", "shift_type": "Late", "rotation_pattern": "Pattern 2"}
    ]
    
    # Create Teams
    teams = {}
    for team_data in teams_config:
        team = Team(
            name=team_data["name"],
            shift_type=team_data["shift_type"],
            rotation_pattern=team_data["rotation_pattern"]
        )
        db.session.add(team)
        teams[team_data["name"]] = team
    db.session.commit()
    logger.info(f"Populated {len(teams)} teams.")

    # Create Users
    users = {}
    for user_data in data.get("users", []):
        user = User(username=user_data["username"], email=user_data["email"])
        user.set_password(user_data["password"])
        for role_name in user_data.get("roles", []):
            if role_name in roles:
                user.roles.append(roles[role_name])
        db.session.add(user)
        users[user_data["username"]] = user
    db.session.commit()
    logger.info(f"Populated {len(users)} users.")

    # Create Skills
    skills = {}
    for skill_data in data.get("skills", []):
        # Handle both string format (old) and dict format (new)
        if isinstance(skill_data, str):
            skill = Skill(name=skill_data)
            skills[skill_data] = skill
        else:
            skill = Skill(name=skill_data["name"])
            skills[skill_data["name"]] = skill
        db.session.add(skill)
    db.session.commit()
    logger.info(f"Populated {len(skills)} skills.")

    # Create Users (Technicians) with Skills
    technicians = {}
    technician_role = Role.query.filter_by(name='Technician').first()
    if not technician_role:
        technician_role = Role(name='Technician')
        db.session.add(technician_role)
        db.session.commit()

    for tech_data in data.get("technicians", []):
        # Handle both string format (old) and dict format (new)
        if isinstance(tech_data, str):
            username = tech_data
            tech_info = {}
        else:
            username = tech_data["name"]
            tech_info = tech_data

        # Check if user exists
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username, email=f"{username}@example.com")
            user.set_password("password")
            user.roles.append(technician_role)
            db.session.add(user)
        
        # Update technician fields
        user.availability_status = tech_info.get("availability_status", "Available")
        
        if "shift_team" in tech_info and tech_info["shift_team"] in teams:
            user.team = teams[tech_info["shift_team"]]
            
        technicians[username] = user
        db.session.flush()

        # Add skills
        if isinstance(tech_data, dict):
            for skill_assignment in tech_data.get("skills", []):
                skill_name = skill_assignment["skill"]
                if skill_name in skills:
                    # Check if skill already assigned
                    existing_skill = UserSkill.query.filter_by(user_id=user.id, skill_id=skills[skill_name].id).first()
                    if not existing_skill:
                        user_skill = UserSkill(
                            user_id=user.id,
                            skill_id=skills[skill_name].id,
                            skill_level=skill_assignment.get("level", 1)
                        )
                        db.session.add(user_skill)
    
    db.session.commit()
    logger.info(f"Populated technicians as Users with skills.")

    # Create Assets
    assets = {}
    for i, asset_data in enumerate(data.get("assets", [])):
        asset = Asset(
            asset_code=asset_data.get("asset_code", f"AST-{i+1:04d}"),
            name=asset_data["name"],
            description=asset_data.get("description", ""),
            asset_type=asset_data.get("asset_type", "equipment"),
            cost_center=asset_data.get("cost_center", "general"),
            status=asset_data.get("status", "Operational")
        )
        db.session.add(asset)
        assets[asset_data["name"]] = asset
    db.session.commit()
    logger.info(f"Populated {len(assets)} assets.")

    # Create Maintenance Orders
    maintenance_orders = {}
    for mo_data in data.get("maintenance_orders", []):
        asset = assets.get(mo_data["asset"])
        if asset:
            due_date = None
            if mo_data.get("due_days_from_now") is not None:
                due_date = datetime.now(timezone.utc) + timedelta(days=mo_data["due_days_from_now"])
            
            mo = MaintenanceOrder(
                asset=asset,
                description=mo_data["description"],
                order_type=mo_data.get("order_type", "PM"),
                status=mo_data.get("status", "Open"),
                due_date=due_date,
                priority=mo_data.get("priority", "Medium"),
                schedule_name=mo_data.get("schedule_name"),
                frequency=mo_data.get("frequency"),
                estimated_completion_time=mo_data.get("estimated_completion_time", 60),
                labour_count=mo_data.get("labour_count", 1),
                justification=mo_data.get("justification")
            )
            db.session.add(mo)
            db.session.flush()  # Get the MO ID

            # Add required skills
            for skill_name in mo_data.get("required_skills", []):
                if skill_name in skills:
                    mo.required_skills.append(skills[skill_name])

            maintenance_orders[mo_data["description"]] = mo

    db.session.commit()
    logger.info(f"Populated {len(maintenance_orders)} maintenance orders with skills.")

    # Create Spare Parts
    for part_data in data.get("spare_parts", []):
        part = SparePart(
            description=part_data.get("description", part_data.get("name", "")),
            manufacturer=part_data.get("manufacturer", ""),
            manufacturer_part_id=part_data.get("manufacturer_part_id", ""),
            stock_quantity=part_data.get("quantity", 0),
            location=part_data.get("location", ""),
            min_quantity=part_data.get("min_quantity", 0)
        )
        db.session.add(part)
    db.session.commit()
    logger.info("Populated spare parts.")

    # Task model removed - legacy data not populated
    # Use MaintenanceOrder for all work orders

    # Create Schedules and Planning Tasks
    from apps.planning.src.services.planning_models import Schedule, PlanningTask

    for schedule_data in data.get("schedules", []):
        schedule = Schedule(
            name=schedule_data["name"],
            start_date=datetime.fromisoformat(schedule_data["start_date"]),
            end_date=datetime.fromisoformat(schedule_data["end_date"]),
            planning_status=schedule_data.get("planning_status", "Draft")
        )
        db.session.add(schedule)
        db.session.flush()  # Get the schedule ID

        # Create planning tasks linked to this schedule
        for mo_description in schedule_data.get("maintenance_orders", []):
            mo = maintenance_orders.get(mo_description)
            if mo:
                planning_task = PlanningTask(
                    schedule_id=schedule.id,
                    maintenance_order_id=mo.id,
                    status='Unplanned'
                )
                db.session.add(planning_task)

    db.session.commit()
    logger.info(f"Populated {len(data.get('schedules', []))} schedules with planning tasks.")

    logger.info("Dummy data population complete.")
