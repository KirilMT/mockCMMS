from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from packages.mockCMMS.src.services.db import db, Asset, MaintenanceOrder, SparePart, User, Role
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps # Import wraps

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
    return render_template('assets.html', assets=all_assets)

@main_bp.route('/assets/add', methods=['GET', 'POST'])
@login_required
def add_asset():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        location = request.form['location']
        status = request.form['status']
        
        new_asset = Asset(name=name, description=description, location=location, status=status)
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
        asset.name = request.form['name']
        asset.description = request.form['description']
        asset.location = request.form['location']
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
    return render_template('maintenance_orders.html', mos=all_mos)

@main_bp.route('/maintenance_orders/add', methods=['GET', 'POST'])
@login_required
def add_mo():
    assets = Asset.query.all() # Needed for asset selection in form
    if request.method == 'POST':
        asset_id = request.form['asset_id']
        description = request.form['description']
        order_type = request.form['order_type']
        status = request.form['status']
        due_date_str = request.form['due_date']
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None
        
        new_mo = MaintenanceOrder(asset_id=asset_id, description=description, order_type=order_type, status=status, due_date=due_date)
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
        due_date_str = request.form['due_date']
        mo.due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None
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
    return render_template('spare_parts.html', spare_parts=all_parts)

@main_bp.route('/spare_parts/add', methods=['GET', 'POST'])
@login_required
def add_spare_part():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        quantity = request.form['quantity']
        location = request.form['location']
        min_quantity = request.form['min_quantity']
        
        new_part = SparePart(name=name, description=description, quantity=quantity, location=location, min_quantity=min_quantity)
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
        part.name = request.form['name']
        part.description = request.form['description']
        part.quantity = request.form['quantity']
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
    all_users = User.query.all()
    return render_template('users.html', users=all_users)

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
    user = User.query.get_or_404(user_id)
    all_roles = Role.query.all()
    return render_template('user_detail.html', user=user, all_roles=all_roles)

@main_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
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
    return render_template('user_detail.html', user=user, all_roles=all_roles)

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

# --- Workforce Manager Integration Route ---
@main_bp.route('/workforce-manager')
@login_required
def workforce_manager_embed():
    return render_template('workforce_manager_embed.html')


