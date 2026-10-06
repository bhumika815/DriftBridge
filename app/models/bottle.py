from datetime import datetime

from app import db


class Bottle(db.Model):
    __tablename__ = "bottles"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    sender_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    status = db.Column(
        db.String(20),
        default="pending",
        nullable=False
    )

    receiver_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    target_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    claimed_at = db.Column(
        db.DateTime,
        nullable=True
    )

    sender = db.relationship(
        "User",
        foreign_keys=[sender_id],
        back_populates="sent_bottles"
    )

    target_user = db.relationship(
        "User",
        foreign_keys=[target_user_id],
        back_populates="targeted_bottles"
    )

    receiver = db.relationship(
        "User",
        foreign_keys=[receiver_id],
        back_populates="received_bottles"
    )

    def __repr__(self):
        return f"<Bottle {self.id} from {self.sender_id}>"