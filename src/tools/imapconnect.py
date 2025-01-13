import imaplib
import email
from email.header import decode_header
from email.utils import getaddresses
from src.tools.decode import parse_email_headers, extract_email_body


from src.tools.tohtml import generate_email_html, generate_email_modal
from src.database.utils import get_last_email_uid, update_last_email_uid

from src.database.models import Mail, Recipient
from datetime import datetime, timedelta
from dateutil.parser import parse
from email.utils import parsedate_to_datetime
import pytz

def mailconnect(email,password,imap_server):
    # IMAP connection and email retrieval (simplified for context)
    mail = imaplib.IMAP4_SSL(imap_server)
    mail.login(email, password)
    print("Logged in successfully.")
    mail.select("inbox")
    return mail


def fetch_newemails_from_server(mail, database):
    last_uid = get_last_email_uid()
    print('LAST UID:',last_uid)

    # TODO:  ensure last_uid is integer type, and not e.g.  b'247440'. Convert it if necessary.

    if int(last_uid) == 0:
        three_days_ago = (datetime.today() - timedelta(days=3)).strftime("%d-%b-%Y")
        status, messages = mail.uid("SEARCH", None, f"SINCE {three_days_ago}")
        print("3 days ago",three_days_ago)
        if status == "OK" and messages[0]:
            email_uids = messages[0].split()
            highest_uid = int(email_uids[-1].decode())  # The most recent email UID
            print(f"Highest UID from today: {highest_uid}")
        else:
            highest_uid = None
            print("No emails found from today.")
        # Step 3: Fetch the last 100 emails based on highest UID
        if highest_uid:
            # Calculate the range for the last 100 emails
            start_uid = max(highest_uid - 100 + 1, 1)  # Ensure we don't go below UID 1
            end_uid = highest_uid

            # Fetch the emails in that UID range
            status, messages = mail.uid("SEARCH", None, f"UID {start_uid}:{end_uid} NOT DELETED")
            if status == "OK":
                uids = messages[0].split()
                print(f"Retrieved UIDs (non-deleted): {[uid.decode() for uid in uids]}")
            else:
                print(f"UID SEARCH failed with status: {status}, messages: {messages}")
    else:
        print("OK UID")
        # Fetch messages with UID greater than or equal to last_uid
        status, messages = mail.uid("SEARCH", None, f"UID {last_uid}:*")

    # Fetch new emails
    email_ids = messages[0].split()


    for email_id in email_ids:
        uid = email_id.decode()
        print("Process now mail", email_id)


        # Fetch the email
        status, msg_data = mail.uid("FETCH", email_id, '(RFC822)')

        if status == "OK":
            print(f"Successfully fetched email UID {email_id.decode()}: {msg_data}")
        else:
            print(f"Failed to fetch email UID {email_id.decode()}: {msg_data}")
        for response_part in msg_data:
            print("Process part: ", response_part)

            if isinstance(response_part, tuple) and len(response_part) > 1:

                metadata = response_part[0]
                raw_email = response_part[1]
                print("Raw Email:", raw_email)

                # Parse email data
                email_data = parse_email_headers(raw_email)
                print("Email:",email_data)

                if Mail.query.filter_by(email_id=email_data["message_id"]).first():
                    print(f"Email with ID {email_id.decode()} already exists in local db. Skipping...")
                else:
                    parsed_email = email.message_from_bytes(raw_email)
                    body = extract_email_body(parsed_email)
                    #print("Email body", body)
                    # Save to the database
                    new_mail = Mail(
                        email_id=email_data["message_id"],
                        sender=email_data['From'],
                        subject=email_data['Subject'],
                        date_received=#parse(email_data['Date']),
                        parsedate_to_datetime(email_data['Date']).astimezone(pytz.utc),
                        body=body,
                        summary="Email summary here",
                    )
                    print("Mail creation is OK")
                    database.session.add(new_mail)
                    database.session.commit()  # Commit to get the mail's ID

                    to_recipients = getaddresses([email_data.get("To", "")])
                    print("Recipients to is ok")
                    # Store recipients
                    for name, mmail in to_recipients:
                        new_recipient = Recipient(
                            email_id=new_mail.id,  # Link to the Mail record
                            recipient=mmail,
                            type="to"
                        )
                        database.session.add(new_recipient)
                    print("Recipients to is added")

                    cc_recipients = getaddresses([email_data.get("Cc", "")])
                    print("Recipients cc is ok")
                    for name, mmail in cc_recipients:
                        new_recipient = Recipient(
                            email_id=new_mail.id,  # Link to the Mail record
                            recipient=mmail,
                            type="cc"
                        )
                        database.session.add(new_recipient)
                    print("Recipients cc is added")

    if email_ids:
        update_last_email_uid(email_ids[-1].decode(),database)
    database.session.commit()







