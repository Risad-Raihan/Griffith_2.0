from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, current_user

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    # Create the Flask app instance
    app = Flask(__name__)

    # Load configuration from config.py
    app.config.from_object('config.Config')

    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Configure LoginManager settings
    login_manager.login_view = "main.admin_login"  # Default login view for unauthorized users

    @login_manager.unauthorized_handler
    def unauthorized():
        """
        Redirect to the appropriate login page based on the user's role or endpoint.
        """
        if not current_user.is_authenticated:
            requested_endpoint = url_for('main.home')
            if requested_endpoint and "super_admin" in requested_endpoint:
                return redirect(url_for('main.super_admin_login'))
            return redirect(url_for('main.admin_login'))
        # Redirect authenticated users without the correct role to home
        return redirect(url_for('main.home'))

    @login_manager.user_loader
    def load_user(user_id):
        """
        Load a pseudo-user (with fixed credentials) for the current session.
        """
        class PseudoUser(UserMixin):
            def __init__(self, user_id, username, role):
                self.id = user_id
                self.username = username
                self.role = role

        if user_id == "1":  # Fixed ID for Admin
            return PseudoUser("1", "admin", "Admin")
        elif user_id == "2":  # Fixed ID for Super Admin
            return PseudoUser("2", "superadmin", "Super Admin")
        return None

    # Import and register Blueprints
    from app.routes import main
    app.register_blueprint(main)

    return app
