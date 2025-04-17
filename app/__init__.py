from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask import render_template
import os

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Default config
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite3'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # Load instance config if exists
    app.config.from_pyfile('config.py', silent=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Setup Flask-Login
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    login_manager.login_view = 'auth.login'

    # Register blueprints
    from .auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    from .planner import planner_bp
    app.register_blueprint(planner_bp, url_prefix='/planner')

    import mimetypes
    from flask import send_from_directory, request

    # Serve React build static files
    @app.route('/static/frontend/<path:filename>')
    def frontend_static(filename):
        return send_from_directory(os.path.join(app.root_path, 'static', 'frontend'), filename)

    # Root route redirects to dashboard or login
    @app.route('/')
    def root():
        if current_user.is_authenticated:
            return redirect(url_for('planner.dashboard'))
        else:
            return redirect(url_for('auth.login'))
            
    # Routes for serving static files and other paths
    @app.route('/<path:path>')
    def serve_react(path):
        # Don't serve React for Flask routes
        if path.startswith('auth') or path.startswith('planner') or path.startswith('api'):
            return ('Not Found', 404)
        
        static_dir = os.path.join(app.root_path, 'static', 'frontend')
        file_path = os.path.join(static_dir, path)
        if path != "" and os.path.exists(file_path) and not os.path.isdir(file_path):
            # Serve static asset
            return send_from_directory(static_dir, path)
        # Otherwise, serve index.html for SPA routing
        return send_from_directory(static_dir, 'index.html')

    return app
