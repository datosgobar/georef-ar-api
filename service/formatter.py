from service import strings
from service import names as N
from flask import make_response, jsonify


def flatten_dict(d, max_depth=3):
    """ Aplana un diccionario recursivamente.
    Lanza un RuntimeError si no se pudo aplanar el diccionario
    con el número especificado de profundidad.

    Args:
        d (dict): Diccionario a aplanar.
        max_depth (int): Profundidad máxima a alcanzar.
    """
    if max_depth <= 0:
        raise RuntimeError("Profundidad máxima alcanzada.")

    for key in list(d.keys()):
        v = d[key]
        if isinstance(v, dict):
            flatten_dict(v, max_depth - 1)

            for subkey, subval in v.items():
                flat_key = '_'.join([key, subkey])
                d[flat_key] = subval

            del d[key]


def format_params_error_dict(error_dict):
    results = []
    for param_name, param_error in error_dict.items():
        results.append({
            'nombre_parametro': param_name,
            'codigo_error': param_error.error_type.value,
            'mensaje': param_error.message,
            'ubicacion': param_error.source
        })

    return results


def create_param_error_response(request, errors):
    if request.method == 'GET':
        errors_fmt = format_params_error_dict(errors[0])
    else:
        errors_fmt = [format_params_error_dict(d) for d in errors]

    return make_response(jsonify({
        'errores': errors_fmt
    }), 400)


def create_es_error_response(request):
    return make_response(jsonify({
        'error': strings.INTERNAL_ERROR
    }), 500)


def create_json_response(request, params_list, name, results, list_results):
    results_formatted = []
    for result, params in zip(results, params_list):
        if params.get(N.FLATTEN, False):
            if list_results:
                for match in result:
                    flatten_dict(match, max_depth=2)
            else:
                flatten_dict(result, max_depth=2)

        results_formatted.append({name: result})

    if request.method == 'GET':
        return make_response(jsonify(results_formatted[0]))
    else:
        return make_response(jsonify({N.RESULTS: results_formatted}))


def create_ok_response(request, params_list, name, results, list_results=True):
    if request.method == 'GET':
        fmt = params_list[0][N.FORMAT]
    else:
        fmt = 'json'

    if fmt == 'json':
        return create_json_response(request, params_list, name, results,
                                    list_results)
