# Add these imports at the top if not already present
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify, abort # Added jsonify, abort
from flask_login import login_required, current_user
# Ensure ALL necessary models are imported here:
from app.models import User, Assignment, AssignmentSubmission, Course, StudentCourse, AttendanceSession, Attendance
from app import db, socketio # Added socketio if needed for real-time updates later
from app.utils.decorators import role_required # Ensure role_required is imported correctly
from app.utils.file_utils import allowed_file
from app.forms import JoinClassForm # Import other forms if needed
from werkzeug.utils import secure_filename
import os
import base64 # For decoding image data
import io # For handling image stream
import pickle # For handling face encodings
from datetime import datetime

# Import face auth functions (adjust path if utils structure is different)
from app.utils import face_auth

bp = Blueprint('student_routes', __name__, url_prefix='/student') # Ensure prefix

# === Existing Student Routes ===
@bp.route('/dashboard')
@login_required
@role_required('student')
def student_dashboard():
    # Update the template path to point to the dashboards folder
    # Pass any necessary data for the dashboard sections
    # Example placeholders (replace with actual queries if needed):
    unsubmitted_assignments = [] # Query for actual unsubmitted assignments
    new_announcements = [] # Query for actual new announcements
    # Pass data to the template
    return render_template('dashboards/student_dash.html',
                           title='Student Dashboard',
                           unsubmitted_assignments=unsubmitted_assignments,
                           new_announcements=new_announcements)


# Placeholder for submit assignment page route (if needed)
@bp.route('/assignment/<int:assignment_id>/submit', methods=['GET', 'POST'])
@login_required
@role_required('student')
def submit_assignment_page(assignment_id):
     assignment = Assignment.query.get_or_404(assignment_id)
     # TODO: Add form handling for submission
     flash('Assignment submission page not fully implemented yet.', 'info')
     # Render a template for submission or handle POST logic
     # For now, redirect back or render placeholder
     return redirect(request.referrer or url_for('student_routes.view_course', course_id=assignment.course_id))


@bp.route('/submit_assignment/<int:assignment_id>', methods=['POST'])
@login_required
@role_required('student')
def submit_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    course_id = assignment.course_id # Get course_id for redirect

    if 'submission_file' not in request.files:
        flash('No file uploaded', 'warning')
        # Redirect back to the course page where the assignment is listed
        return redirect(url_for('student_routes.view_course', course_id=course_id))

    file = request.files['submission_file']
    if file.filename == '':
         flash('No selected file', 'warning')
         return redirect(url_for('student_routes.view_course', course_id=course_id))


    if file and allowed_file(file.filename):
        try:
            submissions_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'submissions', str(course_id))
            os.makedirs(submissions_folder, exist_ok=True) # Ensure folder exists
            # Create a more unique filename
            filename = secure_filename(f"{current_user.id}_{assignment.id}_{datetime.utcnow().timestamp()}_{file.filename}")
            absolute_file_path = os.path.join(submissions_folder, filename)
            file.save(absolute_file_path)
             # Store relative path
            relative_file_path = os.path.join('uploads', 'submissions', str(course_id), filename).replace('\\', '/')


            # Check if submission already exists, update if necessary or prevent re-submission
            existing_submission = AssignmentSubmission.query.filter_by(
                assignment_id=assignment.id,
                student_id=current_user.id
            ).first()

            if existing_submission:
                 # Optionally update the existing submission file/timestamp
                 flash('You have already submitted this assignment. Updating submission.', 'info')
                 existing_submission.file_path = relative_file_path
                 existing_submission.submitted_at = datetime.utcnow()
            else:
                 # Create new submission
                 submission = AssignmentSubmission(
                     assignment_id=assignment.id,
                     student_id=current_user.id,
                     file_path=relative_file_path,
                     submitted_at=datetime.utcnow()
                 )
                 db.session.add(submission)

            db.session.commit()
            flash('Assignment submitted successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting assignment: {str(e)}', 'danger')
    else:
         flash('Invalid file type.', 'warning')

    return redirect(url_for('student_routes.view_course', course_id=course_id))


