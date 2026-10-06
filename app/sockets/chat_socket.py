"""
Socket.IO chat handlers for DriftBridge.

Authoritative implementation of:
- join_conversation
- send_message
- request_translation
- delete_message
"""

import logging
import time

from flask_login import current_user
from flask_socketio import emit, join_room

from app import db, socketio
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user_block import UserBlock
from app.models.content_flag import ContentFlag
from app.services import (
    detect_message_language,
    translate_message_with_word_mapping,
    check_content_safety
)
from app.services.reputation_service import award_points


logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# JOIN CONVERSATION
# ----------------------------------------------------------------------

@socketio.on("join_conversation")
def handle_join_conversation(data):
    """Join a conversation room after verifying authorization."""

    if not current_user.is_authenticated:
        return

    conversation_id = data.get("conversation_id")

    if not conversation_id:
        return

    try:
        conversation_id = int(conversation_id)
    except (TypeError, ValueError):
        return

    conversation = db.session.get(
        Conversation,
        conversation_id
    )

    if conversation is None:
        return

    # Only conversation participants can join the room.
    if (
        conversation.user1_id != current_user.id
        and conversation.user2_id != current_user.id
    ):
        logger.warning(
            "Unauthorized conversation room join denied: "
            "user=%s conversation=%s",
            current_user.id,
            conversation.id
        )
        return

    # A blocked relationship cannot join the conversation room.
    if conversation.user1_id == current_user.id:
        other_user_id = conversation.user2_id
    else:
        other_user_id = conversation.user1_id

    active_block = UserBlock.query.filter(
        (
            (UserBlock.blocker_id == current_user.id)
            &
            (UserBlock.blocked_id == other_user_id)
        )
        |
        (
            (UserBlock.blocker_id == other_user_id)
            &
            (UserBlock.blocked_id == current_user.id)
        )
    ).first()

    if active_block:
        logger.info(
            "Blocked conversation room join denied: "
            "user=%s conversation=%s other_user=%s",
            current_user.id,
            conversation.id,
            other_user_id
        )
        return

    try:
        join_room(
            f"conversation_{conversation.id}"
        )

        logger.info(
            "User %s joined conversation_%s",
            current_user.id,
            conversation.id
        )

    except (ValueError, KeyError) as exc:

        logger.warning(
            "Could not join conversation room: "
            "user=%s conversation=%s error=%s",
            current_user.id,
            conversation.id,
            exc
        )


# ----------------------------------------------------------------------
# SEND MESSAGE
# ----------------------------------------------------------------------

