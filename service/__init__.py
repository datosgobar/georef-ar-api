from flask import Flask
from admin.admin import init_admin

app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')

init_admin(app)

import service.routes

