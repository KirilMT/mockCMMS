from flask import Blueprint, jsonify, request, session
from src.services.db_utils import (
    db,
    Skill,
    Asset,
    MaintenanceOrder,
    SparePart,
    User,
    Role,
    TableConfiguration,
)
import json
from datetime import datetime
from functools import wraps
from sqlalchemy.exc import SQLAlchemyError

api_bp = Blueprint("api", __name__)


# --- Helper Functions ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"message": "Unauthorized: Login required"}), 401
        return f(*args, **kwargs)

    return decorated_function


def get_entity_or_404(model, entity_id, entity_name="Entity"):
    """Get entity by ID or return 404 error."""
    entity = db.session.get(model, entity_id)
    if not entity:
        return None, (jsonify({"error": f"{entity_name} not found"}), 404)
    return entity, None


def validate_json_data(required_fields=None):
    """Validate JSON request data."""
    data = request.get_json()
    if not data:
        return None, (jsonify({"error": "Invalid JSON"}), 400)

    if required_fields:
        missing = [f for f in required_fields if f not in data]
        if missing:
            return None, (
                jsonify({"error": f"Missing required fields: {', '.join(missing)}"}),
                400,
            )

    return data, None


def safe_commit():
    """Commit with rollback on error."""
    try:
        db.session.commit()
        return True, None
    except SQLAlchemyError:
        db.session.rollback()
        return False, (jsonify({"error": "Database error occurred"}), 500)


def parse_datetime_safe(date_str):
    """Parse datetime string safely."""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str)
    except (ValueError, TypeError):
        return None


def sanitize_like_value(value):
    """Sanitize value for SQL LIKE queries to prevent injection."""
    if not isinstance(value, str):
        return str(value)
    return value.replace("%", "\\%").replace("_", "\\_")


# Task endpoints REMOVED - use MaintenanceOrder endpoints (/v1/mos) instead
# Legacy Task model has been deprecated


# --- Asset Endpoints ---
@api_bp.route("/v1/assets", methods=["GET"])
def get_assets():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 100, type=int)
    assets = Asset.query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify([asset.to_dict() for asset in assets.items])


@api_bp.route("/v1/assets/<int:asset_id>", methods=["GET"])
def get_asset(asset_id):
    asset, error = get_entity_or_404(Asset, asset_id, "Asset")
    if error:
        return error
    return jsonify(asset.to_dict())


@api_bp.route("/v1/assets", methods=["POST"])
def add_asset():
    data, error = validate_json_data(["name", "asset_code"])
    if error:
        return error

    new_asset = Asset(
        asset_code=data["asset_code"],
        name=data["name"],
        description=data.get("description"),
        asset_type=data.get("asset_type"),
        cost_center=data.get("cost_center"),
        status=data.get("status", "Operational"),
    )
    db.session.add(new_asset)
    success, error = safe_commit()
    if not success:
        return error
    return jsonify(new_asset.to_dict()), 201


@api_bp.route("/v1/assets/<int:asset_id>", methods=["PUT"])
def update_asset(asset_id):
    asset, error = get_entity_or_404(Asset, asset_id, "Asset")
    if error:
        return error

    data, error = validate_json_data()
    if error:
        return error

    asset.name = data.get("name", asset.name)
    asset.description = data.get("description", asset.description)
    asset.asset_type = data.get("asset_type", asset.asset_type)
    asset.cost_center = data.get("cost_center", asset.cost_center)
    asset.status = data.get("status", asset.status)

    success, error = safe_commit()
    if not success:
        return error
    return jsonify(asset.to_dict())


@api_bp.route("/v1/assets/<int:asset_id>", methods=["DELETE"])
def delete_asset(asset_id):
    asset, error = get_entity_or_404(Asset, asset_id, "Asset")
    if error:
        return error

    db.session.delete(asset)
    success, error = safe_commit()
    if not success:
        return error
    return jsonify({"message": "Asset deleted"}), 200


# --- Maintenance Order Endpoints ---
@api_bp.route("/v1/mos", methods=["GET"])
def get_mos():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 100, type=int)
    mos = MaintenanceOrder.query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify([mo.to_dict() for mo in mos.items])


@api_bp.route("/v1/mos/<int:mo_id>", methods=["GET"])
def get_mo(mo_id):
    mo, error = get_entity_or_404(MaintenanceOrder, mo_id, "Maintenance Order")
    if error:
        return error
    return jsonify(mo.to_dict())


