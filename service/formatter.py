from service import strings
from service import names as N
import geojson
from flask import make_response, jsonify, Response

CSV_SEP = ';'


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
            'codigo_interno': param_error.error_type.value,
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


def create_internal_error_response(request):
    errors = [
        {
            'mensaje': strings.INTERNAL_ERROR
        }
    ]

    return make_response(jsonify({
        'errores': errors
    }), 500)


def create_csv_response(request, name, result):
    def csv_generator():
        first = result[0]
        flatten_dict(first, max_depth=2)
        keys = sorted(first.keys())

        yield '{}\n'.format(CSV_SEP.join(keys))
        
        for match in result:
            flatten_dict(match, max_depth=2)
            values = (str(match[key]) for key in keys)

            yield '{}\n'.format(CSV_SEP.join(values))

    resp = Response(csv_generator(), mimetype='text/csv')
    return make_response((resp, {
        'Content-Disposition': 'attachment; filename={}.csv'.format(
            name.lower())
    }))


def create_geojson_response(request, results, iterable_results):
    if iterable_results:
        items = results[0]
    else:
        items = results

    features = []
    for item in items:
        if N.LAT in item and N.LON in item:
            lat = item.pop(N.LAT)
            lon = item.pop(N.LON)

            # TODO: Cambiar tipos de datos de LAT y LON en índices
            point = geojson.Point((float(lat), float(lon)))
            features.append(geojson.Feature(geometry=point, properties=item))

    return make_response(jsonify(geojson.FeatureCollection(features)))


def create_json_response(request, params_list, name, results,
                         iterable_results):
    results_formatted = []
    for result, params in zip(results, params_list):
        if params.get(N.FLATTEN, False):
            if iterable_results:
                for match in result:
                    flatten_dict(match, max_depth=2)
            else:
                flatten_dict(result, max_depth=2)

        results_formatted.append({name: result})

    if request.method == 'GET':
        return make_response(jsonify(results_formatted[0]))
    else:
        return make_response(jsonify({N.RESULTS: results_formatted}))


def create_ok_response(request, params_list, name, results,
                       iterable_results=True):
    if request.method == 'GET':
        fmt = params_list[0][N.FORMAT]
    else:
        fmt = 'json'

    # TODO: Manejo de campo 'source'

    if fmt == 'json':
        return create_json_response(request, params_list, name, results,
                                    iterable_results)
    elif fmt == 'csv':
        if not iterable_results:
            raise RuntimeError(
                'Se requieren datos iterables para crear una respuesta CSV.')

        return create_csv_response(request, name, results[0])
    elif fmt == 'geojson':
        return create_geojson_response(request, results, iterable_results)
