from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_mail import Mail
from config import Config
from flask import render_template
from datetime import datetime
import pytz  

db = SQLAlchemy()
login = LoginManager()
socketio = SocketIO()
migrate = Migrate()
mail = Mail()

# Configure Flask-Login
login.login_view = 'auth.login'
login.login_message_category = 'info'

@login.user_loader
def load_user(id):
    from app.models import User
    return User.query.get(int(id))

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    login.init_app(app)
    socketio.init_app(app)
    migrate.init_app(app, db)  # Make sure this line is here
    mail.init_app(app)
    
    # Register blueprints
    from app.routes.auth import bp as auth_bp
    from app.routes.teacher_routes import bp as teacher_bp
    from app.routes.student_routes import bp as student_bp
    from app.routes.admin_routes import bp as admin_bp
    from app.routes.chat_routes import bp as chat_bp
   
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(teacher_bp, url_prefix='/teacher')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.jinja_env.globals['timezone'] = pytz.timezone

    @app.route('/')
    def index():
        return render_template('index.html')
    
    # Add template context processor for current year
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}
    
    return app

from app import models