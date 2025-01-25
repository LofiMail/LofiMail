from . import db



class Metadata(db.Model):
    __tablename__ = 'metadata'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(255), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=True)

    def __init__(self, key, value):
        self.key = key
        self.value = value

class Mail(db.Model):
    __tablename__ = 'mails'

    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.String, unique=True, nullable=False, index=True)
    sender = db.Column(db.String, index=True)
    date_received = db.Column(db.DateTime, index=True)
    subject = db.Column(db.String)
    body = db.Column(db.Text)
    summary = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    is_most_recent = db.Column(db.Boolean, default=True)
    parent_email_id = db.Column(db.Integer, db.ForeignKey('mails.id'))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    recipients = db.relationship('Recipient', backref='mail', lazy=True)
    tags = db.relationship('EmailTag', backref='mail', lazy=True)
    actions = db.relationship('Action', backref='mail', lazy=True)


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


class Action(db.Model):
    __tablename__ = 'actions'

    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('mails.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    is_done = db.Column(db.Boolean, default=False)



if __name__ == '__main__':
    from src.app import app
    app.run(debug=True)
    with app.app_context():
        db.create_all()