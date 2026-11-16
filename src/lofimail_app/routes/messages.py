from flask import Blueprint, abort, jsonify

from database.models import Mail
from ..services.email_rendering import db_email_to_modalhtml

bp = Blueprint("messages", __name__)


@bp.route("/get-email-content/<email_id>")
def get_email_content(email_id):
    print("Enter Get_email_content", email_id)
    mail = Mail.query.filter_by(email_id=email_id).first()
    if not mail:
        abort(404, description="Email not found")
    return jsonify({"html": db_email_to_modalhtml(mail)})
