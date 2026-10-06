from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db
from app.models.bottle import Bottle
from app.models.conversation import Conversation
from app.models.user import User
from app.models.user_block import UserBlock


bottle_bp = Blueprint("bottle", __name__)


@bottle_bp.route("/throw", methods=["GET", "POST"])
@login_required
def throw_bottle():
    """
    Send a Bottle into the public Pool.

    A Bottle is NOT sent to a specific user.
    It enters the Pool and can be kept by the first eligible user.
    """

    if request.method == "POST":
        message = request.form.get("message", "").strip()

        if not message:
            flash("Please write a message before sending your bottle.", "error")
            return redirect(url_for("bottle.throw_bottle"))

        if len(message) > 2000:
            flash("Your bottle message is too long.", "error")
            return redirect(url_for("bottle.throw_bottle"))

        bottle = Bottle(
            sender_id=current_user.id,
            message=message,
            status="pending",
            receiver_id=None,
            target_user_id=None,
            created_at=datetime.utcnow(),
        )

        db.session.add(bottle)

        # Keep the existing reputation/points behavior.
        current_user.points += 1

        db.session.commit()

        flash("Your bottle has been sent to the Pool.", "success")
        return redirect(url_for("bottle.pool"))

    return render_template("throw_bottle.html")


@bottle_bp.route("/pool", endpoint="pool")
@bottle_bp.route("/pool", endpoint="bottle_pool")
@login_required
def pool():
    """
    Show the public Bottle Pool.

    Every pending Bottle is available except:
    - the current user's own Bottles
    - Bottles from users blocked by the current user
    - Bottles from users who blocked the current user
    - Bottles that have already been claimed/rejected
    """

    blocked_user_ids = db.session.query(
        UserBlock.blocked_id
    ).filter(
        UserBlock.blocker_id == current_user.id
    )

    users_who_blocked_me = db.session.query(
        UserBlock.blocker_id
    ).filter(
        UserBlock.blocked_id == current_user.id
    )

    bottles = Bottle.query.filter(
        Bottle.status == "pending",
        Bottle.sender_id != current_user.id,
        ~Bottle.sender_id.in_(blocked_user_ids),
        ~Bottle.sender_id.in_(users_who_blocked_me),
    ).order_by(
        Bottle.created_at.desc()
    ).all()

    return render_template(
        "bottle_pool.html",
        bottles=bottles,
    )

@bottle_bp.route("/keep/<int:bottle_id>", methods=["POST"])
@login_required
def keep_bottle(bottle_id):
    """
    Keep a Bottle from the Pool.

    The first person who successfully keeps a pending Bottle
    becomes connected with its sender.
    """

    bottle = db.session.get(Bottle, bottle_id)

    if bottle is None:
        flash("Bottle not found.", "error")
        return redirect(url_for("bottle.pool"))

    if bottle.status != "pending":
        flash("This bottle is no longer available.", "error")
        return redirect(url_for("bottle.pool"))

    # A user cannot keep their own Bottle.
    if bottle.sender_id == current_user.id:
        flash("You cannot keep your own bottle.", "error")
        return redirect(url_for("bottle.pool"))

        # A blocked relationship cannot create a new connection.
    existing_block = UserBlock.query.filter(
        (
            (UserBlock.blocker_id == current_user.id)
            &
            (UserBlock.blocked_id == bottle.sender_id)
        )
        |
        (
            (UserBlock.blocker_id == bottle.sender_id)
            &
            (UserBlock.blocked_id == current_user.id)
        )
    ).first()

    if existing_block:
        flash(
            "You cannot connect with this user because a block is active.",
            "error"
        )
        return redirect(url_for("bottle.pool"))

    # Claim the Bottle.
    bottle.receiver_id = current_user.id
    bottle.claimed_at = datetime.utcnow()
    bottle.status = "claimed"

    # Find an existing conversation between these two users.
    conversation = Conversation.query.filter(
        (
            (Conversation.user1_id == bottle.sender_id)
            &
            (Conversation.user2_id == current_user.id)
        )
        |
        (
            (Conversation.user1_id == current_user.id)
            &
            (Conversation.user2_id == bottle.sender_id)
        )
    ).first()

    # If no conversation exists, create their connection/chat.
    if conversation is None:
        conversation = Conversation(
            user1_id=bottle.sender_id,
            user2_id=current_user.id,
            created_at=datetime.utcnow(),
        )
        db.session.add(conversation)

    # Award points to the person who kept the Bottle.
    current_user.points += 1

    db.session.commit()

    flash("You kept the bottle. You are now connected.", "success")
    return redirect(url_for("chat.conversations"))


@bottle_bp.route("/reject/<int:bottle_id>", methods=["POST"])
@login_required
def reject_bottle(bottle_id):
    """
    Reject a Bottle from the Pool.
    """

    bottle = db.session.get(Bottle, bottle_id)

    if bottle is None:
        flash("Bottle not found.", "error")
        return redirect(url_for("bottle.pool"))

    if bottle.status != "pending":
        flash("This bottle is no longer available.", "error")
        return redirect(url_for("bottle.pool"))

    # A user cannot reject their own Bottle.
    if bottle.sender_id == current_user.id:
        flash("You cannot reject your own bottle.", "error")
        return redirect(url_for("bottle.pool"))

    bottle.status = "rejected"

    db.session.commit()

    flash("Bottle rejected.", "success")
    return redirect(url_for("bottle.pool"))