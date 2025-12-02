from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from src.services.db_utils import db, Asset, MaintenanceOrder, SparePart, User, Role, Team
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
    return_to = request.args.get('return_to', None)
    asset_id = request.args.get('asset_id', None)
    preselected_asset = None
    if asset_id:
        preselected_asset = Asset.query.get(asset_id)

    if request.method == 'POST':
        # Get asset_id from form or fall back to the query parameter
        asset_id_from_form = request.form.get('asset_id')
        if not asset_id_from_form and asset_id:
            # If asset field was disabled, use the asset_id from query parameter
            asset_id_from_form = asset_id

        description = request.form['description']
        order_type = request.form['order_type']
        status = "Open"  # Always set to Open for new MOs
        priority = request.form['priority']
        schedule_name = request.form.get('schedule_name', '')
        frequency = request.form.get('frequency', '')

        # Bug #26: Validate that PM orders have a frequency
        if order_type == 'PM' and not frequency:
            flash('Frequency is required for PM (Preventive Maintenance) orders.', 'error')
            return render_template('maintenance_order_detail.html', mo=None, assets=assets,
                                 return_to=return_to, asset_id=asset_id, preselected_asset=preselected_asset)

        estimated_completion_time = request.form.get('estimated_completion_time', '')
        labour_count = request.form['labour_count']
        assignees = request.form.get('assignees', '')
        justification = request.form.get('justification', '')
        due_date_str = request.form.get('due_date', '')
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None
        
        new_mo = MaintenanceOrder(
            asset_id=asset_id_from_form,
            description=description,
            order_type=order_type,
            status=status,
            priority=priority,
            schedule_name=schedule_name if schedule_name else None,
            frequency=frequency if frequency else None,
            estimated_completion_time=int(estimated_completion_time) if estimated_completion_time else None,
            labour_count=int(labour_count),
            assignees_json=assignees if assignees else None,
            justification=justification if justification else None,
            due_date=due_date,
            created_by=session.get('user_id')
        )
        db.session.add(new_mo)
        db.session.commit()
        flash('Maintenance Order added successfully!', 'success')
        # Use the asset_id from the new_mo object to ensure the correct redirect
        if return_to == 'asset' and new_mo.asset_id:
            return redirect(url_for('main.asset_detail', asset_id=new_mo.asset_id))
        return redirect(url_for('main.maintenance_orders'))

    return render_template('maintenance_order_detail.html', mo=None, assets=assets, return_to=return_to, asset_id=asset_id, preselected_asset=preselected_asset)

@main_bp.route('/maintenance_orders/<int:mo_id>')
@login_required
def mo_detail(mo_id):
    mo = MaintenanceOrder.query.get_or_404(mo_id)
    asset_id = request.args.get('asset_id', None)
    return render_template('maintenance_order_detail.html', mo=mo, assets=Asset.query.all(), asset_id=asset_id, return_to='asset' if asset_id else None)