@api_bp.route("/v1/mos", methods=["POST"])
def add_mo():
    data, error = validate_json_data(["asset_id", "description", "order_type"])
    if error:
        return error

    # Validate asset exists
    asset, error = get_entity_or_404(Asset, data["asset_id"], "Asset")
    if error:
        return error

    # Parse due_date safely
    due_date = None
    if "due_date" in data:
        due_date = parse_datetime_safe(data["due_date"])
        if due_date is None and data["due_date"]:
            return jsonify({"error": "Invalid date format"}), 400

    new_mo = MaintenanceOrder(
        asset_id=data["asset_id"],
        description=data["description"],
        order_type=data["order_type"],
        status=data.get("status", "Open"),
        due_date=due_date,
        priority=data.get("priority", "Undefined"),
    )
    db.session.add(new_mo)

    # Handle required skills
    if "required_skills" in data and isinstance(data["required_skills"], list):
        for skill_name in data["required_skills"]:
            skill = Skill.query.filter_by(name=skill_name).first()
            if not skill:
                skill = Skill(name=skill_name)
                db.session.add(skill)
            new_mo.required_skills.append(skill)

    success, error = safe_commit()
    if not success:
        return error
    return jsonify(new_mo.to_dict()), 201


@api_bp.route("/v1/mos/<int:mo_id>", methods=["PUT"])
def update_mo(mo_id):
    mo, error = get_entity_or_404(MaintenanceOrder, mo_id, "Maintenance Order")
    if error:
        return error

    data, error = validate_json_data()
    if error:
        return error

    mo.description = data.get("description", mo.description)
    mo.order_type = data.get("order_type", mo.order_type)
    mo.status = data.get("status", mo.status)

    if "due_date" in data:
        due_date = parse_datetime_safe(data["due_date"])
        if due_date is None and data["due_date"]:
            return jsonify({"error": "Invalid date format"}), 400
        mo.due_date = due_date

    success, error = safe_commit()
    if not success:
        return error
    return jsonify(mo.to_dict())


@api_bp.route("/v1/mos/<int:mo_id>", methods=["DELETE"])
def delete_mo(mo_id):
    mo, error = get_entity_or_404(MaintenanceOrder, mo_id, "Maintenance Order")
    if error:
        return error

    db.session.delete(mo)
    success, error = safe_commit()
    if not success:
        return error
    return jsonify({"message": "Maintenance Order deleted"}), 200


# --- Spare Part Endpoints ---
@api_bp.route("/v1/spare_parts", methods=["GET"])
def get_spare_parts():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 100, type=int)
    parts = SparePart.query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify([part.to_dict() for part in parts.items])


@api_bp.route("/v1/spare_parts/<int:part_id>", methods=["GET"])
def get_spare_part(part_id):
    part, error = get_entity_or_404(SparePart, part_id, "Spare Part")
    if error:
        return error
    return jsonify(part.to_dict())


@api_bp.route("/v1/spare_parts", methods=["POST"])
def add_spare_part():
    data, error = validate_json_data(["description"])
    if error:
        return error

    new_part = SparePart(
        description=data["description"],
        manufacturer=data.get("manufacturer"),
        manufacturer_part_id=data.get("manufacturer_part_id"),
        stock_quantity=data.get("stock_quantity", 0),
        location=data.get("location"),
        min_quantity=data.get("min_quantity", 0),
    )
    db.session.add(new_part)
    success, error = safe_commit()
    if not success:
        return error
    return jsonify(new_part.to_dict()), 201


@api_bp.route("/v1/spare_parts/<int:part_id>", methods=["PUT"])
def update_spare_part(part_id):
    part, error = get_entity_or_404(SparePart, part_id, "Spare Part")
    if error:
        return error

    data, error = validate_json_data()
    if error:
        return error

    part.description = data.get("description", part.description)
    part.manufacturer = data.get("manufacturer", part.manufacturer)
    part.manufacturer_part_id = data.get(
        "manufacturer_part_id", part.manufacturer_part_id
    )
    part.stock_quantity = data.get("stock_quantity", part.stock_quantity)
    part.location = data.get("location", part.location)
    part.min_quantity = data.get("min_quantity", part.min_quantity)

    success, error = safe_commit()
    if not success:
        return error
    return jsonify(part.to_dict())


@api_bp.route("/v1/spare_parts/<int:part_id>", methods=["DELETE"])
def delete_spare_part(part_id):
    part, error = get_entity_or_404(SparePart, part_id, "Spare Part")
    if error:
        return error

    db.session.delete(part)
    success, error = safe_commit()
    if not success:
        return error
    return jsonify({"message": "Spare Part deleted"}), 200


