from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from run import app
from admin.database import db
from command import CreateUserCommand

migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)
manager.add_command('createuser', CreateUserCommand(db))


if __name__ == '__main__':
    manager.run()
