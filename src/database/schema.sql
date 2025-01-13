CREATE TABLE Mails (
    id SERIAL PRIMARY KEY,
    email_id TEXT UNIQUE NOT NULL, -- Unique ID from IMAP
    sender TEXT,
    subject TEXT,
    date_received TIMESTAMP,
    body TEXT,
    summary TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    parent_email_id INTEGER, -- Links to another email (for replies/forwards)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_email_id) REFERENCES Mails (id) ON DELETE SET NULL
);

CREATE TABLE Recipients (
    id SERIAL PRIMARY KEY,
    email_id INTEGER, -- Email to which this recipient belongs
    recipient TEXT NOT NULL,
    type TEXT CHECK (type IN ('to', 'cc', 'bcc')), -- Recipient type
    FOREIGN KEY (email_id) REFERENCES Mails (id) ON DELETE CASCADE
);

CREATE TABLE Tags (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE
);

CREATE TABLE EmailTags (
    id SERIAL PRIMARY KEY,
    email_id INTEGER,
    tag_id INTEGER,
    FOREIGN KEY (email_id) REFERENCES Mails (id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES Tags (id) ON DELETE CASCADE
);

CREATE TABLE Actions (
    id SERIAL PRIMARY KEY,
    email_id INTEGER,
    description TEXT NOT NULL,
    is_done BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (email_id) REFERENCES Mails (id) ON DELETE CASCADE
);
