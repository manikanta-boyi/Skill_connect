from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash # Add these imports

# Removed @login_manager.user_loader as it belongs in app.py

class User(db.Model, UserMixin):
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(100),nullable=False,unique=True)
    email = db.Column(db.String(100),nullable=False,unique=True)
    password = db.Column(db.String(100),nullable=False) # Consider renaming to password_hash for clarity
    role = db.Column(db.String(50), nullable=False) # Made nullable=False as per form
    location = db.Column(db.String(100), nullable=False) # Made nullable=False as per form
    skill = db.Column(db.String(100), nullable=True)

    requirements = db.relationship('Requirements',backref = 'poster',lazy=True)
    bids = db.relationship('Bid',backref='bidder',lazy=True)

    # Added methods for password hashing and checking
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def get_id(self): # Ensure this is present for Flask-Login
        return str(self.id)

    def __repr__(self):
        return f'<User {self.username}>'


class Requirements(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(150),nullable=False)
    description = db.Column(db.Text,nullable = False)
    skill_needed = db.Column(db.String(100), nullable=True) # FIXED TYPO from skill_neded
    location = db.Column(db.String(100), nullable=False) # Made nullable=False as it's required in form
    voice_file_path = db.Column(db.String(255), nullable=True) # New: path to uploaded audio
    voice_transcription = db.Column(db.Text, nullable=True) # New: transcribed text
    status = db.Column(db.String(50), default='open', nullable=False) # New: For workflow status

    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable = False)

    bids = db.relationship('Bid',backref = 'requirement',lazy=True)

    def __repr__(self):
        return f'<Requirement {self.title}>'


class Bid(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    price = db.Column(db.Float,nullable=False)
    comment = db.Column(db.Text) # FIXED TYPO from coment
    voice_file_path = db.Column(db.String(255), nullable=True) # New: path to uploaded audio
    voice_transcription = db.Column(db.Text, nullable=True) # New: transcribed text
    status = db.Column(db.String(50), default='pending', nullable=False) # New: For bid status

    requirement_id = db.Column(db.Integer,db.ForeignKey('requirements.id'),nullable=False)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)

    def __repr__(self):
        return f'<Bid {self.price}>'