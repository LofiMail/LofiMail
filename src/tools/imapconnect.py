import imaplib
import email
from email.header import decode_header
from email.utils import getaddresses
from src.tools.decode import parse_email_headers, extract_email_body,extract_email_body_newcontent, extract_novel_content


from src.tools.tohtml import generate_email_html, generate_email_modal
from src.database.utils import get_last_email_uid, update_last_email_uid

from src.database.models import Mail, Recipient, FolderStatus
from datetime import datetime, timedelta
from dateutil.parser import parse
from email.utils import parsedate_to_datetime
import pytz

from src.tools.processmail import summarize_body

def mailconnect(email,password,imap_server):
    # IMAP connection and email retrieval (simplified for context)
    mail = imaplib.IMAP4_SSL(imap_server)
    mail.login(email, password)
    print("Logged in successfully.")
    mail.select("inbox")
    return mail

def get_new_emails(mail, database, max_emails=50):
    # Get the date 3 days ago in the format required by IMAP
    three_days_ago = (datetime.now() - timedelta(days=3)).strftime("%d-%b-%Y")

    # Connect to local database
    cursor = database.cursor()

    # Get all folder names
    status, folders_response = mail.list()
    all_new_emails = []
    total_new_count = 0

    for folder_info in folders_response:
        if not folder_info:
            continue

        # Parse folder name from response
        folder_parts = folder_info.decode().split(' "')
        if len(folder_parts) < 2:
            continue

        folder_name = folder_parts[-1].strip('"')

        try:
            # Select the folder
            status, select_data = mail.select(f'"{folder_name}"', readonly=True)
            if status != 'OK':
                continue

            # Get the highest UID we've seen for this folder
            folder_status = FolderStatus.query.filter_by(folder_name=folder_name).first()

            if folder_status:
                highest_uid = int(folder_status.highest_uid)
                three_days_ago = (datetime.now() - timedelta(days=3)).strftime("%d-%b-%Y")

                # Get emails with UIDs higher than our highest AND within date range
                status, messages = mail.uid('SEARCH', None, f'UID {highest_uid + 1}:* SINCE {three_days_ago}')
            else:
                # First time checking this folder
                folder_status = FolderStatus(folder_name=folder_name, highest_uid='0')
                database.session.add(folder_status)

                # Just use the date range for the first check
                three_days_ago = (datetime.now() - timedelta(days=3)).strftime("%d-%b-%Y")
                status, messages = mail.uid('SEARCH', None, f'SINCE {three_days_ago}')

            if status != 'OK' or not messages[0]:
                folder_status.last_checked = datetime.utcnow()
                database.session.commit()
                return []

            uid_list = messages[0].decode().split()

            # Process new emails (limited to max_emails)
            for uid in uid_list[:max_emails]:
                # Fetch and process the email
                email_data = fetch_single_email(mail, folder_name, uid, cursor)

                # Add to results
                all_new_emails.append(email_data)

                # Update the highest UID if this one is higher
                uid_int = int(uid)
                if uid_int > int(folder_status.highest_uid):
                    folder_status.highest_uid = uid

            # Update the last checked time
            folder_status.last_checked = datetime.utcnow()
            # Commit changes to database
            database.commit()
            database.close()

        except Exception as e:
            print(f"Error processing folder {folder_name}: {e}")
        finally:
            # Close the currently selected folder
            mail.close()


    # Logout from server
    mail.logout()

    return all_new_emails

