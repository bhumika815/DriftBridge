from datetime import datetime

from app import db


class VerificationCode(db.Model):
    __tablename__ = "verification_codes"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    purpose = db.Column(
        db.String(50),
        nullable=False,
        index=True
    )

    code_hash = db.Column(
        db.String(255),
        nullable=False
    )

    expires_at = db.Column(
        db.DateTime,
        nullable=False
    )

    attempts = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    used = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )


    user = db.relationship(
        "User",
        backref=db.backref(
            "verification_codes",
            lazy=True,
            cascade="all, delete-orphan"
        )
    )