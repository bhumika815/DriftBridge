"""
Story Routes
Handles story creation, viewing, and management
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime

from app import db
from app.models.story import Story, StoryView
from app.models.conversation import Conversation
from app.services import check_content_safety


story_bp = Blueprint(
    "story",
    __name__,
    url_prefix="/stories"
)


@story_bp.route("/")
@login_required
def my_stories():
    """View user's own stories"""
    stories = Story.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Story.created_at.desc()
    ).all()
    
    # Remove expired stories
    for story in stories:
        if story.is_expired():
            db.session.delete(story)
    db.session.commit()
    
    # Refresh list
    stories = Story.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Story.created_at.desc()
    ).all()
    
    return render_template(
        "my_stories.html",
        stories=stories
    )


@story_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_story():
    """Create a new story"""
    
    if request.method == "POST":
        story_type = request.form.get("story_type", "text")
        
        if story_type == "text":
            text_content = request.form.get("text_content", "").strip()
            background_color = request.form.get("background_color", "#222222")
            
            if not text_content:
                flash("Story content cannot be empty.", "error")
                return redirect(url_for("story.create_story"))
            
            # Check content safety
            is_safe, safety_reason = check_content_safety(text_content)
            
            if not is_safe:
                flash(
                    "Your story contains inappropriate content.",
                    "error"
                )
                return redirect(url_for("story.create_story"))
            
            # Create text story
            story = Story(
                user_id=current_user.id,
                text_content=text_content,
                background_color=background_color,
                media_type='text'
            )
            
            db.session.add(story)
            db.session.commit()
            
            flash("Story posted successfully! It will expire in 24 hours.", "success")
            return redirect(url_for("story.my_stories"))
    
    return render_template("create_story.html")


@story_bp.route("/<int:story_id>")
@login_required
def view_story(story_id):
    """View a specific story"""
    
    story = db.session.get(Story, story_id)
    
    if story is None:
        flash("Story not found.", "error")
        return redirect(url_for("story.feed"))
    
    # Check if expired
    if story.is_expired():
        db.session.delete(story)
        db.session.commit()
        flash("This story has expired.", "error")
        return redirect(url_for("story.feed"))
    
    # Check if user has permission to view
    if not story.is_visible_to(current_user):
        flash("You don't have permission to view this story.", "error")
        return redirect(url_for("story.feed"))
    
    # Record view (if not author and haven't viewed yet)
    if story.user_id != current_user.id and not story.has_viewed(current_user):
        view = StoryView(
            story_id=story.id,
            user_id=current_user.id
        )
        db.session.add(view)
        db.session.commit()
    
    return render_template("view_story.html", story=story)


@story_bp.route("/<int:story_id>/delete", methods=["POST"])
@login_required
def delete_story(story_id):
    """Delete a story"""
    
    story = db.session.get(Story, story_id)
    
    if story is None:
        flash("Story not found.", "error")
        return redirect(url_for("story.my_stories"))
    
    # Only author can delete
    if story.user_id != current_user.id:
        flash("You can only delete your own stories.", "error")
        return redirect(url_for("story.my_stories"))
    
    db.session.delete(story)
    db.session.commit()
    
    flash("Story deleted successfully.", "success")
    return redirect(url_for("story.my_stories"))


@story_bp.route("/feed")
@login_required
def feed():
    """View stories from connections"""
    
    # Get all conversations to find connections
    conversations = Conversation.query.filter(
        (Conversation.user1_id == current_user.id) |
        (Conversation.user2_id == current_user.id)
    ).all()
    
    # Get user IDs of connections
    connection_ids = set()
    for conv in conversations:
        if conv.user1_id == current_user.id:
            connection_ids.add(conv.user2_id)
        else:
            connection_ids.add(conv.user1_id)
    
    if not connection_ids:
        return render_template("story_feed.html", stories=[], users_with_stories={})
    
    # Get active stories from connections
    stories = Story.query.filter(
        Story.user_id.in_(connection_ids),
        Story.expires_at > datetime.utcnow()
    ).order_by(
        Story.created_at.desc()
    ).all()
    
    # Group stories by user
    users_with_stories = {}
    for story in stories:
        if story.author.id not in users_with_stories:
            users_with_stories[story.author.id] = {
                'user': story.author,
                'stories': [],
                'has_unviewed': False
            }
        users_with_stories[story.author.id]['stories'].append(story)
        
        # Check if there are unviewed stories
        if not story.has_viewed(current_user):
            users_with_stories[story.author.id]['has_unviewed'] = True
    
    return render_template(
        "story_feed.html",
        users_with_stories=users_with_stories
    )


@story_bp.route("/<int:story_id>/viewers")
@login_required
def story_viewers(story_id):
    """View who has seen a story"""
    
    story = db.session.get(Story, story_id)
    
    if story is None:
        flash("Story not found.", "error")
        return redirect(url_for("story.my_stories"))
    
    # Only author can see viewers
    if story.user_id != current_user.id:
        flash("You can only view your own story viewers.", "error")
        return redirect(url_for("story.my_stories"))
    
    viewers = StoryView.query.filter_by(
        story_id=story.id
    ).order_by(
        StoryView.viewed_at.desc()
    ).all()
    
    return render_template(
        "story_viewers.html",
        story=story,
        viewers=viewers
    )


@story_bp.route("/user/<int:user_id>")
@login_required
def user_stories(user_id):
    """View all active stories from a specific user"""
    
    from app.models.user import User
    user = db.session.get(User, user_id)
    
    if user is None:
        flash("User not found.", "error")
        return redirect(url_for("story.feed"))
    
    # Get user's active stories
    stories = Story.query.filter(
        Story.user_id == user_id,
        Story.expires_at > datetime.utcnow()
    ).order_by(
        Story.created_at.asc()
    ).all()
    
    # Filter stories user can see
    visible_stories = [s for s in stories if s.is_visible_to(current_user)]
    
    if not visible_stories:
        flash("No active stories from this user.", "error")
        return redirect(url_for("story.feed"))
    
    return render_template(
        "user_stories.html",
        user=user,
        stories=visible_stories
    )
