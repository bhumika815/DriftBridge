from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    abort,
    flash,
    jsonify
)

from flask_login import login_required, current_user

from app import db, socketio
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user_block import UserBlock
from app.services import check_content_safety
from app.services.reputation_service import award_points
from app.services.cloudinary_service import upload_chat_image


chat_bp = Blueprint(
    "chat",
    __name__,
    url_prefix="/chat"
)


# --------------------------------------------------------------
# Conversations
# --------------------------------------------------------------

@chat_bp.route("/conversations")
@login_required
def conversations():

    conversations = Conversation.query.filter(
        (Conversation.user1_id == current_user.id)
        | (Conversation.user2_id == current_user.id)
    ).order_by(
        Conversation.created_at.desc()
    ).all()

    conversation_data = []

    for conversation in conversations:

        if conversation.user1_id == current_user.id:
            other_user = conversation.user2
        else:
            other_user = conversation.user1

        messages = Message.query.filter_by(
            conversation_id=conversation.id
        ).order_by(
            Message.created_at.desc()
        ).all()

        message_count = len(messages)

        latest_message = (
            messages[0]
            if messages
            else None
        )

        if conversation.user1_id == current_user.id:
            current_user_id = conversation.user1_id
            other_user_id = conversation.user2_id
        else:
            current_user_id = conversation.user2_id
            other_user_id = conversation.user1_id

        from app.models.bottle import Bottle

        accepted_bottle = Bottle.query.filter(
            Bottle.status == "claimed",
            (
                (
                    (Bottle.sender_id == current_user_id)
                    &
                    (Bottle.receiver_id == other_user_id)
                )
                |
                (
                    (Bottle.sender_id == other_user_id)
                    &
                    (Bottle.receiver_id == current_user_id)
                )
            )
        ).order_by(
            Bottle.claimed_at.desc()
        ).first()

        conversation_data.append({
            "conversation": conversation,
            "other_user": other_user,
            "message_count": message_count,
            "latest_message": latest_message,
            "accepted_bottle": accepted_bottle
        })

    return render_template(
        "conversations.html",
        conversation_data=conversation_data
    )


# --------------------------------------------------------------
# Block User
# --------------------------------------------------------------

@chat_bp.route(
    "/block/<int:user_id>",
    methods=["POST"]
)
@login_required
def block_user(user_id):

    # A user cannot block themselves.
    if user_id == current_user.id:
        return jsonify({
            "success": False,
            "message": "You cannot block yourself."
        }), 400

    # Make sure the user exists.
    user = db.session.get(
        User,
        user_id
    )

    if user is None:
        return jsonify({
            "success": False,
            "message": "User not found."
        }), 404

    # Check whether this user is already blocked.
    existing_block = UserBlock.query.filter_by(
        blocker_id=current_user.id,
        blocked_id=user.id
    ).first()

    if existing_block:
        return redirect(
            url_for(
                "profile.user_profile",
                user_id=user.id
            )
        )

    # Create the block.
    block = UserBlock(
        blocker_id=current_user.id,
        blocked_id=user.id
    )

    db.session.add(block)

    try:

        db.session.commit()

    except Exception:

        db.session.rollback()

        return jsonify({
            "success": False,
            "message": (
                "Could not block this user. "
                "Please try again."
            )
        }), 500

    return redirect(
        url_for(
            "profile.user_profile",
            user_id=user.id
        )
    )


# --------------------------------------------------------------
# Unblock User
# --------------------------------------------------------------

@chat_bp.route(
    "/unblock/<int:user_id>",
    methods=["POST"]
)
@login_required
def unblock_user(user_id):

    # A user cannot unblock themselves.
    if user_id == current_user.id:
        return jsonify({
            "success": False,
            "message": "You cannot unblock yourself."
        }), 400

    # Make sure the user exists.
    user = db.session.get(
        User,
        user_id
    )

    if user is None:
        return jsonify({
            "success": False,
            "message": "User not found."
        }), 404

    # Find the block created by the current user.
    existing_block = UserBlock.query.filter_by(
        blocker_id=current_user.id,
        blocked_id=user.id
    ).first()

    # If there is no block, there is nothing to remove.
    if existing_block is None:
        return redirect(
            url_for(
                "profile.user_profile",
                user_id=user.id
            )
        )

    db.session.delete(existing_block)

    try:

        db.session.commit()

    except Exception:

        db.session.rollback()

        return jsonify({
            "success": False,
            "message": (
                "Could not unblock this user. "
                "Please try again."
            )
        }), 500

    flash(
        "User unblocked successfully.",
        "success"
    )

    return redirect(
        url_for(
            "profile.user_profile",
            user_id=user.id
        )
    )


