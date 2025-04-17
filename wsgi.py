from app import create_app, db
from app.models import User, Attendance, Assignment, AssignmentSubmission, ChatMessage, CountdownEvent

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 
        'Attendance': Attendance,
        'Assignment': Assignment,
        'AssignmentSubmission': AssignmentSubmission,
        'ChatMessage': ChatMessage,
        'CountdownEvent': CountdownEvent
    }