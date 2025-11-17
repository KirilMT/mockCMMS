import os
import json
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy import Table, Column, Integer, String, ForeignKey, Text, DateTime, Boolean
from datetime import datetime, timedelta, timezone
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
    priority = Column(String(10), nullable=False)
    quantity = Column(Integer, nullable=False)
    task_type = Column(String(10), nullable=False)
    ticket_mo = Column(String(255), nullable=True)
    ticket_url = Column(String(255), nullable=True)
    required_skills = relationship('Skill', secondary=task_skills, back_populates='tasks')

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

    def to_dict(self):
        return {"id": self.id, "name": self.name}

class Skill(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    tasks = relationship('Task', secondary=task_skills, back_populates='required_skills')

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
    assignees = Column(Text, nullable=True)  # JSON array
    created_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    modified_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    modified_on = Column(DateTime, nullable=True)
    labour_count = Column(Integer, default=1)
    associated_mos = Column(Text, nullable=True)  # JSON array
    total_time_on_job = Column(Integer, default=0)  # minutes
    completed_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    completed_on = Column(DateTime, nullable=True)
    justification = Column(Text, nullable=True)
    url = Column(String(500), nullable=True)
    
    asset = relationship('Asset', back_populates='maintenance_orders')
    creator = relationship('User', foreign_keys=[created_by], backref='created_mos')
    modifier = relationship('User', foreign_keys=[modified_by], backref='modified_mos')
    completer = relationship('User', foreign_keys=[completed_by], backref='completed_mos')

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
            "assignees": self.assignees,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "modified_by": self.modified_by,
            "modified_on": self.modified_on.isoformat() if self.modified_on else None,
            "labour_count": self.labour_count,
            "associated_mos": self.associated_mos,
            "total_time_on_job": self.total_time_on_job,
            "completed_by": self.completed_by,
            "completed_on": self.completed_on.isoformat() if self.completed_on else None,
            "justification": self.justification,
            "url": self.url
        }

class SparePart(db.Model):
    id = Column(Integer, primary_key=True)
    description = Column(Text, nullable=False)
    manufacturer = Column(String(255), nullable=True)
    manufacturer_part_id = Column(String(255), nullable=True)
    stock_quantity = Column(Integer, nullable=False, default=0)
    location = Column(String(255), nullable=True)
    min_quantity = Column(Integer, default=0)

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
    roles = relationship('Role', secondary=user_roles, back_populates='users', lazy=True)

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

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description
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
    for skill_name in data.get("skills", []):
        skill = Skill(name=skill_name)
        db.session.add(skill)
        skills[skill_name] = skill
    db.session.commit()
    logger.info(f"Populated {len(skills)} skills.")

    # Create Technicians
    technicians = {}
    for tech_name in data.get("technicians", []):
        tech = Technician(name=tech_name)
        db.session.add(tech)
        technicians[tech_name] = tech
    db.session.commit()
    logger.info(f"Populated {len(technicians)} technicians.")

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
    for mo_data in data.get("maintenance_orders", []):
        asset = assets.get(mo_data["asset"])
        if asset:
            due_date = None
            if mo_data.get("due_days_from_now"):
                due_date = datetime.now(timezone.utc) + timedelta(days=mo_data["due_days_from_now"])
            
            mo = MaintenanceOrder(
                asset=asset,
                description=mo_data["description"],
                order_type=mo_data.get("order_type", "PM"),
                status=mo_data.get("status", "Open"),
                due_date=due_date
            )
            db.session.add(mo)
    db.session.commit()
    logger.info("Populated maintenance orders.")

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

    # Create Tasks
    for task_data in data.get("tasks", []):
        task = Task(
            scheduler_group_task=task_data["scheduler_group_task"],
            planning_notes=task_data.get("planning_notes", ""),
            lines=task_data.get("lines", ""),
            mitarbeiter_pro_aufgabe=task_data.get("mitarbeiter_pro_aufgabe", 1),
            planned_worktime_min=task_data.get("planned_worktime_min", 60),
            priority=task_data.get("priority", "B"),
            quantity=task_data.get("quantity", 1),
            task_type=task_data.get("task_type", "PM"),
            ticket_mo=task_data.get("ticket_mo", ""),
            ticket_url=task_data.get("ticket_url", "")
        )
        
        # Add required skills
        for skill_name in task_data.get("required_skills", []):
            if skill_name in skills:
                task.required_skills.append(skills[skill_name])
        
        db.session.add(task)
    db.session.commit()
    logger.info("Populated tasks.")

    logger.info("Dummy data population complete.")