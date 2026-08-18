"""
Content Flag Model
Tracks flagged content for admin review
"""

from datetime import datetime
from app import db


class ContentFlag(db.Model):
    """Model for tracking flagged inappropriate content"""
    
    __tablename__ = "content_flags"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # Content details
    content_type = db.Column(
        db.String(50),
        nullable=False
    )  # 'message', 'bottle', 'journal', 'story'

    content_id = db.Column(
        db.Integer,
        nullable=False
    )

    content_text = db.Column(
        db.Text,
        nullable=False
    )

    # User who created the content
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # AI analysis
    severity = db.Column(
        db.String(20),
        nullable=False
    )  # 'low', 'medium', 'high'

    ai_reason = db.Column(
        db.Text,
        nullable=True
    )

    # Admin review
    status = db.Column(
        db.String(20),
        default='pending',
        nullable=False
    )  # 'pending', 'reviewed', 'actioned'

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

    # Relationships
    user = db.relationship(
        "User",
        foreign_keys=[user_id],
        backref="content_flags"
    )

    reviewer = db.relationship(
        "User",
        foreign_keys=[reviewed_by],
        backref="reviewed_flags"
    )
