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

    points = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # Bottles sent by this user
    sent_bottles = db.relationship(
        "Bottle",
        foreign_keys="Bottle.sender_id",
        backref="sender",
        lazy=True
    )

    # Bottles received/kept by this user
    received_bottles = db.relationship(
        "Bottle",
        foreign_keys="Bottle.receiver_id",
        backref="receiver",
        lazy=True
    )