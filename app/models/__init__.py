from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
from datetime import datetime
import random
import string

from .user import User
from .course import Course, StudentCourse
from .assignment import Assignment, AssignmentSubmission
from .attendance import Attendance
from .chat import Chat, ChatMessage
from .announcement import Announcement
from .countdown import CountdownEvent
from .material import Material

from .attendance_session import AttendanceSession # Add this line
