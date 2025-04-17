from flask import Blueprint
from app.routes.auth import bp as auth_bp
from app.routes.teacher_routes import bp as teacher_bp
from app.routes.student_routes import bp as student_bp
from app.routes.admin_routes import bp as admin_bp
from app.routes.chat_routes import bp as chat_bp

__all__ = ['auth_bp', 'teacher_bp', 'student_bp', 'admin_bp', 'chat_bp']

main_bp = Blueprint('main', __name__)

from app.routes import auth, teacher_routes, student_routes, admin_routes