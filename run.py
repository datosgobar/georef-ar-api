from flask import Flask
from admin.admin import init_admin, init_login


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.DevelopmentConfig')

    from service.routes import api
    app.register_blueprint(api)

    init_admin(app)
    init_login(app)

    return app

app = create_app()
