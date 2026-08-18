"""
Journal Model
Personal journal entries with privacy settings
"""

from datetime import datetime
from app import db


class Journal(db.Model):
    """Model for personal journal entries"""
    
    __tablename__ = "journals"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # Journal details
    title = db.Column(
        db.String(200),
        nullable=False
    )

    content = db.Column(
        db.Text,
        nullable=False
    )

    # Author
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # Privacy settings
    privacy = db.Column(
        db.String(20),
        default='private',
        nullable=False
    )  # 'private', 'connections', 'public'

    # Metadata
    mood = db.Column(
        db.String(50),
        nullable=True
    )  # Optional mood tag

    tags = db.Column(
        db.String(500),
        nullable=True
    )  # Comma-separated tags

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    author = db.relationship(
        "User",
        backref="journals"
    )

    def __repr__(self):
        return f'<Journal {self.id}: {self.title}>'

    def is_visible_to(self, user):
        """
        Check if this journal is visible to a given user
        
        Args:
            user: User object to check visibility for
            
        Returns:
            Boolean indicating if user can view this journal
        """
        # Author can always see their own journals
        if self.user_id == user.id:
            return True
        
        # Public journals are visible to all
        if self.privacy == 'public':
            return True
        
        # Private journals are only visible to author
        if self.privacy == 'private':
            return False
        
        # Connections-only journals require checking if users have a conversation
        if self.privacy == 'connections':
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
        
        return False
