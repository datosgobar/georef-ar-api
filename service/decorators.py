from functools import wraps
from flask import request
from werkzeug.datastructures import MultiDict

from service.names import RESULTS
from flask import jsonify


def inject_and_rename_entity_param(from_key, to_key, **new_params):
    """
    Inyecta parámetros y renombra la clave en JSON body.

    Args:
        from_key (str): Clave esperada del cliente (ej: 'municipios').
        to_key (str): Clave real que espera el normalizador (ej: 'gobiernos_locales').
        new_params: parámetros a inyectar en la consulta GET o en cada elemento de una consulta POST.
    """

    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if request.method == 'GET':
                # Clonar args y sobrescribir porque es un objeto inmutable
                modified_args = MultiDict(request.args)
                modified_args.update(new_params)

                original_args = request.args
                try:
                    request.args = modified_args
                    response = f(*args, **kwargs)

                    # Intentar revertir el cambio en la respuesta
                    try:
                        if hasattr(response, 'get_json'):
                            resp_json = response.get_json()
                            if isinstance(resp_json, dict) and to_key in resp_json:
                                resp_json[from_key] = resp_json[to_key]
                                del resp_json[to_key]

                                return jsonify(resp_json)
                    except Exception:
                        pass  # Si no se puede parsear como JSON, dejar la respuesta tal cual

                    return response
                finally:
                    # Siempre se retorna el request original
                    request.args = original_args

            elif request.method == 'POST' and request.is_json:
                original_json = request.json

                # Si la clave "from_key" existe y es lista, hacer la transformación
                if isinstance(original_json, dict) and from_key in original_json:
                    items = original_json[from_key]
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict):
                                item.update(new_params)

                        # Renombrar clave para que el normalizador la entienda
                        original_json[to_key] = items
                        del original_json[from_key]

                response = f(*args, **kwargs)

                # Intentar revertir el cambio en la respuesta JSON
                try:
                    if hasattr(response, 'get_json'):
                        resp_json = response.get_json()
                        if isinstance(resp_json, dict) and RESULTS in resp_json:
                            for result in resp_json[RESULTS]:
                                if isinstance(result, dict) and to_key in result:
                                    result[from_key] = result[to_key]
                                    del result[to_key]
                            return jsonify(resp_json)
                except Exception:
                    pass

                return response

            else:
                return f(*args, **kwargs)

        return wrapped

    return decorator
