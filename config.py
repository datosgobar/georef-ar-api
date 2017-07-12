import os
from datetime import timedelta


class Config(object):
    APP_NAME = 'Georef'
    SECRET_KEY = 'georef2017'

    SQLALCHEMY_DATABASE_URI = ''
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_EXPIRATION_DELTA = timedelta(days=30)
    JWT_AUTH_URL_RULE = '/api/v1.0/auth'

    SECURITY_REGISTERABLE = True
    SECURITY_RECOVERABLE = True
    SECURITY_TRACKABLE = True
    SECURITY_PASSWORD_HASH = 'sha512_crypt'
    SECURITY_PASSWORD_SALT = 'add_salt'


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('POSTGRES_CONNECTION')
    DEBUG = True
