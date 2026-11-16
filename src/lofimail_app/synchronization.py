"""Background mail synchronization state and worker."""

import threading
import time

from database import db
from .services.imap import mailconnect, fetch_emails_from_all_folders

sync_state = {"running": False, "message": "Idle", "last_error": None, "progress": 0}
sync_lock = threading.Lock()


def set_sync_state(running=None, message=None, last_error=None, progress=None):
    with sync_lock:
        if running is not None:
            sync_state["running"] = running
        if message is not None:
            sync_state["message"] = message
        if last_error is not None:
            sync_state["last_error"] = last_error
        if progress is not None:
            sync_state["progress"] = progress


def sync_worker(app, user_email=None, user_password=None, imap_server=None):
    """Synchronize mail in a worker thread with an application context."""
    try:
        set_sync_state(running=True, message="Starting sync...", last_error=None, progress=0)
        with app.app_context():
            if not (user_email and user_password and imap_server):
                raise ValueError("Mail connection parameters missing for background sync.")
            set_sync_state(message="Connecting to IMAP server...")
            mail = mailconnect(user_email, user_password, imap_server)
            set_sync_state(message="Fetching new emails (scanning folders)...")
            fetch_emails_from_all_folders(mail, db)
            set_sync_state(message="Finalizing (committing)...", progress=90)
            db.session.commit()
            set_sync_state(message="Sync complete", progress=100)
            time.sleep(0.2)
    except Exception as error:
        set_sync_state(message="Sync failed", last_error=str(error))
        app.logger.exception("Background sync failed")
    finally:
        set_sync_state(running=False)
