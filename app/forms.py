from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateTimeField, TextAreaField, FileField
from wtforms.validators import DataRequired, Email, EqualTo
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('student', 'Student'), ('teacher', 'Teacher'), ('admin', 'Admin')], validators=[DataRequired()])
    submit = SubmitField('Sign Up')

class AssignmentForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    due_date = DateTimeField('Due Date', format='%Y-%m-%d %H:%M:%S')
    attachment = FileField('Attachment')
    submit = SubmitField('Create')

class AttendanceForm(FlaskForm):
    student = SelectField('Student', coerce=int)
    date = DateTimeField('Date', validators=[DataRequired()])
    status = SelectField('Status', choices=[(True, 'Present'), (False, 'Absent')])
    submit = SubmitField('Update')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class PasswordResetRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class PasswordResetForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class JoinClassForm(FlaskForm):
    class_code = StringField('Class Code', validators=[DataRequired(), Length(min=6, max=8)])
    submit = SubmitField('Join Class')


class CourseForm(FlaskForm):
    name = StringField('Course Name', validators=[DataRequired(), Length(min=2, max=100)])
    course_code = StringField('Course Code', validators=[DataRequired(), Length(min=2, max=20)])
    class_number = StringField('Class Number', validators=[DataRequired(), Length(min=1, max=20)])
    semester = SelectField('Semester', choices=[
        ('fall', 'Fall'),
        ('winter', 'Winter'),
        ('interim', 'Interim'),
        ('trisemester', 'Trisemester'),
        ('fallinter', 'Fall-Inter'),
        ('summer', 'Summer')
    ], validators=[DataRequired()])
    session = SelectField('Session', choices=[
        (f'{year}-{year+1}', f'{year}-{year+1}') for year in range(2024, 2036)
    ], validators=[DataRequired()])
    submit = SubmitField('Create Class')

class ChatMessageForm(FlaskForm):
    message = TextAreaField('Message', validators=[DataRequired()])
    attachment = FileField('Attachment')
    submit = SubmitField('Send')

class NewChatForm(FlaskForm):
    student = SelectField('Select Student', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Start Chat')