from flask import url_for, redirect, request
from flask_admin import Admin, expose, helpers, AdminIndexView
from flask_admin.contrib import sqla
import flask_login as login

from werkzeug.security import generate_password_hash

from admin.models import User
from admin.database import db
from admin.forms import LoginForm, RegistrationForm


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
        link = '<p>¿No tiene una cuenta?<a href="' + \
               url_for('.register_view') + '"> Registrarse</a></p>'
        self._template_args['form'] = form
        self._template_args['link'] = link
        return super(MyAdminIndexView, self).index()

    @expose('/register/', methods=('GET', 'POST'))
    def register_view(self):
        form = RegistrationForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = User()

            form.populate_obj(user)

            user.password = generate_password_hash(form.password.data)

            db.session.add(user)
            db.session.commit()

            login.login_user(user)
            return redirect(url_for('.index'))
        link = '<p>¿Ya tiene una cuenta? <a href="' + url_for(
            '.login_view') + '">Inicie sesión.</a></p>'
        self._template_args['form'] = form
        self._template_args['link'] = link
        return super(MyAdminIndexView, self).index()

    @expose('/logout/')
    def logout_view(self):
        login.logout_user()
        return redirect(url_for('.index'))


class MyModelView(sqla.ModelView):
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
