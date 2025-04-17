from datetime import datetime
from app import db
import random
import string
from .attendance_session import AttendanceSession

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    class_number = db.Column(db.String(20), nullable=False)
    session = db.Column(db.String(20), nullable=False)
    semester = db.Column(db.String(20), nullable=False)
    class_code = db.Column(db.String(8), unique=True, nullable=False)
    meet_code = db.Column(db.String(50))
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with teacher
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='teaching_courses') # Changed backref from 'courses'

    @staticmethod
    def generate_class_code():
        length = random.randint(6, 8)
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
            if not Course.query.filter_by(class_code=code).first():
                return code

    @property
    def active_attendance_session(self):
        """Returns the currently active AttendanceSession for this course, or None."""
        # Ensure this import works based on your structure
        # from .attendance_session import AttendanceSession
        return AttendanceSession.query.filter_by(course_id=self.id, end_time=None).first()
    # --- END ADDED PROPERTY ---

class StudentCourse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)


    
    # new
    course = db.relationship('Course', backref='student_enrollments')
    student = db.relationship('User', backref='course_enrollments')



# @property
# def active_attendance_session(self):
#     from .attendance_session import AttendanceSession # Local import
#     return AttendanceSession.query.filter_by(course_id=self.id, end_time=None).first()