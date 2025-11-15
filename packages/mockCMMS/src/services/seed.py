import os
import sys

# Add the monorepo root to sys.path
# This allows imports like 'packages.mockCMMS.src.app' to work
current_dir = os.path.dirname(os.path.abspath(__file__))
monorepo_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..')) # Corrected path
sys.path.insert(0, monorepo_root)

from packages.mockCMMS.src.app import create_app
from packages.mockCMMS.src.services.db import db, Task, Technician, Skill, Asset, MaintenanceOrder, SparePart, User, Role
from datetime import datetime, timedelta, timezone

def seed_data():
    app = create_app()
    with app.app_context():
        db.drop_all() # Clear existing data for a fresh seed
        db.create_all() # Create tables

        # Create Roles
        role_admin = Role(name='Admin', description='Administrator with full access')
        role_user = Role(name='User', description='Standard user with limited access')
        role_technician = Role(name='Technician', description='Can view and update assigned tasks')
        db.session.add_all([role_admin, role_user, role_technician])
        db.session.commit()

        # Create Users
        user_admin = User(username='admin', email='admin@example.com')
        user_admin.set_password('adminpass')
        user_admin.roles.append(role_admin)
        user_admin.roles.append(role_user)

        user_john = User(username='john.doe', email='john.doe@example.com')
        user_john.set_password('johnpass')
        user_john.roles.append(role_user)
        user_john.roles.append(role_technician)

        db.session.add_all([user_admin, user_john])
        db.session.commit()

        # Create Skills
        skill_python = Skill(name='Python')
        skill_flask = Skill(name='Flask')
        skill_db = Skill(name='Database')
        skill_frontend = Skill(name='Frontend')
        skill_network = Skill(name='Network')
        skill_hardware = Skill(name='Hardware')
        skill_electrical = Skill(name='Electrical')
        skill_mechanical = Skill(name='Mechanical')

        db.session.add_all([skill_python, skill_flask, skill_db, skill_frontend, skill_network, skill_hardware, skill_electrical, skill_mechanical])
        db.session.commit()

        # Create Technicians
        tech_alice = Technician(name='Alice')
        tech_bob = Technician(name='Bob')
        tech_charlie = Technician(name='Charlie')

        db.session.add_all([tech_alice, tech_bob, tech_charlie])
        db.session.commit()

        # Create Assets
        asset1 = Asset(name='Server Rack 01', description='Main production server rack', location='Server Room A', status='Operational')
        asset2 = Asset(name='HVAC Unit 03', description='Third floor HVAC system', location='Roof', status='Operational')
        asset3 = Asset(name='CNC Machine 05', description='Precision manufacturing machine', location='Workshop', status='Under Maintenance')
        db.session.add_all([asset1, asset2, asset3])
        db.session.commit()

        # Create Maintenance Orders
        mo1 = MaintenanceOrder(asset=asset1, description='Quarterly server rack inspection', order_type='PM', status='Open', due_date=datetime.now(timezone.utc) + timedelta(days=7))
        mo2 = MaintenanceOrder(asset=asset2, description='HVAC filter replacement', order_type='PM', status='In Progress', due_date=datetime.now(timezone.utc) + timedelta(days=14))
        mo3 = MaintenanceOrder(asset=asset3, description='CNC spindle repair', order_type='Corrective', status='Open', due_date=datetime.now(timezone.utc) + timedelta(days=3))
        db.session.add_all([mo1, mo2, mo3])
        db.session.commit()

        # Create Spare Parts
        part1 = SparePart(name='Server Fan', description='Cooling fan for server racks', quantity=10, location='Warehouse A1', min_quantity=5)
        part2 = SparePart(name='HVAC Filter', description='Standard HVAC filter', quantity=50, location='Warehouse B2', min_quantity=20)
        part3 = SparePart(name='CNC Spindle', description='Replacement spindle for CNC machine', quantity=2, location='Workshop Storage', min_quantity=1)
        db.session.add_all([part1, part2, part3])
        db.session.commit()

        # Create Tasks (existing tasks, now with skills)
        task1 = Task(
            scheduler_group_task='Server Maintenance',
            planning_notes='Check logs, update OS, verify backups',
            lines='Datacenter',
            mitarbeiter_pro_aufgabe=2,
            planned_worktime_min=120,
            priority='A',
            quantity=1,
            task_type='PM',
            ticket_mo='CMMS-101',
            ticket_url='http://mockcmms/tickets/CMMS-101'
        )
        task1.required_skills.extend([skill_network, skill_hardware])

        task2 = Task(
            scheduler_group_task='API Endpoint Debug',
            planning_notes='Investigate /api/v1/tasks performance',
            lines='Backend',
            mitarbeiter_pro_aufgabe=1,
            planned_worktime_min=60,
            priority='B',
            quantity=2,
            task_type='Rep',
            ticket_mo='CMMS-102',
            ticket_url='http://mockcmms/tickets/CMMS-102'
        )
        task2.required_skills.extend([skill_python, skill_flask])

        task3 = Task(
            scheduler_group_task='Frontend UI Fix',
            planning_notes='Adjust dashboard layout for mobile',
            lines='Frontend',
            mitarbeiter_pro_aufgabe=1,
            planned_worktime_min=90,
            priority='C',
            quantity=1,
            task_type='Rep',
            ticket_mo='CMMS-103',
            ticket_url='http://mockcmms/tickets/CMMS-103'
        )
        task3.required_skills.extend([skill_frontend])

        task4 = Task(
            scheduler_group_task='Database Optimization',
            planning_notes='Review slow queries, add indexes',
            lines='Database',
            mitarbeiter_pro_aufgabe=1,
            planned_worktime_min=180,
            priority='A',
            quantity=1,
            task_type='PM',
            ticket_mo='CMMS-104',
            ticket_url='http://mockcmms/tickets/CMMS-104'
        )
        task4.required_skills.extend([skill_db])

        db.session.add_all([task1, task2, task3, task4])
        db.session.commit()

        print("Database seeded successfully!")

if __name__ == '__main__':
    seed_data()
