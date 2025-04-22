from functools import wraps
from flask import request
from werkzeug.datastructures import MultiDict


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
                    return f(*args, **kwargs)
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

                return f(*args, **kwargs)

            else:
                return f(*args, **kwargs)

        return wrapped

    return decorator
