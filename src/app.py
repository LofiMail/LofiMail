from flask import Flask, request, jsonify, render_template, session
from flask import redirect, url_for
from flask import send_file
import edge_tts
import asyncio
import uuid
import threading
import time
import secrets
# Import the mailconnect function
from tools.imapconnect import mailconnect, fetch_emails_from_all_folders
from tools.tohtml import db_email_to_html, db_email_to_modalhtml
from flask_sqlalchemy import SQLAlchemy
from flask import jsonify, abort

from database import db, models
from database.models import Metadata, Mail
from database.utils import fetch_mails_from_local_db

from tools.processmail import update_db_emailtags, summarize_body

import os, re




# Simple in-memory sync status. For multi-process deployments, use Redis/DB.
sync_state = {
    "running": False,
    "message": "Idle",
    "last_error": None,
    "progress": 0,  # optional percent-ish info (0-100)
}
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


def sync_worker(user_email=None, user_password=None, imap_server=None):
    """
    This runs in a thread. It should create its own app context if needed.
    We assume fetch_emails_from_all_folders(mail, db) uses the 'db' SQLAlchemy session object.
    """
    try:
        set_sync_state(running=True, message="Starting sync...", last_error=None, progress=0)
        # Create an app context to use `db` and models safely
        with app.app_context():
            # If you have stored credentials per-session or per-user, pass them here.
            # For simplicity, try to connect using provided args, or implement mailconnect as needed.
            if not (user_email and user_password and imap_server):
                # If you don't pass creds, attempt to use previously-stored connection info or raise.
                raise ValueError("Mail connection parameters missing for background sync.")

            set_sync_state(message="Connecting to IMAP server...")
            mail = mailconnect(user_email, user_password, imap_server)

            set_sync_state(message="Fetching new emails (scanning folders)...")
            # Optionally, you can wrap fetch_emails_from_all_folders to accept a callback
            # so you can update progress. Here we'll do naive progress updates.
            fetch_emails_from_all_folders(mail, db)

            set_sync_state(message="Finalizing (committing)...", progress=90)
            # ensure DB commit if needed (fetch_emails_from_all_folders should commit)
            db.session.commit()

            set_sync_state(message="Sync complete", progress=100)
            # small delay to let frontend show "Done"
            time.sleep(0.2)
    except Exception as e:
        set_sync_state(message="Sync failed", last_error=str(e))
        app.logger.exception("Background sync failed")
    finally:
        # ensure running is cleared
        set_sync_state(running=False)




def generate_unique_filename(email_address, imap_address):
    # Sanitize email address by removing special characters and dots
    sanitized_email = re.sub(r'[^a-zA-Z0-9]', '', email_address)
    sanitized_imap = re.sub(r'[^a-zA-Z0-9]', '', imap_address)

    # Combine both sanitized parts to form a unique identifier
    unique_id = f"{sanitized_email}_{sanitized_imap}"

    return unique_id

def database_connect(app,name="db.sqlite"):
    # Path to the local SQLite database file
    db_path = os.path.join(os.path.dirname(__file__), "database", name)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # PostgreSQL connection string
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@localhost/dbname'
    # app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Ensure the database directory exists
    db_dir = os.path.join(os.path.dirname(__file__), "database")
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    # Initialize the database
    db.init_app(app)

    # Create the database tables explicitly during app creation
    with app.app_context():
        # Automatically create database file and tables if they don't exist
        db.create_all()

        # Initialize the UID key if not already present
        if not Metadata.query.filter_by(key="last_email_uid").first():
            last_email_uid = Metadata(key="last_email_uid", value="0")
            db.session.add(last_email_uid)
            db.session.commit()

