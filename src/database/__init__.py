from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
db = SQLAlchemy()

def init_db(app):
    """
    Initializes the database with the Flask app.
    Call this during app initialization.
    """
    db.init_app(app)
