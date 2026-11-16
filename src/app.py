"""Application entry point; implementation lives in :mod:`lofimail_app`."""

import re

from lofimail_app import create_app, database_connect


def generate_unique_filename(email_address, imap_address):
    """Return a filesystem-friendly identifier for an email/IMAP pair."""
    sanitized_email = re.sub(r"[^a-zA-Z0-9]", "", email_address)
    sanitized_imap = re.sub(r"[^a-zA-Z0-9]", "", imap_address)
    return f"{sanitized_email}_{sanitized_imap}"


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, use_reloader=False)
