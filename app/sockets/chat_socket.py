from flask_login import current_user
from flask_socketio import emit, join_room

from app import db, socketio
from app.models.conversation import Conversation
from app.models.message import Message


@socketio.on("join_conversation")
def handle_join_conversation(data):

    if not current_user.is_authenticated:
        return

    conversation_id = data.get("conversation_id")

    if not conversation_id:
        return

    conversation = db.session.get(
        Conversation,
        int(conversation_id)
    )

    if conversation is None:
        return

    if (
        conversation.user1_id != current_user.id
        and conversation.user2_id != current_user.id
    ):
        return

    join_room(f"conversation_{conversation.id}")


@socketio.on("send_message")
def handle_send_message(data):

    if not current_user.is_authenticated:
        return

    conversation_id = data.get("conversation_id")
    content = data.get("content", "").strip()

    if not conversation_id or not content:
        return

    conversation = db.session.get(
        Conversation,
        int(conversation_id)
    )

    if conversation is None:
        return

    if (
        conversation.user1_id != current_user.id
        and conversation.user2_id != current_user.id
    ):
        return

    message = Message(
        conversation_id=conversation.id,
        sender_id=current_user.id,
        content=content
    )

    db.session.add(message)
    db.session.commit()

    emit(
        "new_message",
        {
            "sender": current_user.username,
            "content": message.content,
            "created_at": message.created_at.strftime("%H:%M")
        },
        room=f"conversation_{conversation.id}"
    )