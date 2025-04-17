# EDUcheck/app/models/attendance_session.py
from datetime import datetime
from app import db

class AttendanceSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) # Added teacher_id
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True) # Null indicates session is active

    # Relationships
    course = db.relationship('Course', backref='attendance_sessions')
    teacher = db.relationship('User', backref='started_attendance_sessions') # Added teacher relationship
    attendance_records = db.relationship('Attendance', backref='session', lazy='dynamic')

    def is_active(self):
        return self.end_time is None

    def __repr__(self):
        return f'<AttendanceSession id={self.id} course_id={self.course_id} start={self.start_time} active={self.is_active()}>'