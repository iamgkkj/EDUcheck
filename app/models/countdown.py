from datetime import datetime
from app import db

class CountdownEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    event_date = db.Column(db.DateTime)
    event_type = db.Column(db.String(20))  # academic, event, assignment
    created_at = db.Column(db.DateTime, default=datetime.utcnow)