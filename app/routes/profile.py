from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user

import cloudinary.uploader

from app import db
from app.services.reputation_service import get_user_trust_info
from app.services.ai_service import SUPPORTED_LANGUAGES
from app.services.cloudinary_service import configure_cloudinary


profile_bp = Blueprint("profile", __name__)


INTERESTS_LIST = [
    "Music",
    "Movies & TV",
    "Books & Reading",
    "Gaming",
    "Coding & Technology",
    "Cybersecurity",
    "Art & Design",
    "Photography",
    "Travel",
    "Sports",
    "Fitness",
    "Food & Cooking",
    "Fashion",
    "Nature",
    "Science",
    "History",
    "Languages",
    "Writing",
    "Business & Entrepreneurship",
    "Anime & Manga",
]


@profile_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        current_user.bio = request.form.get("bio", "").strip()
        current_user.country = request.form.get("country", "").strip()

        # Get multiple selected known/spoken languages.
        spoken_languages = request.form.getlist("languages_spoken")

        # Keep only valid languages.
        spoken_languages = [
            language
            for language in spoken_languages
            if language in SUPPORTED_LANGUAGES
        ]

        # Get multiple selected interests.
        selected_interests = request.form.getlist("interests")

        # Keep only valid interests.
        selected_interests = [
            interest
            for interest in selected_interests
            if interest in INTERESTS_LIST
        ]

        current_user.languages_spoken = ",".join(spoken_languages)
        current_user.interests = ",".join(selected_interests)

        # Learning / translation language remains single-select.
        preferred_language = request.form.get(
            "preferred_language",
            "en"
        ).strip()

        if preferred_language not in SUPPORTED_LANGUAGES:
            preferred_language = "en"

        current_user.preferred_language = preferred_language

        profile_image = request.files.get("profile_image")

        if profile_image and profile_image.filename:
            configure_cloudinary()

            upload_result = cloudinary.uploader.upload(
                profile_image,
                folder="driftbridge/profile_pictures",
                public_id=f"user_{current_user.id}_profile",
                overwrite=True,
                invalidate=True,
                resource_type="image",
            )

            current_user.profile_image_url = upload_result.get(
                "secure_url"
            )

        db.session.commit()

        return redirect(url_for("profile.profile"))

    trust_info = get_user_trust_info(current_user.id)

    return render_template(
        "profile.html",
        user=current_user,
        trust_info=trust_info,
        languages=SUPPORTED_LANGUAGES,
        interests_list=INTERESTS_LIST,
    )


@profile_bp.route("/profile/setup", methods=["GET", "POST"])
@login_required
def profile_setup():
    if request.method == "POST":
        from datetime import date

        date_of_birth = request.form.get(
            "date_of_birth",
            ""
        ).strip()

        gender = request.form.get(
            "gender",
            ""
        ).strip()

        country = request.form.get(
            "country",
            ""
        ).strip()

        bio = request.form.get(
            "bio",
            ""
        ).strip()

        spoken_languages = request.form.getlist(
            "languages_spoken"
        )

        selected_interests = request.form.getlist(
            "interests"
        )

        preferred_language = request.form.get(
            "preferred_language",
            "en"
        ).strip()

        # Get uploaded profile picture.
        profile_image = request.files.get("profile_image")

        # Upload profile picture to Cloudinary if one was selected.
        if profile_image and profile_image.filename:
            configure_cloudinary()

            upload_result = cloudinary.uploader.upload(
                profile_image,
                folder="driftbridge/profile_pictures",
                resource_type="image",
            )

            current_user.profile_image_url = upload_result.get(
                "secure_url"
            )

        # Validate date of birth.
        try:
            dob = date.fromisoformat(date_of_birth)
        except ValueError:
            return render_template(
                "profile_setup.html",
                user=current_user,
                languages=SUPPORTED_LANGUAGES,
                interests_list=INTERESTS_LIST,
                error="Please enter a valid date of birth.",
            )

        # Prevent a future date of birth.
        if dob > date.today():
            return render_template(
                "profile_setup.html",
                user=current_user,
                languages=SUPPORTED_LANGUAGES,
                interests_list=INTERESTS_LIST,
                error="Date of birth cannot be in the future.",
            )

        # Calculate age automatically.
        today = date.today()
        age = today.year - dob.year

        if (today.month, today.day) < (dob.month, dob.day):
            age -= 1

        # Validate gender.
        allowed_genders = {
            "Female",
            "Male",
            "Other"
        }

        if gender not in allowed_genders:
            return render_template(
                "profile_setup.html",
                user=current_user,
                languages=SUPPORTED_LANGUAGES,
                interests_list=INTERESTS_LIST,
                error="Please select a valid gender.",
            )

        # Validate learning/translation language.
        if preferred_language not in SUPPORTED_LANGUAGES:
            preferred_language = "en"

        # Keep only valid spoken languages.
        spoken_languages = [
            language
            for language in spoken_languages
            if language in SUPPORTED_LANGUAGES
        ]

        # Keep only valid interests.
        selected_interests = [
            interest
            for interest in selected_interests
            if interest in INTERESTS_LIST
        ]

        # Save profile information.
        current_user.date_of_birth = dob
        current_user.age = age
        current_user.gender = gender
        current_user.country = country
        current_user.bio = bio
        current_user.languages_spoken = ",".join(
            spoken_languages
        )
        current_user.interests = ",".join(
            selected_interests
        )
        current_user.preferred_language = preferred_language

        db.session.commit()

        return redirect(url_for("profile.profile"))

    return render_template(
        "profile_setup.html",
        user=current_user,
        languages=SUPPORTED_LANGUAGES,
        interests_list=INTERESTS_LIST,
    )

@profile_bp.route("/profile/user/<int:user_id>")
@login_required
def user_profile(user_id):
    from app.models.user import User
    from app.models.story import Story
    from app.models.user_block import UserBlock
    from app.models.conversation import Conversation

    user = db.session.get(User, user_id)

    if user is None:
        return "User not found", 404

    diaries = Story.query.filter_by(
        user_id=user.id
    ).order_by(
        Story.created_at.desc()
    ).all()

    trust_info = get_user_trust_info(user.id)

    # Check whether the current user has blocked this user.
    block_exists = UserBlock.query.filter_by(
        blocker_id=current_user.id,
        blocked_id=user.id
    ).first() is not None

    # Check whether a conversation already exists
    # between the current user and this profile user.
    conversation = Conversation.query.filter(
        db.or_(
            db.and_(
                Conversation.user1_id == current_user.id,
                Conversation.user2_id == user.id
            ),
            db.and_(
                Conversation.user1_id == user.id,
                Conversation.user2_id == current_user.id
            )
        )
    ).first()

    conversation_exists = conversation is not None

    conversation_id = (
        conversation.id
        if conversation is not None
        else None
    )

    return render_template(
        "user_profile.html",
        user=user,
        diaries=diaries,
        trust_info=trust_info,
        block_exists=block_exists,
        conversation_exists=conversation_exists,
        conversation_id=conversation_id
    )