@bp.route('/classes')
@login_required
@role_required('student')
def student_classes():
    form = JoinClassForm()
    # Get all classes the student is enrolled in
    enrollments = StudentCourse.query.filter_by(student_id=current_user.id).all()
    return render_template('dashboards/student_classes.html', form=form, enrollments=enrollments, title='My Classes')


@bp.route('/course/<int:course_id>')
@login_required
@role_required('student')
def view_course(course_id):
    # Check if student is enrolled in this course
    enrollment = StudentCourse.query.filter_by(student_id=current_user.id, course_id=course_id).first_or_404("You are not enrolled in this course.")

    course = enrollment.course # Get the course object from the enrollment

    # Fetch assignments, announcements, materials for this course
    assignments = Assignment.query.filter_by(course_id=course_id).order_by(Assignment.due_date.asc()).all()
    # Assuming you have Announcement and Material models imported
    from app.models import Announcement, Material
    announcements = Announcement.query.filter_by(course_id=course_id).order_by(Announcement.created_at.desc()).all()
    materials = Material.query.filter_by(course_id=course_id).order_by(Material.created_at.desc()).all()

    # TODO: Fetch student rank and attendance percentage for this specific course
    student_rank_in_course = "N/A" # Placeholder
    student_attendance_percent = "N/A" # Placeholder

    return render_template('courses/student_course_view.html',
                           title=course.name,
                           course=course,
                           assignments=assignments,
                           announcements=announcements,
                           materials=materials,
                           student_rank_in_course=student_rank_in_course,
                           student_attendance_percent=student_attendance_percent)


@bp.route('/join_class', methods=['POST']) # Changed to POST only as form is on classes page
@login_required
@role_required('student')
def join_class():
    form = JoinClassForm() # Process the submitted form
    if form.validate_on_submit():
        course = Course.query.filter_by(class_code=form.class_code.data).first()
        if not course:
            flash('Invalid class code!', 'error')
        elif StudentCourse.query.filter_by(student_id=current_user.id, course_id=course.id).first():
            flash('You are already enrolled in this class!', 'warning')
        else:
            try:
                enrollment = StudentCourse(student_id=current_user.id, course_id=course.id)
                db.session.add(enrollment)
                db.session.commit()
                flash('Successfully joined the class!', 'success')
            except Exception as e:
                 db.session.rollback()
                 flash(f'Error joining class: {str(e)}', 'danger')
    else:
         # Handle form validation errors if any (though basic validators are used)
         for field, errors in form.errors.items():
             for error in errors:
                 flash(f"Error in {getattr(form, field).label.text}: {error}", 'error')

    return redirect(url_for('student_routes.student_classes')) # Redirect back to classes page


@bp.route('/profile')
@login_required
@role_required('student')
def student_profile():
    # Fetch data needed for the profile page
    enrolled_courses_count = StudentCourse.query.filter_by(student_id=current_user.id).count()
    submitted_assignments_count = AssignmentSubmission.query.filter_by(student_id=current_user.id).count()
    # Add more data fetching as needed (e.g., grades, attendance)

    return render_template('dashboards/student_profile.html',
                           title='My Profile',
                           enrolled_courses_count=enrolled_courses_count,
                           submitted_assignments_count=submitted_assignments_count)

# ==============================


# === ATTENDANCE ROUTES ===

@bp.route('/attendance', methods=['GET'])
@login_required
@role_required('student')
def manage_attendance():
    """Displays the main attendance page for the student."""
    enrollments = StudentCourse.query.filter_by(student_id=current_user.id).all()
    courses = [enrollment.course for enrollment in enrollments]
    face_registered = current_user.face_encoding is not None

    courses_status = []
    for course in courses:
        active_session = course.active_attendance_session
        already_marked = False
        if active_session:
            # Check if student has an attendance record for this specific active session
            # --- Attendance model is now imported ---
            record = Attendance.query.filter_by(
                session_id=active_session.id,
                student_id=current_user.id
            ).first()
            if record:
                already_marked = True

        courses_status.append({
            'course': course,
            'session_active': active_session is not None,
            'already_marked': already_marked
        })

    return render_template('attendance/student_main.html',
                           title='Attendance',
                           courses_status=courses_status,
                           face_registered=face_registered)

