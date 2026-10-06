from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)
from flask_login import login_required, current_user

from app import db, bcrypt
from app.models.user import User

from app.services.otp_service import send_email_verification_code
from app.services.verification_service import (
    verify_code,
    VERIFICATION_PURPOSE_CHANGE_EMAIL,
    VERIFICATION_PURPOSE_CHANGE_PASSWORD,
    VERIFICATION_PURPOSE_VERIFY_EMAIL
)

settings_bp = Blueprint("settings", __name__)


@settings_bp.route(
    "/settings",
    methods=["GET", "POST"]
)
@login_required
def settings():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        current_password = request.form.get(
            "current_password",
            ""
        )

        # -------------------------------------------------
        # Validate required fields.
        # -------------------------------------------------

        if not username or not email or not current_password:

            flash(
                "Username, email and current password are required.",
                "error"
            )

            return redirect(
                url_for("settings.settings")
            )

        # -------------------------------------------------
        # Validate username length.
        # -------------------------------------------------

        if len(username) > 50:

            flash(
                "Username must be 50 characters or fewer.",
                "error"
            )

            return redirect(
                url_for("settings.settings")
            )

        # -------------------------------------------------
        # Validate email length.
        # -------------------------------------------------

        if len(email) > 120:

            flash(
                "Email must be 120 characters or fewer.",
                "error"
            )

            return redirect(
                url_for("settings.settings")
            )

        # -------------------------------------------------
        # Verify current password.
        # -------------------------------------------------

        if not bcrypt.check_password_hash(
            current_user.password_hash,
            current_password
        ):

            flash(
                "Current password is incorrect.",
                "error"
            )

            return redirect(
                url_for("settings.settings")
            )

        # -------------------------------------------------
        # Check whether another user already has the
        # requested username.
        # -------------------------------------------------

        existing_username = User.query.filter(
            User.username == username,
            User.id != current_user.id
        ).first()

        if existing_username:

            flash(
                "That username is already in use.",
                "error"
            )

            return redirect(
                url_for("settings.settings")
            )

        # -------------------------------------------------
        # Check whether another user already has the
        # requested email.
        # -------------------------------------------------

        existing_email = User.query.filter(
            User.email == email,
            User.id != current_user.id
        ).first()

        if existing_email:

            flash(
                "That email address is already in use.",
                "error"
            )

            return redirect(
                url_for("settings.settings")
            )

        # -------------------------------------------------
        # Update account information.
        # -------------------------------------------------

        current_user.username = username
        current_user.email = email

        db.session.commit()

        flash(
            "Account information updated successfully.",
            "success"
        )

        return redirect(
            url_for("settings.settings")
        )

    return render_template(
        "settings.html",
        user=current_user
    )

@settings_bp.route(
    "/settings/email/request",
    methods=["POST"]
)
@login_required
def request_email_change():

    new_email = request.form.get(
        "email",
        ""
    ).strip().lower()

    # -------------------------------------------------
    # Validate email.
    # -------------------------------------------------

    if not new_email:

        flash(
            "Please enter an email address.",
            "error"
        )

        return redirect(
            url_for("settings.settings")
        )

    # -------------------------------------------------
    # Validate email length.
    # -------------------------------------------------

    if len(new_email) > 120:

        flash(
            "Email must be 120 characters or fewer.",
            "error"
        )

        return redirect(
            url_for("settings.settings")
        )

    # -------------------------------------------------
    # Check whether another account already uses
    # this email address.
    # -------------------------------------------------

    existing_email = User.query.filter(
        User.email == new_email,
        User.id != current_user.id
    ).first()

    if existing_email:

        flash(
            "That email address is already in use.",
            "error"
        )

        return redirect(
            url_for("settings.settings")
        )

    # -------------------------------------------------
    # Do not send an OTP if the email has not changed.
    # -------------------------------------------------

    if new_email == current_user.email.lower():

        flash(
            "This is already your current email address.",
            "error"
        )

        return redirect(
            url_for("settings.settings")
        )

    # -------------------------------------------------
    # Store the pending email in the session.
    # The actual account email will not be changed yet.
    # -------------------------------------------------

    from flask import session

    session["pending_email_change"] = new_email

    # -------------------------------------------------
    # Send the verification code.
    # -------------------------------------------------

    sent, message = send_email_verification_code(
        user_id=current_user.id,
        email=new_email,
        purpose=VERIFICATION_PURPOSE_CHANGE_EMAIL
    )

    if not sent:

        session.pop(
            "pending_email_change",
            None
        )

        flash(
            message,
            "error"
        )

        return redirect(
            url_for("settings.settings")
        )

    flash(
        "A verification code has been sent to your new email address.",
        "success"
    )

    return redirect(
        url_for("settings.settings")
    )


