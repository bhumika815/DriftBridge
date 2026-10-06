import logging

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from flask_login import (
    current_user,
    login_user,
    login_required,
    logout_user
)

from app import db, bcrypt
from app.models.user import User
from app.services.ai_service import SUPPORTED_LANGUAGES
from app.services.otp_service import send_email_verification_code
from app.services.verification_service import (
    verify_code,
    VERIFICATION_PURPOSE_RESET_PASSWORD
)


logger = logging.getLogger(__name__)


auth_bp = Blueprint("auth", __name__)


# =========================================================
# REGISTER
# =========================================================

@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:
        return redirect(url_for("bottle.pool"))

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not email or not password:
            flash(
                "All fields are required.",
                "error"
            )
            return redirect(url_for("auth.register"))

        if password != confirm_password:
            flash(
                "Passwords do not match.",
                "error"
            )
            return redirect(url_for("auth.register"))

        preferred_language = request.form.get(
            "preferred_language",
            "en"
        )

        if preferred_language not in SUPPORTED_LANGUAGES:
            preferred_language = "en"

        existing_user = User.query.filter(
            (User.username == username)
            | (User.email == email)
        ).first()

        if existing_user:
            flash(
                "Username or email already exists.",
                "error"
            )
            return redirect(url_for("auth.register"))

        password_hash = bcrypt.generate_password_hash(
            password
        ).decode("utf-8")

        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            preferred_language=preferred_language
        )

        db.session.add(user)
        db.session.commit()

        logger.info(
            "New user registered: id=%s username=%s",
            user.id,
            user.username
        )

        flash(
            "Registration successful. You can now log in.",
            "success"
        )

        return redirect(url_for("auth.login"))

    return render_template(
        "register.html",
        languages=SUPPORTED_LANGUAGES
    )


# =========================================================
# LOGIN
# =========================================================

@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("bottle.pool"))

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        if not email or not password:
            flash(
                "Please enter both email and password.",
                "error"
            )
            return redirect(
                url_for("auth.login")
            )

        user = User.query.filter_by(
            email=email
        ).first()

        logger.info(
            "LOGIN CHECK: email=%s user_found=%s password_present=%s",
            email,
            bool(user),
            bool(password)
        )

        if user:

            password_matches = bcrypt.check_password_hash(
                user.password_hash,
                password
            )

            logger.info(
                "LOGIN PASSWORD CHECK: user_id=%s matches=%s",
                user.id,
                password_matches
            )

        else:

            password_matches = False

        if user and password_matches:

            # Check whether the account has been suspended
            # by an administrator.

            if user.is_suspended:

                flash(
                    "Your account has been suspended.",
                    "error"
                )

                return redirect(
                    url_for("auth.login")
                )

            login_user(user)

            logger.info(
                "PROFILE CHECK: dob=%s gender=%s country=%s languages=%s interests=%s",
                user.date_of_birth,
                user.gender,
                user.country,
                user.languages_spoken,
                user.interests
            )

            logger.info(
                "User logged in: id=%s username=%s",
                user.id,
                user.username
            )

            # Check whether the user has completed
            # the required profile setup.

            profile_incomplete = (
                user.date_of_birth is None
                or not user.gender
                or not user.country
                or not user.languages_spoken
                or not user.interests
            )

            if profile_incomplete:

                return redirect(
                    url_for("profile.profile_setup")
                )

            return redirect(
                url_for("bottle.pool")
            )

        flash(
            "Invalid email or password.",
            "error"
        )

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "login.html"
    )
# =========================================================
# FORGOT PASSWORD
# =========================================================

@auth_bp.route(
    "/forgot-password",
    methods=["GET", "POST"]
)
def forgot_password():

    if current_user.is_authenticated:
        return redirect(url_for("bottle.pool"))

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        if not email:
            flash(
                "Please enter your email address.",
                "error"
            )

            return redirect(
                url_for("auth.forgot_password")
            )

        user = User.query.filter_by(
            email=email
        ).first()

        # Do not reveal whether an email address
        # belongs to an existing account.
        if user is None:

            flash(
                "If an account exists for this email address, "
                "a verification code has been sent.",
                "success"
            )

            return redirect(
                url_for("auth.forgot_password")
            )

        sent, message = send_email_verification_code(
            user_id=user.id,
            email=user.email,
            purpose=VERIFICATION_PURPOSE_RESET_PASSWORD
        )

        if not sent:

            flash(
                message,
                "error"
            )

            return redirect(
                url_for("auth.forgot_password")
            )

        flash(
            "A verification code has been sent to your email address.",
            "success"
        )

        return redirect(
            url_for(
                "auth.reset_password_verify",
                email=user.email
            )
        )

    return render_template(
        "forgot_password.html"
    )


