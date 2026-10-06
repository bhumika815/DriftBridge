"""
Story Model
Temporary 24-hour stories similar to Instagram/WhatsApp stories
"""

from datetime import datetime, timedelta

from app import db


class Story(db.Model):
    """Model for temporary 24-hour stories."""

    __tablename__ = "stories"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # Story owner
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # Story content
    caption = db.Column(
        db.String(500),
        nullable=True
    )

    media_url = db.Column(
        db.String(500),
        nullable=True
    )  # URL to image/video on Cloudinary

    media_type = db.Column(
        db.String(20),
        nullable=True
    )  # 'image', 'video', 'text'

    # For text-only stories
    text_content = db.Column(
        db.Text,
        nullable=True
    )

    background_color = db.Column(
        db.String(7),
        default="#222222",
        nullable=True
    )  # Hex color for text stories

    # Timestamps
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    expires_at = db.Column(
        db.DateTime,
        nullable=False
    )

    # Relationships
    author = db.relationship(
        "User",
        backref="stories"
    )

    views = db.relationship(
        "StoryView",
        backref="story",
        cascade="all, delete-orphan"
    )

    likes = db.relationship(
        "StoryLike",
        backref="story",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Story {self.id} by {self.user_id}>"

    def __init__(self, **kwargs):
        """Override init to auto-set expiration to 24 hours."""
        super(Story, self).__init__(**kwargs)

        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(hours=24)

    def is_expired(self):
        """Check if story has expired."""
        return datetime.utcnow() > self.expires_at

    def is_visible_to(self, user):
        """
        Check whether this Diary can be viewed by a user.

        Diaries are publicly visible to authenticated users.
        The 24-hour expiry controls Feed visibility only and does
        not determine whether the Diary record can be viewed.
        """
        return True

    def view_count(self):
        """Get number of views for this story."""
        return len(self.views)

    def has_viewed(self, user):
        """Check if a user has viewed this story."""
        return any(view.user_id == user.id for view in self.views)


class StoryView(db.Model):
    """Track who has viewed each story."""

    __tablename__ = "story_views"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    story_id = db.Column(
        db.Integer,
        db.ForeignKey("stories.id"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    viewed_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Relationships
    viewer = db.relationship(
        "User",
        backref="story_views"
    )

    def __repr__(self):
        return f"<StoryView {self.id}: Story {self.story_id} by User {self.user_id}>"


class StoryLike(db.Model):
    """Track users who liked a Diary."""

    __tablename__ = "story_likes"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    story_id = db.Column(
        db.Integer,
        db.ForeignKey("stories.id"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    __table_args__ = (
        db.UniqueConstraint(
            "story_id",
            "user_id",
            name="uq_story_like_user"
        ),
    )

    user = db.relationship(
        "User",
        backref="story_likes"
    )

    def __repr__(self):
        return f"<StoryLike story={self.story_id} user={self.user_id}>"


class StoryComment(db.Model):
    """Store comments made on a Diary."""

    __tablename__ = "story_comments"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    story_id = db.Column(
        db.Integer,
        db.ForeignKey("stories.id"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    comment = db.Column(
        db.String(500),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    story = db.relationship(
        "Story",
        backref=db.backref(
            "comments",
            cascade="all, delete-orphan"
        )
    )

    user = db.relationship(
        "User",
        backref="story_comments"
    )

    def __repr__(self):
        return f"<StoryComment story={self.story_id} user={self.user_id}>"