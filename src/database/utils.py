
from src.database.models import Metadata, Mail  # Adjust the import path if necessary

def get_last_email_uid():
    metadata_entry = Metadata.query.filter_by(key="last_email_uid").first()
    return metadata_entry.value if metadata_entry else "0"

def update_last_email_uid(new_uid,db):
    # TODO:  ensure new_uid is integer type, and not e.g.  b'247440'. Convert it if necessary.
    print("update_last_email_uid:", new_uid)
    metadata_entry = Metadata.query.filter_by(key="last_email_uid").first()
    if metadata_entry:
        metadata_entry.value = str(new_uid)
    else:
        metadata_entry = Metadata(key="last_email_uid", value=str(new_uid))
        db.session.add(metadata_entry)
    db.session.commit()

def fetch_mails_from_local_db(db):
    # Fetch the first 100 emails from the database, ordered by the date_received field (most recent first)
    emails  = (
    Mail.query
    .filter_by(is_most_recent=True)
    .order_by(Mail.date_received.desc())
    .limit(100)
    .all()
)

    return emails

