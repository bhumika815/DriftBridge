from flask import Blueprint, render_template, request, redirect, url_for, abort, flash
from flask_login import login_required, current_user

from app import db
from app.models.conversation import Conversation
from app.models.message import Message
from app.services import check_content_safety
from app.services.reputation_service import award_points


chat_bp = Blueprint(
    "chat",
    __name__,
    url_prefix="/chat"
)


@chat_bp.route("/conversations")
@login_required
def conversations():

    conversations = Conversation.query.filter(
        (Conversation.user1_id == current_user.id)
        |
        (Conversation.user2_id == current_user.id)
    ).order_by(
        Conversation.created_at.desc()
    ).all()

    return render_template(
        "conversations.html",
        conversations=conversations
    )


@chat_bp.route("/<int:conversation_id>", methods=["GET", "POST"])
@login_required
def chat(conversation_id):

    conversation = Conversation.query.get_or_404(conversation_id)

    # Authorization: only participants can access this conversation.
    if (
        conversation.user1_id != current_user.id
        and conversation.user2_id != current_user.id
    ):
        abort(403)

    # Find the other person in the conversation
    if conversation.user1_id == current_user.id:
        other_user = conversation.user2
    else:
        other_user = conversation.user1

    # Handle sending a message (HTTP fallback — same rules as Socket.IO)
    if request.method == "POST":

        content = request.form.get("content", "").strip()

        if not content:
            flash("Message cannot be empty.", "error")
            return redirect(
                url_for("chat.chat", conversation_id=conversation.id)
            )
        if len(content) > 2000:
            flash(
                "Message is too long. Maximum 2000 characters allowed.",
                "error"
            )
            return redirect(
                url_for("chat.chat", conversation_id=conversation.id)
            )

        # Content moderation
        is_safe, safety_reason = check_content_safety(content)
        if not is_safe:
            flash(
                "Your message contains inappropriate content and cannot "
                "be sent.",
                "error"
            )
            return redirect(
                url_for("chat.chat", conversation_id=conversation.id)
            )

        sender_language = current_user.preferred_language or 'en'

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
        emit(
            "message_error",
            {
                "error": "Message could not be sent. Please try again."
            }
        )
        return

    # --- Determine the other participant ---

    # Get all messages in this conversation
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
