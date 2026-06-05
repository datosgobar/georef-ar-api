import functools
import json
import logging
from functools import wraps
from flask import request, make_response
from contextvars import ContextVar

from georef_ar_address.address_parser import TreeVisitor
from werkzeug.datastructures import MultiDict, ImmutableMultiDict

from service.data import ElasticsearchSearch


def add_params(**new_params):
    """
    Agrega parámetros a la consulta GET o POST.

    Args:
        params: parámetros a inyectar en la consulta GET o en cada elemento de una consulta POST.
    """

    def decorator(endpoint_func):

        @wraps(endpoint_func)
        def wrapped():

            if request.method == 'GET':
                original_args = request.args

                # Clonar args, modificar y sobrescribir porque es un objeto inmutable
                modified_args = MultiDict(original_args)
                modified_args.update(new_params)
                request.args = modified_args

                result = endpoint_func()

                request.args = original_args

            elif request.method == 'POST' and request.is_json:
                original_json = request.json

                if isinstance(request.json, dict):
                    for params in request.json.values():
                        if isinstance(params, list):
                            for item in params:
                                item.update(new_params)

                result = endpoint_func()

                request.json.update(original_json)

            else:
                result = endpoint_func()

            return result

        return wrapped

    return decorator

_request_logs = ContextVar("request_logs", default=[])

class AddressAPIHandler(logging.Handler):

    def emit(self, record):
        logs_list = _request_logs.get()

        def get_msg(rec):
            raw_msg = rec.msg

            if hasattr(raw_msg, 'to_dict'):
                serializable_msg = raw_msg.to_dict()
            elif isinstance(raw_msg, (dict, list, str, int, float, bool)) or raw_msg is None:
                serializable_msg = raw_msg
            elif isinstance(raw_msg, TreeVisitor):
                serializable_msg = {
                    'address_type': raw_msg.address_type,
                    'tree': raw_msg._tree,
                    'rank': raw_msg._rank,
                    'components_leaves_indices': raw_msg._components_leaves_indices
                }
            elif isinstance(raw_msg, ElasticsearchSearch):
                serializable_msg = {
                    'SearchType': type(raw_msg).__name__,
                    'query': raw_msg._search.to_dict()
                }
            else:
                serializable_msg = str(raw_msg)

            return serializable_msg

        if logs_list is not None:
            logs_list.append({
                'function': f"{record.funcName}",
                "data": get_msg(record)
            })

_LOGGERS_SETUP_DONE = False

def setup_loggers_once():

    global _LOGGERS_SETUP_DONE
    if _LOGGERS_SETUP_DONE:
        return

    address_logger = logging.getLogger("georef_ar_address")

    if not any(isinstance(h, AddressAPIHandler) for h in address_logger.handlers):
        handler = AddressAPIHandler()
        address_logger.addHandler(handler)

    address_logger.setLevel(logging.DEBUG)
    _LOGGERS_SETUP_DONE = True


def with_request_logger(handler):
    @wraps(handler)
    def wrapper(*args, **kwargs):
        # Asegurar configuración sin tocar app.py
        setup_loggers_once()

        # Extraer y limpiar parámetro 'debug'
        params = MultiDict(request.args)
        debug = params.pop("debug", None)
        request.args = ImmutableMultiDict(params)

        token = None
        if debug:
            token = _request_logs.set([])

        response = None
        try:
            response = handler(*args, **kwargs)
        finally:
            if debug:
                captured = _request_logs.get()
                _request_logs.reset(token)

                if captured:
                    if isinstance(response, dict):
                        response["steps"] = captured

                    elif hasattr(response, 'get_json'):
                        content = response.get_json()
                        if isinstance(content, dict):
                            content["steps"] = captured
                            response = make_response(
                                json.dumps(content),
                                response.status_code
                            )
                            response.headers['Content-Type'] = 'application/json'

        return response

    return wrapper


def deprecated(current_endpoint, alternative_endpoint):
    """
    Decorador explícito para rutas obsoletas en Flask.

    :param current_endpoint: El nombre del endpoint obsoleto (ej: 'municipios')
    :param alternative_endpoint: El nombre del nuevo recurso reemplazo (ej: 'gobiernos-locales')
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_path = request.path

            full_alternative_path = current_path.replace(current_endpoint, alternative_endpoint)

            # Ejecución normal de la ruta de Flask
            response = func(*args, **kwargs)
            response = make_response(response)

            # Cabeceras HTTP adaptativas para los clientes
            response.headers['Deprecation'] = 'true'
            response.headers['Link'] = f'<{full_alternative_path}>; rel="successor-version"'
            response.headers['Warning'] = f'199 - "Endpoint obsoleto. Migrar a {full_alternative_path}"'

            return response

        return wrapper

    return decorator