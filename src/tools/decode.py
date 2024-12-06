

from email.header import decode_header

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
