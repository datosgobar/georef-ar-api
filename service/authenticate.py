from flask_security.utils import verify_password

from admin.models import user_data_store


def authenticate(username, password):
    user = user_data_store.find_user(username=username)
    print(verify_password(password, user.password))
    if user and username == user.username and \
            verify_password(password, user.password) and user.active:
        return user
    return None


def identity(payload):
    user = user_data_store.find_user(id=payload['identity'])
    return user
