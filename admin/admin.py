import flask_login as login

from flask_admin import AdminIndexView, expose, helpers, Admin
from flask import redirect, url_for, request
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib import sqla

from admin.forms import LoginForm
from admin.models import User, Role
from admin.database import db


class MyAdminIndexView(AdminIndexView):

    @expose('/')
    def index(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))
        return super(MyAdminIndexView, self).index()

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
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


class UserModelView(sqla.ModelView):
    # create_template = 'create.html'
    column_list = ('username', 'email', 'active')

    def is_accessible(self):
        return login.current_user.is_authenticated


def init_login(app):
    login_manager = login.LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.query(User).get(user_id)


def init_admin(app):
    admin = Admin(app, name='Georef', index_view=MyAdminIndexView(),
                  base_template='admin/master.html')
    admin.add_view(UserModelView(User, db.session))
    admin.add_view(ModelView(Role, db.session))
    db.init_app(app)