def create_app():
    app = Flask(__name__)
    database_connect(app)

    # --- Automatic secret key handling ---
    keyfile = "secret_key.txt"

    if os.path.exists(keyfile):
        # Reuse the same key (keeps sessions working between restarts)
        with open(keyfile, "r") as f:
            app.secret_key = f.read().strip()
    else:
        # Generate a new random one and save it for next time
        new_key = secrets.token_hex(32)
        with open(keyfile, "w") as f:
            f.write(new_key)
        app.secret_key = new_key


    @app.route('/')
    def index():
        return render_template('login.html')  # Render your login form template

    @app.route('/start_sync', methods=['POST'])
    def start_sync():
        """
        Start a background sync thread. Returns immediately with status.
        Expect JSON body like: {"email":"...", "password":"...", "imap":"imap.example.com"}
        or pick the credentials from the logged-in session if you manage them.
        """
        if sync_state["running"]:
            return jsonify({"status": "already_running", "message": sync_state["message"]}), 200

        email = session.get('email')
        password = session.get('password')
        imap_server = session.get('imap')

        if not (email and password and imap_server):
            return jsonify({"status": "error", "message": "Not logged in"}), 403

        t = threading.Thread(target=sync_worker, args=(email, password, imap_server), daemon=True)
        t.start()
        return jsonify({"status": "started", "message": "Background sync started"}), 202

    @app.route('/sync_status', methods=['GET'])
    def sync_status():
        """Return current sync status."""
        with sync_lock:
            return jsonify({
                "running": sync_state["running"],
                "message": sync_state["message"],
                "last_error": sync_state["last_error"],
                "progress": sync_state["progress"]
            })

    @app.route('/login', methods=['POST'])
    def connect_mail():
        # with open("log.txt", "a", encoding="utf-8") as f:
        #     f.write("Hello from /login\n")
        # print(f"Request object: {request}")
        try:
            # Extract form data
            email = request.form.get('email')
            password = request.form.get('password')
            imap_server = request.form.get('imap')

            print(f"Login information: {email, imap_server}")


            # Perform IMAP connection
            mail = mailconnect(email, password, imap_server)
            # Return success response
            print(jsonify({'status': 'success', 'message': 'Logged in successfully!'}))

            # ✅ Store minimal info in session (password stays only for current session)
            session['email'] = email
            session['password'] = password
            session['imap'] = imap_server

            # Optionally, run initial local fetch to populate DB
            #fetch_emails_from_all_folders(mail, db)

            # Redirect to mailbox (the page with Sync button)
            return redirect(url_for('show_mailbox'))
            #
            # print("\n**************\nNow retrieveing emails from local db\n***************\n")
            # mails = fetch_mails_from_local_db(db)
            # htmlmails=[]
            #
            # EXCLUDED_FOLDERS = ["Spam", "Trash", "Sent", "Junk", "Deleted Items",
            #                     "Replied"]  # Adjust based on server naming
            #
            # for _email in mails:
            #     print(
            #         f"ID: {_email.id}, Email_id: {_email.email_id}, Subject: {_email.subject}, From: {_email.sender}, Date: {_email.date_received}")
            #     if _email.server_folder not in EXCLUDED_FOLDERS and _email.sender != email:
            #         update_db_emailtags(_email, db)
            #         html = db_email_to_html(_email, selfmail=email)
            #         htmlmails.append(html)
            #
            # return render_template('lofimail.html', mails=htmlmails)

        except Exception as e:
            # Handle errors and return failure response
            print(f"Error: {e}")
            print(jsonify({'status': 'error', 'message': str(e)}))
            return render_template('login.html')

    @app.route('/mailbox')
    def show_mailbox():
        email = session.get('email')
        if not email:
            return redirect(url_for('login_page'))  # or wherever your login form is

        mails = fetch_mails_from_local_db(db)
        htmlmails = []
        EXCLUDED_FOLDERS = ["Spam", "Trash", "Sent", "Junk", "Deleted Items", "Replied"]

        for _email in mails:
            if _email.server_folder not in EXCLUDED_FOLDERS and _email.sender != email:
                update_db_emailtags(_email, db)
                html = db_email_to_html(_email, selfmail=email)
                htmlmails.append(html)

        return render_template('lofimail.html', mails=htmlmails, selfmail=email)

    @app.route('/mails_fragment')
    def mails_fragment():
        """
        Return an HTML fragment with the mails list. In your code you build htmlmails list.
        Here we reuse your rendering function that creates HTML for mails (db_email_to_html).
        You can also render a template fragment with a Jinja template for each mail.
        """
        email = session.get('email')
        if not email:
            return redirect(url_for('login_page'))  # or wherever your login form is

        mails = fetch_mails_from_local_db(db)
        htmlmails = []
        EXCLUDED_FOLDERS = ["Spam", "Trash", "Sent", "Junk", "Deleted Items", "Replied"]

        for _email in mails:
            if _email.server_folder not in EXCLUDED_FOLDERS and _email.sender != email:
                update_db_emailtags(_email, db)
                html = db_email_to_html(_email, selfmail=email)
                htmlmails.append(html)

        #return render_template('lofimail.html', mails=htmlmails, selfmail=email)
        # Return the inner HTML content only
        return "\n".join(htmlmails)
        #return jsonify({"html": "".join(htmlmails)})


    @app.route("/get-email-content/<email_id>")
    def get_email_content(email_id):
        # Fetch and parse the email content

        print("Enter Get_email_content", email_id)
        mail = Mail.query.filter_by(email_id=email_id).first()

        if not mail:
            # Return a 404 error if the mail is not found
            abort(404, description="Email not found")

        email_content = db_email_to_modalhtml(mail)  # Your function to generate the HTML content
        #print("Email_content:", email_content)

        return jsonify({"html": email_content})


    @app.route('/lofimail')
    def lofi_mail():
        # Handle direct access if needed
        return render_template('lofimail.html')

    from tools.tospeech import speak_text
    @app.route('/speak')
    def speak():
        text = request.args.get('text', '')
        print("SPEAK",text)
        return speak_text(text)

    # from tools.tospeech import generate_tts
    # @app.route('/speak')
    # def speak(text):
    #    # text = request.args.get("text", "Bonjour Jean, bienvenue sur StaRL !")
    #     voice = request.args.get("voice", "fr-FR-DeniseNeural")
    #     filename = f"tmp_{uuid.uuid4()}.mp3"
    #
    #     try:
    #         asyncio.run(generate_tts(text, voice, filename))
    #
    #         # Wait briefly if file not yet fully written
    #         for _ in range(10):
    #             if os.path.exists(filename) and os.path.getsize(filename) > 0:
    #                 break
    #             time.sleep(0.1)
    #
    #         if not os.path.exists(filename):
    #             return jsonify({"error": "Audio file was not generated"}), 500
    #
    #         response = send_file(filename, mimetype="audio/mpeg")
    #
    #         @response.call_on_close
    #         def cleanup():
    #             try:
    #                 os.remove(filename)
    #             except Exception:
    #                 pass
    #
    #         return response
    #
    #     except Exception as e:
    #         print("❌ Error:", e)
    #         return jsonify({"error": str(e)}), 500
    return app




if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, use_reloader=False)
