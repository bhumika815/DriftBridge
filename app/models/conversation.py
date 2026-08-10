from datetime import datetime

from app import db


class Conversation(db.Model):
    __tablename__ = "conversations"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user1_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    user2_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    user1 = db.relationship(
        "User",
        foreign_keys=[user1_id],
        backref="conversations_as_user1"
    )

    user2 = db.relationship(
        "User",
        foreign_keys=[user2_id],
        backref="conversations_as_user2"
    )