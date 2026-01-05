"""Simulation Service Module.

This module provides the DataSimulationService class for generating randomized mock data
for testing and demonstration purposes.
"""

import json
import logging
import os
import random
import uuid
from datetime import datetime, timedelta, timezone

from src.services.db_utils import (
    Asset,
    MaintenanceOrder,
    Role,
    SparePart,
    Team,
    User,
    db,
)

logger = logging.getLogger(__name__)


class DataSimulationService:
    """Service to generate random data for stress testing and demos."""

    _constants = None

    @classmethod
    def _load_constants(cls):
        """Load constants from the centralized configuration file."""
        if cls._constants:
            return

        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(
                current_dir, "..", "config", "dropdown_options.json"
            )
            with open(config_path, "r", encoding="utf-8") as f:
                cls._constants = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            # Fallback if config fails (should verify in tests)
            logger.error(f"Error loading simulation config: {e}")
            cls._constants = {}

    @classmethod
    def _get_option(cls, entity, field):
        """Retrieve a random option for a given entity and field."""
        cls._load_constants()
        options = cls._constants.get(entity, {}).get(field, [])
        return random.choice(options) if options else f"Default {field}"

    @staticmethod
    def generate_random_assets(count=10):
        """Generate random assets."""
        generated = []
        # Ensure prefixes available
        prefixes = ["PUMP", "MOTOR", "CONV", "ROBOT", "PRESS", "DRILL"]

        for _ in range(count):
            prefix = random.choice(prefixes)
            # Use short UUID for cleaner codes
            unique_id = uuid.uuid4().hex[:6].upper()
            asset_code = f"{prefix}-{unique_id}"

            asset_type = DataSimulationService._get_option("Asset", "asset_type")
            status = DataSimulationService._get_option("Asset", "status")
            cost_center = DataSimulationService._get_option("Asset", "cost_center")

            asset = Asset(
                name=f"Asset {asset_code}",
                asset_code=asset_code,
                description=f"Simulated {asset_type} {asset_code}",
                asset_type=asset_type,
                cost_center=cost_center,
                status=status,
            )
            db.session.add(asset)
            generated.append(asset)

        db.session.commit()
        return generated

    @staticmethod
    def generate_random_users(count=10):
        """Generate random users with various roles, teams, and availability."""
        # Ensure Teams exist
        DataSimulationService._load_constants()
        team_names = DataSimulationService._constants.get("Team", {}).get(
            "names", ["Team A", "Team B"]
        )
        DataSimulationService._constants.get("User", {}).get("roles", ["Technician"])

        teams = []
        for t_name in team_names:
            team = Team.query.filter_by(name=t_name).first()
            if not team:
                team = Team(name=t_name)
                db.session.add(team)
            teams.append(team)
        db.session.commit()

        generated = []
        for _ in range(count):
            uid = uuid.uuid4().hex[:8]
            username = f"user_{uid}"
            email = f"{username}@example.com"

            # Randomize Role
            role_name = DataSimulationService._get_option("User", "roles")
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                role = Role(name=role_name, description=f"{role_name} Role")
                db.session.add(role)
                db.session.commit()  # Commit role creation immediately

            user = User(username=username, email=email)
            user.set_password("password123")
            user.roles.append(role)
            user.team = random.choice(teams)
            user.availability_status = DataSimulationService._get_option(
                "User", "availability_status"
            )

            db.session.add(user)
            generated.append(user)

        db.session.commit()
        return generated

    @staticmethod
    def generate_random_orders(count=10):
        """Generate random maintenance orders for existing assets."""
        assets = Asset.query.all()
        technicians = (
            User.query.join(User.roles).filter(Role.name == "Technician").all()
        )
        teams = Team.query.all()

        if not assets:
            return []

        generated = []
        now = datetime.now(timezone.utc)

        for i in range(count):
            asset = random.choice(assets)
            mo_type = DataSimulationService._get_option(
                "MaintenanceOrder", "order_type"
            )
            status = DataSimulationService._get_option("MaintenanceOrder", "status")
            priority = DataSimulationService._get_option("MaintenanceOrder", "priority")
            frequency = DataSimulationService._get_option(
                "MaintenanceOrder", "frequency"
            )
            justification = DataSimulationService._get_option(
                "MaintenanceOrder", "justification"
            )

            # Create simulated dates
            created_delta = random.randint(1, 365)
            created_at = now - timedelta(days=created_delta)
            due_at = created_at + timedelta(days=random.randint(1, 30))

            schedule_name = f"{frequency} {mo_type} Plan"

            # Assignees Logic
            assignees = []

            # Every 100th order -> Assign Full Team (All users in that team)
            if (i + 1) % 100 == 0 and teams:
                team = random.choice(teams)
                assignees = team.users  # Assign ALL users in the team
            else:
                # Assign 1 to 3 random technicians if available
                # Note: We prefer technicians for work orders, but could be any user?
                # Keeping 'technicians' list for individual assignment to be realistic.
                if technicians:
                    k = random.randint(1, min(3, len(technicians)))
                    assignees = random.sample(technicians, k)

            labour_count = len(assignees)

            description = (
                f"Simulated {mo_type} for {asset.name} - Issue {uuid.uuid4().hex[:4]}"
            )

            mo = MaintenanceOrder(
                description=description,
                asset_id=asset.id,
                order_type=mo_type,
                status=status,
                priority=priority,
                due_date=due_at,
                created_at=created_at,
                estimated_completion_time=random.randint(30, 480),
                schedule_name=schedule_name,
                frequency=frequency,
                labour_count=labour_count,
                justification=justification,
                assignees=assignees,
            )
            db.session.add(mo)
            generated.append(mo)

        db.session.commit()
        return generated

    @staticmethod
    def generate_random_spare_parts(count=10):
        """Generate random spare parts."""
        generated = []
        for _ in range(count):
            uid = uuid.uuid4().hex[:6].upper()
            part_name = f"Part-{uid}"

            location = DataSimulationService._get_option("SparePart", "location")
            manufacturer = DataSimulationService._get_option(
                "SparePart", "manufacturer"
            )

            part = SparePart(
                description=f"Simulated Spare Part {part_name}",
                manufacturer=manufacturer,
                manufacturer_part_id=f"MFG-{uid}",
                stock_quantity=random.randint(0, 1000),
                min_quantity=random.randint(5, 50),
                location=location,
            )
            db.session.add(part)
            generated.append(part)

        db.session.commit()
        return generated
