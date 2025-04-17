# Add these imports at the top of app/routes/teacher_routes.py if not already present
from flask import render_template, request, flash, redirect, url_for, Blueprint, current_app, abort, jsonify
from flask_login import login_required, current_user
from app import db, socketio # Make sure socketio is imported
# Ensure all necessary models are imported here:
from app.models import User, Course, Assignment, Announcement, Material, AttendanceSession, StudentCourse, Attendance
from app.forms import AttendanceForm, AssignmentForm, CourseForm # Add other forms if needed
from app.utils.decorators import role_required
from app.utils.file_utils import allowed_file
import os
from werkzeug.utils import secure_filename
from datetime import datetime

bp = Blueprint('teacher_routes', __name__)

# @bp.route('/attendance', methods=['GET'])
# @login_required
# @role_required('teacher')
# def manage_attendance():
#     """Displays the main attendance management page for the teacher."""
#     # Get courses taught by the current teacher
#     courses = Course.query.filter_by(teacher_id=current_user.id).order_by(Course.name).all()
#     # The template will check course.active_attendance_session for each course
#     return render_template('attendance/teacher_main.html',
#                            title='Manage Attendance',
#                            courses=courses)

# @bp.route('/course/<int:course_id>/start_attendance', methods=['POST'])
# @login_required
# @role_required('teacher')
# def start_attendance(course_id):
#     """Starts a new attendance session for a course."""
#     course = Course.query.get_or_404(course_id)
#     # Verify teacher owns the course
#     if course.teacher_id != current_user.id:
#         abort(403)

#     # Check if a session is already active for this course
#     if course.active_attendance_session:
#         flash('An attendance session is already active for this course.', 'warning')
#         return redirect(url_for('teacher_routes.manage_attendance'))

#     # Create and start a new session
#     new_session = AttendanceSession(
#         course_id=course.id,
#         teacher_id=current_user.id,
#         start_time=datetime.utcnow()
#         # end_time is None by default, indicating active
#     )
#     db.session.add(new_session)
#     db.session.commit()

#     # Notify students via Socket.IO (optional but recommended)
#     try:
#         socketio.emit('attendance_started', {'course_id': course.id}, room=f'course_{course.id}') # Emit to a room for the course
#         print(f"SocketIO event 'attendance_started' emitted for course {course.id}")
#     except Exception as e:
#         print(f"Error emitting SocketIO event: {e}")


#     flash(f'Attendance session started for {course.name}.', 'success')
#     return redirect(url_for('teacher_routes.manage_attendance'))

# @bp.route('/course/<int:course_id>/end_attendance', methods=['POST'])
# @login_required
# @role_required('teacher')
# def end_attendance(course_id):
#     """Ends the currently active attendance session for a course."""
#     course = Course.query.get_or_404(course_id)
#     # Verify teacher owns the course
#     if course.teacher_id != current_user.id:
#         abort(403)

#     # Find the active session
#     active_session = course.active_attendance_session
#     if not active_session:
#         flash('No active attendance session found for this course.', 'warning')
#         return redirect(url_for('teacher_routes.manage_attendance'))

#     # End the session
#     active_session.end_time = datetime.utcnow()
#     db.session.commit()

#     # Notify students via Socket.IO (optional but recommended)
#     try:
#         socketio.emit('attendance_ended', {'course_id': course.id}, room=f'course_{course.id}') # Emit to a room for the course
#         print(f"SocketIO event 'attendance_ended' emitted for course {course.id}")
#     except Exception as e:
#         print(f"Error emitting SocketIO event: {e}")


#     flash(f'Attendance session ended for {course.name}.', 'success')
#     return redirect(url_for('teacher_routes.manage_attendance'))

# # Placeholder route for viewing/modifying records (implement later)
# @bp.route('/course/<int:course_id>/attendance_records', methods=['GET'])
# @login_required
# @role_required('teacher')
# def view_attendance_records(course_id):
#     """Displays a list of past attendance sessions for a course."""
#     course = Course.query.get_or_404(course_id)
#     if course.teacher_id != current_user.id:
#         abort(403)

