from datetime import datetime

from flask_login import UserMixin

from app import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    email_verified = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
        server_default="0"
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    bio = db.Column(
        db.String(500),
        nullable=True
    )

    interests = db.Column(
        db.String(500),
        nullable=True
    )

    age = db.Column(
        db.Integer,
        nullable=True
    )

    country = db.Column(
        db.String(100),
        nullable=True
    )

    date_of_birth = db.Column(
        db.Date,
        nullable=True
    )

    gender = db.Column(
        db.String(20),
        nullable=True
    )

    profile_image_url = db.Column(
        db.String(500),
        nullable=True
    )

    languages_spoken = db.Column(
        db.String(500),
        nullable=True
    )

    preferred_language = db.Column(
        db.String(10),
        default="en",
        nullable=False
    )

    points = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )

    is_admin = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
        server_default="0"
    )
    is_suspended = db.Column(
    db.Boolean,
    default=False,
    nullable=False,
    server_default="0"
)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # Bottles sent by this user.
    sent_bottles = db.relationship(
        "Bottle",
        foreign_keys="Bottle.sender_id",
        back_populates="sender",
        lazy=True
    )

    # Bottles specifically sent to this user.
    targeted_bottles = db.relationship(
        "Bottle",
        foreign_keys="Bottle.target_user_id",
        back_populates="target_user",
        lazy=True
    )

    # Bottles accepted/kept by this user.
    received_bottles = db.relationship(
        "Bottle",
        foreign_keys="Bottle.receiver_id",
        back_populates="receiver",
        lazy=True
    )