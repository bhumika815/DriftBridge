from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user

from app import db
from app.services.reputation_service import get_user_trust_info


profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        current_user.bio = request.form.get("bio", "").strip()
        current_user.interests = request.form.get("interests", "").strip()
        current_user.preferred_language = request.form.get("preferred_language", "en")

        db.session.commit()

        return redirect(url_for("profile.profile"))

    trust_info = get_user_trust_info(current_user.id)
    return render_template("profile.html", user=current_user, trust_info=trust_info)