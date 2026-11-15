"""Routes for starting and inspecting mailbox synchronization."""

import threading

from flask import current_app, jsonify, session

from ..synchronization import set_sync_state, sync_lock, sync_state, sync_worker


def start_sync():
    if sync_state["running"]:
        return jsonify({
            "status": "already_running",
            "message": sync_state["message"],
        }), 200

    email = session.get("email")
    password = session.get("password")
    imap_server = session.get("imap")

    if not (email and password and imap_server):
        return jsonify({"status": "error", "message": "Not logged in"}), 403

    application = current_app._get_current_object()
    thread = threading.Thread(
        target=sync_worker,
        args=(application, email, password, imap_server),
        daemon=True,
    )
    thread.start()
    return jsonify({"status": "started", "message": "Background sync started"}), 202


def sync_status():
    with sync_lock:
        return jsonify({
            "running": sync_state["running"],
            "message": sync_state["message"],
            "last_error": sync_state["last_error"],
            "progress": sync_state["progress"],
        })


def register_synchronization_routes(app):
    app.add_url_rule(
        "/start_sync",
        endpoint="start_sync",
        view_func=start_sync,
        methods=["POST"],
    )
    app.add_url_rule(
        "/sync_status",
        endpoint="sync_status",
        view_func=sync_status,
        methods=["GET"],
    )
