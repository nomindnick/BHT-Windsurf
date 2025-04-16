from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
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
    app.register_blueprint(auth_bp)
    from .planner import planner_bp
    app.register_blueprint(planner_bp)

    @app.route("/")
    def home():
        return render_template("home.html")

    return app
