"""HTTP route registration, grouped by feature."""

from flask import render_template


def register_routes(app):
    from .authentication import bp as authentication_bp
    from .mailbox import bp as mailbox_bp
    from .messages import bp as messages_bp
    from .speech import bp as speech_bp
    from .synchronization import bp as synchronization_bp

    app.register_blueprint(authentication_bp)
    app.register_blueprint(mailbox_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(speech_bp)
    app.register_blueprint(synchronization_bp)

    @app.route("/")
    def index():
        return render_template("login.html")

    @app.route("/login", methods=["GET"], endpoint="login_page")
    def login_page():
        return render_template("login.html")
