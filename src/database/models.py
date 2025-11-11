from . import db
from datetime import datetime


class Metadata(db.Model):
    __tablename__ = 'metadata'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(255), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=True)

    def __init__(self, key, value):
        self.key = key
        self.value = value

class FolderStatus(db.Model):
    __tablename__ = 'folder_statuses'
    id = db.Column(db.Integer, primary_key=True)
    folder_name = db.Column(db.String, unique=True, nullable=False, index=True)
    highest_uid = db.Column(db.String, nullable=False, default='0')
    last_checked = db.Column(db.DateTime, default=datetime.utcnow)

class Mail(db.Model):
    __tablename__ = 'mails'
    id = db.Column(db.Integer, primary_key=True)
    # IMAP-specific identifiers
    server_uid = db.Column(db.String, nullable=False)
    server_folder = db.Column(db.String, nullable=False)

    # Add a unique constraint on the combination of folder and UID
    __table_args__ = (
        db.UniqueConstraint('server_uid', 'server_folder', name='_folder_uid_uc'),
        # Adding an index for faster lookups
        db.Index('idx_folder_uid', 'server_folder', 'server_uid'),
    )

    email_id = db.Column(db.String, unique=True, nullable=False, index=True) # Internal lofi ID
    sender = db.Column(db.String, index=True)
    date_received = db.Column(db.DateTime, index=True)
    subject = db.Column(db.String)
    body = db.Column(db.Text)
    summary = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    is_most_recent = db.Column(db.Boolean, default=True)
    parent_email_id = db.Column(db.Integer, db.ForeignKey('mails.id'))
    #conversation_email_id = db.Column(db.Integer, db.ForeignKey('mails.id')) #Internal lof Id of root mail.
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    recipients = db.relationship('Recipient', backref='mail', lazy=True)
    #servertags = db.relationship('ServerTag', backref='mail', lazy=True)
    tags = db.relationship('EmailTag', backref='mail', lazy=True)
    actions = db.relationship('Action', backref='mail', lazy=True)

    # ✅ New column for the server folder path
    server_folder = db.Column(db.String, nullable=True, index=True)


# class Conversation(db.Model):
#     __tablename__ = 'conversations'
#     id = db.Column(db.Integer, primary_key=True)
#     rootmail_id = db.Column(db.String, index=True)


class Recipient(db.Model):
    __tablename__ = 'recipients'

    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('mails.id'), nullable=False)
    recipient = db.Column(db.String, nullable=False)
    type = db.Column(db.Enum('to', 'cc', 'bcc', name='recipient_types'))


class Tag(db.Model):
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)

class EmailTag(db.Model):
    __tablename__ = 'email_tags'

    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('mails.id'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'), nullable=False)
    tag = db.relationship('Tag', backref='email_tags')  # Add this line ✅

# class ServerTag(db.Model):
#     __tablename__ = 'server_tags'
#
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String, unique=True)
# class ServerEmailTag(db.Model):
#     __tablename__ = 'server_email_tags'
#
#     id = db.Column(db.Integer, primary_key=True)
#     email_id = db.Column(db.Integer, db.ForeignKey('mails.id'), nullable=False)
#     tag_id = db.Column(db.Integer, db.ForeignKey('server_tags.id'), nullable=False)


class Action(db.Model):
    __tablename__ = 'actions'

    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('mails.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    is_done = db.Column(db.Boolean, default=False)



if __name__ == '__main__':
    from app import app
    app.run(debug=True)
    with app.app_context():
        db.create_all()