#     # Fetch only ended sessions, ordered most recent first
#     sessions = AttendanceSession.query.filter(
#             AttendanceSession.course_id == course.id,
#             AttendanceSession.end_time != None # Ensure session has ended
#         ).order_by(AttendanceSession.start_time.desc()).all()

#     return render_template('attendance/view_records.html',
#                            title=f"Attendance Records for {course.name}",
#                            course=course,
#                            sessions=sessions)

# @bp.route('/session/<int:session_id>/modify', methods=['GET', 'POST'])
# @login_required
# @role_required('teacher')
# def modify_attendance_session(session_id):
#     """Displays and handles modification of attendance for a specific session."""
#     session = AttendanceSession.query.get_or_404(session_id)
#     course = session.course
#     # Verify teacher owns the course associated with the session
#     if course.teacher_id != current_user.id:
#         abort(403)

#     # Get students enrolled in the course
#     enrollments = StudentCourse.query.filter_by(course_id=course.id).all()
#     students = [enrollment.student for enrollment in enrollments]

#     if request.method == 'POST':
#         # Process the submitted form data
#         try:
#             for student in students:
#                 submitted_status = request.form.get(f'status_{student.id}')
#                 if not submitted_status:
#                     # Skip if no status submitted for this student (e.g., form issue)
#                     continue

#                 # Find existing attendance record for this student and session
#                 attendance_record = Attendance.query.filter_by(
#                     session_id=session.id,
#                     student_id=student.id
#                 ).first()

#                 if attendance_record:
#                     # Update existing record
#                     if submitted_status == 'absent':
#                          # Option 1: Delete the record if marked absent
#                          # db.session.delete(attendance_record)
#                          # Option 2: Update status to absent (keeping the record)
#                          attendance_record.status = submitted_status
#                     else:
#                         attendance_record.status = submitted_status
#                         # Optionally update marked_at if needed, though original time might be preferred
#                         # attendance_record.marked_at = datetime.utcnow()
#                 else:
#                     # Create new record only if status is not 'absent'
#                     if submitted_status != 'absent':
#                         new_record = Attendance(
#                             student_id=student.id,
#                             course_id=course.id,
#                             session_id=session.id,
#                             status=submitted_status,
#                             marked_at=datetime.utcnow() # Mark as modified now
#                         )
#                         db.session.add(new_record)

#             db.session.commit()
#             flash(f'Attendance updated successfully for session started at {session.start_time.strftime("%Y-%m-%d %H:%M")}.', 'success')
#             return redirect(url_for('teacher_routes.manage_attendance')) # Redirect back to main attendance page

#         except Exception as e:
#             db.session.rollback()
#             flash(f'Error updating attendance: {str(e)}', 'danger')
#             # Reload the GET request data below

#     # --- GET Request Logic ---
#     # Fetch existing attendance records for this session to pre-populate the form
#     existing_records_list = Attendance.query.filter_by(session_id=session.id).all()
#     # Convert list to dict for easier lookup in template: {student_id: status}
#     attendance_statuses = {record.student_id: record.status for record in existing_records_list}

#     return render_template('attendance/modify_session.html',
#                            title=f"Modify Attendance for {course.name}",
#                            session=session,
#                            students=students,
#                            attendance_statuses=attendance_statuses)

@bp.route('/dashboard')
@login_required
@role_required('teacher')
def teacher_dashboard():
    # Get teacher's courses and assignments
    courses = Course.query.filter_by(teacher_id=current_user.id).all()
    assignments = Assignment.query.filter_by(teacher_id=current_user.id).order_by(Assignment.created_at.desc()).limit(5).all()
    return render_template('dashboards/teacher_dash.html', 
                         title='Teacher Dashboard',
                         courses=courses,
                         assignments=assignments)

