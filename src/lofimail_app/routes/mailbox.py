"""Mailbox page and message-list fragment routes."""

from flask import redirect, render_template, session, url_for

from database import db
from database.utils import fetch_mails_from_local_db
from tools.processmail import update_db_emailtags
from tools.tohtml import db_email_to_html


EXCLUDED_FOLDERS = ["Spam", "Trash", "Sent", "Junk", "Deleted Items", "Replied"]


def _render_mail_list(email):
    mails = fetch_mails_from_local_db(db)
    htmlmails = []

    for mail in mails:
        if mail.server_folder not in EXCLUDED_FOLDERS and mail.sender != email:
            update_db_emailtags(mail, db)
            htmlmails.append(db_email_to_html(mail, selfmail=email))

    return htmlmails


def show_mailbox():
    email = session.get("email")
    if not email:
        return redirect(url_for("login_page"))

    htmlmails = _render_mail_list(email)
    return render_template("lofimail.html", mails=htmlmails, selfmail=email)


def mails_fragment():
    email = session.get("email")
    if not email:
        return redirect(url_for("login_page"))

    return "\n".join(_render_mail_list(email))


def lofi_mail():
    return render_template("lofimail.html")


def register_mailbox_routes(app):
    app.add_url_rule("/mailbox", endpoint="show_mailbox", view_func=show_mailbox, methods=["GET"])
    app.add_url_rule(
        "/mails_fragment",
        endpoint="mails_fragment",
        view_func=mails_fragment,
        methods=["GET"],
    )
    app.add_url_rule("/lofimail", endpoint="lofi_mail", view_func=lofi_mail, methods=["GET"])
