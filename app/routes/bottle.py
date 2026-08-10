from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db
from app.models.bottle import Bottle
from app.models.conversation import Conversation


bottle_bp = Blueprint(
    "bottle",
    __name__,
    url_prefix="/bottles"
)


@bottle_bp.route("/throw", methods=["GET", "POST"])
@login_required
def throw_bottle():

    if request.method == "POST":
        message = request.form.get("message", "").strip()

        if not message:
            flash(
                "Please write a message before throwing your bottle.",
                "error"
            )
            return redirect(url_for("bottle.throw_bottle"))

        bottle = Bottle(
            sender_id=current_user.id,
            message=message
        )

        db.session.add(bottle)
        db.session.commit()

        flash("Your bottle has been thrown!", "success")

        return redirect(url_for("bottle.throw_bottle"))

    return render_template("throw_bottle.html")


@bottle_bp.route("/pool")
@login_required
def bottle_pool():

    bottles = Bottle.query.filter_by(
        status="available"
    ).filter(
        Bottle.sender_id != current_user.id
    ).order_by(
        Bottle.created_at.desc()
    ).all()

    return render_template(
        "bottle_pool.html",
        bottles=bottles
    )


@bottle_bp.route("/keep/<int:bottle_id>")
@login_required
def keep_bottle(bottle_id):

    bottle = db.session.get(Bottle, bottle_id)

    if bottle is None:
        flash("Bottle not found.", "error")
        return redirect(url_for("bottle.bottle_pool"))

    # Prevent users from keeping their own bottle
    if bottle.sender_id == current_user.id:
        flash(
            "You cannot keep your own bottle.",
            "error"
        )
        return redirect(url_for("bottle.bottle_pool"))

    # Only available bottles can be claimed
    if bottle.status != "available":
        flash(
            "This bottle has already been kept by someone else.",
            "error"
        )
        return redirect(url_for("bottle.bottle_pool"))

    # Claim the bottle
    bottle.receiver_id = current_user.id
    bottle.status = "claimed"

    # Check whether a conversation already exists
    conversation = Conversation.query.filter(
        (
            (Conversation.user1_id == bottle.sender_id) &
            (Conversation.user2_id == current_user.id)
        )
        |
        (
            (Conversation.user1_id == current_user.id) &
            (Conversation.user2_id == bottle.sender_id)
        )
    ).first()

    # Create a conversation only if one doesn't already exist
    if conversation is None:
        conversation = Conversation(
            user1_id=bottle.sender_id,
            user2_id=current_user.id
        )

        db.session.add(conversation)

    # Save the bottle claim and conversation together
    db.session.commit()

    flash("Bottle kept successfully!", "success")

    return redirect(url_for("bottle.bottle_pool"))


@bottle_bp.route("/connections")
@login_required
def connections():

    sent_connections = Bottle.query.filter_by(
        sender_id=current_user.id,
        status="claimed"
    ).all()

    received_connections = Bottle.query.filter_by(
        receiver_id=current_user.id,
        status="claimed"
    ).all()

    return render_template(
        "connections.html",
        sent_connections=sent_connections,
        received_connections=received_connections
    )