@settings_bp.route(
    "/settings/email/verification/request",
    methods=["POST"]
)
@login_required
def request_email_verification():

    if current_user.email_verified:

        flash(
            "Your email address is already verified.",
            "success"
        )

        return redirect(
            url_for("settings.settings")
        )

    sent, message = send_email_verification_code(
        user_id=current_user.id,
        email=current_user.email,
        purpose=VERIFICATION_PURPOSE_VERIFY_EMAIL
    )

    if not sent:

        flash(
            message,
            "error"
        )

        return redirect(
            url_for("settings.settings")
        )

    session["email_verification_pending"] = True

    flash(
        "A verification code has been sent to your email address.",
        "success"
    )

    return redirect(
        url_for("settings.settings")
    )


@settings_bp.route(
    "/settings/email/verify",
    methods=["POST"]
)
@login_required
def verify_email_change():

    otp = request.form.get(
        "otp",
        ""
    ).strip()

    pending_email = session.get(
        "pending_email_change"
    )

    # -------------------------------------------------
    # Make sure an email change is actually pending.
    # -------------------------------------------------

    if not pending_email:

        flash(
            "There is no pending email change.",
            "error"
        )

        return redirect(
            url_for("settings.settings")
        )

    # -------------------------------------------------
    # Validate OTP input.
    # -------------------------------------------------

    if not otp:

        flash(
            "Please enter the verification code.",
            "error"
        )

        return redirect(
            url_for("settings.settings")
        )

    # -------------------------------------------------
    # Verify the OTP for this user and purpose.
    # -------------------------------------------------

    verified, message = verify_code(
        user_id=current_user.id,
        purpose=VERIFICATION_PURPOSE_CHANGE_EMAIL,
        otp=otp
    )

    if not verified:

        flash(
            message,
            "error"
        )

        return redirect(
            url_for("settings.settings")
        )

    # -------------------------------------------------
    # Check again that the pending email is still
    # available and not already registered.
    # -------------------------------------------------

    existing_email = User.query.filter(
        User.email == pending_email,
        User.id != current_user.id
    ).first()

    if existing_email:

        session.pop(
            "pending_email_change",
            None
        )

        flash(
            "That email address is already in use.",
            "error"
        )

        return redirect(
            url_for("settings.settings")
        )

    # -------------------------------------------------
    # Apply the verified email change.
    # -------------------------------------------------

    current_user.email = pending_email
    current_user.email_verified = True

    db.session.commit()

    session.pop("pending_email_change", None)

    flash(
    "Your email address has been updated and verified successfully.",
    "success"
)

    return redirect(
        url_for("settings.settings")
    )

@settings_bp.route(
    "/settings/email/verification/verify",
    methods=["POST"]
)
@login_required
def verify_account_email():

    otp = request.form.get(
        "otp",
        ""
    ).strip()

    if not session.get("email_verification_pending"):

        flash(
            "There is no pending email verification.",
            "error"
        )

        return redirect(
            url_for("settings.settings")
        )

    if not otp:

        flash(
            "Please enter the verification code.",
            "error"
        )

        return redirect(
            url_for("settings.settings")
        )

    verified, message = verify_code(
        user_id=current_user.id,
        purpose=VERIFICATION_PURPOSE_VERIFY_EMAIL,
        otp=otp
    )

    if not verified:

        flash(
            message,
            "error"
        )

        return redirect(
            url_for("settings.settings")
        )

    current_user.email_verified = True

    db.session.commit()

    session.pop(
        "email_verification_pending",
        None
    )

    flash(
        "Your email address has been verified successfully.",
        "success"
    )

    return redirect(
        url_for("settings.settings")
    )

