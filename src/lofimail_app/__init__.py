"""Flask application factory and shared configuration."""

import os
import secrets

from flask import Flask

from database import db
from database.models import Metadata


def database_connect(app, name="db.sqlite"):
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", name)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    db.init_app(app)
    with app.app_context():
        db.create_all()
        if not Metadata.query.filter_by(key="last_email_uid").first():
            db.session.add(Metadata(key="last_email_uid", value="0"))
            db.session.commit()


def _configure_secret_key(app):
    keyfile = "secret_key.txt"
    if os.path.exists(keyfile):
        with open(keyfile, "r") as secret_file:
            app.secret_key = secret_file.read().strip()
    else:
        app.secret_key = secrets.token_hex(32)
        with open(keyfile, "w") as secret_file:
            secret_file.write(app.secret_key)


def create_app():
    source_dir = os.path.dirname(os.path.dirname(__file__))
    app = Flask(
        __name__,
        template_folder=os.path.join(source_dir, "templates"),
        static_folder=os.path.join(source_dir, "static"),
    )
    database_connect(app)
    _configure_secret_key(app)

    from .routes import register_routes
    register_routes(app)
    return app