@bp.route('/face/register', methods=['GET'])
@login_required
@role_required('student')
def face_register_page():
    """Displays the page for registering face ID."""
    if current_user.face_encoding:
        flash('Face ID already registered.', 'info')
        return redirect(url_for('student_routes.manage_attendance'))
    return render_template('attendance/face_register.html', title='Register Face ID')

@bp.route('/face/register', methods=['POST'])
@login_required
@role_required('student')
def face_register_submit():
    """Handles the submission of face image data for registration."""
    if current_user.face_encoding:
        return jsonify({'success': False, 'message': 'Face ID already registered.'}), 400

    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({'success': False, 'message': 'No image data received.'}), 400

    try:
        image_data = data['image'].split(',')[1]
        image_bytes = base64.b64decode(image_data)
        image_stream = io.BytesIO(image_bytes)
    except Exception as e:
        current_app.logger.error(f"Error decoding image: {e}")
        return jsonify({'success': False, 'message': 'Invalid image data format.'}), 400

    try:
        encoding = face_auth.register_face(current_user.id, image_stream)
        if encoding:
             # Assuming register_face now handles commit
             return jsonify({'success': True, 'message': 'Face ID registered successfully!'})
        else:
             return jsonify({'success': False, 'message': 'No face detected or error during registration.'}), 400
    except Exception as e:
         current_app.logger.error(f"Error during face registration process: {e}", exc_info=True)
         return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/course/<int:course_id>/mark_attendance', methods=['GET'])
@login_required
@role_required('student')
def mark_attendance_page(course_id):
    """Displays the page for marking attendance for a specific course."""
    course = Course.query.get_or_404(course_id)
    enrollment = StudentCourse.query.filter_by(student_id=current_user.id, course_id=course_id).first_or_404("Not enrolled.")

    if not current_user.face_encoding:
         flash('You need to register your Face ID before marking attendance.', 'warning')
         # Redirect to registration page instead of main attendance page
         return redirect(url_for('student_routes.face_register_page'))

    active_session = course.active_attendance_session
    if not active_session:
        flash('Attendance session is not active for this course.', 'warning')
        return redirect(url_for('student_routes.manage_attendance'))

    # --- Attendance model is now imported ---
    record = Attendance.query.filter_by(session_id=active_session.id, student_id=current_user.id).first()
    if record:
         flash('You have already marked attendance for this session.', 'info')
         return redirect(url_for('student_routes.manage_attendance'))

    # Ensure template path is correct (e.g., attendance/mark_attendance.html)
    return render_template('attendance/mark_attendance.html', title=f'Mark Attendance for {course.name}', course_id=course_id)


@bp.route('/course/<int:course_id>/mark_attendance', methods=['POST'])
@login_required
@role_required('student')
def mark_attendance_submit(course_id):
    """Handles the submission of face image data for marking attendance."""
    course = Course.query.get_or_404(course_id)
    if not current_user.face_encoding:
        return jsonify({'success': False, 'message': 'Face ID not registered.'}), 400

    active_session = course.active_attendance_session
    if not active_session:
        return jsonify({'success': False, 'message': 'Attendance session is not active.'}), 400

    # --- Attendance model is now imported ---
    existing_record = Attendance.query.filter_by(session_id=active_session.id, student_id=current_user.id).first()
    if existing_record:
        return jsonify({'success': False, 'message': 'Attendance already marked for this session.'}), 400

    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({'success': False, 'message': 'No image data received.'}), 400

    try:
        image_data = data['image'].split(',')[1]
        image_bytes = base64.b64decode(image_data)
        image_stream = io.BytesIO(image_bytes)
    except Exception as e:
        current_app.logger.error(f"Error decoding image: {e}")
        return jsonify({'success': False, 'message': 'Invalid image data format.'}), 400

    try:
        is_match = face_auth.verify_face(current_user.id, image_stream)

        if is_match:
            # --- Attendance model is now imported ---
            new_record = Attendance(
                student_id=current_user.id,
                course_id=course.id,
                session_id=active_session.id,
                status='present',
                marked_at=datetime.utcnow()
            )
            db.session.add(new_record)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Attendance marked successfully!'})
        else:
            return jsonify({'success': False, 'message': 'Face verification failed. Please try again.'})
    except Exception as e:
        current_app.logger.error(f"Error during face verification/attendance marking: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500

# === END ATTENDANCE ROUTES ===

