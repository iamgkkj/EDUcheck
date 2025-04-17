from app import create_app, db
from app.models.user import User

def create_teacher_account():
    app = create_app()
    with app.app_context():
        # Check if teacher account already exists
        existing_teacher = User.query.filter_by(username='teacher').first()
        if existing_teacher:
            print('Teacher account already exists!')
            return
        
        # Create new teacher account
        teacher = User(
            username='teacher',
            email='teacher@educheck.com',
            role='teacher'
        )
        teacher.set_password('password123')
        
        try:
            db.session.add(teacher)
            db.session.commit()
            print('Teacher account created successfully!')
            print('Username: teacher')
            print('Password: password123')
        except Exception as e:
            db.session.rollback()
            print(f'Error creating teacher account: {str(e)}')

if __name__ == '__main__':
    create_teacher_account()