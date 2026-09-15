"""
Socket.IO chat handlers for DriftBridge.

This is the SINGLE authoritative implementation of the
join_conversation, send_message, and request_translation events.
"""

import logging

from flask_login import current_user
from flask_socketio import emit, join_room

from app import db, socketio
from app.models.conversation import Conversation
from app.models.message import Message
from app.services import (
    detect_message_language,
    translate_message_with_word_mapping,
    check_content_safety
)
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
        logger.warning(
            "Unauthorized room join attempt: user=%s conversation=%s",
            current_user.id,
            conversation.id
        )
        return

    try:
        join_room(f"conversation_{conversation.id}")
    except (ValueError, KeyError) as exc:
        logger.warning(
            "Could not join conversation room: user=%s conversation=%s error=%s",
            current_user.id,
            conversation.id,
            exc
        )


@socketio.on("send_message")
def handle_send_message(data):
    """Handle an outgoing chat message with moderation."""

    if not current_user.is_authenticated:
        return

    conversation_id = data.get("conversation_id")
    content = (data.get("content") or "").strip()

    if not conversation_id or not content:
        return

    if len(content) > 2000:
        emit(
            "message_error",
            {
                "error": "Messages must be 2000 characters or fewer."
            }
        )
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
        logger.warning(
            "Unauthorized message attempt: user=%s conversation=%s",
            current_user.id,
            conversation.id
        )
        return

    # --------------------------------------------------------------
    # Content moderation
    # --------------------------------------------------------------

    is_safe, safety_reason = check_content_safety(content)

    if not is_safe:
        emit(
            "message_blocked",
            {
                "error": (
                    "Your message contains inappropriate content "
                    "and cannot be sent."
                ),
                "reason": (
                    safety_reason
                    or "Please maintain respectful communication."
                )
            }
        )
        return

    # --------------------------------------------------------------
    # Persist the original message
    # --------------------------------------------------------------

    sender_language = detect_message_language(
        content,
        current_user.preferred_language
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

        logger.exception(
            "Failed to persist message in conversation %s",
            conversation.id
        )

        emit(
            "message_error",
            {
                "error": "Message could not be sent. Please try again."
            }
        )
        return

    # --------------------------------------------------------------
    # Award reputation points
    # --------------------------------------------------------------

    award_points(
        current_user.id,
        "message_sent"
    )

    # --------------------------------------------------------------
    # Emit ONLY the original message
    #
    # Translation is requested by the recipient when they
    # tap the message.
    # --------------------------------------------------------------

    emit(
        "new_message",
        {
            "message_id": message.id,
            "sender_id": current_user.id,
            "sender": current_user.username,
            "content": message.content,
            "original_language": sender_language,
            "created_at": message.created_at.strftime(
                "%d %b %Y, %I:%M %p"
            )
        },
        room=f"conversation_{conversation.id}"
    )


@socketio.on("request_translation")
def handle_request_translation(data):
    """
    Translate a message when the recipient requests it.

    The recipient's preferred language from their profile is used
    as the target language.
    """

    if not current_user.is_authenticated:
        return

    message_id = data.get("message_id")

    if not message_id:
        return

    message = db.session.get(
        Message,
        int(message_id)
    )

    if message is None:
        return

    conversation = db.session.get(
        Conversation,
        message.conversation_id
    )

    if conversation is None:
        return

    # --------------------------------------------------------------
    # Authorization
    # --------------------------------------------------------------

    if (
        conversation.user1_id != current_user.id
        and conversation.user2_id != current_user.id
    ):
        logger.warning(
            "Unauthorized translation attempt: user=%s message=%s",
            current_user.id,
            message.id
        )
        return

    # --------------------------------------------------------------
    # Recipient's preferred language
    # --------------------------------------------------------------

    target_language = current_user.preferred_language or "en"

    # --------------------------------------------------------------
    # If the message is already in the recipient's language,
    # no translation is necessary.
    # --------------------------------------------------------------

    if target_language == message.original_language:
        emit(
            "translation_result",
            {
                "message_id": message.id,
                "translated_content": message.content,
                "target_language": target_language,
                "words": []
            }
        )
        return

    # --------------------------------------------------------------
    # Request word-level translation
    # --------------------------------------------------------------

    success, result = translate_message_with_word_mapping(
        message.content,
        target_language,
        message.original_language,
        message_id=message.id
    )

    if not success:
        emit(
            "translation_failed",
            {
                "message_id": message.id,
                "reason": result
            }
        )
        return

    # --------------------------------------------------------------
    # Send translation + word mapping back ONLY to requester
    # --------------------------------------------------------------

    emit(
        "translation_result",
        {
            "message_id": message.id,
            "translated_content": result["translated_text"],
            "target_language": target_language,
            "words": result.get("words", [])
        }
    )