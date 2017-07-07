from admin.database import db
from flask_security import UserMixin


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(45))
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))