# =========================================================
# RESET PASSWORD - OTP VERIFICATION
# =========================================================

@auth_bp.route(
    "/reset-password/verify",
    methods=["GET", "POST"]
)
def reset_password_verify():

    if current_user.is_authenticated:
        return redirect(url_for("bottle.pool"))

    email = request.args.get(
        "email",
        ""
    ).strip().lower()

    if not email:

        flash(
            "Please start the password reset process again.",
            "error"
        )

        return redirect(
            url_for("auth.forgot_password")
        )

    user = User.query.filter_by(
        email=email
    ).first()

    if user is None:

        flash(
            "Please start the password reset process again.",
            "error"
        )

        return redirect(
            url_for("auth.forgot_password")
        )

    if request.method == "POST":

        otp = request.form.get(
            "otp",
            ""
        ).strip()

        if not otp:

            flash(
                "Please enter the verification code.",
                "error"
            )

            return redirect(
                url_for(
                    "auth.reset_password_verify",
                    email=email
                )
            )

        verified, message = verify_code(
            user_id=user.id,
            purpose=VERIFICATION_PURPOSE_RESET_PASSWORD,
            otp=otp
        )

        if not verified:

            flash(
                message,
                "error"
            )

            return redirect(
                url_for(
                    "auth.reset_password_verify",
                    email=email
                )
            )

        session["password_reset_user_id"] = user.id
        session["password_reset_verified"] = True

        return redirect(
            url_for(
                "auth.reset_password"
            )
        )

    return render_template(
        "reset_password_verify.html",
        email=email
    )


# =========================================================
# RESET PASSWORD - SET NEW PASSWORD
# =========================================================

