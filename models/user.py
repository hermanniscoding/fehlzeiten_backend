from copy import error
from flask_sqlalchemy import SQLAlchemy
from .schoolday import db



# db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(50), unique = True)
    password = db.Column(db.String(80))
    admin = db.Column(db.Boolean)

