"""Módulo 'routes' de georef-api

Declara las rutas de los recursos que expone la API e
invoca las funciones que procesan dichos recursos.
"""

from functools import wraps
from flask import request, Blueprint
from service import app, normalizer, formatter


def disable_cache(f):
    """Dada una función que maneja una request HTTP, modifica los valores de
    los headers para deshabilitar el cacheo de respuestas.

    Args:
        f (function): Función utilizada para manejar un endpoint HTTP de flask.

    Returns:
        function: Endpoint con decorador aplicado.

    """
    @wraps(f)
    def decorated_func(*args, **kwargs):
        resp = f(*args, **kwargs)
        resp.cache_control.no_cache = True
        return resp

    return decorated_func


@app.errorhandler(404)
def handle_404(_):
    return formatter.create_404_error_response(app.url_map)


@app.errorhandler(405)
def handle_405(_):
    return formatter.create_405_error_response(app.url_map)


# API v1.0
bp_v1_0 = Blueprint('georef_v1.0', __name__)


@bp_v1_0.route('/provincias', methods=['GET', 'POST'])
def get_states():
    return normalizer.process_state(request)


@bp_v1_0.route('/departamentos', methods=['GET', 'POST'])
def get_departments():
    return normalizer.process_department(request)


@bp_v1_0.route('/municipios', methods=['GET', 'POST'])
def get_municipalities():
    return normalizer.process_municipality(request)


@bp_v1_0.route('/localidades', methods=['GET', 'POST'])
def get_localities():
    return normalizer.process_locality(request)


@bp_v1_0.route('/calles', methods=['GET', 'POST'])
def get_streets():
    return normalizer.process_street(request)


@bp_v1_0.route('/direcciones', methods=['GET', 'POST'])
def get_addresses():
    return normalizer.process_address(request)


@bp_v1_0.route('/ubicacion', methods=['GET', 'POST'])
@disable_cache
def get_placement():
    return normalizer.process_place(request)


# Última versión de la API
app.register_blueprint(bp_v1_0, url_prefix='/api')

# v1.0
app.register_blueprint(bp_v1_0, url_prefix='/api/v1.0')