@settings_bp.route(
    "/settings/password/request",
    methods=["POST"]
)
@login_required
def request_password_change():

    current_password = request.form.get(
        "current_password",
        ""
    )

    new_password = request.form.get(
        "new_password",
        ""
    )

    confirm_password = request.form.get(
        "confirm_password",
        ""
    )

    # -------------------------------------------------
    # Validate required fields.
    # -------------------------------------------------

    if not current_password or not new_password or not confirm_password:

        flash(
            "All password fields are required.",
            "error"
        )

        return redirect(
            url_for("settings.settings")
        )

    # -------------------------------------------------
    # Verify the current password.
    # -------------------------------------------------

    if not bcrypt.check_password_hash(
        current_user.password_hash,
        current_password
    ):

        flash(
            "Current password is incorrect.",
            "error"
        )

        return redirect(
            url_for("settings.settings")
        )

    # -------------------------------------------------
    # Make sure the new passwords match.
    # -------------------------------------------------

    if new_password != confirm_password:

        flash(
            "New passwords do not match.",
            "error"
        )

        return redirect(
            url_for("settings.settings")
        )

    # -------------------------------------------------
    # Basic password length validation.
    # -------------------------------------------------

    if len(new_password) < 8:

        flash(
            "New password must be at least 8 characters long.",
            "error"
        )

        return redirect(
            url_for("settings.settings")
        )

    # -------------------------------------------------
    # Do not allow the same password.
    # -------------------------------------------------

    if bcrypt.check_password_hash(
        current_user.password_hash,
        new_password
    ):

        flash(
            "Your new password must be different from your current password.",
            "error"
        )

        return redirect(
            url_for("settings.settings")
        )

    # -------------------------------------------------
    # Store the new password temporarily in the session.
    # It will only be applied after successful OTP
    # verification.
    # -------------------------------------------------

    session["pending_password_hash"] = (
        bcrypt.generate_password_hash(
            new_password
        ).decode("utf-8")
    )

    # -------------------------------------------------
    # Send the verification code to the verified
    # account email.
    # -------------------------------------------------

    if not current_user.email_verified:

        session.pop(
            "pending_password_hash",
            None
        )

        flash(
            "Please verify your email address before changing your password.",
            "error"
        )

        return redirect(
            url_for("settings.settings")
        )

    sent, message = send_email_verification_code(
        user_id=current_user.id,
        email=current_user.email,
        purpose=VERIFICATION_PURPOSE_CHANGE_PASSWORD
    )

    if not sent:

        session.pop(
            "pending_password_hash",
            None
        )

        flash(
            message,
            "error"
        )

        return redirect(
            url_for("settings.settings")
        )

    session["password_change_pending"] = True

    flash(
        "A verification code has been sent to your verified email address.",
        "success"
    )

    return redirect(
        url_for("settings.settings")
    )


@settings_bp.route(
    "/settings/password/verify",
    methods=["POST"]
)
@login_required
def verify_password_change():

    otp = request.form.get(
        "otp",
        ""
    ).strip()

    # -------------------------------------------------
    # Make sure there is a pending password change.
    # -------------------------------------------------

    if not session.get("password_change_pending"):
        flash(
            "There is no pending password change.",
            "error"
        )

        return redirect(
            url_for("settings.settings")
        )

    # -------------------------------------------------
    # Make sure an OTP was entered.
    # -------------------------------------------------

    if not otp:
        flash(
            "Please enter the verification code.",
            "error"
        )

        return redirect(
            url_for("settings.settings")
        )

    # -------------------------------------------------
    # Make sure the temporary password hash exists.
    # -------------------------------------------------

    pending_password_hash = session.get(
        "pending_password_hash"
    )

    if not pending_password_hash:

        session.pop(
            "password_change_pending",
            None
        )

        flash(
            "The password change request has expired. Please start again.",
            "error"
        )

        return redirect(
            url_for("settings.settings")
        )

    # -------------------------------------------------
    # Verify the OTP.
    # -------------------------------------------------

    verified, message = verify_code(
        user_id=current_user.id,
        purpose=VERIFICATION_PURPOSE_CHANGE_PASSWORD,
        otp=otp
    )

    if not verified:

        flash(
            message,
            "error"
        )

        return redirect(
            url_for("settings.settings")
        )

    # -------------------------------------------------
    # OTP is correct.
    # Apply the new password.
    # -------------------------------------------------

    current_user.password_hash = pending_password_hash

    db.session.commit()

    # -------------------------------------------------
    # Clear the temporary password-change state.
    # -------------------------------------------------

    session.pop(
        "pending_password_hash",
        None
    )

    session.pop(
        "password_change_pending",
        None
    )

    flash(
        "Your password has been changed successfully.",
        "success"
    )

    return redirect(
        url_for("settings.settings")
    )