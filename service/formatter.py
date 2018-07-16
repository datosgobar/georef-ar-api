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


def create_param_error_response_single(errors):
    errors_fmt = format_params_error_dict(errors)

    return make_response(jsonify({
        'errores': errors_fmt
    }), 400)


def create_param_error_response_bulk(errors):
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


def create_csv_response(name, result):
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


def create_geojson_response(result, iterable_result):
    if iterable_result:
        items = result
    else:
        items = [result]

    features = []
    for item in items:
        if N.LAT in item and N.LON in item:
            lat = item.pop(N.LAT)
            lon = item.pop(N.LON)

            # TODO: Cambiar tipos de datos de LAT y LON en índices
            point = geojson.Point((float(lat), float(lon)))
            features.append(geojson.Feature(geometry=point, properties=item))

    return make_response(jsonify(geojson.FeatureCollection(features)))


def format_result_json(name, result, fmt, iterable_result):
    if fmt.get(N.FLATTEN, False):
        if iterable_result:
            for match in result:
                flatten_dict(match, max_depth=2)
        else:
            flatten_dict(result, max_depth=2)

    return {name: result}


def create_json_response_single(name, result, fmt, iterable_result):
    json_response = format_result_json(name, result, fmt, iterable_result)
    return make_response(jsonify(json_response))


def create_json_response_bulk(name, results, formats, iterable_result):
    json_results = [
        format_result_json(name, result, fmt, iterable_result)
        for result, fmt in zip(results, formats)
    ]

    return make_response(jsonify({
        N.RESULTS: json_results
    }))


def create_ok_response(name, result, fmt, iterable_result=True):
    if fmt[N.FORMAT] == 'json':
        return create_json_response_single(name, result, fmt, iterable_result)
    elif fmt[N.FORMAT] == 'csv':
        if not iterable_result:
            raise RuntimeError(
                'Se requieren datos iterables para crear una respuesta CSV.')

        return create_csv_response(name, result)
    elif fmt[N.FORMAT] == 'geojson':
        return create_geojson_response(result, iterable_result)


def create_ok_response_bulk(name, results, formats, iterable_result=True):
    return create_json_response_bulk(name, results, formats, iterable_result)
