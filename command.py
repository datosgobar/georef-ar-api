import re
import sys

from flask_script import Command, prompt_pass, prompt
from werkzeug.security import generate_password_hash

from admin.models import User


EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")


class CreateUserCommand(Command):

    def __init__(self, db):
        super(CreateUserCommand, self).__init__()
        self.__db = db

    def run(self):
        username = prompt('Usuario')

        email = prompt('Email')
        email_confirm = prompt('Confirmar email')

        if not email == email_confirm:
            sys.exit('\nError al crear usuario: Los emails no coinciden ')

        if not EMAIL_REGEX.match(email):
            sys.exit('\nError al crear usuario: Email inválido')

        password = prompt_pass('Contraseña')
        password_confirm = prompt_pass('Confirmar contraseña')

        if not password == password_confirm:
            sys.exit('\nError al crear usuario: Las contraseñas no coinciden')

        admin = User(
            username=username, email=email,
            password=generate_password_hash(password), active=True
        )
        self.__db.session.add(admin)
        self.__db.session.commit()
        print("Listo!")