@bp.route('/course/<int:course_id>/create_assignment', methods=['GET', 'POST'])
@login_required
@role_required('teacher')
def create_assignment(course_id):
    course = Course.query.get_or_404(course_id)
    if course.teacher_id != current_user.id:
        abort(403)
    form = AssignmentForm()
    if form.validate_on_submit():
        file = form.attachment.data
        if file and allowed_file(file.filename):
            try:
                assignments_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'assignments')
                os.makedirs(assignments_folder, exist_ok=True) # Ensure folder exists
                filename = secure_filename(f"{course_id}_{current_user.id}_{datetime.utcnow().timestamp()}_{file.filename}")
                absolute_file_path = os.path.join(assignments_folder, filename)
                file.save(absolute_file_path)
                # Store relative path for access via url_for('static', ...)
                file_path = os.path.join('uploads', 'assignments', filename).replace('\\', '/')
            except Exception as e:
                flash(f'Error saving file: {str(e)}', 'danger')
                return render_template('assignments/create.html', title='Create Assignment', form=form, course_id=course_id) # Render again on error

        # Combine date and time from form if they are separate fields
        due_datetime = None
        if hasattr(form, 'due_date') and hasattr(form, 'due_time') and form.due_date.data and form.due_time.data:
             due_datetime = datetime.combine(form.due_date.data, form.due_time.data)
        elif hasattr(form, 'due_date') and form.due_date.data: # If only DateTimeField is used
             due_datetime = form.due_date.data


        assignment = Assignment(
            title=form.title.data,
            description=form.description.data,
            due_date=due_datetime, # Use combined datetime
            file_path=file_path, # Use the potentially saved path
            teacher_id=current_user.id,
            course_id=course_id
        )
        try:
            db.session.add(assignment)
            db.session.commit()
            flash('Assignment created successfully!', 'success')
            return redirect(url_for('teacher_routes.course_page', course_id=course_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating assignment: {str(e)}', 'danger')

    # Ensure the template path is correct if using subfolders
    return render_template('assignments/create.html', title='Create Assignment', form=form, course_id=course_id)

@bp.route('/create_course', methods=['GET', 'POST'])
@login_required
@role_required('teacher')
def create_course():
    form = CourseForm()
    if form.validate_on_submit():
        course = Course(
            name=form.name.data,
            class_code=Course.generate_class_code(),
            class_number=form.class_number.data,
            semester=form.semester.data,
            session=form.session.data,
            teacher_id=current_user.id
        )
        db.session.add(course)
        db.session.commit()
        flash('Class created successfully!')
        return redirect(url_for('teacher_routes.course_page', course_id=course.id))
    return render_template('courses/create.html', form=form)

@bp.route('/course/<int:course_id>')
@login_required
@role_required('teacher')
def course_page(course_id):
    course = Course.query.get_or_404(course_id)
    if course.teacher_id != current_user.id:
        abort(403)
    # Fetch related data needed for the course page template
    # e.g., assignments = course.assignments
    # e.g., announcements = course.announcements
    # e.g., materials = course.materials
    # e.g., enrollments = course.student_enrollments
    return render_template('courses/course_page.html', course=course)

@bp.route('/update_meet/<int:course_id>', methods=['POST'])
@login_required
@role_required('teacher')
def update_meet(course_id):
    # This route seems designed for AJAX/Fetch updates
    course = Course.query.get_or_404(course_id)
    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Forbidden'}), 403
    try:
        meet_code = request.form.get('meet_code', '')
        course.meet_code = meet_code # Update meet code
        db.session.commit()
        return jsonify({'success': True, 'message': 'Meet link updated.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@bp.route('/course/<int:course_id>/create_announcement', methods=['POST'])
@login_required
@role_required('teacher')
def create_announcement(course_id):
    course = Course.query.get_or_404(course_id)
    if course.teacher_id != current_user.id:
        abort(403)

    title = request.form.get('title')
    content = request.form.get('content')

    if not title or not content:
        flash('Title and content are required for announcements.', 'warning')
        return redirect(url_for('teacher_routes.course_page', course_id=course_id))

    try:
        announcement = Announcement(
            title=title,
            content=content,
            course_id=course_id,
            teacher_id=current_user.id # Ensure teacher_id is set
            # created_at defaults to now
        )
        db.session.add(announcement)
        db.session.commit()
        flash('Announcement created successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating announcement: {str(e)}', 'danger')

    return redirect(url_for('teacher_routes.course_page', course_id=course_id))

@bp.route('/course/<int:course_id>/upload_material', methods=['POST'])
@login_required
@role_required('teacher')
def upload_material(course_id):
    course = Course.query.get_or_404(course_id)
    if course.teacher_id != current_user.id:
        abort(403)

    file = request.files.get('file')
    title = request.form.get('title')
    description = request.form.get('description')

    if not file or not title:
         flash('File and Title are required for materials.', 'warning')
         return redirect(url_for('teacher_routes.course_page', course_id=course_id))

    if allowed_file(file.filename):
        try:
            materials_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'materials')
            os.makedirs(materials_folder, exist_ok=True) # Ensure folder exists
            # Create a more unique filename
            filename = secure_filename(f"{course_id}_{current_user.id}_{datetime.utcnow().timestamp()}_{file.filename}")
            absolute_file_path = os.path.join(materials_folder, filename)
            file.save(absolute_file_path)
            # Store relative path for access via url_for('static', ...)
            relative_file_path = os.path.join('uploads', 'materials', filename).replace('\\', '/')

            material = Material(
                title=title,
                description=description if description else "", # Handle optional description
                file_path=relative_file_path, # Store relative path
                course_id=course_id
                # created_at defaults to now
            )
            db.session.add(material)
            db.session.commit()
            flash('Material uploaded successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error uploading material: {str(e)}', 'danger')
    else:
        flash('Invalid file type.', 'warning')

    return redirect(url_for('teacher_routes.course_page', course_id=course_id))


@bp.route('/profile')
@login_required
@role_required('teacher')
def profile():
    # Fetch data needed specifically for the profile page
    courses = Course.query.filter_by(teacher_id=current_user.id).all()
    assignments = Assignment.query.filter_by(teacher_id=current_user.id).all()
    # Add more data fetching if needed
    return render_template('dashboards/teacher_profile.html',
                           title=f"{current_user.username}'s Profile", # Dynamic title
                           courses=courses,
                           assignments=assignments)


# === ATTENDANCE ROUTES ===

@bp.route('/attendance', methods=['GET'])
@login_required
@role_required('teacher')
def manage_attendance():
    """Displays the main attendance management page for the teacher."""
    courses = Course.query.filter_by(teacher_id=current_user.id).order_by(Course.name).all()
    return render_template('attendance/teacher_main.html',
                           title='Manage Attendance',
                           courses=courses)

@bp.route('/course/<int:course_id>/start_attendance', methods=['POST'])
@login_required
@role_required('teacher')
def start_attendance(course_id):
    """Starts a new attendance session for a course."""
    course = Course.query.get_or_404(course_id)
    if course.teacher_id != current_user.id:
        abort(403)

    # Use the property to check for active session
    if course.active_attendance_session:
        flash('An attendance session is already active for this course.', 'warning')
        return redirect(url_for('teacher_routes.manage_attendance'))

    try:
        new_session = AttendanceSession( # Now AttendanceSession should be defined
            course_id=course.id,
            teacher_id=current_user.id,
            start_time=datetime.utcnow()
        )
        db.session.add(new_session)
        db.session.commit()

        # Notify students via Socket.IO
        try:
            socketio.emit('attendance_started', {'course_id': course.id}, room=f'course_{course.id}')
            print(f"SocketIO event 'attendance_started' emitted for course {course.id}")
        except Exception as e:
            print(f"Error emitting SocketIO event: {e}") # Log socket errors

        flash(f'Attendance session started for {course.name}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error starting attendance session: {str(e)}', 'danger')

    return redirect(url_for('teacher_routes.manage_attendance'))

@bp.route('/course/<int:course_id>/end_attendance', methods=['POST'])
@login_required
@role_required('teacher')
def end_attendance(course_id):
    """Ends the currently active attendance session for a course."""
    course = Course.query.get_or_404(course_id)
    if course.teacher_id != current_user.id:
        abort(403)

    active_session = course.active_attendance_session
    if not active_session:
        flash('No active attendance session found for this course.', 'warning')
        return redirect(url_for('teacher_routes.manage_attendance'))

    try:
        active_session.end_time = datetime.utcnow()
        db.session.commit()

        # Notify students via Socket.IO
        try:
            socketio.emit('attendance_ended', {'course_id': course.id}, room=f'course_{course.id}')
            print(f"SocketIO event 'attendance_ended' emitted for course {course.id}")
        except Exception as e:
            print(f"Error emitting SocketIO event: {e}") # Log socket errors

        flash(f'Attendance session ended for {course.name}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error ending attendance session: {str(e)}', 'danger')

    return redirect(url_for('teacher_routes.manage_attendance'))


@bp.route('/course/<int:course_id>/attendance_records', methods=['GET'])
@login_required
@role_required('teacher')
def view_attendance_records(course_id):
    """Displays a list of past attendance sessions for a course."""
    course = Course.query.get_or_404(course_id)
    if course.teacher_id != current_user.id:
        abort(403)

    sessions = AttendanceSession.query.filter(
            AttendanceSession.course_id == course.id,
            AttendanceSession.end_time != None
        ).order_by(AttendanceSession.start_time.desc()).all()

    return render_template('attendance/view_records.html',
                           title=f"Attendance Records for {course.name}",
                           course=course,
                           sessions=sessions)

@bp.route('/session/<int:session_id>/modify', methods=['GET', 'POST'])
@login_required
@role_required('teacher')
def modify_attendance_session(session_id):
    """Displays and handles modification of attendance for a specific session."""
    session = AttendanceSession.query.get_or_404(session_id)
    course = session.course
    if course.teacher_id != current_user.id:
        abort(403)

    enrollments = StudentCourse.query.filter_by(course_id=course.id).all()
    students = [enrollment.student for enrollment in enrollments]

    if request.method == 'POST':
        try:
            for student in students:
                submitted_status = request.form.get(f'status_{student.id}')
                if not submitted_status:
                    continue

                attendance_record = Attendance.query.filter_by(
                    session_id=session.id,
                    student_id=student.id
                ).first()

                if attendance_record:
                    if submitted_status == 'absent':
                        # Option: Update status to absent
                         attendance_record.status = submitted_status
                         # Option: Delete record if marking absent
                         # db.session.delete(attendance_record)
                    else:
                        attendance_record.status = submitted_status
                elif submitted_status != 'absent': # Only create if not absent
                    new_record = Attendance(
                        student_id=student.id,
                        course_id=course.id,
                        session_id=session.id,
                        status=submitted_status,
                        marked_at=datetime.utcnow()
                    )
                    db.session.add(new_record)

            db.session.commit()
            flash(f'Attendance updated successfully for session started at {session.start_time.strftime("%Y-%m-%d %H:%M")}.', 'success')
            return redirect(url_for('teacher_routes.manage_attendance'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating attendance: {str(e)}', 'danger')
            # Need to refetch data for GET if POST fails and rerenders
            existing_records_list = Attendance.query.filter_by(session_id=session.id).all()
            attendance_statuses = {record.student_id: record.status for record in existing_records_list}
            return render_template('attendance/modify_session.html',
                                   title=f"Modify Attendance for {course.name}",
                                   session=session,
                                   students=students,
                                   attendance_statuses=attendance_statuses)


    # --- GET Request Logic ---
    existing_records_list = Attendance.query.filter_by(session_id=session.id).all()
    attendance_statuses = {record.student_id: record.status for record in existing_records_list}

    return render_template('attendance/modify_session.html',
                           title=f"Modify Attendance for {course.name}",
                           session=session,
                           students=students,
                           attendance_statuses=attendance_statuses)
