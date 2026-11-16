from flask import Blueprint, redirect, render_template, session, url_for

from database import db
from database.utils import fetch_mails_from_local_db
from ..services.email_processing import update_db_emailtags
from ..services.email_rendering import db_email_to_html

bp = Blueprint("mailbox", __name__)
EXCLUDED_FOLDERS = ["Spam", "Trash", "Sent", "Junk", "Deleted Items", "Replied"]


def _render_mails(email):
    mails = fetch_mails_from_local_db(db)
    htmlmails = []
    for mail in mails:
        if mail.server_folder not in EXCLUDED_FOLDERS and mail.sender != email:
            update_db_emailtags(mail, db)
            htmlmails.append(db_email_to_html(mail, selfmail=email))
    return htmlmails


@bp.route("/mailbox")
def show_mailbox():
    email = session.get("email")
    if not email:
        return redirect(url_for("login_page"))
    return render_template("lofimail.html", mails=_render_mails(email), selfmail=email)


@bp.route("/mails_fragment")
def mails_fragment():
    email = session.get("email")
    if not email:
        return redirect(url_for("login_page"))
    return "\n".join(_render_mails(email))


@bp.route("/lofimail")
def lofi_mail():
    return render_template("lofimail.html")
