from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user

from app import db


profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        current_user.bio = request.form.get("bio", "").strip()
        current_user.interests = request.form.get("interests", "").strip()

        db.session.commit()

        return redirect(url_for("profile.profile"))

    return render_template("profile.html", user=current_user)