from flask import Blueprint, redirect, render_template, request, session, url_for

from ..services.imap import mailconnect

bp = Blueprint("authentication", __name__)


@bp.route("/login", methods=["POST"])
def connect_mail():
    try:
        email = request.form.get("email")
        password = request.form.get("password")
        imap_server = request.form.get("imap")
        print(f"Login information: {email, imap_server}")
        mailconnect(email, password, imap_server)
        session["email"] = email
        session["password"] = password
        session["imap"] = imap_server
        return redirect(url_for("mailbox.show_mailbox"))
    except Exception as error:
        print(f"Error: {error}")
        return render_template("login.html")