# DEPRECATED
def htmlmails(mail, email_ids,myemail="your_email@example.com"):
    mails_html = []
    for email_id in email_ids:
        status, msg_data = mail.fetch(email_id, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                # Parse the email
                msg = email.message_from_bytes(response_part[1])
                email_data = parse_email_headers(msg)
                # Generate the HTML for the email
                html = generate_email_html(email_id,email_data, myemail)
                print("htmlmails: Generate email html output")
                print(html)
                mails_html.append(html)
    return mails_html


def displaymails(mail, email_ids):
    # Fetch the first 10 emails
    for i, email_id in enumerate(email_ids):
        # Fetch the email by ID
        status, msg_data = mail.fetch(email_id, "(RFC822)")
        # print("*************\n",status,"\n",msg_data,"\n///////////////")

        status, data = mail.fetch(email_id, '(UID)')
        # Parse the UID from the response
        if status == "OK":
            uid = data[0].decode().split()[2]

        # Parse the email
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                # Decode the email subject
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    # Convert to string
                    subject = subject.decode(encoding if encoding else "utf-8")
                print(f"Email {i + 1} Subject: {subject}")

                # Get sender
                from_ = msg.get("From")
                print(f"From: {from_}")
                to_ = msg.get("To")
                print(f"To: {to_}")

                # If the email has a body, print it
                if msg.is_multipart():
                    for part in msg.walk():
                        # Look for plain text or HTML part
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            print(f"Body: {body}")
                            break
                else:
                    body = msg.get_payload(decode=True).decode()
                    print(f"Body: {body}")

    return uid



if __name__ == '__main__':
    try:

        # Account credentials
        # email_address = "email"  # Replace with your email address
        # password = "ipassword"  # Replace with your LDAP password
        # imap_server = "imap.company.fr"  # Replace with your IMAP server address

        # Connect to the server and log in
        mail = mailconnect(email_address,password,imap_server)

        # Search for all emails
        # status, messages = mail.search(None, "ALL")
        status, messages = mail.search(None, 'SINCE', '25-Nov-2024')
        # status, messages = mail.uid('search', None, 'UID 1000:*')
        # status, messages = mail.uid('search', None, f'UID {uid}:*')

        # Get the list of email IDs
        email_ids = messages[0].split()[:10]

        # uid=displaymails(mail,email_ids)
        # htmlmails(mail,email_ids)
        html = generate_email_modal(mail, email_ids[2])

        # Print or save the HTML for rendering
        print(html)

        # Close the connection and logout
        mail.logout()


        ###################
        # Check for mails after 5000:
        last_processed_uid = "5000"  # Replace with the last stored UID

        # Search for new emails with UID greater than the last processed
        status, messages = mail.uid("SEARCH", f"UID {last_processed_uid}:*")
        new_email_uids = messages[0].split()

        # Update last_processed_uid to the newest UID
        if new_email_uids:
            last_processed_uid = new_email_uids[-1].decode()
            print(f"Updated last UID to: {last_processed_uid}")

        # Fetch and process the new emails
        for uid in new_email_uids:
            status, data = mail.uid("FETCH", uid, "(RFC822)")
            email_message = email.message_from_bytes(data[0][1])
            # Process the email

    except Exception as e:
        print(f"An error occurred: {e}")
