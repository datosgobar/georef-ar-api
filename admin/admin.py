from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from admin.models import User
from admin.database import db


def init_admin(app):
    admin = Admin(app, name='Georef', template_mode='bootstrap3')
    admin.add_view(ModelView(User, db.session))
    db.init_app(app)
