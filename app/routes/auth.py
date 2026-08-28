import logging

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_user, login_required, logout_user

from app import db, bcrypt
from app.models.user import User
from app.services.ai_service import SUPPORTED_LANGUAGES


logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:
        return redirect(url_for("auth.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not email or not password:
            flash("All fields are required.", "error")
            return redirect(url_for("auth.register"))

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("auth.register"))

        preferred_language = request.form.get("preferred_language", "en")
        if preferred_language not in SUPPORTED_LANGUAGES:
            preferred_language = "en"

        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            flash("Username or email already exists.", "error")
            return redirect(url_for("auth.register"))

        password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            preferred_language=preferred_language
        )

        db.session.add(user)
        db.session.commit()

        logger.info("New user registered: id=%s username=%s", user.id, user.username)

        flash("Registration successful. You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template(
        "register.html",
        languages=SUPPORTED_LANGUAGES
    )


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("auth.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter both email and password.", "error")
            return redirect(url_for("auth.login"))

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            logger.info("User logged in: id=%s username=%s", user.id, user.username)
            return redirect(url_for("auth.dashboard"))

        flash("Invalid email or password.", "error")
        return redirect(url_for("auth.login"))

    return render_template("login.html")


@auth_bp.route("/dashboard")
@login_required
def dashboard():

    from app.models.bottle import Bottle
    from app.models.conversation import Conversation
    from app.models.message import Message
    from app.models.story import Story
    from app.services.reputation_service import get_user_trust_info
    from datetime import datetime

    bottles_thrown = Bottle.query.filter_by(
        sender_id=current_user.id
    ).count()

    bottles_kept = Bottle.query.filter_by(
        receiver_id=current_user.id
    ).count()

    connection_count = Conversation.query.filter(
        (Conversation.user1_id == current_user.id)
        | (Conversation.user2_id == current_user.id)
    ).count()

    conversations = Conversation.query.filter(
        (Conversation.user1_id == current_user.id)
        | (Conversation.user2_id == current_user.id)
    ).order_by(Conversation.created_at.desc()).limit(5).all()

    recent_conversations = []
    for conv in conversations:
        other_user = conv.user2 if conv.user1_id == current_user.id else conv.user1
        last_msg = Message.query.filter_by(
            conversation_id=conv.id
        ).order_by(Message.created_at.desc()).first()
        recent_conversations.append({
            "conversation": conv,
            "other_user": other_user,
            "last_message": last_msg
        })

    connection_ids = set()
    for conv in conversations:
        if conv.user1_id == current_user.id:
            connection_ids.add(conv.user2_id)
        else:
            connection_ids.add(conv.user1_id)

    active_stories = []
    if connection_ids:
        active_stories = Story.query.filter(
            Story.user_id.in_(connection_ids),
            Story.expires_at > datetime.utcnow()
        ).order_by(Story.created_at.desc()).limit(8).all()

    trust_info = get_user_trust_info(current_user.id)

    return render_template(
        "dashboard.html",
        bottles_thrown=bottles_thrown,
        bottles_kept=bottles_kept,
        connection_count=connection_count,
        recent_conversations=recent_conversations,
        active_stories=active_stories,
        trust_info=trust_info
    )


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))
