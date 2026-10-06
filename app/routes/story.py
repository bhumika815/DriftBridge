"""
Story Routes
Handles story creation, viewing, and management
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime

from app import db
from app.models.story import Story, StoryView, StoryLike, StoryComment
from app.models.conversation import Conversation



story_bp = Blueprint(
    "story",
    __name__,
    url_prefix="/stories"
)


@story_bp.route("/")
@login_required
def my_stories():
    """View all of the user's Diaries."""

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
    
   # Expiry controls Feed visibility only.
   # Diaries remain permanently available from the owner's profile.
    
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


@story_bp.route("/<int:story_id>/like", methods=["POST"])
@login_required
def toggle_like(story_id):
    """Like or unlike a Diary."""

    story = db.session.get(Story, story_id)

    if story is None:
        return jsonify({
            "success": False,
            "message": "Diary not found."
        }), 404

    existing_like = StoryLike.query.filter_by(
        story_id=story.id,
        user_id=current_user.id
    ).first()

    if existing_like:
        # Unlike
        db.session.delete(existing_like)
        liked = False
    else:
        # Like
        like = StoryLike(
            story_id=story.id,
            user_id=current_user.id
        )
        db.session.add(like)
        liked = True

    db.session.commit()

    like_count = StoryLike.query.filter_by(
        story_id=story.id
    ).count()

    return jsonify({
        "success": True,
        "liked": liked,
        "like_count": like_count
    })



@story_bp.route("/<int:story_id>/comment", methods=["POST"])
@login_required
def add_comment(story_id):
    """Add a comment to a Diary."""

    story = db.session.get(Story, story_id)

    if story is None:
        return jsonify({
            "success": False,
            "message": "Diary not found."
        }), 404

    data = request.get_json(silent=True) or {}
    comment_text = data.get("comment", "").strip()

    if not comment_text:
        return jsonify({
            "success": False,
            "message": "Comment cannot be empty."
        }), 400

    if len(comment_text) > 500:
        return jsonify({
            "success": False,
            "message": "Comment must be 500 characters or less."
        }), 400

    comment = StoryComment(
        story_id=story.id,
        user_id=current_user.id,
        comment=comment_text
    )

    db.session.add(comment)
    db.session.commit()

    return jsonify({
        "success": True,
        "comment": {
            "id": comment.id,
            "username": current_user.username,
            "comment": comment.comment
        }
    })

@story_bp.route("/<int:story_id>/comments")
@login_required
def get_comments(story_id):
    """Get comments according to Diary comment privacy rules."""

    story = db.session.get(Story, story_id)

    if story is None:
        return jsonify({
            "success": False,
            "message": "Diary not found."
        }), 404

    if story.user_id == current_user.id:
        # Diary owner sees ALL comments.
        comments = StoryComment.query.filter_by(
            story_id=story.id
        ).order_by(
            StoryComment.created_at.asc()
        ).all()

    else:
        # Other users see ONLY their own comment.
        comments = StoryComment.query.filter_by(
            story_id=story.id,
            user_id=current_user.id
        ).order_by(
            StoryComment.created_at.asc()
        ).all()

    return jsonify({
        "success": True,
        "comments": [
            {
                "id": comment.id,
                "username": comment.user.username,
                "comment": comment.comment,
                "created_at": comment.created_at.strftime("%B %d, %Y")
            }
            for comment in comments
        ]
    })



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
    """View all active Diaries from all users."""

    stories = Story.query.filter(
        Story.expires_at > datetime.utcnow()
    ).order_by(
        Story.created_at.desc()
    ).all()

    return render_template(
        "story_feed.html",
        stories=stories
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
    """View all Diaries from a specific user."""
    
    from app.models.user import User
    user = db.session.get(User, user_id)
    
    if user is None:
        flash("User not found.", "error")
        return redirect(url_for("story.feed"))
    
    # Get all of the user's Diaries.
    # Expiration only controls visibility in the main Diary Feed.
    stories = Story.query.filter(
        Story.user_id == user_id
    ).order_by(
        Story.created_at.asc()
    ).all()
    
    # Filter stories user can see
    visible_stories = [s for s in stories if s.is_visible_to(current_user)]
    
    if not visible_stories:
        flash("No Diaries available from this user.", "error")
        return redirect(url_for("story.feed"))
    
    return render_template(
        "user_stories.html",
        user=user,
        stories=visible_stories
    )
