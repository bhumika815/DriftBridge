from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_user, login_required, logout_user

from app import db, bcrypt
from app.models.user import User


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():

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
            password_hash=password_hash
        )

        db.session.add(user)
        db.session.commit()

        flash("Registration successful. You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(
          user.password_hash,
          password
    ):
         login_user(user)

        return redirect(url_for("auth.dashboard"))
        flash("Invalid email or password.", "error")
        return redirect(url_for("auth.login"))

    return render_template("login.html")


@auth_bp.route("/dashboard")
@login_required
def dashboard():

    from app.models.bottle import Bottle
    from app.models.conversation import Conversation

    bottles_thrown = Bottle.query.filter_by(
        sender_id=current_user.id
    ).count()

    bottles_kept = Bottle.query.filter_by(
        receiver_id=current_user.id
    ).count()

    connection_count = Conversation.query.filter(
        (
            (Conversation.user1_id == current_user.id)
        )
        |
        (
            (Conversation.user2_id == current_user.id)
        )
    ).count()

    return render_template(
        "dashboard.html",
        bottles_thrown=bottles_thrown,
        bottles_kept=bottles_kept,
        connection_count=connection_count
    )


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()

    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))