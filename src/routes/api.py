from flask import Blueprint, jsonify, request, session
from src.services.db_utils import db, Skill, Asset, MaintenanceOrder, SparePart, User, Role, TableConfiguration
import json
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

# Task endpoints REMOVED - use MaintenanceOrder endpoints (/v1/mos) instead
# Legacy Task model has been deprecated

# --- Asset Endpoints ---
@api_bp.route('/v1/assets', methods=['GET'])
def get_assets():
    assets = Asset.query.all()
    return jsonify([asset.to_dict() for asset in assets])

@api_bp.route('/v1/assets/<int:asset_id>', methods=['GET'])
def get_asset(asset_id):
    asset = db.session.get(Asset, asset_id)
    if not asset:
        return jsonify({"error": "Asset not found"}), 404
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
    asset = db.session.get(Asset, asset_id)
    if not asset:
        return jsonify({"error": "Asset not found"}), 404
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
    asset = db.session.get(Asset, asset_id)
    if not asset:
        return jsonify({"error": "Asset not found"}), 404
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
    mo = db.session.get(MaintenanceOrder, mo_id)
    if not mo:
        return jsonify({"error": "Maintenance Order not found"}), 404
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
        due_date=datetime.fromisoformat(data['due_date']) if 'due_date' in data else None,
        priority=data.get('priority', 'Undefined')
    )
    db.session.add(new_mo) # Add to session before manipulating relationships

    # Handle required skills
    if 'required_skills' in data and isinstance(data['required_skills'], list):
        for skill_name in data['required_skills']:
            skill = Skill.query.filter_by(name=skill_name).first()
            if not skill:
                skill = Skill(name=skill_name)
                db.session.add(skill)
            new_mo.required_skills.append(skill)

    db.session.commit()
    return jsonify(new_mo.to_dict()), 201

@api_bp.route('/v1/mos/<int:mo_id>', methods=['PUT'])
def update_mo(mo_id):
    mo = db.session.get(MaintenanceOrder, mo_id)
    if not mo:
        return jsonify({"error": "Maintenance Order not found"}), 404
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
    mo = db.session.get(MaintenanceOrder, mo_id)
    if not mo:
        return jsonify({"error": "Maintenance Order not found"}), 404
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
    part = db.session.get(SparePart, part_id)
    if not part:
        return jsonify({"error": "Spare Part not found"}), 404
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
    part = db.session.get(SparePart, part_id)
    if not part:
        return jsonify({"error": "Spare Part not found"}), 404
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
    part = db.session.get(SparePart, part_id)
    if not part:
        return jsonify({"error": "Spare Part not found"}), 404
    db.session.delete(part)
    db.session.commit()
    return jsonify({"message": "Spare Part deleted"}), 200

# --- User and Role Endpoints ---
@api_bp.route('/v1/users', methods=['GET'])
def get_users():
    # Eager load roles and team to prevent N+1 queries
    users = User.query.options(db.joinedload(User.roles), db.joinedload(User.team)).all()
    return jsonify([user.to_dict(include_roles=True) for user in users])

