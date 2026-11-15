"""HTTP route registration."""

from .authentication import register_authentication_routes
from .mailbox import register_mailbox_routes
from .messages import register_message_routes
from .speech import register_speech_routes
from .synchronization import register_synchronization_routes


def register_routes(app):
    """Register all routes while preserving their original endpoint names."""
    register_authentication_routes(app)
    register_synchronization_routes(app)
    register_mailbox_routes(app)
    register_message_routes(app)
    register_speech_routes(app)