# --- User and Role Endpoints ---
@api_bp.route("/v1/users", methods=["GET"])
def get_users():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 100, type=int)
    # Eager load roles and team to prevent N+1 queries
    users = User.query.options(
        db.joinedload(User.roles), db.joinedload(User.team)
    ).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify([user.to_dict(include_roles=True) for user in users.items])


@api_bp.route("/v1/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user, error = get_entity_or_404(User, user_id, "User")
    if error:
        return error
    return jsonify(user.to_dict(include_roles=True))


@api_bp.route("/v1/users", methods=["POST"])
def register_user():
    data, error = validate_json_data(["username", "email", "password"])
    if error:
        return error

    if (
        User.query.filter_by(username=data["username"]).first()
        or User.query.filter_by(email=data["email"]).first()
    ):
        return jsonify({"error": "Username or email already exists"}), 409

    new_user = User(username=data["username"], email=data["email"])
    new_user.set_password(data["password"])

    if "roles" in data and isinstance(data["roles"], list):
        for role_name in data["roles"]:
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                role = Role(name=role_name)
                db.session.add(role)
            new_user.roles.append(role)

    db.session.add(new_user)
    success, error = safe_commit()
    if not success:
        return error
    return jsonify(new_user.to_dict(include_roles=True)), 201


@api_bp.route("/v1/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    user, error = get_entity_or_404(User, user_id, "User")
    if error:
        return error

    data, error = validate_json_data()
    if error:
        return error

    user.username = data.get("username", user.username)
    user.email = data.get("email", user.email)
    if "password" in data:
        user.set_password(data["password"])
    user.is_active = data.get("is_active", user.is_active)

    if "roles" in data and isinstance(data["roles"], list):
        user.roles = []
        for role_name in data["roles"]:
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                role = Role(name=role_name)
                db.session.add(role)
            user.roles.append(role)

    success, error = safe_commit()
    if not success:
        return error
    return jsonify(user.to_dict(include_roles=True))


@api_bp.route("/v1/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    user, error = get_entity_or_404(User, user_id, "User")
    if error:
        return error

    db.session.delete(user)
    success, error = safe_commit()
    if not success:
        return error
    return jsonify({"message": "User deleted"}), 200


@api_bp.route("/v1/roles", methods=["GET"])
def get_roles():
    roles = Role.query.all()
    return jsonify([role.to_dict() for role in roles])


@api_bp.route("/v1/roles", methods=["POST"])
def add_role():
    data, error = validate_json_data(["name"])
    if error:
        return error

    if Role.query.filter_by(name=data["name"]).first():
        return jsonify({"error": "Role name already exists"}), 409

    new_role = Role(name=data["name"], description=data.get("description"))
    db.session.add(new_role)
    success, error = safe_commit()
    if not success:
        return error
    return jsonify(new_role.to_dict()), 201


# --- Authentication Endpoints ---
@api_bp.route("/v1/auth/login", methods=["POST"])
def login():
    data, error = validate_json_data(["username", "password"])
    if error:
        return jsonify({"message": "Username and password required"}), 400

    user = User.query.filter_by(username=data["username"]).first()
    if user and user.check_password(data["password"]):
        session["user_id"] = user.id
        return (
            jsonify(
                {
                    "message": "Login successful",
                    "user": user.to_dict(include_roles=True),
                }
            ),
            200,
        )
    return jsonify({"message": "Invalid credentials"}), 401


@api_bp.route("/v1/auth/logout", methods=["POST"])
@login_required
def logout():
    session.pop("user_id", None)
    return jsonify({"message": "Logged out successfully"}), 200


@api_bp.route("/v1/auth/status", methods=["GET"])
def auth_status():
    if "user_id" in session:
        user = db.session.get(User, session["user_id"])
        if user:
            return (
                jsonify({"logged_in": True, "user": user.to_dict(include_roles=True)}),
                200,
            )
    return jsonify({"logged_in": False}), 200


# --- Table Configuration API ---
@api_bp.route("/table-config/<page_name>", methods=["GET"])
@login_required
def get_table_configs(page_name):
    configs = TableConfiguration.query.filter_by(
        user_id=session["user_id"], page_name=page_name
    ).all()
    return jsonify([config.to_dict() for config in configs])


@api_bp.route("/table-config/<page_name>", methods=["POST"])
@login_required
def save_table_config(page_name):
    data, error = validate_json_data(["config_name"])
    if error:
        return error

    # If setting as default, remove default from other configs
    if data.get("is_default"):
        TableConfiguration.query.filter_by(
            user_id=session["user_id"], page_name=page_name, is_default=True
        ).update({"is_default": False})
        db.session.flush()

    config = TableConfiguration(
        user_id=session["user_id"],
        page_name=page_name,
        config_name=data["config_name"],
        column_order=data.get("column_order"),
        hidden_columns=data.get("hidden_columns"),
        filters=data.get("filters"),
        sort_config=data.get("sort_config"),
        is_default=data.get("is_default", False),
    )

    db.session.add(config)
    success, error = safe_commit()
    if not success:
        return error
    return jsonify({"success": True, "id": config.id})


@api_bp.route("/table-config/<int:config_id>", methods=["DELETE"])
@login_required
def delete_table_config(config_id):
    config, error = get_entity_or_404(TableConfiguration, config_id, "Configuration")
    if error:
        return error

    if config.user_id != session["user_id"]:
        return jsonify({"error": "Configuration not owned by user"}), 403

    db.session.delete(config)
    success, error = safe_commit()
    if not success:
        return error
    return jsonify({"success": True})


@api_bp.route("/table-config/<int:config_id>", methods=["PUT"])
@login_required
def update_table_config(config_id):
    config, error = get_entity_or_404(TableConfiguration, config_id, "Configuration")
    if error:
        return error

    if config.user_id != session["user_id"]:
        return jsonify({"error": "Configuration not owned by user"}), 403

    data, error = validate_json_data()
    if error:
        return error

    if "column_order" in data:
        config.column_order = data["column_order"]
    if "hidden_columns" in data:
        config.hidden_columns = data["hidden_columns"]
    if "filters" in data:
        config.filters = data["filters"]
    if "sort_config" in data:
        config.sort_config = data["sort_config"]

    success, error = safe_commit()
    if not success:
        return error
    return jsonify({"success": True})


@api_bp.route("/table-config/<page_name>/<int:config_id>/set-default", methods=["POST"])
@login_required
def set_default_table_config(page_name, config_id):
    config, error = get_entity_or_404(TableConfiguration, config_id, "Configuration")
    if error:
        return error

    if config.user_id != session["user_id"]:
        return jsonify({"error": "Configuration not owned by user"}), 403

    # Remove default from all configs for this page
    TableConfiguration.query.filter_by(
        user_id=session["user_id"], page_name=page_name, is_default=True
    ).update({"is_default": False})
    db.session.flush()

    config.is_default = True
    success, error = safe_commit()
    if not success:
        return error
    return jsonify({"success": True})


@api_bp.route(
    "/table-config/<page_name>/<int:config_id>/remove-default", methods=["POST"]
)
@login_required
def remove_default_table_config(page_name, config_id):
    config, error = get_entity_or_404(TableConfiguration, config_id, "Configuration")
    if error:
        return error

    if config.user_id != session["user_id"]:
        return jsonify({"error": "Configuration not owned by user"}), 403

    config.is_default = False
    success, error = safe_commit()
    if not success:
        return error
    return jsonify({"success": True})


# --- Enhanced Data Endpoints ---
@api_bp.route("/<entity>/filtered", methods=["GET"])
def get_filtered_data(entity):
    models = {
        "assets": Asset,
        "maintenance_orders": MaintenanceOrder,
        "spare_parts": SparePart,
        "users": User,
    }

    if entity not in models:
        return jsonify({"error": "Invalid entity"}), 400

    model = models[entity]
    query = model.query

    # Apply filters
    filters = request.args.get("filters")
    if filters:
        try:
            filter_dict = json.loads(filters)
            for column, filter_config in filter_dict.items():
                if hasattr(model, column):
                    column_attr = getattr(model, column)
                    value = filter_config.get("value")
                    operator = filter_config.get("operator")

                    if operator == "contains":
                        sanitized_value = sanitize_like_value(value)
                        query = query.filter(column_attr.like(f"%{sanitized_value}%"))
                    elif operator == "equals":
                        query = query.filter(column_attr == value)
                    elif operator == "not_equals":
                        query = query.filter(column_attr != value)
        except (json.JSONDecodeError, KeyError, TypeError):
            return jsonify({"error": "Invalid filter format"}), 400

    # Apply sorting
    sort_column = request.args.get("sort_column")
    sort_direction = request.args.get("sort_direction", "asc")

    if sort_column and hasattr(model, sort_column):
        column_attr = getattr(model, sort_column)
        if sort_direction == "desc":
            query = query.order_by(column_attr.desc())
        else:
            query = query.order_by(column_attr.asc())

    # Apply pagination
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 100, type=int)
    results = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify([item.to_dict() for item in results.items])
