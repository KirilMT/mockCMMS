# src/services/db_seeding.py
"""Database seeding helper functions."""

import json
import logging
import os
from datetime import datetime, timedelta, timezone

from .db_utils import (
    Asset,
    MaintenanceOrder,
    Role,
    Skill,
    SparePart,
    Team,
    User,
    UserSkill,
    db,
)

_CORE_SEED_PREFIX = "[SEED][CORE]"


class _SeedLoggerAdapter(logging.LoggerAdapter):
    """Attach a stable core seeding prefix to log messages."""

    def process(self, msg, kwargs):
        return f"{self.extra['seed_prefix']} {msg}", kwargs


def _get_seed_logger(logger):
    """Return a logger that prefixes core seeding messages consistently."""
    if (
        isinstance(logger, logging.LoggerAdapter)
        and logger.extra.get("seed_prefix") == _CORE_SEED_PREFIX
    ):
        return logger
    return _SeedLoggerAdapter(logger, {"seed_prefix": _CORE_SEED_PREFIX})


def _load_dummy_data(logger):
    """Load and parse the dummy data JSON file."""
    dummy_data_path = ""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dummy_data_path = os.path.join(
        current_dir, "..", "..", "test_data", "dummy_data.json"
    )
    try:
        with open(dummy_data_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("Dummy data file not found")
    except json.JSONDecodeError:
        logger.error("Error decoding dummy data JSON")
    return None


def _get_or_create(model, **kwargs):
    """Fetches a database object or creates it if it doesn't exist."""
    instance = db.session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    instance = model(**kwargs)
    db.session.add(instance)
    return instance, True


def _create_roles(roles_data, logger):
    """Create roles from data, ensuring no duplicates."""
    roles = {}
    for role_info in roles_data:
        role, created = _get_or_create(Role, name=role_info["name"])
        if created:
            role.description = role_info.get("description", "")
        roles[role.name] = role
    logger.info(f"Loaded {len(roles)} roles.")
    return roles


def _create_teams(teams_data, logger):
    """Create shift teams."""
    teams = {}
    for team_info in teams_data:
        team, _ = _get_or_create(Team, name=team_info["name"])
        teams[team.name] = team
    logger.info(f"Loaded {len(teams)} teams.")
    return teams


def _create_users(users_data, roles, teams, logger):
    """Create users and assign roles and teams."""
    for user_info in users_data:
        user, created = _get_or_create(User, username=user_info["username"])
        if created:
            user.email = user_info["email"]
            user.set_password(user_info["password"])
            user.team = teams.get(user_info.get("team"))
            for role_name in user_info.get("roles", []):
                if role_name in roles and roles[role_name] not in user.roles:
                    user.roles.append(roles[role_name])
    logger.info(f"Processed {len(users_data)} users.")
    return users_data  # Return users_data to access 'team' info later if needed


def _assign_technician_teams(technicians_data, logger):
    """Assign teams and skills to technicians based on extended technician data."""
    team_count = 0
    skill_count = 0
    for tech_info in technicians_data:
        user = User.query.filter_by(username=tech_info["name"]).first()
        if not user:
            continue

        # Assign Team
        if tech_info.get("shift_team"):
            team = Team.query.filter_by(name=tech_info["shift_team"]).first()
            if team:
                user.team = team
                team_count += 1

        # Assign Skills
        skills_list = tech_info.get("skills", [])
        if skills_list:
            for skill_data in skills_list:
                skill_name = skill_data.get("skill")
                skill_level = skill_data.get("level", 1)

                if skill_name:
                    skill, _ = _get_or_create(Skill, name=skill_name)
                    user_skill, created = _get_or_create(
                        UserSkill, user=user, skill=skill
                    )
                    user_skill.skill_level = skill_level
                    if created:
                        skill_count += 1

    logger.info(
        f"Assigned teams to {team_count} technicians and processed "
        f"{skill_count} new skill associations."
    )


def _create_skills(skills_data, logger):
    """Create skills and associate them with users."""
    skills = {}
    for skill_info in skills_data:
        skill, _ = _get_or_create(Skill, name=skill_info["name"])
        skills[skill.name] = skill
        for user_skill_info in skill_info.get("users", []):
            user = User.query.filter_by(username=user_skill_info["username"]).first()
            if user:
                user_skill, created = _get_or_create(UserSkill, user=user, skill=skill)
                if created:
                    user_skill.skill_level = user_skill_info.get("level", 1)
    logger.info(f"Loaded {len(skills)} skills and their user associations.")
    return skills


def _create_assets(assets_data, logger):
    """Create assets."""
    assets = {}
    for i, asset_info in enumerate(assets_data):
        asset, _ = _get_or_create(Asset, name=asset_info["name"])
        asset.asset_code = asset_info.get("asset_code", f"AST-{i + 1:04d}")
        asset.description = asset_info.get("description", "")
        asset.asset_type = asset_info.get("asset_type", "equipment")
        asset.cost_center = asset_info.get("cost_center", "general")
        asset.status = asset_info.get("status", "Operational")
        assets[asset.name] = asset
    logger.info(f"Processed {len(assets_data)} assets.")
    return assets


def get_seeding_base_date():
    """Get the base date for seeding data.

    If FIXED_DATE_SEEDING env var is set, use that date (parsed as YYYY-MM-DD).
    Otherwise, use current UTC time.
    """
    fixed_date_str = os.environ.get("FIXED_DATE_SEEDING")
    if fixed_date_str:
        try:
            # Parse YYYY-MM-DD and set time to ~mid-day UTC for stability
            dt = datetime.strptime(fixed_date_str, "%Y-%m-%d")
            return dt.replace(
                hour=12, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
            )
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def _resolve_mo_assignees(assignee_tokens):
    """Resolve assignee tokens like user:<username> or team:<team_name> to users."""
    resolved_users = []
    seen_user_ids = set()

    for token in assignee_tokens or []:
        if not isinstance(token, str):
            continue
        value = token.strip()
        if not value:
            continue

        if value.startswith("user:"):
            username = value.split(":", 1)[1].strip()
            user = User.query.filter_by(username=username).first()
            if user and user.id not in seen_user_ids:
                resolved_users.append(user)
                seen_user_ids.add(user.id)
            continue

        if value.startswith("team:"):
            team_name = value.split(":", 1)[1].strip()
            team = Team.query.filter_by(name=team_name).first()
            if not team:
                continue
            for user in User.query.filter_by(team_id=team.id).all():
                if user.id not in seen_user_ids:
                    resolved_users.append(user)
                    seen_user_ids.add(user.id)

    return resolved_users


def _create_maintenance_orders(orders_data, assets, skills, logger):
    """Create maintenance orders."""
    base_now = get_seeding_base_date()

    for mo_info in orders_data:
        asset = assets.get(mo_info["asset"])
        if asset:
            due_date = None
            created_at = base_now

            if mo_info.get("due_date"):
                due_date = datetime.fromisoformat(mo_info["due_date"])
                if due_date.tzinfo is None:
                    due_date = due_date.replace(tzinfo=timezone.utc)
            elif mo_info.get("due_days_from_now") is not None:
                due_date = base_now + timedelta(days=mo_info["due_days_from_now"])
            elif mo_info.get("due_days_from_weekend") is not None:
                days_until_saturday = (5 - base_now.weekday()) % 7
                next_saturday = base_now + timedelta(days=days_until_saturday)
                due_date = next_saturday + timedelta(
                    days=mo_info["due_days_from_weekend"]
                )

            if mo_info.get("created_at"):
                created_at = datetime.fromisoformat(mo_info["created_at"])
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
            elif mo_info.get("created_hours_ago") is not None:
                created_at = base_now - timedelta(hours=mo_info["created_hours_ago"])

            mo, _ = _get_or_create(
                MaintenanceOrder, description=mo_info["description"], asset=asset
            )
            mo.title = mo_info.get("title")  # New field
            mo.category = mo_info.get("category")  # New field
            mo.order_type = mo_info.get("order_type", "PM")
            mo.status = mo_info.get("status", "Open")
            mo.due_date = due_date
            mo.created_at = created_at
            mo.priority = mo_info.get("priority", "Medium")
            mo.schedule_name = mo_info.get("schedule_name")
            mo.frequency = mo_info.get("frequency")
            mo.estimated_completion_time = mo_info.get("estimated_completion_time", 60)
            mo.labour_count = mo_info.get("labour_count", 1)
            mo.justification = mo_info.get("justification")

            # Breakdown-specific fields (for Reactive MOs)
            mo.downtime_duration = mo_info.get("downtime_duration")
            mo.root_cause = mo_info.get("root_cause")
            mo.recovery = mo_info.get("recovery")

            assignee_tokens = mo_info.get("assignees", [])
            mo.assignees_json = json.dumps(assignee_tokens) if assignee_tokens else None
            mo.assignees = _resolve_mo_assignees(assignee_tokens)

            for skill_name in mo_info.get("required_skills", []):
                if (
                    skill_name in skills
                    and skills[skill_name] not in mo.required_skills
                ):
                    mo.required_skills.append(skills[skill_name])
    logger.info(f"Processed {len(orders_data)} maintenance orders.")


def _create_spare_parts(parts_data, logger):
    """Create spare parts."""
    for part_info in parts_data:
        part, _ = _get_or_create(SparePart, description=part_info["description"])
        part.manufacturer = part_info.get("manufacturer", "")
        part.manufacturer_part_id = part_info.get("manufacturer_part_id", "")
        part.stock_quantity = part_info.get("quantity", 0)
        part.location = part_info.get("location", "")
        part.min_quantity = part_info.get("min_quantity", 0)
    logger.info(f"Processed {len(parts_data)} spare parts.")


def populate_dummy_data(logger):
    """Populates the database with initial dummy data."""
    logger = _get_seed_logger(logger)
    logger.info("Checking if database needs to be populated.")
    first_role = Role.query.first()
    if first_role or User.query.first():
        logger.info("Database already contains data. Skipping main population.")
        return

    logger.info("Populating database with dummy data.")
    data = _load_dummy_data(logger)
    if not data:
        return

    with db.session.begin_nested():
        roles = _create_roles(data.get("roles", []), logger)
        teams = _create_teams(data.get("teams", []), logger)
        _create_users(data.get("users", []), roles, teams, logger)
        _assign_technician_teams(data.get("technicians", []), logger)
        skills = _create_skills(data.get("skills", []), logger)
        assets = _create_assets(data.get("assets", []), logger)
        _create_maintenance_orders(
            data.get("maintenance_orders", []), assets, skills, logger
        )
        _create_spare_parts(data.get("spare_parts", []), logger)

    db.session.commit()
    logger.info("Dummy data population complete.")
