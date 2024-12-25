from flask import Flask, request, jsonify, render_template, session
import time
# Import the mailconnect function
from src.tools.imapconnect import mailconnect, htmlmails
from src.tools.tohtml import  generate_email_modal

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('login.html')  # Render your login form template

@app.route('/login', methods=['POST'])
def connect_mail():
    try:
        # Extract form data
        email = request.form.get('email')
        password = request.form.get('password')
        imap_server = request.form.get('imap')

        print(f"Login information: {email, password, imap_server}")

        # Perform IMAP connection
        mail = mailconnect(email, password, imap_server)

        print("Connection OK")


        #time.sleep(5)

        status, messages = mail.search(None, 'SINCE', '19-Dec-2024')
        print("MESSAGES", messages)
        email_ids = messages[0].split()[:10]
        mails = htmlmails(mail,email_ids,myemail=email)

        #Here, we should download all mails contents entirely, not just ids !! [Caching mail is not possible, and alternative is to reconnect all the time, we don't want that]
        #for email_id in email_ids:
        #    status, data = mail.fetch(email_id, "(RFC822)")


        # Return success response
        print(jsonify({'status': 'success', 'message': 'Logged in successfully!'}))

        return render_template('lofimail.html', mails=mails)

    except Exception as e:
        # Handle errors and return failure response
        print(f"Error: {e}")
        print(jsonify({'status': 'error', 'message': str(e)}))
        return render_template('login.html')



@app.route("/get-email-content/<email_id>")
def get_email_content(email_id):
    # Fetch and parse the email content

    print("Enter Get_email_content", email_id)
    mail = cache.get('mail_connection')
    if not mail:
        print("NO MAIL IN CACHE")
        return jsonify({"html": "Error: Not connected to the mail server"}), 401

    email_content = generate_email_modal(mail, email_id)  # Your function to generate the HTML content
    print("Email_content:", email_content)

    return jsonify({"html": email_content})


@app.route('/lofimail')
def lofi_mail():
    # Handle direct access if needed
    return render_template('lofimail.html')

if __name__ == '__main__':
    app.run(debug=True)
