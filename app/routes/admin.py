from datetime import datetime
from functools import wraps

from flask import (
    Blueprint,
    abort,
    render_template,
    request,
    redirect,
    url_for
)

from flask_login import (
    login_required,
    current_user
)

from app import db

from app.models.user_report import UserReport
from app.models.content_flag import ContentFlag
from app.models.user import User


admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)


# ----------------------------------------------------------------------
# ADMIN ACCESS CONTROL
# ----------------------------------------------------------------------

def admin_required(view_function):
    """
    Allow access only to authenticated administrator accounts.
    """

    @wraps(view_function)
    @login_required
    def wrapped_view(*args, **kwargs):

        if not current_user.is_admin:
            abort(403)

        return view_function(
            *args,
            **kwargs
        )

    return wrapped_view


# ----------------------------------------------------------------------
# ADMIN DASHBOARD
# ----------------------------------------------------------------------

@admin_bp.route("/")
@admin_required
def dashboard():

    pending_reports = UserReport.query.filter_by(
        status="pending"
    ).count()

    pending_flags = ContentFlag.query.filter_by(
        status="pending"
    ).count()

    total_reports = UserReport.query.count()

    total_flags = ContentFlag.query.count()

    return render_template(
        "admin/dashboard.html",
        pending_reports=pending_reports,
        pending_flags=pending_flags,
        total_reports=total_reports,
        total_flags=total_flags
    )


# ----------------------------------------------------------------------
# USER REPORTS
# ----------------------------------------------------------------------

@admin_bp.route("/reports")
@admin_required
def reports():

    reports = UserReport.query.order_by(
        UserReport.created_at.desc()
    ).all()

    return render_template(
        "admin/reports.html",
        reports=reports
    )


@admin_bp.route(
    "/reports/<int:report_id>/update",
    methods=["POST"]
)
@admin_required
def update_report(report_id):

    report = db.session.get(
        UserReport,
        report_id
    )

    if report is None:
        abort(404)

    status = request.form.get(
        "status",
        ""
    ).strip()

    admin_notes = request.form.get(
        "admin_notes",
        ""
    ).strip()

    allowed_statuses = {
        "reviewed",
        "actioned"
    }

    if status not in allowed_statuses:
        abort(400)

    report.status = status
    report.admin_notes = admin_notes or None
    report.reviewed_by = current_user.id
    report.reviewed_at = datetime.utcnow()

    db.session.commit()

    return redirect(
        url_for(
            "admin.reports"
        )
    )


# ----------------------------------------------------------------------
# CONTENT FLAGS
# ----------------------------------------------------------------------

@admin_bp.route("/flags")
@admin_required
def flags():

    flags = ContentFlag.query.order_by(
        ContentFlag.created_at.desc()
    ).all()

    return render_template(
        "admin/flags.html",
        flags=flags
    )


@admin_bp.route(
    "/flags/<int:flag_id>/update",
    methods=["POST"]
)
@admin_required
def update_flag(flag_id):

    flag = db.session.get(
        ContentFlag,
        flag_id
    )

    if flag is None:
        abort(404)

    status = request.form.get(
        "status",
        ""
    ).strip()

    admin_notes = request.form.get(
        "admin_notes",
        ""
    ).strip()

    allowed_statuses = {
        "reviewed",
        "actioned"
    }

    if status not in allowed_statuses:
        abort(400)

    flag.status = status
    flag.admin_notes = admin_notes or None
    flag.reviewed_by = current_user.id
    flag.reviewed_at = datetime.utcnow()

    db.session.commit()

    return redirect(
        url_for(
            "admin.flags"
        )
    )


# ----------------------------------------------------------------------
# USER MANAGEMENT
# ----------------------------------------------------------------------

@admin_bp.route("/users")
@admin_required
def users():

    users = User.query.order_by(
        User.username.asc()
    ).all()

    return render_template(
        "admin/users.html",
        users=users
    )


@admin_bp.route(
    "/users/<int:user_id>/toggle-admin",
    methods=["POST"]
)
@admin_required
def toggle_admin(user_id):

    user = db.session.get(
        User,
        user_id
    )

    if user is None:
        abort(404)

    # An administrator cannot remove their own admin access.
    if user.id == current_user.id:
        abort(400)

    user.is_admin = not user.is_admin

    db.session.commit()

    return redirect(
        url_for(
            "admin.users"
        )
    )

    # ----------------------------------------------------------------------
# USER SUSPENSION
# ----------------------------------------------------------------------

@admin_bp.route(
    "/users/<int:user_id>/toggle-suspension",
    methods=["POST"]
)
@admin_required
def toggle_suspension(user_id):

    user = db.session.get(
        User,
        user_id
    )

    if user is None:
        abort(404)

    # An administrator cannot suspend their own account.
    if user.id == current_user.id:
        abort(400)

    user.is_suspended = not user.is_suspended

    db.session.commit()

    return redirect(
        url_for(
            "admin.users"
        )
    )