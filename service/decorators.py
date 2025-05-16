from functools import wraps
from flask import request
from werkzeug.datastructures import MultiDict


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