@main_bp.route('/maintenance_orders/<int:mo_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_mo(mo_id):
    mo = MaintenanceOrder.query.get_or_404(mo_id)
    assets = Asset.query.all()
    return_to = request.args.get('return_to', None)
    asset_id = request.args.get('asset_id', None)

    if request.method == 'POST':
        mo.asset_id = request.form['asset_id']
        mo.description = request.form['description']
        mo.order_type = request.form['order_type']
        mo.status = request.form['status']
        mo.priority = request.form['priority']
        schedule_name = request.form.get('schedule_name', '')
        mo.schedule_name = schedule_name if schedule_name else None
        frequency = request.form.get('frequency', '')

        # Bug #26: Validate that PM orders have a frequency
        if mo.order_type == 'PM' and not frequency:
            flash('Frequency is required for PM (Preventive Maintenance) orders.', 'error')
            return render_template('maintenance_order_detail.html', mo=mo, assets=assets,
                                 return_to=return_to, asset_id=asset_id)

        mo.frequency = frequency if frequency else None
        estimated_time = request.form.get('estimated_completion_time', '')
        mo.estimated_completion_time = int(estimated_time) if estimated_time else None
        mo.labour_count = int(request.form['labour_count'])
        assignees = request.form.get('assignees', '')
        mo.assignees_json = assignees if assignees else None
        justification = request.form.get('justification', '')
        mo.justification = justification if justification else None
        due_date_str = request.form.get('due_date', '')
        mo.due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None
        mo.modified_by = session.get('user_id')
        mo.modified_on = datetime.utcnow()
        db.session.commit()
        flash('Maintenance Order updated successfully!', 'success')
        # Redirect based on where the user came from
        if return_to == 'asset' and asset_id:
            return redirect(url_for('main.asset_detail', asset_id=asset_id))
        return redirect(url_for('main.maintenance_orders'))

    return render_template('maintenance_order_detail.html', mo=mo, assets=assets, return_to=return_to, asset_id=asset_id)

@main_bp.route('/maintenance_orders/<int:mo_id>/delete', methods=['POST'])
@login_required
def delete_mo(mo_id):
    mo = MaintenanceOrder.query.get_or_404(mo_id)
    asset_id = mo.asset_id  # Save asset_id before deleting
    db.session.delete(mo)
    db.session.commit()
    flash('Maintenance Order deleted successfully!', 'success')

    # Check if the delete was initiated from an asset detail page
    referrer = request.referrer
    if referrer and 'assets/' in referrer and asset_id:
        return redirect(url_for('main.asset_detail', asset_id=asset_id))
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
    # Eager load roles and team to prevent N+1 queries
    all_users = User.query.options(db.joinedload(User.roles), db.joinedload(User.team)).all()
    users_data = [user.to_dict(include_roles=True) for user in all_users]
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
    # Technician import removed

    user = User.query.get_or_404(user_id)
    all_roles = Role.query.all()

    # Check if this user has Technician role
    is_technician = any(role.name == 'Technician' for role in user.roles)

    return render_template('user_detail.html', user=user, all_roles=all_roles, is_technician=is_technician)

@main_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    # Technician import removed

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
    is_technician = any(role.name == 'Technician' for role in user.roles)

    return render_template('user_detail.html', user=user, all_roles=all_roles, is_technician=is_technician)

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
    # Deprecated route - redirect to users
    flash('Technician view is deprecated. Please use User view.', 'warning')
    return redirect(url_for('main.users'))

# --- Planning Integration Route ---
@main_bp.route('/planning')
@login_required
def planning():
    return redirect(url_for('planning.index_route'))

@main_bp.route('/shift_calendar')
@login_required
def shift_calendar():
    import calendar
    from datetime import datetime
    from src.services.db_utils import Team
    
    year = request.args.get('year', type=int, default=datetime.now().year)
    month = request.args.get('month', type=int, default=datetime.now().month)
    
    # Navigation logic
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year
        
    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year
        
    month_name = calendar.month_name[month]
    
    # Generate calendar days
    num_days = calendar.monthrange(year, month)[1]
    calendar_days = []
    
    teams = Team.query.all()
    
    for day in range(1, num_days + 1):
        date_obj = datetime(year, month, day)
        week_num = date_obj.isocalendar()[1]
        is_odd_week = (week_num % 2) != 0
        
        day_data = {
            'date_str': date_obj.strftime('%Y-%m-%d'),
            'day_name': date_obj.strftime('%A'),
            'week_num': week_num,
            'is_today': date_obj.date() == datetime.now().date(),
            'early_teams': [],
            'late_teams': []
        }
        
        # Use shared utility to get correct teams for this date
        from src.services.shift_utils import get_shift_teams
        early_team, late_team = get_shift_teams(date_obj, teams)
        
        if early_team:
            day_data['early_teams'].append({'name': early_team.name, 'users': early_team.users})
        if late_team:
            day_data['late_teams'].append({'name': late_team.name, 'users': late_team.users})
                    
        calendar_days.append(day_data)
        
    return render_template('shift_calendar.html', 
                         calendar_days=calendar_days,
                         year=year, month=month, month_name=month_name,
                         prev_year=prev_year, prev_month=prev_month,
                         next_year=next_year, next_month=next_month)


