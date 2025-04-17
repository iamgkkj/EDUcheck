from app.models import User, AssignmentSubmission

def calculate_leaderboard():
    students = User.query.filter_by(role='student').all()
    leaderboard = []
    
    for student in students:
        total_score = sum([
            submission.grade for submission in 
            AssignmentSubmission.query.filter_by(student_id=student.id)
            if submission.grade is not None
        ])
        leaderboard.append({
            'student': student,
            'score': total_score
        })
    
    return sorted(leaderboard, key=lambda x: x['score'], reverse=True)