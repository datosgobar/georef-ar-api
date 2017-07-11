from flask import url_for, redirect, request
from flask_admin import Admin, expose, helpers, AdminIndexView
from flask_admin.contrib import sqla
from flask_admin.contrib.sqla import ModelView
import flask_login as login

from admin.models import User
from admin.database import db
from admin.forms import LoginForm


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):

        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))
        return super(MyAdminIndexView, self).index()

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        # handle user login
        form = LoginForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = form.get_user()
            login.login_user(user)

        if login.current_user.is_authenticated:
            return redirect(url_for('.index'))
        self._template_args['form'] = form
        return super(MyAdminIndexView, self).index()

    @expose('/logout/')
    def logout_view(self):
        login.logout_user()
        return redirect(url_for('.index'))


class MyModelView(sqla.ModelView):
    create_template = 'create.html'
    column_list = ('username', 'email', 'active')

    def is_accessible(self):
        return login.current_user.is_authenticated


def init_login(app):
    login_manager = login.LoginManager()
    login_manager.init_app(app)

    # Create user loader function
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.query(User).get(user_id)


def init_admin(app):
    admin = Admin(app, name='Georef', index_view=MyAdminIndexView(),
                  base_template='admin/my_master.html')
    admin.add_view(MyModelView(User, db.session))
    db.init_app(app)
