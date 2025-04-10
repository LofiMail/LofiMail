from email.utils import parseaddr, parsedate_to_datetime
from datetime import datetime
from src.tools.decode import decode_mime_text
from src.tools.processmail import summarize_body, highlight_important_words, process_email


import pytz
import html



from html import escape
def convert_text_to_html(text):
    # Escape any existing HTML entities to prevent rendering issues
    escaped_text = escape(text)

    # Regex to find URLs
    url_pattern = r'(https?://[^\s]+)'

    # Replace URLs with clickable HTML links
    html_text = re.sub(url_pattern, r'<a href="\1" target="_blank" class="link">Link</a><br>', escaped_text)

    html_text=re.sub(r"\r?\n", "<br>", html_text.strip())

    # Add simple <p> tags for formatting
    return f"<p>{html_text}</p>"

def db_email_to_html(email,selfmail=""):

    id = email.id
    email_id= email.email_id
    sender = email.sender
    date_received = email.date_received
    subject = email.subject
    body = email.body
    summary= email.summary
    is_read= email.is_read
    parent_email_id= email.parent_email_id
    created_at = email.created_at
    # recipients
    recipients = email.recipients
    # tags
    tag_names = [email_tag.tag.name for email_tag in email.tags]
    print("Tag names:", tag_names)
    # actions




    print("email_id:",email_id)
    title = decode_mime_text(subject)

    print("Title:",title)

    sender_email = parseaddr(sender)[1]  # Extract the email address
    print("sender_email:",sender_email)
    # Extract the main initial from the sender's name or email
    main_initial = sender_email[0].upper() if sender_email else "?"
    print("main_initial:",main_initial)



    print("date_received",date_received)
    if date_received.tzinfo is None:
        # If the received_time is naive, localize it to UTC
        date_received = pytz.utc.localize(date_received)
    # Decode time:
    now_time = datetime.now(pytz.utc)
    #received_time = parsedate_to_datetime(date_received).astimezone(pytz.utc)
    time_diff = now_time - date_received
    print(time_diff)
    if time_diff.days > 0:
        time_display = f"{time_diff.days}d"
    elif time_diff.seconds > 3600:
        time_display = f"{time_diff.seconds // 3600}h"
    else:
        time_display = f"{time_diff.seconds // 60}m"


    print("time_display:",time_display)


    participants = [decode_mime_text(recipient.recipient) for recipient in recipients]
    participants = [p for p in participants if p != "None" and p != selfmail]

    participant_count = len(participants)
    print("participant_count:",participant_count)

    if participant_count > 3:
        participant_title = ", ".join(participants[:3])  # Limit to the first 3 names for the title
        participant_title += f", +{participant_count - 3} other(s)"
    else:
        participant_title = ", ".join(participants)


    print("participant_title:", participant_title)

    participant_count_html = ""
    if participant_count > 0:
        participant_count_html = f"""<span class="participant-count">+{participant_count}</span>"""

    participant_title = html.escape(participant_title)
    main_initial = html.escape(main_initial)
    sender_email = html.escape(sender_email)
    title = html.escape(title)

    #TODO: This is a stub. For later: compute some category automatically based on analysis of email content + recipients.
    category = "one"
    category_name = "Technical"
    #tag_names
    from src.tools.processmail import CATEGORY_KEYWORDS
    nb_category = 6
    ordinal = {1: "one",2:"two",3:"three",4:"four",5:"five", 6:"six"}

    html_cat = ""
    category_text = ""
    for tagn in tag_names:
        if tagn in CATEGORY_KEYWORDS:
            i = list(CATEGORY_KEYWORDS).index(tagn)
            if (i<nb_category):
                ctext = ordinal[i+1]
                html_cat+=f"""<span class="email-category {ctext}">{tagn}</span>"""
                category_text+= f""" {ctext}"""
    print("CATEGORIES",html_cat, category_text)

    conversation_class = ""
    if (parent_email_id):
        conversation_class= "conversation"

    html_code = f"""
        <div class="email-item {conversation_class} {category_text}" onclick="fetchAndShowEmailContent('{email_id}')">
                    <div class="email-conversation-summary">
                        <div class="conversation-icon" title="{participant_title}">
                            <span class="main-initial">{main_initial}</span>
                            {participant_count_html}
                        </div>
                    </div>
                    <span class="email-sender">{sender_email}</span>
                    <span class="email-title">{title}</span>
                    {html_cat}
                    <span class="email-timestamp">{time_display}</span>
                    <span class="email-flags" title="Important">⭐</span>
                    <span class="email-snooze" title="Snooze this email" onclick="snoozeEmail(event, this)">⏰</span>
        </div>
        """
    return html_code

# Function to generate HTML for an email
# DEPRECATED
def generate_email_html(email_id,email_data, current_email):
    # Extract email details
    sender = email_data["From"]
    sender_email = parseaddr(sender)[1]  # Extract the email address
    encoded_title = email_data["Subject"]

    title = decode_mime_text(encoded_title)

    timestamp = email_data["Date"]
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
    participants = email_data["To"]
    if "Cc" in email_data:
        if email_data["Cc"]:
            for e in email_data["Cc"]:
                participants += ", " + e


    participants = decode_mime_text(participants)
    # print(participants)
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

    category = "one"
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



def db_email_to_modalhtml(email,selfmail=""):

    id = email.id
    email_id= email.email_id
    sender = email.sender
    date_received = email.date_received
    subject = email.subject
    body = email.body
    summary= email.summary
    is_read= email.is_read
    parent_email_id= email.parent_email_id
    created_at = email.created_at
    # recipients
    recipients = email.recipients
    # tags
    tags = email.tags
    # actions




    print("email_id:",email_id)
    title = decode_mime_text(subject)


    sender_name, sender_email = parseaddr(sender)
    sender_name = decode_mime_text(sender_name) or sender_email


    # Recipients
    recipient_list = [parseaddr(recipient.recipient) for recipient in recipients]
    recipient_html = ''.join(
        f'<span class="recipient recipient-category-{(i + 1) % 5}">{decode_mime_text(name) or _email}</span>\n'
        for i, (name, _email) in enumerate(recipient_list) if (decode_mime_text(name) or _email) != "None"
    )



    # Extract email body
    #print("SUMMARY:", summary)
    #body_summary = summarize_body(summary)
    body_summary = summary
    #Use highlight_important_words


    #body = process_email(body)
    #body = extract_body_fragments(body)

    # Clean the body (convert line breaks to HTML-friendly <br>)
    body_html = re.sub(r"\r?\n", "<br>", body.strip())


    # Clean the body (convert line breaks to HTML-friendly <br>)
    body_summary_html = convert_text_to_html(body_summary)



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
                <button class="close-button" onclick="closeEmail('messageModal')" title="Close mail">❌</button>
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
    	        <div>{body_summary_html}</div>
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


# DEPRECATED
def generate_email_modal(mail, email_id):
    """
    Generate an HTML modal for an email's content.

    Parameters:
    - mail: an instance of the IMAP connection (e.g., `imaplib.IMAP4_SSL`).
    - email_id: the UID of the email to fetch.

    Returns:
    - HTML string of the email modal.
    """
    print("Generate Email Modal",email_id)
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

