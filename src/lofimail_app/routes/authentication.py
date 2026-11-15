"""Login and landing-page routes."""

from flask import render_template, redirect, request, session, url_for

from tools.imapconnect import mailconnect


def index():
    return render_template("login.html")


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

        return redirect(url_for("show_mailbox"))
    except Exception as error:
        print(f"Error: {error}")
        return render_template("login.html")


def register_authentication_routes(app):
    app.add_url_rule("/", endpoint="index", view_func=index, methods=["GET"])
    app.add_url_rule("/login", endpoint="connect_mail", view_func=connect_mail, methods=["POST"])
