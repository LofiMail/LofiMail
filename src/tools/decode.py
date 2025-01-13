import re

from email.header import Header, decode_header, make_header
import hashlib



def is_valid_message_id(message_id):
    return re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", message_id) is not None



def decode_mime_text(text):
    # Regex to find MIME-encoded parts
    mime_pattern = r'=\?[^?]+\?[BQ]\?[^?]+\?='

    # Function to decode a single MIME-encoded segment
    def decode_mime_part(match):
        part = match.group(0)
        decoded_parts = decode_header(part)
        return ''.join(
            part.decode(encoding or "utf-8") if isinstance(part, bytes) else part
            for part, encoding in decoded_parts
        )

    # Replace all MIME-encoded parts with their decoded values
    decoded_text = re.sub(mime_pattern, decode_mime_part, text)
    return decoded_text


import email

def parse_email_headers(raw_email):
    parsed_email = email.message_from_bytes(raw_email)
    print("Parsed email:", parsed_email)
    try:
        message_id = parsed_email.get("Message-ID")
    except Exception as e:
        # Handle unexpected parsing errors
        print(f"Error parsing email: {e}")
        message_id= None
    print("Message id",message_id)
    if (message_id is None) or (not is_valid_message_id(message_id)):
        # Fallback: Create a synthetic unique ID
        fallback_id = f"{parsed_email['Date']}-{parsed_email['From']}-{parsed_email['Subject']}"
        #message_id = fallback_id.encode('utf-8').hex()
        message_id = hashlib.sha256(fallback_id.encode('utf-8')).hexdigest()
        message_id = message_id.strip("<>")
        print(f"Generated synthetic Message-ID: {message_id}")
    else:
        # Use regex to clean the Message-ID
        match = re.match(r'<([^>]+)>', message_id.strip())
        if match:
            message_id = match.group(1)  # Extract content inside angle brackets
        else:
            message_id = message_id.strip()  # Fallback to raw stripping
            print(f"Warning: Message-ID is not well-formed, using raw version: {message_id}")

    # Extract metadata
    references = parsed_email['References']

    subject_header = parsed_email.get("Subject")
    print("Check Header...")
    # if isinstance(subject_header, Header):
    #     subject = str(subject_header)
    #     print("THIS IS a HEADER OBJECT")
    # else:
    #     subject = make_header(decode_header(subject_header))

    try:
        subject = str(make_header(decode_header(subject_header)))
    except Exception as e:
        print(f"Error decoding subject: {e}")
        subject = "Unknown Subject"  # Fallback if decoding fails


    return {
        'message_id': message_id,
        'From': parsed_email.get("From"),
        'Subject': subject,
        'Date': parsed_email.get("Date"),
        "To": parsed_email.get("To"),
        "Cc": parsed_email.get("Cc"),
        'in_reply_to': parsed_email.get('In-Reply-To'),
        'references': references.split() if references else None,
    }


def extract_email_body(parsed_email):
    try:
        if parsed_email.is_multipart():
            body = ""
            for part in parsed_email.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                # Ignore attachments and only get text/plain or text/html
                if content_type in ("text/plain", "text/html") and "attachment" not in content_disposition:
                    payload = part.get_payload(decode=True)
                    if payload:
                        body += payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        else:
            # If not multipart, get the payload directly
            body = parsed_email.get_payload(decode=True)
            if body:
                body = body.decode(parsed_email.get_content_charset() or "utf-8", errors="replace")

        return body or "[No body content found]"

    except Exception as e:
        print(f"Error extracting email body: {e}")
        return "[Error extracting email body]"


def extract_novel_content(email_body):
    """
    Extract only the novel (new) content from an email body by removing quoted or forwarded content.
    """
    reply_markers = [
        r"On .* wrote:",  # Gmail-style
        r"From: .*",  # Generic "From"
        r"Sent: .*",  # Outlook-style
        r"-----",  # Outlook
        r"-----Original Message-----",  # Outlook
        r"> .*",  # Quoted lines (Thunderbird-style)
    ]

    # Combine all markers into a single regex
    pattern = "|".join(reply_markers)

    # Split the body on the first occurrence of any marker
    split_body = re.split(pattern, email_body, flags=re.IGNORECASE)

    # The first part before any marker is the new content
    return split_body[0].strip() if split_body else email_body.strip()
