from datetime import datetime

from app import db


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    conversation_id = db.Column(
        db.Integer,
        db.ForeignKey("conversations.id"),
        nullable=False
    )

    sender_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    content = db.Column(
        db.Text,
        nullable=False
    )

    # Original language of the message
    original_language = db.Column(
        db.String(10),
        default="en",
        nullable=False
    )

    # Type of message:
    # text = normal text message
    # image = uploaded image message
    message_type = db.Column(
        db.String(20),
        default="text",
        nullable=False
    )

    # Cloudinary URL for image messages.
    # NULL for normal text messages.
    media_url = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    conversation = db.relationship(
        "Conversation",
        backref="messages"
    )

    sender = db.relationship(
        "User",
        backref="sent_messages"
    )