@auth_bp.route(
    "/reset-password",
    methods=["GET", "POST"]
)
def reset_password():

    if current_user.is_authenticated:
        return redirect(url_for("bottle.pool"))

    if not session.get("password_reset_verified"):

        flash(
            "Please verify your email before resetting your password.",
            "error"
        )

        return redirect(
            url_for("auth.forgot_password")
        )

    user_id = session.get(
        "password_reset_user_id"
    )

    if not user_id:

        session.pop(
            "password_reset_verified",
            None
        )

        flash(
            "Your password reset session has expired. "
            "Please start again.",
            "error"
        )

        return redirect(
            url_for("auth.forgot_password")
        )

    user = db.session.get(
        User,
        user_id
    )

    if user is None:

        session.pop(
            "password_reset_user_id",
            None
        )

        session.pop(
            "password_reset_verified",
            None
        )

        flash(
            "Your password reset session is no longer valid.",
            "error"
        )

        return redirect(
            url_for("auth.forgot_password")
        )

    if request.method == "POST":

        new_password = request.form.get(
            "new_password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if not new_password or not confirm_password:

            flash(
                "Both password fields are required.",
                "error"
            )

            return redirect(
                url_for("auth.reset_password")
            )

        if new_password != confirm_password:

            flash(
                "Passwords do not match.",
                "error"
            )

            return redirect(
                url_for("auth.reset_password")
            )

        if len(new_password) < 8:

            flash(
                "New password must be at least 8 characters long.",
                "error"
            )

            return redirect(
                url_for("auth.reset_password")
            )

        if bcrypt.check_password_hash(
            user.password_hash,
            new_password
        ):

            flash(
                "Your new password must be different "
                "from your previous password.",
                "error"
            )

            return redirect(
                url_for("auth.reset_password")
            )

        user.password_hash = (
            bcrypt.generate_password_hash(
                new_password
            ).decode("utf-8")
        )

        db.session.commit()

        # The reset authorization must be single-use.
        session.pop(
            "password_reset_user_id",
            None
        )

        session.pop(
            "password_reset_verified",
            None
        )

        flash(
            "Your password has been reset successfully. "
            "You can now log in.",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "reset_password.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@auth_bp.route("/logout")
@login_required
def logout():

    logout_user()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(
        url_for("auth.login")
    )


# =========================================================
# DELETE ACCOUNT
# =========================================================

@auth_bp.route(
    "/delete-account",
    methods=["POST"]
)
@login_required
def delete_account():

    user_id = current_user.id
    username = current_user.username

    try:

        from app.models.bottle import Bottle
        from app.models.conversation import Conversation
        from app.models.message import Message

        from app.models.story import (
            Story,
            StoryView,
            StoryLike,
            StoryComment
        )

        from app.models.user_block import UserBlock
        from app.models.content_flag import ContentFlag

        # -------------------------------------------------
        # 1. Find conversations belonging to this user.
        # -------------------------------------------------

        conversations = Conversation.query.filter(
            (Conversation.user1_id == user_id)
            | (Conversation.user2_id == user_id)
        ).all()

        conversation_ids = [
            conversation.id
            for conversation in conversations
        ]

        # -------------------------------------------------
        # 2. Delete messages belonging to those
        #    conversations.
        # -------------------------------------------------

        if conversation_ids:

            Message.query.filter(
                Message.conversation_id.in_(conversation_ids)
            ).delete(
                synchronize_session=False
            )

        Message.query.filter_by(
            sender_id=user_id
        ).delete(
            synchronize_session=False
        )

        # -------------------------------------------------
        # 3. Delete conversations involving this user.
        # -------------------------------------------------

        if conversation_ids:

            Conversation.query.filter(
                Conversation.id.in_(conversation_ids)
            ).delete(
                synchronize_session=False
            )

        # -------------------------------------------------
        # 4. Delete Bottles involving this user.
        # -------------------------------------------------

        Bottle.query.filter(
            (Bottle.sender_id == user_id)
            | (Bottle.receiver_id == user_id)
            | (Bottle.target_user_id == user_id)
        ).delete(
            synchronize_session=False
        )

        # -------------------------------------------------
        # 5. Delete Diary interactions made by this user.
        # -------------------------------------------------

        StoryView.query.filter_by(
            user_id=user_id
        ).delete(
            synchronize_session=False
        )

        StoryLike.query.filter_by(
            user_id=user_id
        ).delete(
            synchronize_session=False
        )

        StoryComment.query.filter_by(
            user_id=user_id
        ).delete(
            synchronize_session=False
        )

        # -------------------------------------------------
        # 6. Find the user's Diaries.
        # -------------------------------------------------

        stories = Story.query.filter_by(
            user_id=user_id
        ).all()

        story_ids = [
            story.id
            for story in stories
        ]

        # -------------------------------------------------
        # 7. Delete interactions belonging to the user's
        #    own Diaries.
        # -------------------------------------------------

        if story_ids:

            StoryView.query.filter(
                StoryView.story_id.in_(story_ids)
            ).delete(
                synchronize_session=False
            )

            StoryLike.query.filter(
                StoryLike.story_id.in_(story_ids)
            ).delete(
                synchronize_session=False
            )

            StoryComment.query.filter(
                StoryComment.story_id.in_(story_ids)
            ).delete(
                synchronize_session=False
            )

        # -------------------------------------------------
        # 8. Delete the user's Diaries.
        # -------------------------------------------------

        Story.query.filter_by(
            user_id=user_id
        ).delete(
            synchronize_session=False
        )

        # -------------------------------------------------
        # 9. Delete every block involving this user.
        # -------------------------------------------------

        UserBlock.query.filter(
            (UserBlock.blocker_id == user_id)
            | (UserBlock.blocked_id == user_id)
        ).delete(
            synchronize_session=False
        )

        # -------------------------------------------------
        # 10. Delete ContentFlags created by this user.
        # -------------------------------------------------

        ContentFlag.query.filter_by(
            user_id=user_id
        ).delete(
            synchronize_session=False
        )

        # -------------------------------------------------
        # 11. Delete review references involving this user.
        # -------------------------------------------------

        ContentFlag.query.filter_by(
            reviewed_by=user_id
        ).delete(
            synchronize_session=False
        )

        # -------------------------------------------------
        # 12. Delete the actual User record.
        # -------------------------------------------------

        user = db.session.get(
            User,
            user_id
        )

        if user is not None:
            db.session.delete(user)

        # -------------------------------------------------
        # 13. Commit the entire deletion as one transaction.
        # -------------------------------------------------

        db.session.commit()

        # -------------------------------------------------
        # 14. End the Flask-Login session.
        # -------------------------------------------------

        logout_user()

        logger.info(
            "User account deleted: id=%s username=%s",
            user_id,
            username
        )

        flash(
            "Your account has been permanently deleted.",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )

    except Exception:

        db.session.rollback()

        logger.exception(
            "Account deletion failed: id=%s username=%s",
            user_id,
            username
        )

        flash(
            "We could not delete your account. "
            "No changes were made.",
            "error"
        )

        return redirect(
            url_for("profile.profile")
        )