def fetch_single_email(mail, folder_name, email_uid, database_cursor):
    # First get just headers to check if we want this email
    status, header_data = mail.uid('FETCH', email_uid, '(BODY.PEEK[HEADER])')
    if status != 'OK':
        return {}

    # Parse header to get basic info
    raw_header = header_data[0][1]
    email_message = email.message_from_bytes(raw_header)
    subject = email_message['Subject']
    sender = email_message['From']
    date = email_message['Date']

    # Now fetch the full message
    status, full_data = mail.uid('FETCH', uid, '(RFC822)')
    if status != 'OK':
        return {}

    raw_email = full_data[0][1]
    full_message = email.message_from_bytes(raw_email)

    # Store email in local database
    database_cursor.execute(
        "INSERT INTO emails (folder, uid, subject, sender, date, content) VALUES (?, ?, ?, ?, ?, ?)",
        (folder_name, uid, subject, sender, date, raw_email)
    )

    # Add to our results
    email_data = {
        'folder': folder_name,
        'uid': uid,
        'subject': subject,
        'sender': sender,
        'date': date,
        'full_message': full_message
    }
    return email_data


# Currently main function called:
def fetch_emails_from_all_folders(mail, database):
    last_uid = get_last_email_uid()
    print('LAST UID:', last_uid)
    # TODO:  ensure last_uid is integer type, and not e.g.  b'247440'. Convert it if necessary.

    status, folders = mail.list()
    if status != "OK":
        print("Failed to retrieve folders.")
        return

    highest_uid = last_uid
  # Loop through each folder and fetch emails
    for folder in folders:
        parts = folder.decode().split(' "/" ')
        if len(parts) < 2:
            print(f"Skipping invalid folder format: {folder}")
            continue

        folder_name = parts[-1].strip('"')  # Extract the folder name, removing extra quotes
        print(f"Checking folder: {folder_name}")

        # Select the folder
        status, _ = mail.select(f'"{folder_name}"', readonly=True)  # Readonly mode to avoid modifying status
        if status != "OK":
            print(f"Skipping folder {folder_name} (selection failed).")
            continue

        email_ids=fetch_newemails_from_folder(mail, database,last_uid, folder_name=folder_name)
        if email_ids:
            highest_uid = max(highest_uid, email_ids[-1].decode())

    update_last_email_uid(highest_uid, database)
    database.session.commit()

def fetch_emails_from_all_folders2(mail, database):
    last_uid = get_last_email_uid()
    print('LAST UID:', last_uid)
    # TODO:  ensure last_uid is integer type, and not e.g.  b'247440'. Convert it if necessary.

    status, folders = mail.list()
    if status != "OK":
        print("Failed to retrieve folders.")
        return
    full_email_uids= []

    # Loop through each folder and fetch emails
    for folder in folders:
        parts = folder.decode().split(' "/" ')
        if len(parts) < 2:
            print(f"Skipping invalid folder format: {folder}")
            continue

        folder_name = parts[-1].strip('"')  # Extract the folder name, removing extra quotes
        print(f"Checking folder: {folder_name}")

        # Select the folder
        status, _ = mail.select(f'"{folder_name}"', readonly=True)  # Readonly mode to avoid modifying status
        if status != "OK":
            print(f"Skipping folder {folder_name} (selection failed).")
            continue

        if int(last_uid) == 0:
            # Search emails in this folder
            three_days_ago = (datetime.today() - timedelta(days=3)).strftime("%d-%b-%Y")
            status, messages = mail.uid("SEARCH", None, f"SINCE {three_days_ago}")
            if status == "OK" and messages[0]:
                email_uids = messages[0].split()
                highest_uid = int(email_uids[-1].decode())  # The most recent email UID
                lowest_uid = int(email_uids[0].decode())  # The most recent email UID
                print(f"Found {len(email_uids)} emails in {folder_name}")
                # Step 3: Fetch the last 100 emails based on highest UID
                if highest_uid:
                    # Calculate the range for the last 100 emails
                    start_uid = max(lowest_uid - 100 + 1, 1)  # Ensure we don't go below UID 1
                    end_uid = highest_uid

                    # Fetch the emails in that UID range
                    status, messages = mail.uid("SEARCH", None, f"UID {start_uid}:{end_uid} NOT DELETED")
                    if status == "OK":
                        email_uids = messages[0].split()
                        full_email_uids +=email_uids
                        print(f"Retrieved UIDs (non-deleted): {[uid.decode() for uid in email_uids]}")
                    else:
                        print(f"UID SEARCH failed with status: {status}, messages: {messages}")
        else:
            # Fetch messages with UID greater than or equal to last_uid
            status, messages = mail.uid("SEARCH", None, f"UID {last_uid}:*")
            if status == "Ok":
                email_uids = messages[0].split()
                full_email_uids += email_uids
                print(f"Found {len(email_uids)} emails in {folder_name}")
                print(f"Retrieved UIDs (non-deleted): {[uid.decode() for uid in email_uids]}")

    print(f"Found {len(full_email_uids)} novel emails")
    highest_uid = last_uid
    for uid in full_email_uids:
        fetch_email(mail, uid, database)  # Fetch and process emails as before
        highest_uid = max(highest_uid, uid.decode())
    if full_email_uids:
        update_last_email_uid(highest_uid, database)
    database.session.commit()


