"""Data Simulation Service for generating high-volume mock data."""

import random
import uuid
from datetime import datetime, timedelta, timezone
from src.services.db_utils import db, Asset, User, MaintenanceOrder, Role, Team

class DataSimulationService:
    """Service to generate random data for stress testing and demos."""

    ASSET_TYPES = ["equipment", "vehicle", "tool", "facility"]
    ASSET_PREFIXES = ["PUMP", "MOTOR", "CONV", "ROBOT", "PRESS", "DRILL"]

    MO_STATUSES = ["Open", "In Progress", "Pending", "Closed", "Cancelled"]
    MO_TYPES = ["PM", "CM", "PdM", "Emergency"]
    MO_PRIORITIES = ["Low", "Medium", "High", "Critical"]

    @staticmethod
    def generate_random_assets(count=10):
        """Generate random assets."""
        generated = []
        for _ in range(count):
            prefix = random.choice(DataSimulationService.ASSET_PREFIXES)
            unique_id = uuid.uuid4().hex[:6].upper()
            asset_code = f"{prefix}-{unique_id}"

            asset = Asset(
                name=f"Asset {asset_code}",
                asset_code=asset_code,
                description=f"Simulated {random.choice(DataSimulationService.ASSET_TYPES)} {asset_code}",
                asset_type=random.choice(DataSimulationService.ASSET_TYPES),
                cost_center=f"CC-{random.randint(100, 999)}",
                status=random.choice(["Operational", "Under Maintenance", "Offline"])
            )
            db.session.add(asset)
            generated.append(asset)

        db.session.commit()
        return generated

    @staticmethod
    def generate_random_technicians(count=10):
        """Generate random technicians."""
        # Ensure Technician role exists
        tech_role = Role.query.filter_by(name="Technician").first()
        if not tech_role:
            tech_role = Role(name="Technician", description="Maintenance Technician")
            db.session.add(tech_role)
            db.session.commit()

        # Ensure at least one team exists
        team = Team.query.filter_by(name="Team A").first()
        if not team:
            # Try to get any team
            team = Team.query.first()
            if not team:
                team = Team(name="Team A")
                db.session.add(team)
                db.session.commit()

        generated = []
        for _ in range(count):
            uid = uuid.uuid4().hex[:8]
            username = f"tech_{uid}"
            email = f"{username}@example.com"

            user = User(username=username, email=email)
            user.set_password("password123")
            user.roles.append(tech_role)
            user.team = team

            db.session.add(user)
            generated.append(user)

        db.session.commit()
        return generated

    @staticmethod
    def generate_random_orders(count=10):
        """Generate random maintenance orders for existing assets."""
        assets = Asset.query.all()
        if not assets:
            return []

        generated = []
        now = datetime.now(timezone.utc)

        for _ in range(count):
            asset = random.choice(assets)
            mo_type = random.choice(DataSimulationService.MO_TYPES)

            # Create simulated dates
            created_delta = random.randint(1, 365)
            created_at = now - timedelta(days=created_delta)
            due_at = created_at + timedelta(days=random.randint(1, 30))

            description = f"Simulated {mo_type} for {asset.name} - Issue {uuid.uuid4().hex[:4]}"

            mo = MaintenanceOrder(
                description=description,
                asset_id=asset.id,
                order_type=mo_type,
                status=random.choice(DataSimulationService.MO_STATUSES),
                priority=random.choice(DataSimulationService.MO_PRIORITIES),
                due_date=due_at,
                created_at=created_at,
                estimated_completion_time=random.randint(30, 480)
            )
            db.session.add(mo)
            generated.append(mo)

        db.session.commit()
        return generated