@socketio.on("send_message")
def handle_send_message(data):
    """Handle an outgoing chat message with moderation."""

    if not current_user.is_authenticated:
        return

    conversation_id = data.get("conversation_id")
    content = (data.get("content") or "").strip()
    client_message_id = data.get("client_message_id")

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

    try:
        conversation_id = int(conversation_id)
    except (TypeError, ValueError):
        emit(
            "message_error",
            {
                "error": "Invalid conversation."
            }
        )
        return

    conversation = db.session.get(
        Conversation,
        conversation_id
    )

    if conversation is None:
        emit(
            "message_error",
            {
                "error": "Conversation not found."
            }
        )
        return

    # --------------------------------------------------------------
    # Authorization
    # --------------------------------------------------------------

    if (
        conversation.user1_id != current_user.id
        and conversation.user2_id != current_user.id
    ):
        logger.warning(
            "Unauthorized message attempt: user=%s conversation=%s",
            current_user.id,
            conversation.id
        )

        emit(
            "message_error",
            {
                "error": (
                    "You are not authorized to send messages "
                    "in this conversation."
                )
            }
        )

        return

    # --------------------------------------------------------------
    # Block protection
    # --------------------------------------------------------------

    if conversation.user1_id == current_user.id:
        other_user_id = conversation.user2_id
    else:
        other_user_id = conversation.user1_id

    active_block = UserBlock.query.filter(
        (
            (UserBlock.blocker_id == current_user.id)
            &
            (UserBlock.blocked_id == other_user_id)
        )
        |
        (
            (UserBlock.blocker_id == other_user_id)
            &
            (UserBlock.blocked_id == current_user.id)
        )
    ).first()

    if active_block:
        emit(
            "message_error",
            {
                "error": (
                    "This message cannot be sent because "
                    "a block is active between the users."
                )
            }
        )

        logger.info(
            "Blocked message attempt: "
            "user=%s conversation=%s other_user=%s",
            current_user.id,
            conversation.id,
            other_user_id
        )

        return

    # --------------------------------------------------------------
    # AI content moderation
    # --------------------------------------------------------------

    is_safe, safety_reason = check_content_safety(
        content
    )

    if not is_safe:

        # ----------------------------------------------------------
        # Record the blocked content for admin review.
        #
        # The message has NOT been saved to the messages table,
        # so there is no Message ID available yet.
        #
        # content_id therefore uses 0 for blocked messages that
        # never become Message records.
        # ----------------------------------------------------------

        content_flag = ContentFlag(
            content_type="message",
            content_id=0,
            content_text=content,
            user_id=current_user.id,
            severity="high",
            ai_reason=safety_reason,
            status="pending"
        )

        try:
            db.session.add(content_flag)
            db.session.commit()

        except Exception:

            db.session.rollback()

            logger.exception(
                "Failed to record AI content flag: "
                "user=%s conversation=%s",
                current_user.id,
                conversation.id
            )

        # ----------------------------------------------------------
        # Do NOT save or broadcast the toxic message.
        # ----------------------------------------------------------

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

        logger.warning(
            "[TOXICITY AI] Message blocked: "
            "user=%s conversation=%s",
            current_user.id,
            conversation.id
        )

        return

    # --------------------------------------------------------------
    # Detect message language
    # --------------------------------------------------------------

    try:
        sender_language = detect_message_language(
            content
        )

    except Exception as exc:

        logger.exception(
            "Failed to detect message language: "
            "user=%s conversation=%s error=%s",
            current_user.id,
            conversation.id,
            exc
        )

        # Fall back to English if language detection fails.
        sender_language = "en"

    # --------------------------------------------------------------
    # Save the message to the database
    # --------------------------------------------------------------

    try:

        message = Message(
            conversation_id=conversation.id,
            sender_id=current_user.id,
            content=content,
            original_language=sender_language
        )

        db.session.add(message)
        db.session.commit()

    except Exception as exc:

        db.session.rollback()

        logger.exception(
            "Failed to save chat message: "
            "user=%s conversation=%s error=%s",
            current_user.id,
            conversation.id,
            exc
        )

        emit(
            "message_error",
            {
                "error": (
                    "Message could not be sent. "
                    "Please try again."
                )
            }
        )

        return

    # --------------------------------------------------------------
    # REAL-TIME DELIVERY
    #
    # Send the message to both users immediately after the
    # message has been successfully saved.
    # --------------------------------------------------------------

    emit(
        "new_message",
        {
            "message_id": message.id,
            "client_message_id": client_message_id,
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

    # --------------------------------------------------------------
    # Reputation
    #
    # This must NOT delay real-time message delivery.
    # If reputation processing fails, the chat message is still
    # already delivered.
    # --------------------------------------------------------------

    try:

        award_points(
            current_user.id,
            "message_sent"
        )

    except Exception:

        db.session.rollback()

        logger.exception(
            "Failed to award reputation points for message %s",
            message.id
        )


# ----------------------------------------------------------------------
# REQUEST TRANSLATION
# ----------------------------------------------------------------------

@socketio.on("request_translation")
def handle_request_translation(data):
    """
    Translate a message when the current user requests it.

    The current user's preferred language is used as the target.
    """

    if not current_user.is_authenticated:
        return

    message_id = data.get("message_id")

    if not message_id:
        return

    try:
        message_id = int(message_id)
    except (TypeError, ValueError):
        return

    chat_message = db.session.get(
        Message,
        message_id
    )

    if chat_message is None:

        emit(
            "translation_failed",
            {
                "message_id": message_id,
                "reason": "Message not found."
            }
        )

        return

    conversation = db.session.get(
        Conversation,
        chat_message.conversation_id
    )

    if conversation is None:

        emit(
            "translation_failed",
            {
                "message_id": chat_message.id,
                "reason": "Conversation not found."
            }
        )

        return

    # --------------------------------------------------------------
    # Authorization
    # --------------------------------------------------------------

    if (
        conversation.user1_id != current_user.id
        and conversation.user2_id != current_user.id
    ):

        logger.warning(
            "Unauthorized translation attempt: "
            "user=%s message=%s",
            current_user.id,
            chat_message.id
        )

        emit(
            "translation_failed",
            {
                "message_id": chat_message.id,
                "reason": (
                    "You are not allowed to translate "
                    "this message."
                )
            }
        )

        return

    # --------------------------------------------------------------
    # Block protection
    # --------------------------------------------------------------

    if conversation.user1_id == current_user.id:
        other_user_id = conversation.user2_id
    else:
        other_user_id = conversation.user1_id

    active_block = UserBlock.query.filter(
        (
            (UserBlock.blocker_id == current_user.id)
            &
            (UserBlock.blocked_id == other_user_id)
        )
        |
        (
            (UserBlock.blocker_id == other_user_id)
            &
            (UserBlock.blocked_id == current_user.id)
        )
    ).first()

    if active_block:

        emit(
            "translation_failed",
            {
                "message_id": chat_message.id,
                "reason": (
                    "Translation is unavailable because "
                    "a block is active between the users."
                )
            }
        )

        logger.info(
            "Blocked translation attempt: "
            "user=%s message=%s other_user=%s",
            current_user.id,
            chat_message.id,
            other_user_id
        )

        return

    # --------------------------------------------------------------
    # Target language
    # --------------------------------------------------------------

    target_language = (
        current_user.preferred_language
        or "en"
    )

    source_language = (
        chat_message.original_language
        or "en"
    )

    # --------------------------------------------------------------
    # Same language
    # --------------------------------------------------------------

    if target_language == source_language:

        emit(
            "translation_result",
            {
                "message_id": chat_message.id,
                "translated_content": chat_message.content,
                "target_language": target_language,
                "words": []
            }
        )

        return

    # --------------------------------------------------------------
    # Translation
    # --------------------------------------------------------------

    translation_start = time.perf_counter()

    logger.info(
        "[CHAT TRANSLATION] Starting translation: "
        "message_id=%s source=%s target=%s",
        chat_message.id,
        source_language,
        target_language
    )

    try:

        success, result = (
            translate_message_with_word_mapping(
                chat_message.content,
                target_language,
                source_language,
                message_id=chat_message.id
            )
        )

    except Exception as exc:

        translation_time = (
            time.perf_counter()
            - translation_start
        )

        logger.exception(
            "[CHAT TRANSLATION] Unexpected failure "
            "after %.3f seconds: message_id=%s error=%s",
            translation_time,
            chat_message.id,
            exc
        )

        emit(
            "translation_failed",
            {
                "message_id": chat_message.id,
                "reason": (
                    "Translation could not be completed."
                )
            }
        )

        return

    translation_time = (
        time.perf_counter()
        - translation_start
    )

    logger.info(
        "[CHAT TRANSLATION] AI service returned after "
        "%.3f seconds: message_id=%s success=%s",
        translation_time,
        chat_message.id,
        success
    )

    # --------------------------------------------------------------
    # IMPORTANT:
    #
    # translate_message_with_word_mapping() returns:
    #
    #     (True, result_dict)
    #
    # OR:
    #
    #     (False, error_string)
    #
    # Therefore we MUST check success before accessing
    # result["translated_text"].
    # --------------------------------------------------------------

    if not success:

        emit(
            "translation_failed",
            {
                "message_id": chat_message.id,
                "reason": (
                    result
                    if isinstance(result, str)
                    else "Translation failed."
                )
            }
        )

        return

    if not isinstance(result, dict):

        logger.error(
            "[CHAT TRANSLATION] Invalid result type: "
            "message_id=%s type=%s",
            chat_message.id,
            type(result).__name__
        )

        emit(
            "translation_failed",
            {
                "message_id": chat_message.id,
                "reason": "Translation returned an invalid result."
            }
        )

        return

    translated_content = (
        result.get("translated_text") or ""
    ).strip()

    if not translated_content:

        emit(
            "translation_failed",
            {
                "message_id": chat_message.id,
                "reason": "Translation returned empty content."
            }
        )

        return

    # --------------------------------------------------------------
    # Send translation ONLY to requester
    # --------------------------------------------------------------

    emit(
        "translation_result",
        {
            "message_id": chat_message.id,
            "translated_content": translated_content,
            "target_language": target_language,
            "words": result.get("words", [])
        }
    )

    logger.info(
        "[CHAT TRANSLATION] Translation delivered: "
        "message_id=%s target=%s total=%.3f seconds.",
        chat_message.id,
        target_language,
        translation_time
    )


# ----------------------------------------------------------------------
# DELETE MESSAGE
# ----------------------------------------------------------------------

@socketio.on("delete_message")
def handle_delete_message(data):
    """Delete a message owned by the current user."""

    if not current_user.is_authenticated:
        return

    message_id = data.get("message_id")

    if not message_id:
        return

    try:
        message_id = int(message_id)

    except (TypeError, ValueError):

        emit(
            "delete_message_error",
            {
                "message_id": message_id,
                "error": "Invalid message."
            }
        )

        return

    chat_message = db.session.get(
        Message,
        message_id
    )

    if chat_message is None:

        emit(
            "delete_message_error",
            {
                "message_id": message_id,
                "error": "Message not found."
            }
        )

        return

    conversation = db.session.get(
        Conversation,
        chat_message.conversation_id
    )

    if conversation is None:

        emit(
            "delete_message_error",
            {
                "message_id": chat_message.id,
                "error": "Conversation not found."
            }
        )

        return

    # --------------------------------------------------------------
    # Authorization: conversation participant
    # --------------------------------------------------------------

    if (
        conversation.user1_id != current_user.id
        and conversation.user2_id != current_user.id
    ):

        logger.warning(
            "Unauthorized message deletion attempt: "
            "user=%s message=%s conversation=%s",
            current_user.id,
            chat_message.id,
            conversation.id
        )

        emit(
            "delete_message_error",
            {
                "message_id": chat_message.id,
                "error": (
                    "You are not allowed to delete "
                    "this message."
                )
            }
        )

        return

    # --------------------------------------------------------------
    # Block protection
    # --------------------------------------------------------------

    if conversation.user1_id == current_user.id:
        other_user_id = conversation.user2_id
    else:
        other_user_id = conversation.user1_id

    active_block = UserBlock.query.filter(
        (
            (UserBlock.blocker_id == current_user.id)
            &
            (UserBlock.blocked_id == other_user_id)
        )
        |
        (
            (UserBlock.blocker_id == other_user_id)
            &
            (UserBlock.blocked_id == current_user.id)
        )
    ).first()

    if active_block:

        emit(
            "delete_message_error",
            {
                "message_id": chat_message.id,
                "error": (
                    "This message cannot be deleted because "
                    "a block is active between the users."
                )
            }
        )

        logger.info(
            "Blocked message deletion attempt: "
            "user=%s message=%s other_user=%s",
            current_user.id,
            chat_message.id,
            other_user_id
        )

        return

    # --------------------------------------------------------------
    # Authorization: own message only
    # --------------------------------------------------------------

    if chat_message.sender_id != current_user.id:

        emit(
            "delete_message_error",
            {
                "message_id": chat_message.id,
                "error": (
                    "You can only delete your own messages."
                )
            }
        )

        return

    # --------------------------------------------------------------
    # Delete
    # --------------------------------------------------------------

    try:

        db.session.delete(chat_message)
        db.session.commit()

    except Exception:

        db.session.rollback()

        logger.exception(
            "Failed to delete message %s",
            chat_message.id
        )

        emit(
            "delete_message_error",
            {
                "message_id": chat_message.id,
                "error": (
                    "Message could not be deleted. "
                    "Please try again."
                )
            }
        )

        return

    # --------------------------------------------------------------
    # Tell both users
    # --------------------------------------------------------------

    emit(
        "message_deleted",
        {
            "message_id": chat_message.id
        },
        room=f"conversation_{conversation.id}"
    )

    logger.info(
        "Message deleted: message_id=%s user=%s",
        chat_message.id,
        current_user.id
    )