"""Individual email rendering routes."""

from flask import abort, jsonify

from database.models import Mail
from tools.tohtml import db_email_to_modalhtml


def get_email_content(email_id):
    print("Enter Get_email_content", email_id)
    mail = Mail.query.filter_by(email_id=email_id).first()

    if not mail:
        abort(404, description="Email not found")

    email_content = db_email_to_modalhtml(mail)
    return jsonify({"html": email_content})


def register_message_routes(app):
    app.add_url_rule(
        "/get-email-content/<email_id>",
        endpoint="get_email_content",
        view_func=get_email_content,
        methods=["GET"],
    )
