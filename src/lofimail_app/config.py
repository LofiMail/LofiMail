"""Application and local database configuration."""

import os
import secrets

from database import db
from database.models import Metadata


def configure_application(app, database_name="db.sqlite"):
    """Configure the existing local SQLite database and Flask secret key."""
    source_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    database_directory = os.path.join(source_directory, "database")
    os.makedirs(database_directory, exist_ok=True)

    database_path = os.path.join(database_directory, database_name)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{database_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

        if not Metadata.query.filter_by(key="last_email_uid").first():
            db.session.add(Metadata(key="last_email_uid", value="0"))
            db.session.commit()

    # Preserve the existing key-file location and persistence behaviour.
    keyfile = "secret_key.txt"
    if os.path.exists(keyfile):
        with open(keyfile, "r") as key_file:
            app.secret_key = key_file.read().strip()
    else:
        app.secret_key = secrets.token_hex(32)
        with open(keyfile, "w") as key_file:
            key_file.write(app.secret_key)
