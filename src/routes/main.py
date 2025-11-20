from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from src.services.db_utils import db, Asset, MaintenanceOrder, SparePart, User, Role
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime

main_bp = Blueprint('main', __name__)

# --- Helper for Authentication ---
def login_required(f):
    @wraps(f) # Use wraps to preserve function metadata
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Login required to access this page.', 'warning')
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function

# --- General Routes ---
@main_bp.route('/')
def index():
    return redirect(url_for('main.assets'))

@main_bp.route('/tickets/<string:ticket_id>')
def ticket_page(ticket_id):
    return render_template('ticket.html', ticket_id=ticket_id)

@main_bp.route('/maintenance_grid/<string:ids>')
def maintenance_grid_page(ids):
    return render_template('maintenance_grid.html', ids=ids)

# --- Asset Routes ---
@main_bp.route('/assets')
@login_required
def assets():
    all_assets = Asset.query.all()
    assets_data = [asset.to_dict() for asset in all_assets]
    return render_template('assets.html', assets=assets_data)

@main_bp.route('/assets/add', methods=['GET', 'POST'])
@login_required
def add_asset():
    if request.method == 'POST':
        asset_code = request.form['asset_code']
        name = request.form['name']
        description = request.form['description']
        asset_type = request.form['asset_type']
        cost_center = request.form['cost_center']
        status = request.form['status']
        
        new_asset = Asset(
            asset_code=asset_code,
            name=name, 
            description=description, 
            asset_type=asset_type,
            cost_center=cost_center,
            status=status
        )
        db.session.add(new_asset)
        db.session.commit()
        flash('Asset added successfully!', 'success')
        return redirect(url_for('main.assets'))
    return render_template('asset_detail.html', asset=None)

