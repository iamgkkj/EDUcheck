# EDUcheck/app/models/attendance.py
from datetime import datetime
from app import db

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) # Corrected FK
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('attendance_session.id'), nullable=False) # Link to session
    marked_at = db.Column(db.DateTime, default=datetime.utcnow) # Timestamp for when marked
    status = db.Column(db.String(20), default='present') # Status (present, absent, late?)
    # Removed 'date' column as session start/end times are more specific

    # Relationships (backref comes from AttendanceSession)
    # student = relationship defined in User model
    # course = relationship defined in Course model

    def __repr__(self):
         return f'<Attendance id={self.id} student={self.student_id} session={self.session_id} status={self.status}>'