def fetch_email(mail, email_id, database):
    """ Fetch and process a single email by UID """

    uid = email_id.decode()
    print("Process now mail", email_id, uid)

    status, flags_response = mail.uid("FETCH", email_id, "(FLAGS)")
    # Ensure response is valid
    if flags_response and isinstance(flags_response[0], tuple):
        is_unread = b"\\Seen" not in flags_response[0][1]  # Check flags properly
        print(f"Email UID {email_id} originally unread: {is_unread}")
    else:
        print(f"Warning: Could not retrieve flags for email UID {email_id}.")
        is_unread = False  # Assume it's read if we can't determine

    # Fetch the email
    status, msg_data = mail.uid("FETCH", email_id, '(RFC822)')  # This fetches the mail and tag is as "Read" on the server.
    # status, msg_data = mail.uid("FETCH", email_id, '(BODY.PEEK[])') # This fetches the mail only.

    if is_unread:
        mail.uid("STORE", email_id, "-FLAGS", r"(\Seen)")
        print(f"Email UID {email_id} marked back as unread.")

    if status == "OK":
        print(f"Successfully fetched email UID {email_id.decode()}")
    else:
        print(f"Failed to fetch email UID {email_id.decode()}")
    for response_part in msg_data:
        #print("Process part: ", response_part)

        if isinstance(response_part, tuple) and len(response_part) > 1:

            metadata = response_part[0]
            raw_email = response_part[1]
            print("Raw Email:", raw_email)

            # Parse email data
            email_data = parse_email_headers(raw_email)
            print("Email:", email_data)

            if Mail.query.filter_by(email_id=email_data["message_id"]).first():
                print(f"Email with ID {email_id.decode()} already exists in local db. Skipping...")
            else:
                parsed_email = email.message_from_bytes(raw_email)
                body = extract_email_body(parsed_email)
                summary = extract_novel_content(extract_email_body_newcontent(parsed_email))
                summary = summarize_body(summary)
                # print("Email body", body)
                # Save to the database
                new_mail = Mail(
                    email_id=email_data["message_id"],
                    sender=email_data['From'],
                    subject=email_data['Subject'],
                    date_received=  # parse(email_data['Date']),
                    parsedate_to_datetime(email_data['Date']).astimezone(pytz.utc),
                    body=body,
                    summary=summary,
                    parent_email_id=email_data['in_reply_to'],
                    is_most_recent=True,
                )
                print("Mail creation is OK")
                database.session.add(new_mail)
                database.session.commit()  # Commit to get the mail's ID

                if new_mail.parent_email_id:
                    # TODO: not "id=" it should be the processed id...
                    parent_email = Mail.query.filter_by(id=new_mail.parent_email_id).first()
                    if parent_email:
                        parent_email.is_most_recent = False
                database.session.commit()

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






