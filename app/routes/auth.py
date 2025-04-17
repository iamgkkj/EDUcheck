from flask import render_template, redirect, url_for, flash, request, current_app, abort
from app import db
from flask import Blueprint
from app.models import User
from app.forms import LoginForm, RegistrationForm, PasswordResetRequestForm, PasswordResetForm
from flask_login import login_required, login_user, current_user, logout_user
from app.utils.file_utils import allowed_file
from werkzeug.utils import secure_filename
import os
import pickle
from app.utils.face_auth import register_face
from flask_mail import Message
from app import mail

bp = Blueprint('auth', __name__)

@bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'teacher':
            return redirect(url_for('teacher_routes.teacher_dashboard'))
        return redirect(url_for('student_routes.student_dashboard'))
    return render_template('index.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    role = request.args.get('role')
    
    # If no role is specified, show the login menu
    if not role:
        return render_template('auth/login_menu.html')
    
    # Validate role
    if role not in ['student', 'teacher', 'admin']:
        flash('Invalid login type', 'error')
        return redirect(url_for('auth.login'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'error')
            return redirect(url_for('auth.login', role=role))
        
        # Check if user role matches the requested role
        if user.role != role:
            flash(f'This account is not registered as a {role}', 'error')
            return redirect(url_for('auth.login', role=role))
        
        login_user(user, remember=form.remember_me.data)
        
        # Add debug print
        print(f"User {user.username} logged in successfully as {user.role}")
        
        # Redirect based on role - using the correct endpoint names
        if user.role == 'student':
            return redirect(url_for('student_routes.student_dashboard'))  # Changed from dashboard to student_dashboard
        elif user.role == 'teacher':
            return redirect(url_for('teacher_routes.teacher_dashboard'))  # Using teacher_dashboard as suggested by error
        elif user.role == 'admin':
            return redirect(url_for('admin_routes.admin_dashboard'))  # Changed from dashboard to admin_dashboard
    
    # Render the appropriate template based on role
    if role == 'student':
        return render_template('auth/student_login.html', title='Student Login', form=form)
    elif role == 'teacher':
        return render_template('auth/teacher_login.html', title='Teacher Login', form=form)
    elif role == 'admin':
        return render_template('auth/admin_login.html', title='Admin Login', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        try:
            db.session.commit()
            flash('Your account has been created! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'error')
    
    return render_template('auth/register.html', title='Register', form=form)

@bp.route('/face_register', methods=['POST'])
@login_required
def face_register():
    if 'face_image' not in request.files:
        flash('No image uploaded')
        return redirect(url_for('student_routes.profile'))
    
    file = request.files['face_image']
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{current_user.id}_face.jpg")
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profile_pics', filename)
        file.save(filepath)
        
        # Save face encoding
        encoding = register_face(current_user.id, filepath)
        if encoding:
            current_user.face_encoding = pickle.dumps(encoding)
            db.session.commit()
            flash('Face registered successfully!')
        else:
            flash('No face detected in image')
    return redirect(url_for('student_routes.profile'))

@bp.route('/login/<role>', methods=['GET', 'POST'])
def role_login(role):
    if role not in ['student', 'teacher', 'admin']:
        abort(404)
        
    form = LoginForm()
    if form.validate_on_submit():
        # Authentication logic
        return redirect(url_for(f'{role}_routes.dashboard'))
    return render_template(f'auth/{role}/login.html', form=form, role=role)

@bp.route('/password-reset', methods=['GET', 'POST'])
def password_reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.get_reset_token()
            msg = Message('Password Reset Request',
                          sender='noreply@educheck.com',
                          recipients=[user.email])
            msg.body = f'''To reset your password, visit the following link:
{url_for('auth.password_reset_token', token=token, _external=True)}

If you did not make this request, ignore this email.
'''
            mail.send(msg)
        flash('Check your email for reset instructions', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/password_reset_request.html', title='Reset Password', form=form)

@bp.route('/password-reset/<token>', methods=['GET', 'POST'])
def password_reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_reset_token(token)
    if not user:
        flash('Invalid or expired token', 'warning')
        return redirect(url_for('auth.password_reset_request'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been updated!', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/password_reset.html', title='Reset Password', form=form)

# Remove this duplicate route or rename it
# @bp.route('/role/<string:role>', methods=['GET', 'POST'])
# def role_login(role):
#     if role not in ['student', 'teacher', 'admin']:
#         abort(404)
#     
#     if current_user.is_authenticated:
#         return redirect(url_for(f'{role}_routes.dashboard'))
#     
#     form = LoginForm()
#     if form.validate_on_submit():
#         user = User.query.filter_by(username=form.username.data).first()
#         if user and user.check_password(form.password.data) and user.role == role:
#             login_user(user, remember=form.remember_me.data)
#             return redirect(url_for(f'{role}_routes.dashboard'))
#         flash('Invalid credentials or role mismatch', 'danger')
#     
#     return render_template(f'auth/{role}_login.html', form=form, role=role.capitalize())

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('auth.login'))