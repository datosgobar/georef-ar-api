"""Módulo 'routes' de georef-api

Declara las rutas de los recursos que expone la API e
invoca las funciones que procesan dichos recursos.
"""

from service import app, normalizer
from flask import request
from functools import wraps


def disable_cache(f):
    """Dada una función que maneja una request HTTP, modifica los valores de
    los headers para deshabilitar el cacheo de respuestas.

    Args:
    f (function): Función utilizada para manejar un endpoint HTTP de flask.

    """
    @wraps(f)
    def decorated_func(*args, **kwargs):
        resp = f(*args, **kwargs)
        resp.cache_control.no_cache = True
        return resp

    return decorated_func


@app.route('/api/v1.0/provincias', methods=['GET', 'POST'])
def get_states():
    return normalizer.process_state(request)


@app.route('/api/v1.0/departamentos', methods=['GET', 'POST'])
def get_departments():
    return normalizer.process_department(request)


@app.route('/api/v1.0/municipios', methods=['GET', 'POST'])
def get_municipalities():
    return normalizer.process_municipality(request)


@app.route('/api/v1.0/localidades', methods=['GET', 'POST'])
def get_localities():
    return normalizer.process_locality(request)


@app.route('/api/v1.0/calles', methods=['GET', 'POST'])
def get_streets():
    return normalizer.process_street(request)


@app.route('/api/v1.0/direcciones', methods=['GET', 'POST'])
def get_addresses():
    return normalizer.process_address(request)


@app.route('/api/v1.0/ubicacion', methods=['GET', 'POST'])
@disable_cache
def get_placement():
    return normalizer.process_place(request)
