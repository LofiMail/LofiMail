from flask import Flask, request, jsonify, render_template, session
import time
# Import the mailconnect function
from src.tools.imapconnect import mailconnect, fetch_emails_from_all_folders
from src.tools.tohtml import db_email_to_html, db_email_to_modalhtml
from src.tools.tohtml import  generate_email_modal
from flask_sqlalchemy import SQLAlchemy
from flask import jsonify, abort

from src.database import db, models
from src.database.models import Metadata, Mail
from src.database.utils import fetch_mails_from_local_db

from src.tools.processmail import update_db_emailtags, summarize_body

import os, re


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


    @app.route('/')
    def index():
        return render_template('login.html')  # Render your login form template

    @app.route('/login', methods=['POST'])
    def connect_mail():
        print(f"Request object: {request}")
        try:
            # Extract form data
            email = request.form.get('email')
            password = request.form.get('password')
            imap_server = request.form.get('imap')

            print(f"Login information: {email, password, imap_server}")


            # Perform IMAP connection
            mail = mailconnect(email, password, imap_server)
            # Return success response
            print(jsonify({'status': 'success', 'message': 'Logged in successfully!'}))

            # Fetch new mails from the imap server to the database.
            fetch_emails_from_all_folders(mail, db)

            print("\n**************\nNow retrieveing emails from local db\n***************\n")
            mails = fetch_mails_from_local_db(db)
            htmlmails=[]

            EXCLUDED_FOLDERS = ["Spam", "Trash", "Sent", "Junk", "Deleted Items",
                                "Replied"]  # Adjust based on server naming

            for _email in mails:
                print(
                    f"ID: {_email.id}, Email_id: {_email.email_id}, Subject: {_email.subject}, From: {_email.sender}, Date: {_email.date_received}")
                if _email.server_folder not in EXCLUDED_FOLDERS and _email.sender != email:
                    update_db_emailtags(_email, db)
                    html = db_email_to_html(_email, selfmail=email)
                    htmlmails.append(html)



            # #time.sleep(5)
            # status, messages = mail.search(None, 'SINCE', '19-Dec-2024')
            # print("MESSAGES", messages)
            # email_ids = messages[0].split()[:10]
            # mails = htmlmails(mail,email_ids,myemail=email)


            #Here, we should download all mails contents entirely, not just ids !! [Caching mail is not possible, and alternative is to reconnect all the time, we don't want that]
            #for email_id in email_ids:
            #    status, data = mail.fetch(email_id, "(RFC822)")



            return render_template('lofimail.html', mails=htmlmails)

        except Exception as e:
            # Handle errors and return failure response
            print(f"Error: {e}")
            print(jsonify({'status': 'error', 'message': str(e)}))
            return render_template('login.html')



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



    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
