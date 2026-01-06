from src.app import create_app
from src.services.db_utils import db, User

app = create_app()
with app.app_context():
    user = User.query.filter_by(username='admin').first()
    if user:
        user.set_password('password')
        db.session.commit()
        print("Admin password reset to 'password'")
    else:
        print("Admin user not found")
