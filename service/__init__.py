from flask import Flask
from service.admin import db
from service.admin import init_admin
from service.database import db
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

app = Flask(__name__)
app.config.from_object('service.config.DevelopmentConfig')

migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)

init_admin(app)

import service.routes

if __name__ == '__main__':
    manager.run()
