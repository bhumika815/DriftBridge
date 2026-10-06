from datetime import datetime

from app import db


class UserReport(db.Model):
    __tablename__ = "user_reports"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    reporter_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    reported_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    reason = db.Column(
        db.String(100),
        nullable=False
    )

    details = db.Column(
        db.Text,
        nullable=True
    )

    status = db.Column(
        db.String(20),
        default="pending",
        nullable=False
    )
    admin_notes = db.Column(
        db.Text,
        nullable=True
    )

    reviewed_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    reviewed_at = db.Column(
        db.DateTime,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    reporter = db.relationship(
        "User",
        foreign_keys=[reporter_id],
        backref="reports_submitted"
    )

    reported_user = db.relationship(
        "User",
        foreign_keys=[reported_user_id],
        backref="reports_received"
    )

    reviewer = db.relationship(
        "User",
        foreign_keys=[reviewed_by],
        backref="reviewed_user_reports"
    )

    def __repr__(self):
        return (
            f"<UserReport reporter={self.reporter_id} "
            f"reported={self.reported_user_id} "
            f"status={self.status}>"
        )
    