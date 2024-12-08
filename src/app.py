from flask import Flask, request, jsonify, render_template
import time
# Import the mailconnect function
from src.tools.imapconnect import mailconnect

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
        #mail = mailconnect(email, password, imap_server)
        time.sleep(5)

        mails = ["Mail 1", "Mail 2", "Mail 3"]
        # Return success response
        print(jsonify({'status': 'success', 'message': 'Logged in successfully!'}))

        return render_template('lofimail.html', mails=mails)
    except Exception as e:
        # Handle errors and return failure response
        print(f"Error: {e}")
        print(jsonify({'status': 'error', 'message': str(e)}))
        return render_template('lofimail.html', mails=mail)



@app.route('/lofimail')
def lofi_mail():
    # Handle direct access if needed
    return render_template('lofimail.html')

if __name__ == '__main__':
    app.run(debug=True)