# --------------------------------------------------------------
# Report User
# --------------------------------------------------------------

@chat_bp.route(
    "/report/<int:user_id>",
    methods=["POST"]
)
@login_required
def report_user(user_id):

    from app.models.user_report import UserReport

    # A user cannot report themselves.
    if user_id == current_user.id:
        return jsonify({
            "success": False,
            "message": "You cannot report yourself."
        }), 400

    # Make sure the user exists.
    user = db.session.get(
        User,
        user_id
    )

    if user is None:
        return jsonify({
            "success": False,
            "message": "User not found."
        }), 404

    reason = request.form.get(
        "reason",
        ""
    ).strip()

    details = request.form.get(
        "details",
        ""
    ).strip()

    # A report must have a reason.
    if not reason:
        return jsonify({
            "success": False,
            "message": (
                "Please provide a reason for the report."
            )
        }), 400

    report = UserReport(
        reporter_id=current_user.id,
        reported_user_id=user.id,
        reason=reason,
        details=details or None,
        status="pending"
    )

    db.session.add(report)

    try:

        db.session.commit()

    except Exception:

        db.session.rollback()

        return jsonify({
            "success": False,
            "message": (
                "Could not submit the report. "
                "Please try again."
            )
        }), 500

    flash(
        "Report submitted successfully.",
        "success"
    )

    return redirect(
        url_for(
            "profile.user_profile",
            user_id=user.id
        )
    )


# --------------------------------------------------------------
# Chat Image Upload
# --------------------------------------------------------------

@chat_bp.route(
    "/<int:conversation_id>/upload-image",
    methods=["POST"]
)
@login_required
def upload_image(conversation_id):

    conversation = Conversation.query.get_or_404(
        conversation_id
    )

    # ----------------------------------------------------------
    # Authorization
    # ----------------------------------------------------------

    if (
        conversation.user1_id != current_user.id
        and conversation.user2_id != current_user.id
    ):
        abort(403)

    # Find the other person.
    if conversation.user1_id == current_user.id:
        other_user = conversation.user2
    else:
        other_user = conversation.user1

    # ----------------------------------------------------------
    # Block protection
    # ----------------------------------------------------------

    active_block = UserBlock.query.filter(
        (
            (UserBlock.blocker_id == current_user.id)
            &
            (UserBlock.blocked_id == other_user.id)
        )
        |
        (
            (UserBlock.blocker_id == other_user.id)
            &
            (UserBlock.blocked_id == current_user.id)
        )
    ).first()

    if active_block:
        abort(403)

    # ----------------------------------------------------------
    # Validate uploaded file
    # ----------------------------------------------------------

    image_file = request.files.get(
        "image"
    )

    if image_file is None:
        return jsonify({
            "success": False,
            "message": "No image was selected."
        }), 400

    if not image_file.filename:
        return jsonify({
            "success": False,
            "message": "No image was selected."
        }), 400

    # Allowed image MIME types.
    allowed_types = {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif"
    }

    if image_file.mimetype not in allowed_types:
        return jsonify({
            "success": False,
            "message": (
                "Invalid image format. "
                "Please use JPG, PNG, WEBP, or GIF."
            )
        }), 400

    # ----------------------------------------------------------
    # File size validation
    # ----------------------------------------------------------

    image_file.seek(
        0,
        2
    )

    file_size = image_file.tell()

    image_file.seek(0)

    max_size = 10 * 1024 * 1024

    if file_size > max_size:
        return jsonify({
            "success": False,
            "message": (
                "Image is too large. "
                "Maximum size is 10 MB."
            )
        }), 400

    # ----------------------------------------------------------
    # Upload and save message
    # ----------------------------------------------------------

    try:

        # Upload image to Cloudinary.
        image_url = upload_chat_image(
            image_file
        )

        sender_language = (
            current_user.preferred_language
            or "en"
        )

        # Create image message.
        message = Message(
            conversation_id=conversation.id,
            sender_id=current_user.id,
            content="[Image]",
            original_language=sender_language,
            message_type="image",
            media_url=image_url
        )

        db.session.add(message)

        db.session.commit()

        # ------------------------------------------------------
        # REAL-TIME IMAGE DELIVERY
        # ------------------------------------------------------
        #
        # Image messages are uploaded through HTTP instead of
        # the normal Socket.IO send_message event.
        #
        # Therefore we explicitly broadcast the saved message
        # to the conversation room.
        # ------------------------------------------------------
         
        print(
            f"[IMAGE SOCKET] Broadcasting image message "
            f"{message.id} to conversation_{conversation.id}"
        )
        
        socketio.emit(
            "new_message",
            {
                "message_id": message.id,
                "client_message_id": None,
                "sender_id": current_user.id,
                "sender": current_user.username,
                "content": message.content,
                "original_language": sender_language,
                "message_type": message.message_type,
                "media_url": message.media_url,
                "created_at": message.created_at.strftime(
                    "%d %b %Y, %I:%M %p"
                )
            },
            room=f"conversation_{conversation.id}"
        )

        # ------------------------------------------------------
        # Reputation
        # ------------------------------------------------------

        try:

            award_points(
                current_user.id,
                "message_sent"
            )

        except Exception:

            # The message has already been successfully saved
            # and delivered, so reputation failure must not make
            # the image upload appear to have failed.
            db.session.rollback()

        # ------------------------------------------------------
        # Return successful response
        # ------------------------------------------------------

        return jsonify({
            "success": True,
            "message": {
                "id": message.id,
                "conversation_id": message.conversation_id,
                "sender_id": message.sender_id,
                "content": message.content,
                "message_type": message.message_type,
                "media_url": message.media_url,
                "created_at": (
                    message.created_at.isoformat()
                )
            }
        })

    except Exception:

        db.session.rollback()

        return jsonify({
            "success": False,
            "message": (
                "Image upload failed. "
                "Please try again."
            )
        }), 500