def fetch_newemails_from_folder(mail, database, last_uid,folder_name):
    # TODO:  ensure last_uid is integer type, and not e.g.  b'247440'. Convert it if necessary.

    if int(last_uid) == 0: #First connection !
        three_days_ago = (datetime.today() - timedelta(days=3)).strftime("%d-%b-%Y")
        status, messages = mail.uid("SEARCH", None, f"SINCE {three_days_ago}")
        print("Looking for mails received up to 3 days ago",three_days_ago)
        if status == "OK" and messages[0]:
            email_uids = messages[0].split()
            highest_uid = int(email_uids[-1].decode())  # The most recent email UID
            lowest_uid = int(email_uids[0].decode())  # The most ancient email UID
            print(f"Highest UID from today: {highest_uid}")
        else:
            print("No emails found from 3 days ago.")
            nine_days_ago = (datetime.today() - timedelta(days=9)).strftime("%d-%b-%Y")
            status, messages = mail.uid("SEARCH", None, f"SINCE {nine_days_ago}")
            print("Looking for mails received up to 9 days ago",nine_days_ago)
            if status == "OK" and messages[0]:
                email_uids = messages[0].split()
                highest_uid = int(email_uids[-1].decode())
            else:
                highest_uid = None
                print("No emails found from 9 days ago.")
        # Step 3: Fetch the last 100 emails based on highest UID
        #if highest_uid:
        #    # Calculate the range for the last 100 emails
        #    start_uid = max(lowest_uid - 100 + 1, 1)  # Ensure we don't go below UID 1
        #    end_uid = highest_uid
        #
        #    # Fetch the emails in that UID range
        #    status, messages = mail.uid("SEARCH", None, f"UID {start_uid}:{end_uid} NOT DELETED")
        #    if status == "OK":
        #        uids = messages[0].split()
        #        print(f"Retrieved UIDs (non-deleted): {[uid.decode() for uid in uids]}")
        #    else:
        #        print(f"UID SEARCH failed with status: {status}, messages: {messages}")
    else:
        print("OK UID")
        # Fetch messages with UID greater than or equal to last_uid
        #Careful: assumes last_iud not too old (better retrieve last3= 3 days).
        status, messages = mail.uid("SEARCH", None, f"UID {last_uid}:*")
        if status == "OK" and messages[0]:
            email_uids = messages[0].split()
            highest_uid = int(email_uids[-1].decode())
        else:
            highest_uid = None

    if highest_uid:
        # Fetch new emails
        email_ids = messages[0].split()

        for email_id in email_ids[-5:]:
            uid = email_id.decode()
            print("Process now mail", email_id, "uid:", uid)

            status, flags_response = mail.uid("FETCH", email_id, "(FLAGS)")
            is_unread = b"\\Seen" not in flags_response[0]  # Check if \Seen flag is NOT present

            # Fetch the email
            status, msg_data = mail.uid("FETCH", email_id, '(RFC822)') # This fetches the mail and tag is as "Read" on the server.
            #status, msg_data = mail.uid("FETCH", email_id, '(BODY.PEEK[])') # This fetches the mail only.

            if is_unread:
                mail.uid("STORE", email_id, "-FLAGS", r"(\Seen)")
                print(f"Email UID {email_id} marked back as unread.")

            if status == "OK":
                print(f"Successfully fetched email UID {email_id.decode()}") #: {msg_data}")
            else:
                print(f"Failed to fetch email UID {email_id.decode()}")#: {msg_data}")
            for response_part in msg_data:
                #print("Process part: ", response_part)

                if isinstance(response_part, tuple) and len(response_part) > 1:
                    metadata = response_part[0]
                    raw_email = response_part[1]
                    #print("Raw Email:", raw_email)

                    # Parse email data
                    email_data = parse_email_headers(raw_email)
                    #print("Email:",email_data)

                    if Mail.query.filter_by(email_id=email_data["message_id"]).first():
                        print(f"Email with ID {email_id.decode()} already exists in local db. Skipping...")
                    else:
                        parsed_email = email.message_from_bytes(raw_email)
                        body = extract_email_body(parsed_email)
                        summary = extract_novel_content(extract_email_body_newcontent(parsed_email))
                        summary = summarize_body(summary)
                        #print("Email body", body)
                        # Save to the database
                        new_mail = Mail(
                            email_id=email_data["message_id"],# Internal Lofi ID
                            server_uid=uid,
                            sender=email_data['From'],
                            subject=email_data['Subject'],
                            date_received=#parse(email_data['Date']),
                            parsedate_to_datetime(email_data['Date']).astimezone(pytz.utc),
                            body=body,
                            summary=summary,
                            parent_email_id=email_data['in_reply_to'],
                            is_most_recent=True,
                            server_folder = folder_name,
                        )
                        print("Mail creation is OK")
                        database.session.add(new_mail)
                        database.session.commit()  # Commit to get the mail's ID

                        if new_mail.parent_email_id:
                            #TODO: not "id=" it should be the processed id...
                            parent_email = Mail.query.filter_by(id=new_mail.parent_email_id).first()
                            if parent_email:
                                parent_email.is_most_recent = False
                        database.session.commit()

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
        database.session.commit()
        return email_ids




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
            lowest_uid = int(email_uids[0].decode())  # The most recent email UID
            print(f"Highest UID from today: {highest_uid}")
        else:
            highest_uid = None
            print("No emails found from today.")
        # Step 3: Fetch the last 100 emails based on highest UID
        if highest_uid:
            # Calculate the range for the last 100 emails
            start_uid = max(lowest_uid - 100 + 1, 1)  # Ensure we don't go below UID 1
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

        status, flags_response = mail.uid("FETCH", email_id, "(FLAGS)")
        is_unread = b"\\Seen" not in flags_response[0]  # Check if \Seen flag is NOT present

        # Fetch the email
        status, msg_data = mail.uid("FETCH", email_id, '(RFC822)') # This fetches the mail and tag is as "Read" on the server.
        #status, msg_data = mail.uid("FETCH", email_id, '(BODY.PEEK[])') # This fetches the mail only.

        if is_unread:
            mail.uid("STORE", email_id, "-FLAGS", r"(\Seen)")
            print(f"Email UID {email_id} marked back as unread.")

        if status == "OK":
            print(f"Successfully fetched email UID {email_id.decode()}") #: {msg_data}")
        else:
            print(f"Failed to fetch email UID {email_id.decode()}")#: {msg_data}")
        for response_part in msg_data:
            #print("Process part: ", response_part)

            if isinstance(response_part, tuple) and len(response_part) > 1:

                metadata = response_part[0]
                raw_email = response_part[1]
                #print("Raw Email:", raw_email)

                # Parse email data
                email_data = parse_email_headers(raw_email)
                #print("Email:",email_data)

                if Mail.query.filter_by(email_id=email_data["message_id"]).first():
                    print(f"Email with ID {email_id.decode()} already exists in local db. Skipping...")
                else:
                    parsed_email = email.message_from_bytes(raw_email)
                    body = extract_email_body(parsed_email)
                    summary = extract_novel_content(extract_email_body_newcontent(parsed_email))
                    summary = summarize_body(summary)
                    #print("Email body", body)
                    # Save to the database
                    new_mail = Mail(
                        email_id=email_data["message_id"],
                        sender=email_data['From'],
                        subject=email_data['Subject'],
                        date_received=#parse(email_data['Date']),
                        parsedate_to_datetime(email_data['Date']).astimezone(pytz.utc),
                        body=body,
                        summary=summary,
                        parent_email_id=email_data['in_reply_to'],
                        is_most_recent=True,
                    )
                    print("Mail creation is OK")
                    database.session.add(new_mail)
                    database.session.commit()  # Commit to get the mail's ID

                    if new_mail.parent_email_id:
                        #TODO: not "id=" it should be the processed id...
                        parent_email = Mail.query.filter_by(id=new_mail.parent_email_id).first()
                        if parent_email:
                            parent_email.is_most_recent = False
                    database.session.commit()

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
                #print(html)
                mails_html.append(html)
    return mails_html


# DEPRECATED
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
                            #print(f"Body: {body}")
                            break
                else:
                    body = msg.get_payload(decode=True).decode()
                    #print(f"Body: {body}")

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
