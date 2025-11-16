from flask import Blueprint, jsonify, request, session
from src.services.db_utils import db, Task, Skill, Technician, Asset, MaintenanceOrder, SparePart, User, Role
from sqlalchemy.exc import IntegrityError
from datetime import datetime

api_bp = Blueprint('api', __name__)

# --- Helper for Authentication (Basic Mock) ---
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"message": "Unauthorized: Login required"}), 401
        return f(*args, **kwargs)
    return decorated_function

# --- Task Endpoints (Existing) ---
@api_bp.route('/v1/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()
    return jsonify([task.to_dict() for task in tasks])

@api_bp.route('/v1/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = Task.query.get_or_404(task_id)
    return jsonify(task.to_dict())

@api_bp.route('/v1/tasks', methods=['POST'])
def add_task():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    required_fields = ['scheduler_group_task', 'mitarbeiter_pro_aufgabe', 'planned_worktime_min', 'priority', 'quantity', 'task_type']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    new_task = Task(
        scheduler_group_task=data['scheduler_group_task'],
        planning_notes=data.get('planning_notes'),
        lines=data.get('lines'),
        mitarbeiter_pro_aufgabe=data['mitarbeiter_pro_aufgabe'],
        planned_worktime_min=data['planned_worktime_min'],
        priority=data['priority'],
        quantity=data['quantity'],
        task_type=data['task_type'],
        ticket_mo=data.get('ticket_mo'),
        ticket_url=data.get('ticket_url')
    )

    if 'required_skills' in data and isinstance(data['required_skills'], list):
        for skill_name in data['required_skills']:
            skill = Skill.query.filter_by(name=skill_name).first()
            if not skill:
                skill = Skill(name=skill_name)
                db.session.add(skill)
            new_task.required_skills.append(skill)

    db.session.add(new_task)
    db.session.commit()
    return jsonify(new_task.to_dict()), 201

@api_bp.route('/v1/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    task.scheduler_group_task = data.get('scheduler_group_task', task.scheduler_group_task)
    task.planning_notes = data.get('planning_notes', task.planning_notes)
    task.lines = data.get('lines', task.lines)
    task.mitarbeiter_pro_aufgabe = data.get('mitarbeiter_pro_aufgabe', task.mitarbeiter_pro_aufgabe)
    task.planned_worktime_min = data.get('planned_worktime_min', task.planned_worktime_min)
    task.priority = data.get('priority', task.priority)
    task.quantity = data.get('quantity', task.quantity)
    task.task_type = data.get('task_type', task.task_type)
    task.ticket_mo = data.get('ticket_mo', task.ticket_mo)
    task.ticket_url = data.get('ticket_url', task.ticket_url)

    if 'required_skills' in data and isinstance(data['required_skills'], list):
        task.required_skills = [] # Clear existing skills
        for skill_name in data['required_skills']:
            skill = Skill.query.filter_by(name=skill_name).first()
            if not skill:
                skill = Skill(name=skill_name)
                db.session.add(skill)
            task.required_skills.append(skill)

    db.session.commit()
    return jsonify(task.to_dict())

@api_bp.route('/v1/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "Task deleted"}), 200

# --- Asset Endpoints ---
@api_bp.route('/v1/assets', methods=['GET'])
def get_assets():
    assets = Asset.query.all()
    return jsonify([asset.to_dict() for asset in assets])

@api_bp.route('/v1/assets/<int:asset_id>', methods=['GET'])
def get_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    return jsonify(asset.to_dict())

@api_bp.route('/v1/assets', methods=['POST'])
def add_asset():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Name is required"}), 400
    new_asset = Asset(
        name=data['name'],
        description=data.get('description'),
        location=data.get('location'),
        status=data.get('status', 'Operational')
    )
    db.session.add(new_asset)
    db.session.commit()
    return jsonify(new_asset.to_dict()), 201

@api_bp.route('/v1/assets/<int:asset_id>', methods=['PUT'])
def update_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    asset.name = data.get('name', asset.name)
    asset.description = data.get('description', asset.description)
    asset.location = data.get('location', asset.location)
    asset.status = data.get('status', asset.status)
    db.session.commit()
    return jsonify(asset.to_dict())

@api_bp.route('/v1/assets/<int:asset_id>', methods=['DELETE'])
def delete_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    db.session.delete(asset)
    db.session.commit()
    return jsonify({"message": "Asset deleted"}), 200

# --- Maintenance Order Endpoints ---
@api_bp.route('/v1/mos', methods=['GET'])
def get_mos():
    mos = MaintenanceOrder.query.all()
    return jsonify([mo.to_dict() for mo in mos])

@api_bp.route('/v1/mos/<int:mo_id>', methods=['GET'])
def get_mo(mo_id):
    mo = MaintenanceOrder.query.get_or_404(mo_id)
    return jsonify(mo.to_dict())

@api_bp.route('/v1/mos', methods=['POST'])
def add_mo():
    data = request.get_json()
    if not data or 'asset_id' not in data or 'description' not in data or 'order_type' not in data:
        return jsonify({"error": "Asset ID, description, and order type are required"}), 400
    new_mo = MaintenanceOrder(
        asset_id=data['asset_id'],
        description=data['description'],
        order_type=data['order_type'],
        status=data.get('status', 'Open'),
        due_date=datetime.fromisoformat(data['due_date']) if 'due_date' in data else None
    )
    db.session.add(new_mo)
    db.session.commit()
    return jsonify(new_mo.to_dict()), 201

@api_bp.route('/v1/mos/<int:mo_id>', methods=['PUT'])
def update_mo(mo_id):
    mo = MaintenanceOrder.query.get_or_404(mo_id)
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    mo.description = data.get('description', mo.description)
    mo.order_type = data.get('order_type', mo.order_type)
    mo.status = data.get('status', mo.status)
    if 'due_date' in data:
        mo.due_date = datetime.fromisoformat(data['due_date']) if data['due_date'] else None
    db.session.commit()
    return jsonify(mo.to_dict())

@api_bp.route('/v1/mos/<int:mo_id>', methods=['DELETE'])
def delete_mo(mo_id):
    mo = MaintenanceOrder.query.get_or_404(mo_id)
    db.session.delete(mo)
    db.session.commit()
    return jsonify({"message": "Maintenance Order deleted"}), 200

# --- Spare Part Endpoints ---
@api_bp.route('/v1/spare_parts', methods=['GET'])
def get_spare_parts():
    parts = SparePart.query.all()
    return jsonify([part.to_dict() for part in parts])

@api_bp.route('/v1/spare_parts/<int:part_id>', methods=['GET'])
def get_spare_part(part_id):
    part = SparePart.query.get_or_404(part_id)
    return jsonify(part.to_dict())

@api_bp.route('/v1/spare_parts', methods=['POST'])
def add_spare_part():
    data = request.get_json()
    if not data or 'name' not in data or 'quantity' not in data:
        return jsonify({"error": "Name and quantity are required"}), 400
    new_part = SparePart(
        name=data['name'],
        description=data.get('description'),
        quantity=data['quantity'],
        location=data.get('location'),
        min_quantity=data.get('min_quantity', 0)
    )
    db.session.add(new_part)
    db.session.commit()
    return jsonify(new_part.to_dict()), 201

@api_bp.route('/v1/spare_parts/<int:part_id>', methods=['PUT'])
def update_spare_part(part_id):
    part = SparePart.query.get_or_404(part_id)
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    part.name = data.get('name', part.name)
    part.description = data.get('description', part.description)
    part.quantity = data.get('quantity', part.quantity)
    part.location = data.get('location', part.location)
    part.min_quantity = data.get('min_quantity', part.min_quantity)
    db.session.commit()
    return jsonify(part.to_dict())

@api_bp.route('/v1/spare_parts/<int:part_id>', methods=['DELETE'])
def delete_spare_part(part_id):
    part = SparePart.query.get_or_404(part_id)
    db.session.delete(part)
    db.session.commit()
    return jsonify({"message": "Spare Part deleted"}), 200

# --- User and Role Endpoints ---
@api_bp.route('/v1/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict(include_roles=True) for user in users])

@api_bp.route('/v1/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict(include_roles=True))

@api_bp.route('/v1/users', methods=['POST'])
def register_user():
    data = request.get_json()
    if not data or 'username' not in data or 'email' not in data or 'password' not in data:
        return jsonify({"error": "Username, email, and password are required"}), 400
    
    if User.query.filter_by(username=data['username']).first() or User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Username or email already exists"}), 409

    new_user = User(username=data['username'], email=data['email'])
    new_user.set_password(data['password'])
    
    if 'roles' in data and isinstance(data['roles'], list):
        for role_name in data['roles']:
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                role = Role(name=role_name)
                db.session.add(role)
            new_user.roles.append(role)

    db.session.add(new_user)
    db.session.commit()
    return jsonify(new_user.to_dict(include_roles=True)), 201

@api_bp.route('/v1/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    
    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    if 'password' in data:
        user.set_password(data['password'])
    user.is_active = data.get('is_active', user.is_active)

    if 'roles' in data and isinstance(data['roles'], list):
        user.roles = [] # Clear existing roles
        for role_name in data['roles']:
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                role = Role(name=role_name)
                db.session.add(role)
            user.roles.append(role)

    db.session.commit()
    return jsonify(user.to_dict(include_roles=True))

@api_bp.route('/v1/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted"}), 200

@api_bp.route('/v1/roles', methods=['GET'])
def get_roles():
    roles = Role.query.all()
    return jsonify([role.to_dict() for role in roles])

@api_bp.route('/v1/roles', methods=['POST'])
def add_role():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Role name is required"}), 400
    
    if Role.query.filter_by(name=data['name']).first():
        return jsonify({"error": "Role name already exists"}), 409

    new_role = Role(name=data['name'], description=data.get('description'))
    db.session.add(new_role)
    db.session.commit()
    return jsonify(new_role.to_dict()), 201

# --- Authentication Endpoints ---
@api_bp.route('/v1/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"message": "Username and password required"}), 400

    user = User.query.filter_by(username=data['username']).first()
    if user and user.check_password(data['password']):
        session['user_id'] = user.id
        return jsonify({"message": "Login successful", "user": user.to_dict(include_roles=True)}), 200
    return jsonify({"message": "Invalid credentials"}), 401

@api_bp.route('/v1/auth/logout', methods=['POST'])
@login_required
def logout():
    session.pop('user_id', None)
    return jsonify({"message": "Logged out successfully"}), 200

@api_bp.route('/v1/auth/status', methods=['GET'])
def auth_status():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return jsonify({"logged_in": True, "user": user.to_dict(include_roles=True)}), 200
    return jsonify({"logged_in": False}), 200