# --------------------------------------------------------------
# Chat
# --------------------------------------------------------------

@chat_bp.route(
    "/<int:conversation_id>",
    methods=["GET", "POST"]
)
@login_required
def chat(conversation_id):

    conversation = Conversation.query.get_or_404(
        conversation_id
    )

    # ----------------------------------------------------------
    # Authorization
    # ----------------------------------------------------------

    if (
        conversation.user1_id != current_user.id
        and conversation.user2_id != current_user.id
    ):
        abort(403)

    # Find the other person.
    if conversation.user1_id == current_user.id:
        other_user = conversation.user2
    else:
        other_user = conversation.user1

    # ----------------------------------------------------------
    # Block protection
    # ----------------------------------------------------------

    active_block = UserBlock.query.filter(
        (
            (UserBlock.blocker_id == current_user.id)
            &
            (UserBlock.blocked_id == other_user.id)
        )
        |
        (
            (UserBlock.blocker_id == other_user.id)
            &
            (UserBlock.blocked_id == current_user.id)
        )
    ).first()

    if active_block:
        abort(403)

    # ----------------------------------------------------------
    # HTTP fallback message sending
    # ----------------------------------------------------------

    if request.method == "POST":

        content = request.form.get(
            "content",
            ""
        ).strip()

        if not content:
            flash(
                "Message cannot be empty.",
                "error"
            )

            return redirect(
                url_for(
                    "chat.chat",
                    conversation_id=conversation.id
                )
            )

        if len(content) > 2000:
            flash(
                "Message is too long. "
                "Maximum 2000 characters allowed.",
                "error"
            )

            return redirect(
                url_for(
                    "chat.chat",
                    conversation_id=conversation.id
                )
            )

        # Content moderation.
        is_safe, safety_reason = check_content_safety(
            content
        )

        if not is_safe:

            flash(
                "Your message contains inappropriate content "
                "and cannot be sent.",
                "error"
            )

            return redirect(
                url_for(
                    "chat.chat",
                    conversation_id=conversation.id
                )
            )

        sender_language = (
            current_user.preferred_language
            or "en"
        )

        message = Message(
            conversation_id=conversation.id,
            sender_id=current_user.id,
            content=content,
            original_language=sender_language
        )

        db.session.add(message)

        try:

            db.session.commit()

        except Exception:

            db.session.rollback()

            flash(
                "Message could not be sent. "
                "Please try again.",
                "error"
            )

            return redirect(
                url_for(
                    "chat.chat",
                    conversation_id=conversation.id
                )
            )

        award_points(
            current_user.id,
            "message_sent"
        )

        return redirect(
            url_for(
                "chat.chat",
                conversation_id=conversation.id
            )
        )

    # ----------------------------------------------------------
    # Load messages
    # ----------------------------------------------------------

    messages = Message.query.filter_by(
        conversation_id=conversation.id
    ).order_by(
        Message.created_at.asc()
    ).all()

    return render_template(
        "chat.html",
        conversation=conversation,
        other_user=other_user,
        messages=messages
    )