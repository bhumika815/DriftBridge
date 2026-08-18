from flask_login import current_user
from flask_socketio import emit, join_room

from app import db, socketio
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.services import translate_message, check_content_safety


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

    # Check content safety (hate speech detection)
    is_safe, safety_reason = check_content_safety(content)
    
    if not is_safe:
        emit(
            "message_blocked",
            {
                "error": "Your message contains inappropriate content and cannot be sent.",
                "reason": "Please maintain respectful communication."
            }
        )
        return

    # Get sender's language preference
    sender_language = current_user.preferred_language or 'en'

    # Create message with original language
    message = Message(
        conversation_id=conversation.id,
        sender_id=current_user.id,
        content=content,
        original_language=sender_language
    )

    db.session.add(message)
    db.session.commit()

    # Get the other user's language preference
    other_user_id = (
        conversation.user2_id 
        if conversation.user1_id == current_user.id 
        else conversation.user1_id
    )
    other_user = db.session.get(User, other_user_id)
    other_user_language = other_user.preferred_language or 'en'

    # Translate message if languages are different
    translated_content = content
    if sender_language != other_user_language:
        try:
            translated_content = translate_message(
                content,
                other_user_language,
                sender_language
            )
        except Exception as e:
            print(f"Translation error: {e}")
            translated_content = content

    # Emit message to both users
    emit(
        "new_message",
        {
            "message_id": message.id,
            "sender_id": current_user.id,
            "sender": current_user.username,
            "content": message.content,
            "original_language": sender_language,
            "created_at": message.created_at.strftime("%H:%M")
        },
        room=f"conversation_{conversation.id}"
    )

    # Send translated version to the other user only
    emit(
        "translated_message",
        {
            "message_id": message.id,
            "translated_content": translated_content,
            "target_language": other_user_language
        },
        room=f"conversation_{conversation.id}",
        skip_sid=current_user.get_id()
    )