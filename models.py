from extensions import db, login_manager
from flask_login import UserMixin


    

class User(db.Model,UserMixin):
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(100),nullable=False,unique=True)
    email = db.Column(db.String(100),nullable=False,unique=True)
    password = db.Column(db.String(100),nullable=False)
    role = db.Column(db.String(50))
    location = db.Column(db.String(100))
    skill = db.Column(db.String(100), nullable=True)

    requirements = db.relationship('Requirements',backref = 'poster',lazy=True)
    bids = db.relationship('Bid',backref='bidder',lazy=True)


class Requirements(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(150),nullable=False)
    description = db.Column(db.Text,nullable = False)
    skill_needed = db.Column(db.String(100))
    location = db.Column(db.String(100))

    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable = False)

    bids = db.relationship('Bid',backref = 'requirement',lazy=True)

class Bid(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    price = db.Column(db.Float,nullable=False)
    coment = db.Column(db.Text)
    requirement_id = db.Column(db.Integer,db.ForeignKey('requirements.id'),nullable=False)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