@api_bp.route('/v1/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
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
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
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
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
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
        user = db.session.get(User, session['user_id'])
        if user:
            return jsonify({"logged_in": True, "user": user.to_dict(include_roles=True)}), 200
    return jsonify({"logged_in": False}), 200

# --- Table Configuration API ---
@api_bp.route('/table-config/<page_name>', methods=['GET'])
def get_table_configs(page_name):
    if 'user_id' not in session:
        return jsonify({"error": "Authentication required"}), 401
    
    configs = TableConfiguration.query.filter_by(
        user_id=session['user_id'], 
        page_name=page_name
    ).all()
    
    return jsonify([config.to_dict() for config in configs])

@api_bp.route('/table-config/<page_name>', methods=['POST'])
def save_table_config(page_name):
    if 'user_id' not in session:
        return jsonify({"error": "Authentication required"}), 401
    
    data = request.get_json()
    
    # If setting as default, remove default from other configs
    if data.get('is_default'):
        TableConfiguration.query.filter_by(
            user_id=session['user_id'],
            page_name=page_name,
            is_default=True
        ).update({'is_default': False})
    
    config = TableConfiguration(
        user_id=session['user_id'],
        page_name=page_name,
        config_name=data['config_name'],
        column_order=data.get('column_order'),
        hidden_columns=data.get('hidden_columns'),
        filters=data.get('filters'),
        sort_config=data.get('sort_config'),
        is_default=data.get('is_default', False)
    )
    
    db.session.add(config)
    db.session.commit()
    
    return jsonify({"success": True, "id": config.id})

@api_bp.route('/table-config/<int:config_id>', methods=['DELETE'])
def delete_table_config(config_id):
    if 'user_id' not in session:
        return jsonify({"error": "Authentication required"}), 401
    
    config = db.session.get(TableConfiguration, config_id)
    if not config or config.user_id != session['user_id']:
        return jsonify({"error": "Configuration not found or not owned by user"}), 404

    db.session.delete(config)
    db.session.commit()
    
    return jsonify({"success": True})

@api_bp.route('/table-config/<int:config_id>', methods=['PUT'])
def update_table_config(config_id):
    if 'user_id' not in session:
        return jsonify({"error": "Authentication required"}), 401

    config = db.session.get(TableConfiguration, config_id)
    if not config or config.user_id != session['user_id']:
        return jsonify({"error": "Configuration not found or not owned by user"}), 404

    data = request.get_json()

    # Update configuration fields
    if 'column_order' in data:
        config.column_order = data['column_order']
    if 'hidden_columns' in data:
        config.hidden_columns = data['hidden_columns']
    if 'filters' in data:
        config.filters = data['filters']
    if 'sort_config' in data:
        config.sort_config = data['sort_config']

    db.session.commit()

    return jsonify({"success": True})

@api_bp.route('/table-config/<page_name>/<int:config_id>/set-default', methods=['POST'])
def set_default_table_config(page_name, config_id):
    if 'user_id' not in session:
        return jsonify({"error": "Authentication required"}), 401

    # Remove default from all configs for this page
    TableConfiguration.query.filter_by(
        user_id=session['user_id'],
        page_name=page_name,
        is_default=True
    ).update({'is_default': False})

    # Set this config as default
    config = db.session.get(TableConfiguration, config_id)
    if not config or config.user_id != session['user_id']:
        return jsonify({"error": "Configuration not found or not owned by user"}), 404

    config.is_default = True
    db.session.commit()

    return jsonify({"success": True})

@api_bp.route('/table-config/<page_name>/<int:config_id>/remove-default', methods=['POST'])
def remove_default_table_config(page_name, config_id):
    if 'user_id' not in session:
        return jsonify({"error": "Authentication required"}), 401

    # Remove default from this config
    config = db.session.get(TableConfiguration, config_id)
    if not config or config.user_id != session['user_id']:
        return jsonify({"error": "Configuration not found or not owned by user"}), 404

    config.is_default = False
    db.session.commit()

    return jsonify({"success": True})

# --- Enhanced Data Endpoints ---
@api_bp.route('/<entity>/filtered', methods=['GET'])
def get_filtered_data(entity):
    models = {
        'assets': Asset,
        'maintenance_orders': MaintenanceOrder,
        'spare_parts': SparePart,
        'users': User
    }
    
    if entity not in models:
        return jsonify({"error": "Invalid entity"}), 400
    
    model = models[entity]
    query = model.query
    
    # Apply filters
    filters = request.args.get('filters')
    if filters:
        try:
            filter_dict = json.loads(filters)
            for column, filter_config in filter_dict.items():
                if hasattr(model, column):
                    column_attr = getattr(model, column)
                    value = filter_config['value']
                    operator = filter_config['operator']
                    
                    if operator == 'contains':
                        query = query.filter(column_attr.like(f'%{value}%'))
                    elif operator == 'equals':
                        query = query.filter(column_attr == value)
                    elif operator == 'not_equals':
                        query = query.filter(column_attr != value)
        except json.JSONDecodeError:
            pass
    
    # Apply sorting
    sort_column = request.args.get('sort_column')
    sort_direction = request.args.get('sort_direction', 'asc')
    
    if sort_column and hasattr(model, sort_column):
        column_attr = getattr(model, sort_column)
        if sort_direction == 'desc':
            query = query.order_by(column_attr.desc())
        else:
            query = query.order_by(column_attr.asc())
    
    results = query.all()
    return jsonify([item.to_dict() for item in results])
