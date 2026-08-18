"""
Story Model
Temporary 24-hour stories similar to Instagram/WhatsApp stories
"""

from datetime import datetime, timedelta
from app import db


class Story(db.Model):
    """Model for temporary 24-hour stories"""
    
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
        default='#222222',
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

    def __repr__(self):
        return f'<Story {self.id} by {self.user_id}>'

    def __init__(self, **kwargs):
        """Override init to auto-set expiration to 24 hours"""
        super(Story, self).__init__(**kwargs)
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(hours=24)

    def is_expired(self):
        """Check if story has expired"""
        return datetime.utcnow() > self.expires_at

    def is_visible_to(self, user):
        """
        Check if this story is visible to a given user
        Stories are visible to the author and their connections
        
        Args:
            user: User object to check visibility for
            
        Returns:
            Boolean indicating if user can view this story
        """
        # Author can always see their own stories
        if self.user_id == user.id:
            return True
        
        # Check if expired
        if self.is_expired():
            return False
        
        # Check if users have a conversation (are connected)
        from app.models.conversation import Conversation
        
        conversation = Conversation.query.filter(
            (
                (Conversation.user1_id == self.user_id) &
                (Conversation.user2_id == user.id)
            )
            |
            (
                (Conversation.user1_id == user.id) &
                (Conversation.user2_id == self.user_id)
            )
        ).first()
        
        return conversation is not None

    def view_count(self):
        """Get number of views for this story"""
        return len(self.views)

    def has_viewed(self, user):
        """Check if a user has viewed this story"""
        return any(view.user_id == user.id for view in self.views)


class StoryView(db.Model):
    """Track who has viewed each story"""
    
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
        return f'<StoryView {self.id}: Story {self.story_id} by User {self.user_id}>'
