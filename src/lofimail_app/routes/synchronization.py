import threading

from flask import Blueprint, current_app, jsonify, session

from ..synchronization import sync_lock, sync_state, sync_worker

bp = Blueprint("synchronization", __name__)


@bp.route("/start_sync", methods=["POST"])
def start_sync():
    if sync_state["running"]:
        return jsonify({"status": "already_running", "message": sync_state["message"]}), 200
    email, password, imap_server = (session.get(key) for key in ("email", "password", "imap"))
    if not (email and password and imap_server):
        return jsonify({"status": "error", "message": "Not logged in"}), 403
    thread = threading.Thread(
        target=sync_worker,
        args=(current_app._get_current_object(), email, password, imap_server),
        daemon=True,
    )
    thread.start()
    return jsonify({"status": "started", "message": "Background sync started"}), 202


@bp.route("/sync_status", methods=["GET"])
def sync_status():
    with sync_lock:
        return jsonify({
            "running": sync_state["running"],
            "message": sync_state["message"],
            "last_error": sync_state["last_error"],
            "progress": sync_state["progress"],
        })
