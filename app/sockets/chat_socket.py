"""
Socket.IO chat handlers for DriftBridge.

This is the SINGLE authoritative implementation of the
join_conversation and send_message events. The app factory imports
this module via import_module("app.sockets.chat_socket").
"""

import logging

from flask_login import current_user
from flask_socketio import emit, join_room

from app import db, socketio
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.services import translate_message, check_content_safety
from app.services.reputation_service import award_points


logger = logging.getLogger(__name__)


@socketio.on("join_conversation")
def handle_join_conversation(data):
    """Join a conversation room (authorized to participants only)."""

    if not current_user.is_authenticated:
        return

    conversation_id = data.get("conversation_id")
    if not conversation_id:
        return

    conversation = db.session.get(Conversation, int(conversation_id))
    if conversation is None:
        return

    if (
        conversation.user1_id != current_user.id
        and conversation.user2_id != current_user.id
    ):
        logger.warning(
            "Unauthorized room join attempt: user=%s conversation=%s",
            current_user.id, conversation.id
        )
        return

    join_room(f"conversation_{conversation.id}")


@socketio.on("send_message")
def handle_send_message(data):
    """Handle an outgoing chat message with moderation + translation."""

    if not current_user.is_authenticated:
        return

    conversation_id = data.get("conversation_id")
    content = (data.get("content") or "").strip()

    if not conversation_id or not content:
        return

    if len(content) > 2000:
        emit("message_error", {"error": "Messages must be 2000 characters or fewer."})
        return

    conversation = db.session.get(Conversation, int(conversation_id))
    if conversation is None:
        return

    if (
        conversation.user1_id != current_user.id
        and conversation.user2_id != current_user.id
    ):
        logger.warning(
            "Unauthorized message attempt: user=%s conversation=%s",
            current_user.id, conversation.id
        )
        return

    # --- Content moderation (hate-speech detection) ---
    is_safe, safety_reason = check_content_safety(content)
    if not is_safe:
        emit(
            "message_blocked",
            {
                "error": "Your message contains inappropriate content and "
                         "cannot be sent.",
                "reason": "Please maintain respectful communication."
            }
        )
        return

    # --- Persist the original message ---
    sender_language = current_user.preferred_language or 'en'

    message = Message(
        conversation_id=conversation.id,
        sender_id=current_user.id,
        content=content,
        original_language=sender_language
    )
    try:
        db.session.add(message)
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception(
            "Failed to persist message in conversation %s",
            conversation.id,
        )
        emit("message_error", {"error": "Failed to send message. Please try again."})
        return

    # --- Determine the other participant ---
    other_user_id = (
        conversation.user2_id
        if conversation.user1_id == current_user.id
        else conversation.user1_id
    )
    other_user = db.session.get(User, other_user_id)
    other_user_language = other_user.preferred_language if other_user else 'en'

    # --- Award reputation points (key must match POINTS dict) ---
    award_points(current_user.id, 'message_sent')

    # --- Emit original message to everyone in the room ---
    emit(
        "new_message",
        {
            "message_id": message.id,
            "sender_id": current_user.id,
            "sender": current_user.username,
            "content": message.content,
            "original_language": sender_language,
            "created_at": message.created_at.strftime("%d %b %Y, %I:%M %p")
        },
        room=f"conversation_{conversation.id}"
    )

    # --- Translation (only when languages differ) ---
    if sender_language != other_user_language:
        success, translated = translate_message(
            content,
            other_user_language,
            sender_language,
            message_id=message.id
        )

        if success and translated:
            emit(
                "translated_message",
                {
                    "message_id": message.id,
                    "translated_content": translated,
                    "target_language": other_user_language,
                    "original_content": content
                },
                room=f"conversation_{conversation.id}",
                skip_sid=current_user.get_id()
            )
        else:
            logger.warning(
                "Translation not emitted (failed) — message_id=%s "
                "source=%s target=%s",
                message.id, sender_language, other_user_language
            )
            emit(
                "translation_failed",
                {
                    "message_id": message.id,
                    "reason": "AI translation is currently unavailable."
                },
                room=f"conversation_{conversation.id}",
                skip_sid=current_user.get_id()
            )
