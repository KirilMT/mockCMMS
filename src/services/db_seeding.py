"""Database seeding helper functions."""
from datetime import datetime, timedelta, timezone
from .db_utils import (
    db, Role, Team, User, Skill, UserSkill, Asset,
    MaintenanceOrder, SparePart
)


def _load_dummy_data(dummy_data_path, logger):
    """Load and parse dummy data JSON file."""
    import json
    try:
        with open(dummy_data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("Dummy data file not found at %s", dummy_data_path)
        return None
    except json.JSONDecodeError:
        logger.error("Error decoding JSON from %s", dummy_data_path)
        return None


def _create_roles(data, logger):
    """Create roles from data."""
    roles = {}
    for role_data in data.get("roles", []):
        role = Role(name=role_data["name"], description=role_data.get("description", ""))
        db.session.add(role)
        roles[role_data["name"]] = role
    db.session.commit()
    logger.info("Populated %d roles.", len(roles))
    return roles


def _create_teams(logger):
    """Create shift teams."""
    teams_config = [
        {"name": "Team A", "shift_type": "Early", "rotation_pattern": "Pattern 1"},
        {"name": "Team B", "shift_type": "Late", "rotation_pattern": "Pattern 1"},
        {"name": "Team C", "shift_type": "Early", "rotation_pattern": "Pattern 2"},
        {"name": "Team D", "shift_type": "Late", "rotation_pattern": "Pattern 2"}
    ]
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
    logger.info("Populated %d teams.", len(teams))
    return teams


def _create_users(data, roles, logger):
    """Create users from data."""
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
    logger.info("Populated %d users.", len(users))
    return users


def _create_skills(data, logger):
    """Create skills from data."""
    skills = {}
    for skill_data in data.get("skills", []):
        if isinstance(skill_data, str):
            skill = Skill(name=skill_data)
            skills[skill_data] = skill
        else:
            skill = Skill(name=skill_data["name"])
            skills[skill_data["name"]] = skill
        db.session.add(skill)
    db.session.commit()
    logger.info("Populated %d skills.", len(skills))
    return skills


def _create_technicians(data, teams, skills, logger):
    """Create technicians with skills."""
    technicians = {}
    technician_role = Role.query.filter_by(name='Technician').first()
    if not technician_role:
        technician_role = Role(name='Technician')
        db.session.add(technician_role)
        db.session.commit()

    for tech_data in data.get("technicians", []):
        if isinstance(tech_data, str):
            username = tech_data
            tech_info = {}
        else:
            username = tech_data["name"]
            tech_info = tech_data

        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username, email=f"{username}@example.com")
            user.set_password("password")
            user.roles.append(technician_role)
            db.session.add(user)

        user.availability_status = tech_info.get("availability_status", "Available")
        if "shift_team" in tech_info and tech_info["shift_team"] in teams:
            user.team = teams[tech_info["shift_team"]]

        technicians[username] = user
        db.session.flush()

        if isinstance(tech_data, dict):
            for skill_assignment in tech_data.get("skills", []):
                skill_name = skill_assignment["skill"]
                if skill_name in skills:
                    existing_skill = UserSkill.query.filter_by(
                        user_id=user.id, skill_id=skills[skill_name].id).first()
                    if not existing_skill:
                        user_skill = UserSkill(
                            user_id=user.id,
                            skill_id=skills[skill_name].id,
                            skill_level=skill_assignment.get("level", 1)
                        )
                        db.session.add(user_skill)

    db.session.commit()
    logger.info("Populated technicians as Users with skills.")
    return technicians


def _create_assets(data, logger):
    """Create assets from data."""
    assets = {}
    for i, asset_data in enumerate(data.get("assets", [])):
        asset = Asset(
            asset_code=asset_data.get("asset_code", f"AST-{i + 1:04d}"),
            name=asset_data["name"],
            description=asset_data.get("description", ""),
            asset_type=asset_data.get("asset_type", "equipment"),
            cost_center=asset_data.get("cost_center", "general"),
            status=asset_data.get("status", "Operational")
        )
        db.session.add(asset)
        assets[asset_data["name"]] = asset
    db.session.commit()
    logger.info("Populated %d assets.", len(assets))
    return assets


def _create_maintenance_orders(data, assets, skills, logger):
    """Create maintenance orders from data."""
    maintenance_orders = {}
    for mo_data in data.get("maintenance_orders", []):
        asset = assets.get(mo_data["asset"])
        if asset:
            due_date = None
            if mo_data.get("due_days_from_now") is not None:
                due_date = datetime.now(timezone.utc) + timedelta(
                    days=mo_data["due_days_from_now"])

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
            db.session.flush()

            for skill_name in mo_data.get("required_skills", []):
                if skill_name in skills:
                    mo.required_skills.append(skills[skill_name])

            maintenance_orders[mo_data["description"]] = mo

    db.session.commit()
    logger.info("Populated %d maintenance orders with skills.", len(maintenance_orders))
    return maintenance_orders


def _create_spare_parts(data, logger):
    """Create spare parts from data."""
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


def _create_schedules(data, maintenance_orders, logger):
    """Create planning schedules if planning app is enabled."""
    import os
    if os.getenv('PLANNING_ENABLED', 'False').lower() not in ('true', '1', 't'):
        return

    try:
        from apps.planning.src.services.planning_models import Schedule, PlanningTask

        for schedule_data in data.get("schedules", []):
            schedule = Schedule(
                name=schedule_data["name"],
                start_date=datetime.fromisoformat(schedule_data["start_date"]),
                end_date=datetime.fromisoformat(schedule_data["end_date"]),
                planning_status=schedule_data.get("planning_status", "Draft")
            )
            db.session.add(schedule)
            db.session.flush()

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
        logger.info("Populated %d schedules with planning tasks.", len(data.get('schedules', [])))
    except ImportError:
        logger.warning("Could not import planning models. Skipping schedule seeding.")
    except Exception as e:
        logger.error("An error occurred during schedule seeding: %s", e)
