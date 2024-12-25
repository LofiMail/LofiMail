from email.utils import parseaddr, parsedate_to_datetime
from datetime import datetime
from src.tools.decode import decode_mime_text

import pytz
import html


# Function to generate HTML for an email
def generate_email_html(email_id,email_data, current_email):
    # Extract email details
    sender = email_data["From"]
    sender_email = parseaddr(sender)[1]  # Extract the email address
    encoded_title = email_data["Subject"]

    title = decode_mime_text(encoded_title)

    timestamp = email_data["Date"]
    participants = email_data["To"]
    if "Cc" in email_data:
        if email_data["Cc"]:
            for e in email_data["Cc"]:
                participants += ", " + e
    participants = decode_mime_text(participants)
    # print(participants)
    # Format the timestamp
    now_time = datetime.now(pytz.utc)
    received_time = parsedate_to_datetime(timestamp)
    converted_time = received_time.astimezone(pytz.utc)
    time_diff = now_time - converted_time
    print(time_diff)
    if time_diff.days > 0:
        time_display = f"{time_diff.days}d"
    elif time_diff.seconds > 3600:
        time_display = f"{time_diff.seconds // 3600}h"
    else:
        time_display = f"{time_diff.seconds // 60}m"

    # Generate the participant details
    all_recipients = [
        addr for addr in [r.strip() for r in participants.split(",")] if addr and addr != current_email
    ]
    participant_count = len(all_recipients)
    participant_title = ", ".join(all_recipients[:3])  # Limit to the first 3 names for the title
    if participant_count > 3:
        participant_title += f", +{participant_count - 3} other(s)"

    # Extract the main initial from the sender's name or email
    main_initial = sender_email[0].upper() if sender_email else "?"

    category = "technical"
    category_name = "Technical"

    participant_title = html.escape(participant_title)
    main_initial = html.escape(main_initial)
    sender_email = html.escape(sender_email)
    title = html.escape(title)

    participant_count_html = ""
    if participant_count>1:
        participant_count_html = f"""<span class="participant-count">+{participant_count - 1}</span>"""

    # onclick="openMessage('messageModal')"
    # Generate the HTML
    html_code = f"""
    <div class="email-item conversation {category}" onclick="fetchAndShowEmailContent('{ email_id.decode('utf-8')  }')">
                <div class="email-conversation-summary">
                    <div class="conversation-icon" title="{participant_title}">
                        <span class="main-initial">{main_initial}</span>
                        {participant_count_html}
                    </div>
                </div>
                <span class="email-sender ">{sender_email}</span>
                <span class="email-title">{title}</span>
                <span class="email-category {category}">{category_name}</span>
                <span class="email-timestamp">{time_display}</span>
                <span class="email-flags" title="Important">⭐</span>
                <span class="email-snooze" title="Snooze this email" onclick="snoozeEmail(event, this)">⏰</span>
    </div>
    """
    return html_code


import email, re
def generate_email_modal(mail, email_id):
    """
    Generate an HTML modal for an email's content.

    Parameters:
    - mail: an instance of the IMAP connection (e.g., `imaplib.IMAP4_SSL`).
    - email_id: the UID of the email to fetch.

    Returns:
    - HTML string of the email modal.
    """
    print("Generate Email Modal",mail,email_id)
    # Fetch the email by ID
    status, data = mail.fetch(email_id, "(RFC822)")
    if status != "OK":
        return f"<div>Error fetching email with ID {email_id}</div>"

    raw_email = data[0][1]
    email_message = email.message_from_bytes(raw_email)

    # Decode email components
    # def decode_part(part):
    #     return ''.join(
    #         part.decode(encoding or "utf-8") if isinstance(part, bytes) else part
    #         for part, encoding in decode_header(part)
    #     )

    # Email components
    title = decode_mime_text(email_message.get("Subject", "No Subject"))
    sender_name, sender_email = parseaddr(email_message.get("From"))
    sender_name = decode_mime_text(sender_name) or sender_email

    # Recipients
    recipients = email_message.get("To", "")
    recipient_list = [parseaddr(addr) for addr in recipients.split(",")]
    recipient_html = ''.join(
        f'<span class="recipient recipient-category-{i + 1}">{decode_mime_text(name) or email}</span>'
        for i, (name, email) in enumerate(recipient_list)
    )

    # Extract email body
    body = ""
    if email_message.is_multipart():
        for part in email_message.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8")
                break
    else:
        body = email_message.get_payload(decode=True).decode(email_message.get_content_charset() or "utf-8")

    # Clean the body (convert line breaks to HTML-friendly <br>)
    body_html = re.sub(r"\r?\n", "<br>", body.strip())

    # Generate HTML
    html = f"""
        <div class="message-header">{title}</div> 
        <div class="message-meta">
            <div class="author">
                <span class="fromto">by</span>
                <span class="author author-category-1">{sender_name}</span>
            </div>
            <div class="recipients">
                <span class="fromto">to</span>
                {recipient_html}
            </div>  
            <button class="voice-button" onclick="speakMail()" title="Listen to mail">🔊</button>
            <button class="close-button" onclick="closeEmail()" title="Close mail">❌</button>
        </div>
        <hr class="message-separator">
        <div class="message-body">{body_html}</div>
        <div class="message-actions">
            <button class="reply">Reply</button>
            <button class="forward">Forward</button>
            <button class="archive">Archive</button>
        </div>
        <div class="feature-box feature-summary">
            <div class="feature-title">Summary</div>
            <hr class="feature-separator">
	        <div>Team meeting scheduled for tomorrow at 10:00 AM.</div>
        </div>
        <div class="feature-box feature-actions">
          <div class="feature-title">Quick links</div>
          <hr class="feature-separator">
          <ul>
            <li><a href="#">📅 Add meeting to Calendar</a></li>
            <li><a href="#">⏰ Remind me to reply tomorrow at 11:00 AM</a></li>
            <li><a href="#">🔄 Follow-up client in 2 Days</a></li>
            <li><a href="#">📨 Delegate to Sarah for review and add a task for her to check it by Friday</a></li>
            <li><a href="#">⏳ Finish Reviewing by Tomorrow Morning</a></li>
            <li><a href="#">⚡ Categorize as High-Priority for this Afternoon</a></li>
            <li><a href="#">🗓️ Review later during 'Admin Hour'</a></li>
          </ul>
    </div>
  </div>
    """
    return html

