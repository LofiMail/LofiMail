import imaplib
import email
from email.header import decode_header

from src.tools.tohtml import generate_email_html, generate_email_modal



def mailconnect(email,password,imap_server):
    # IMAP connection and email retrieval (simplified for context)
    mail = imaplib.IMAP4_SSL(imap_server)
    mail.login(email, password)
    print("Logged in successfully.")
    mail.select("inbox")
    return mail



def htmlmails(mail, email_ids,myemail="your_email@example.com"):
    mails_html = []
    for email_id in email_ids:
        status, msg_data = mail.fetch(email_id, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                # Parse the email
                msg = email.message_from_bytes(response_part[1])
                email_data = {
                    "From": msg.get("From"),
                    "Subject": msg.get("Subject"),
                    "Date": msg.get("Date"),
                    "To": msg.get("To"),
                    "Cc": msg.get("Cc"),
                }
                print("Ok")
                # Generate the HTML for the email
                html = generate_email_html(email_id,email_data, myemail)
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
