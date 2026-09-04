import logging

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO
from flask_wtf import CSRFProtect
from importlib import import_module

from app.config import Config


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()
socketio = SocketIO()
csrf = CSRFProtect()

logger = logging.getLogger(__name__)


def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    socketio.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "error"

    from app.models.user import User
    from app.models.bottle import Bottle
    from app.models.conversation import Conversation
    from app.models.message import Message
    from app.models.content_flag import ContentFlag
    from app.models.journal import Journal
    from app.models.story import Story, StoryView

    from app.routes.bottle import bottle_bp
    from app.routes.auth import auth_bp
    from app.routes.profile import profile_bp
    from app.routes.chat import chat_bp
    from app.routes.journal import journal_bp
    from app.routes.story import story_bp

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(bottle_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(journal_bp)
    app.register_blueprint(story_bp)

    # Load Socket.IO event handlers
    import_module("app.sockets.chat_socket")

    @app.route("/")
    def home():
        return render_template("landing.html")

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.exception("Internal server error: %s", e)
        return render_template("errors/500.html"), 500

    return app