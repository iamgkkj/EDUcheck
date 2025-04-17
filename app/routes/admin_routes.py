from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import User
from app import db
from app.utils import role_required  # Add this import

bp = Blueprint('admin_routes', __name__)

@bp.route('/dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    # Update the template path to point to the dashboards folder
    return render_template('dashboards/admin_dash.html', title='Admin Dashboard')