@main_bp.route('/assets/<int:asset_id>')
@login_required
def asset_detail(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    return render_template('asset_detail.html', asset=asset)

@main_bp.route('/assets/<int:asset_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    if request.method == 'POST':
        asset.asset_code = request.form['asset_code']
        asset.name = request.form['name']
        asset.description = request.form['description']
        asset.asset_type = request.form['asset_type']
        asset.cost_center = request.form['cost_center']
        asset.status = request.form['status']
        db.session.commit()
        flash('Asset updated successfully!', 'success')
        return redirect(url_for('main.assets'))
    return render_template('asset_detail.html', asset=asset)

@main_bp.route('/assets/<int:asset_id>/delete', methods=['POST'])
@login_required
def delete_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    db.session.delete(asset)
    db.session.commit()
    flash('Asset deleted successfully!', 'success')
    return redirect(url_for('main.assets'))

# --- Maintenance Order Routes ---
@main_bp.route('/maintenance_orders')
@login_required
def maintenance_orders():
    all_mos = MaintenanceOrder.query.all()
    mos_data = []
    for mo in all_mos:
        mo_dict = mo.to_dict()
        mo_dict['asset_name'] = mo.asset.name if mo.asset else 'N/A'
        mos_data.append(mo_dict)
    return render_template('maintenance_orders.html', mos=mos_data)

@main_bp.route('/maintenance_orders/add', methods=['GET', 'POST'])
@login_required
def add_mo():
    assets = Asset.query.all()
    if request.method == 'POST':
        asset_id = request.form['asset_id']
        description = request.form['description']
        order_type = request.form['order_type']
        status = request.form['status']
        priority = request.form['priority']
        schedule_name = request.form['schedule_name']
        frequency = request.form['frequency']
        estimated_completion_time = request.form['estimated_completion_time']
        labour_count = request.form['labour_count']
        assignees = request.form['assignees']
        justification = request.form['justification']
        due_date_str = request.form['due_date']
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None
        
        new_mo = MaintenanceOrder(
            asset_id=asset_id,
            description=description,
            order_type=order_type,
            status=status,
            priority=priority,
            schedule_name=schedule_name if schedule_name else None,
            frequency=frequency if frequency else None,
            estimated_completion_time=int(estimated_completion_time) if estimated_completion_time else None,
            labour_count=int(labour_count),
            assignees=assignees if assignees else None,
            justification=justification if justification else None,
            due_date=due_date,
            created_by=session.get('user_id')
        )
        db.session.add(new_mo)
        db.session.commit()
        flash('Maintenance Order added successfully!', 'success')
        return redirect(url_for('main.maintenance_orders'))
    return render_template('maintenance_order_detail.html', mo=None, assets=assets)

@main_bp.route('/maintenance_orders/<int:mo_id>')
@login_required
def mo_detail(mo_id):
    mo = MaintenanceOrder.query.get_or_404(mo_id)
    return render_template('maintenance_order_detail.html', mo=mo, assets=Asset.query.all())

@main_bp.route('/maintenance_orders/<int:mo_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_mo(mo_id):
    mo = MaintenanceOrder.query.get_or_404(mo_id)
    assets = Asset.query.all()
    if request.method == 'POST':
        mo.asset_id = request.form['asset_id']
        mo.description = request.form['description']
        mo.order_type = request.form['order_type']
        mo.status = request.form['status']
        mo.priority = request.form['priority']
        mo.schedule_name = request.form['schedule_name'] if request.form['schedule_name'] else None
        mo.frequency = request.form['frequency'] if request.form['frequency'] else None
        mo.estimated_completion_time = int(request.form['estimated_completion_time']) if request.form['estimated_completion_time'] else None
        mo.labour_count = int(request.form['labour_count'])
        mo.assignees = request.form['assignees'] if request.form['assignees'] else None
        mo.justification = request.form['justification'] if request.form['justification'] else None
        due_date_str = request.form['due_date']
        mo.due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None
        mo.modified_by = session.get('user_id')
        mo.modified_on = datetime.utcnow()
        db.session.commit()
        flash('Maintenance Order updated successfully!', 'success')
        return redirect(url_for('main.maintenance_orders'))
    return render_template('maintenance_order_detail.html', mo=mo, assets=assets)

@main_bp.route('/maintenance_orders/<int:mo_id>/delete', methods=['POST'])
@login_required
def delete_mo(mo_id):
    mo = MaintenanceOrder.query.get_or_404(mo_id)
    db.session.delete(mo)
    db.session.commit()
    flash('Maintenance Order deleted successfully!', 'success')
    return redirect(url_for('main.maintenance_orders'))

# --- Spare Part Routes ---
@main_bp.route('/spare_parts')
@login_required
def spare_parts():
    all_parts = SparePart.query.all()
    parts_data = [part.to_dict() for part in all_parts]
    return render_template('spare_parts.html', spare_parts=parts_data)

@main_bp.route('/spare_parts/add', methods=['GET', 'POST'])
@login_required
def add_spare_part():
    if request.method == 'POST':
        description = request.form['description']
        manufacturer = request.form['manufacturer']
        manufacturer_part_id = request.form['manufacturer_part_id']
        stock_quantity = request.form['stock_quantity']
        location = request.form['location']
        min_quantity = request.form['min_quantity']
        
        new_part = SparePart(
            description=description,
            manufacturer=manufacturer,
            manufacturer_part_id=manufacturer_part_id,
            stock_quantity=stock_quantity,
            location=location,
            min_quantity=min_quantity
        )
        db.session.add(new_part)
        db.session.commit()
        flash('Spare Part added successfully!', 'success')
        return redirect(url_for('main.spare_parts'))
    return render_template('spare_part_detail.html', part=None)

@main_bp.route('/spare_parts/<int:part_id>')
@login_required
def spare_part_detail(part_id):
    part = SparePart.query.get_or_404(part_id)
    return render_template('spare_part_detail.html', part=part)

@main_bp.route('/spare_parts/<int:part_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_spare_part(part_id):
    part = SparePart.query.get_or_404(part_id)
    if request.method == 'POST':
        part.description = request.form['description']
        part.manufacturer = request.form['manufacturer']
        part.manufacturer_part_id = request.form['manufacturer_part_id']
        part.stock_quantity = request.form['stock_quantity']
        part.location = request.form['location']
        part.min_quantity = request.form['min_quantity']
        db.session.commit()
        flash('Spare Part updated successfully!', 'success')
        return redirect(url_for('main.spare_parts'))
    return render_template('spare_part_detail.html', part=part)

@main_bp.route('/spare_parts/<int:part_id>/delete', methods=['POST'])
@login_required
def delete_spare_part(part_id):
    part = SparePart.query.get_or_404(part_id)
    db.session.delete(part)
    db.session.commit()
    flash('Spare Part deleted successfully!', 'success')
    return redirect(url_for('main.spare_parts'))

# --- User and Role Routes ---
@main_bp.route('/users')
@login_required
def users():
    from src.services.db_utils import Technician

    # Get all users
    all_users = User.query.all()
    users_data = []
    for user in all_users:
        user_dict = user.to_dict(include_roles=True)
        user_dict['roles_display'] = ', '.join(user_dict.get('roles', []))
        user_dict['is_active'] = 'Yes' if user_dict['is_active'] else 'No'

        # Check if this user has Technician role
        user_dict['is_technician'] = any(role.name == 'Technician' for role in user.roles)

        if user_dict['is_technician']:
            # Try to find matching technician by username
            technician = Technician.query.filter_by(name=user.username).first()
            if technician:
                user_dict['technician_id'] = technician.id
                user_dict['technician_status'] = technician.availability_status
                user_dict['skill_count'] = len(technician.skills)
                user_dict['skills'] = ', '.join([f"{ts.skill.name}(L{ts.skill_level})" for ts in technician.skills])
            else:
                user_dict['technician_status'] = 'Not Linked'
                user_dict['skill_count'] = 0
                user_dict['skills'] = '-'
        else:
            user_dict['technician_status'] = '-'
            user_dict['skill_count'] = 0
            user_dict['skills'] = '-'

        users_data.append(user_dict)

    return render_template('users.html', users=users_data)

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        roles_selected = request.form.getlist('roles') # Get list of selected roles

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('main.register'))
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return redirect(url_for('main.register'))

        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        for role_name in roles_selected:
            role = Role.query.filter_by(name=role_name).first()
            if role:
                new_user.roles.append(role)
        
        db.session.add(new_user)
        db.session.commit()
        flash('User registered successfully!', 'success')
        return redirect(url_for('main.users'))
    
    all_roles = Role.query.all()
    return render_template('user_detail.html', user=None, all_roles=all_roles)

@main_bp.route('/users/<int:user_id>')
@login_required
def user_detail(user_id):
    from src.services.db_utils import Technician

    user = User.query.get_or_404(user_id)
    all_roles = Role.query.all()

    # Check if this user has Technician role
    technician = None
    if user and any(role.name == 'Technician' for role in user.roles):
        # Try to find matching technician by username
        technician = Technician.query.filter_by(name=user.username).first()

    return render_template('user_detail.html', user=user, all_roles=all_roles, technician=technician)

@main_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    from src.services.db_utils import Technician

    user = User.query.get_or_404(user_id)
    all_roles = Role.query.all()
    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        password = request.form['password']
        if password: # Only update password if provided
            user.set_password(password)
        user.is_active = 'is_active' in request.form # Check if checkbox is ticked

        roles_selected = request.form.getlist('roles')
        user.roles = [] # Clear existing roles
        for role_name in roles_selected:
            role = Role.query.filter_by(name=role_name).first()
            if role:
                user.roles.append(role)

        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('main.users'))

    # Check if this user has Technician role
    technician = None
    if user and any(role.name == 'Technician' for role in user.roles):
        # Try to find matching technician by username
        technician = Technician.query.filter_by(name=user.username).first()

    return render_template('user_detail.html', user=user, all_roles=all_roles, technician=technician)

@main_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('main.users'))

# --- Authentication Routes ---
@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('main.index')) # Already logged in
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username # Store username in session
            flash('Logged in successfully!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@main_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))

# --- Technician Detail Route (for detailed skills view) ---
@main_bp.route('/technicians/<int:technician_id>')
@login_required
def technician_detail(technician_id):
    from src.services.db_utils import Technician
    technician = Technician.query.get_or_404(technician_id)

    # Try to find the associated user by matching username
    user = User.query.filter_by(username=technician.name).first()

    return render_template('technician_detail.html', technician=technician, user=user)

# --- Planning Integration Route ---
@main_bp.route('/planning')
@main_bp.route('/planning')
@login_required
def planning():
    return render_template('planning.html')


