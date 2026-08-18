"""
Journal Routes
Handles journal CRUD operations and viewing
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app import db
from app.models.journal import Journal
from app.models.conversation import Conversation
from app.services import check_content_safety


journal_bp = Blueprint(
    "journal",
    __name__,
    url_prefix="/journals"
)


@journal_bp.route("/")
@login_required
def my_journals():
    """View user's own journals"""
    journals = Journal.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Journal.created_at.desc()
    ).all()
    
    return render_template(
        "my_journals.html",
        journals=journals
    )


@journal_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_journal():
    """Create a new journal entry"""
    
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        privacy = request.form.get("privacy", "private")
        mood = request.form.get("mood", "").strip()
        tags = request.form.get("tags", "").strip()
        
        # Validation
        if not title:
            flash("Please provide a title for your journal.", "error")
            return redirect(url_for("journal.create_journal"))
        
        if not content:
            flash("Journal content cannot be empty.", "error")
            return redirect(url_for("journal.create_journal"))
        
        # Check content safety
        is_safe, safety_reason = check_content_safety(content)
        
        if not is_safe:
            flash(
                "Your journal contains inappropriate content. Please maintain respectful communication.",
                "error"
            )
            return redirect(url_for("journal.create_journal"))
        
        # Create journal
        journal = Journal(
            title=title,
            content=content,
            user_id=current_user.id,
            privacy=privacy,
            mood=mood if mood else None,
            tags=tags if tags else None
        )
        
        db.session.add(journal)
        db.session.commit()
        
        flash("Journal entry created successfully!", "success")
        return redirect(url_for("journal.my_journals"))
    
    return render_template("create_journal.html")


@journal_bp.route("/<int:journal_id>")
@login_required
def view_journal(journal_id):
    """View a specific journal entry"""
    
    journal = db.session.get(Journal, journal_id)
    
    if journal is None:
        flash("Journal not found.", "error")
        return redirect(url_for("journal.my_journals"))
    
    # Check if user has permission to view
    if not journal.is_visible_to(current_user):
        flash("You don't have permission to view this journal.", "error")
        return redirect(url_for("journal.my_journals"))
    
    return render_template("view_journal.html", journal=journal)


@journal_bp.route("/<int:journal_id>/edit", methods=["GET", "POST"])
@login_required
def edit_journal(journal_id):
    """Edit a journal entry"""
    
    journal = db.session.get(Journal, journal_id)
    
    if journal is None:
        flash("Journal not found.", "error")
        return redirect(url_for("journal.my_journals"))
    
    # Only author can edit
    if journal.user_id != current_user.id:
        flash("You can only edit your own journals.", "error")
        return redirect(url_for("journal.my_journals"))
    
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        privacy = request.form.get("privacy", "private")
        mood = request.form.get("mood", "").strip()
        tags = request.form.get("tags", "").strip()
        
        # Validation
        if not title or not content:
            flash("Title and content are required.", "error")
            return redirect(url_for("journal.edit_journal", journal_id=journal_id))
        
        # Check content safety
        is_safe, safety_reason = check_content_safety(content)
        
        if not is_safe:
            flash(
                "Your journal contains inappropriate content.",
                "error"
            )
            return redirect(url_for("journal.edit_journal", journal_id=journal_id))
        
        # Update journal
        journal.title = title
        journal.content = content
        journal.privacy = privacy
        journal.mood = mood if mood else None
        journal.tags = tags if tags else None
        
        db.session.commit()
        
        flash("Journal updated successfully!", "success")
        return redirect(url_for("journal.view_journal", journal_id=journal.id))
    
    return render_template("edit_journal.html", journal=journal)


@journal_bp.route("/<int:journal_id>/delete", methods=["POST"])
@login_required
def delete_journal(journal_id):
    """Delete a journal entry"""
    
    journal = db.session.get(Journal, journal_id)
    
    if journal is None:
        flash("Journal not found.", "error")
        return redirect(url_for("journal.my_journals"))
    
    # Only author can delete
    if journal.user_id != current_user.id:
        flash("You can only delete your own journals.", "error")
        return redirect(url_for("journal.my_journals"))
    
    db.session.delete(journal)
    db.session.commit()
    
    flash("Journal deleted successfully.", "success")
    return redirect(url_for("journal.my_journals"))


@journal_bp.route("/discover")
@login_required
def discover_journals():
    """Discover public journals from other users"""
    
    # Get all public journals except user's own
    journals = Journal.query.filter(
        Journal.privacy == 'public',
        Journal.user_id != current_user.id
    ).order_by(
        Journal.created_at.desc()
    ).limit(50).all()
    
    return render_template(
        "discover_journals.html",
        journals=journals
    )


@journal_bp.route("/connections")
@login_required
def connections_journals():
    """View journals from connections"""
    
    # Get all conversations
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
    
    # Get journals from connections with 'connections' or 'public' privacy
    journals = Journal.query.filter(
        Journal.user_id.in_(connection_ids),
        Journal.privacy.in_(['connections', 'public'])
    ).order_by(
        Journal.created_at.desc()
    ).all()
    
    return render_template(
        "connections_journals.html",
        journals=journals
    )
