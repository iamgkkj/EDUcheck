from app import create_app, db
from app.models import User, Attendance, Assignment, AssignmentSubmission, ChatMessage, CountdownEvent

app = create_app()

with app.app_context():
    # Create all tables
    db.create_all()
    print("Database tables created successfully!")