"""Flask application factory for LofiMail."""

import nltk
from flask import Flask

from .config import configure_application
from .routes import register_routes


def create_app():
    """Create and configure a LofiMail application instance."""
    app = Flask(__name__)

    configure_application(app)

    # Keep the NLP resources available as in the original application.
    # Downloads happen during application creation rather than module import.
    nltk.download("punkt")
    nltk.download("punkt_tab")

    register_routes(app)
    return app
