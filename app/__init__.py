import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import logging
from dotenv import load_dotenv
from flask_cors import CORS

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='/static')

    instance_path = os.path.join(app.root_path, 'instance')
    os.makedirs(instance_path, exist_ok=True)
    logger.debug(f"Instance path set to: {instance_path}")

    try:
        from config import Config
        app.config.from_object(Config)
        logger.debug(f"Loaded SECRET_KEY: {app.config['SECRET_KEY']}")  # Debug key
        if not app.config.get('SECRET_KEY'):
            app.config['SECRET_KEY'] = os.urandom(24)
            logger.warning("SECRET_KEY not found in Config, using random value. Set a secure key in production.")
    except ImportError as e:
        raise ImportError(f"Failed to load configuration: {e}")
    except AttributeError as e:
        raise ValueError(f"Configuration error: {e}. Ensure Config class has required attributes.")

    try:
        db.init_app(app)
        login_manager.init_app(app)
        login_manager.login_view = 'main.login_page'
        login_manager.session_protection = 'strong'
        csrf.init_app(app)
        migrate.init_app(app, db)
        CORS(app, supports_credentials=True)
        app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    except Exception as e:
        logger.error(f"Failed to initialize extensions: {e}")
        raise RuntimeError(f"Failed to initialize extensions: {e}")

    from app.models import User, Artisan, Message, Review
    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    @login_manager.user_loader
    def load_user(user_id):
        logger.debug(f"Loading user with ID: {user_id}")
        return User.query.get(int(user_id))

    return app
