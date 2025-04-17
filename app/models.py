# app/models.py
from datetime import datetime
from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
# from app import app

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20))  # student, teacher, admin
    face_encoding = db.Column(db.LargeBinary)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    assignments = db.relationship('AssignmentSubmission', backref='student', lazy='dynamic')
    # Specify foreign_keys for sent_messages to resolve ambiguity
    sent_messages = db.relationship('ChatMessage', 
                                   foreign_keys='ChatMessage.sender_id',
                                   backref='sender', 
                                   lazy='dynamic')
    # Add received_messages relationship
    received_messages = db.relationship('ChatMessage',
                                       foreign_keys='ChatMessage.receiver_id',
                                       backref='receiver',
                                       lazy='dynamic')
    attendance_records = db.relationship('Attendance', backref='student', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')
    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

import random
import string
from datetime import datetime

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    class_number = db.Column(db.String(20), nullable=False)
    session = db.Column(db.String(20), nullable=False)
    semester = db.Column(db.String(20), nullable=False)
    class_code = db.Column(db.String(8), unique=True, nullable=False)
    meet_code = db.Column(db.String(50))
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    teacher = db.relationship('User', backref='teaching_courses')

    @staticmethod
    def generate_class_code():
        length = random.randint(6, 8)
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
            if not Course.query.filter_by(class_code=code).first():
                return code

class StudentCourse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

class Assignment(db.Model):
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime)
    file_path = db.Column(db.String(255))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    submissions = db.relationship('AssignmentSubmission', backref='assignment', lazy=True)
    course = db.relationship('Course', backref='assignments')
    teacher = db.relationship('User', backref='created_assignments')

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='present')



class AssignmentSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    file_path = db.Column(db.String(256))
    grade = db.Column(db.Float)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    file_path = db.Column(db.String(256))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    course = db.relationship('Course', backref='announcements')
    teacher = db.relationship('User', backref='created_announcements')

class CountdownEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    event_date = db.Column(db.DateTime)
    event_type = db.Column(db.String(20))  # academic, event, assignment
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(255), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with Course
    course = db.relationship('Course', backref='materials')

@login.user_loader
def load_user(id):
    return User.query.get(int(id))