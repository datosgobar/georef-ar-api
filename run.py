from flask import Flask
from flask_jwt import JWT
from flask_security import Security

from admin.admin import init_admin, init_login
from service.authenticate import authenticate, identity, user_data_store


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    from service.routes import api
    app.register_blueprint(api)

    return app

# Inicializa la instancia de la aplicación
app = create_app()

# Inicializa Flask Admin
init_admin(app)

# Inicializa Login Manager
init_login(app)

# Inicializa JWT
jwt = JWT(app, authenticate, identity)

# Inicializa Flask Security
security = Security(app, user_data_store)
