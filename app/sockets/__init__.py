from flask import request
from flask_login import current_user
from flask_socketio import emit, join_room

from app import socketio, db
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

    # Make sure the user belongs to this conversation
    if (
        conversation.user1_id != current_user.id
        and conversation.user2_id != current_user.id
    ):
        return

    room = f"conversation_{conversation.id}"

    join_room(room)


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

    # Make sure the user belongs to this conversation
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

    room = f"conversation_{conversation.id}"

    emit(
        "new_message",
        {
            "sender_id": current_user.id,
            "content": message.content,
            "created_at": message.created_at.strftime("%H:%M")
        },
        to=room
    )