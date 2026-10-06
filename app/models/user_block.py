from datetime import datetime

from app import db


class UserBlock(db.Model):
    __tablename__ = "user_blocks"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    blocker_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    blocked_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    blocker = db.relationship(
        "User",
        foreign_keys=[blocker_id],
        backref="users_blocked"
    )

    blocked = db.relationship(
        "User",
        foreign_keys=[blocked_id],
        backref="blocked_by_users"
    )

    __table_args__ = (
        db.UniqueConstraint(
            "blocker_id",
            "blocked_id",
            name="uq_user_block"
        ),
    )

    def __repr__(self):
        return (
            f"<UserBlock blocker={self.blocker_id} "
            f"blocked={self.blocked_id}>"
        )
    