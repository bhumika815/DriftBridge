from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user

from app import db
from app.models.conversation import Conversation
from app.models.message import Message


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

    # Make sure the logged-in user belongs to this conversation
    if (
        conversation.user1_id != current_user.id
        and conversation.user2_id != current_user.id
    ):
        return "Unauthorized", 403

    # Find the other person in the conversation
    if conversation.user1_id == current_user.id:
        other_user = conversation.user2
    else:
        other_user = conversation.user1

    # Handle sending a message
    if request.method == "POST":

        content = request.form.get("content", "").strip()

        if not content:
            return redirect(
                url_for(
                    "chat.chat",
                    conversation_id=conversation.id
                )
            )

        message = Message(
            conversation_id=conversation.id,
            sender_id=current_user.id,
            content=content
        )

        db.session.add(message)
        db.session.commit()

        return redirect(
            url_for(
                "chat.chat",
                conversation_id=conversation.id
            )
        )

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