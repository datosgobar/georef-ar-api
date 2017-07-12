from admin.database import db
from flask_security import UserMixin, RoleMixin, SQLAlchemyUserDatastore

roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(),
                                 db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer(),
                                 db.ForeignKey('role.id')))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    active = db.Column(db.Boolean())
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.Text(), nullable=False)
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

    def __unicode__(self):
        return self.username

    def __str__(self):
        return self.username


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


user_data_store = SQLAlchemyUserDatastore(db, User, Role)
