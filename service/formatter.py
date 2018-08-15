"""Módulo 'formatter' de georef-api

Contiene funciones que establecen la presentación de los datos obtenidos desde
las consultas a los índices o a la base de datos.
"""

from service import strings
from service import names as N
import geojson
from flask import make_response, jsonify, Response

CSV_SEP = ','
CSV_ESCAPE = '"'
CSV_NEWLINE = '\n'
FLAT_SEP = '_'

STATES_CSV_FIELDS = [
    (N.ID, [N.STATE, N.ID]),
    (N.NAME, [N.STATE, N.NAME]),
    (N.C_LAT, [N.STATE, N.C_LAT]),
    (N.C_LON, [N.STATE, N.C_LON]),
    (N.SOURCE, [N.STATE, N.SOURCE])
]

DEPARTMENTS_CSV_FIELDS = [
    (N.ID, [N.DEPT, N.ID]),
    (N.NAME, [N.DEPT, N.NAME]),
    (N.C_LAT, [N.DEPT, N.C_LAT]),
    (N.C_LON, [N.DEPT, N.C_LON]),
    (N.STATE_ID, [N.STATE, N.ID]),
    (N.STATE_NAME, [N.STATE, N.NAME]),
    (N.SOURCE, [N.DEPT, N.SOURCE])
]

MUNICIPALITIES_CSV_FIELDS = [
    (N.ID, [N.MUN, N.ID]),
    (N.NAME, [N.MUN, N.NAME]),
    (N.C_LAT, [N.MUN, N.C_LAT]),
    (N.C_LON, [N.MUN, N.C_LON]),
    (N.STATE_ID, [N.STATE, N.ID]),
    (N.STATE_NAME, [N.STATE, N.NAME]),
    (N.DEPT_ID, [N.DEPT, N.ID]),
    (N.DEPT_NAME, [N.DEPT, N.NAME]),
    (N.SOURCE, [N.MUN, N.SOURCE])
]

LOCALITIES_CSV_FIELDS = [
    (N.ID, [N.LOCALITY, N.ID]),
    (N.NAME, [N.LOCALITY, N.NAME]),
    (N.C_LAT, [N.LOCALITY, N.C_LAT]),
    (N.C_LON, [N.LOCALITY, N.C_LON]),
    (N.STATE_ID, [N.STATE, N.ID]),
    (N.STATE_NAME, [N.STATE, N.NAME]),
    (N.DEPT_ID, [N.DEPT, N.ID]),
    (N.DEPT_NAME, [N.DEPT, N.NAME]),
    (N.MUN_ID, [N.MUN, N.ID]),
    (N.MUN_NAME, [N.MUN, N.NAME]),
    (N.LOCALITY_TYPE, [N.LOCALITY, N.LOCALITY_TYPE]),
    (N.SOURCE, [N.LOCALITY, N.SOURCE])
]

STREETS_CSV_FIELDS = [
    (N.ID, [N.STREET, N.ID]),
    (N.NAME, [N.STREET, N.NAME]),
    (N.START_R, [N.STREET, N.START_R]),
    (N.START_L, [N.STREET, N.START_L]),
    (N.END_R, [N.STREET, N.END_R]),
    (N.END_L, [N.STREET, N.END_L]),
    (N.FULL_NAME, [N.STREET, N.FULL_NAME]),
    (N.ROAD_TYPE, [N.STREET, N.ROAD_TYPE]),
    (N.STATE_ID, [N.STATE, N.ID]),
    (N.STATE_NAME, [N.STATE, N.NAME]),
    (N.DEPT_ID, [N.DEPT, N.ID]),
    (N.DEPT_NAME, [N.DEPT, N.NAME]),
    (N.SOURCE, [N.STREET, N.SOURCE])
]

ADDRESSES_CSV_FIELDS = [
    (N.ID, [N.STREET, N.ID]),
    (N.NAME, [N.STREET, N.NAME]),
    (N.DOOR_NUM, [N.STREET, N.DOOR_NUM]),
    (N.FULL_NAME, [N.STREET, N.FULL_NAME]),
    (N.ROAD_TYPE, [N.STREET, N.ROAD_TYPE]),
    (N.STATE_ID, [N.STATE, N.ID]),
    (N.STATE_NAME, [N.STATE, N.NAME]),
    (N.DEPT_ID, [N.DEPT, N.ID]),
    (N.DEPT_NAME, [N.DEPT, N.NAME]),
    (N.LOCATION_LAT, [N.ADDRESS, N.LAT]),
    (N.LOCATION_LON, [N.ADDRESS, N.LON]),
    (N.SOURCE, [N.STREET, N.SOURCE])
]


def flatten_dict(d, max_depth=3, sep=FLAT_SEP):
    """Aplana un diccionario recursivamente. Modifica el diccionario original.
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
            flatten_dict(v, max_depth - 1, sep)

            for subkey, subval in v.items():
                flat_key = sep.join([key, subkey])
                d[flat_key] = subval

            del d[key]


def format_params_error_dict(error_dict):
    """Toma un diccionario de errores de parámetros y les da una estructura
    apropiada para ser incluidos en una respuesta HTTP con contenido JSON.

    Args:
        error_dict (dict): Diccionario de errores.

    Returns:
        list: Lista de errores, cada elemento corresponde a un ítem del
            diccionario recibido.

    """
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
    """Toma un diccionario de errores de parámetros y devuelve una respuesta
    HTTP 400 con contenido JSON detallando los errores.

    Args:
        errors (dict): Diccionario de errores.

    Returns:
        flask.Response: Respuesta HTTP con errores.

    """
    errors_fmt = format_params_error_dict(errors)

    return make_response(jsonify({
        'errores': errors_fmt
    }), 400)


def create_param_error_response_bulk(errors):
    """Toma una lista de diccionarios de errores de parámetros y devuelve una
    respuesta HTTP 400 con contenido JSON detallando todos los errores.

    Args:
        errors (list): Lista de diccionarios de errores.

    Returns:
        flask.Response: Respuesta HTTP con errores.

    """
    errors_fmt = [format_params_error_dict(d) for d in errors]

    return make_response(jsonify({
        'errores': errors_fmt
    }), 400)


def create_404_error_response():
    """Retorna un error HTTP con código 404.

    Returns:
        flask.Response: Respuesta HTTP con error 404.

    """
    errors = [
        {
            'mensaje': strings.NOT_FOUND
        }
    ]

    return make_response(jsonify({
        'errores': errors
    }), 404)


def create_internal_error_response():
    """Retorna un error HTTP con código 500.

    Returns:
        flask.Response: Respuesta HTTP con error 500.

    """
    errors = [
        {
            'mensaje': strings.INTERNAL_ERROR
        }
    ]

    return make_response(jsonify({
        'errores': errors
    }), 500)


def create_csv_response(name, result, fmt):
    """Toma un resultado (iterable) de una consulta, y devuelve una respuesta
    HTTP 200 con el resultado en formato CSV.

    Args:
        name (str): Nombre de la entidad que fue consultada.
        result (list): Lista de entidades.
        fmt (dict): Parámetros de formato.

    Returns:
        flask.Response: Respuesta HTTP con contenido CSV.

    """
    def csv_generator():
        keys = []
        field_names = []
        for original_field, csv_field_name in fmt[N.CSV_FIELDS]:
            if original_field in fmt[N.FIELDS]:
                keys.append(original_field.replace('.', FLAT_SEP))
                field_names.append(FLAT_SEP.join(csv_field_name))

        yield '{}{}'.format(CSV_SEP.join(field_names), CSV_NEWLINE)

        for match in result:
            flatten_dict(match, max_depth=2)

            values = []
            for key in keys:
                original_val = match[key]
                val = str(original_val) if original_val is not None else ''

                escape = False
                if CSV_SEP in val or CSV_NEWLINE in val:
                    escape = True

                if CSV_ESCAPE in val:
                    val = val.replace(CSV_ESCAPE, CSV_ESCAPE * 2)
                    escape = True

                if escape:
                    values.append('{}{}{}'.format(CSV_ESCAPE, val, CSV_ESCAPE))
                else:
                    values.append(val)

            yield '{}{}'.format(CSV_SEP.join(values), CSV_NEWLINE)

    resp = Response(csv_generator(), mimetype='text/csv')
    return make_response((resp, {
        'Content-Disposition': 'attachment; filename={}.csv'.format(
            name.lower())
    }))


def create_geojson_response(result, iterable_result):
    """Toma un resultado de una consulta, y devuelve una respuesta
    HTTP 200 con el resultado en formato GeoJSON.

    Args:
        result (list, dict): Entidad o lista de entidades.
        iterable_result (bool): Verdadero si el resultado es iterable. Si no lo
            es, internamente se crea una lista de un elemento con el resultado
            adentro.

    Returns:
        flask.Response: Respuesta HTTP con contenido GeoJSON.

    """
    if iterable_result:
        items = result
    else:
        items = [result]

    features = []
    for item in items:
        lat = item.pop(N.LAT, None) or item.pop(N.C_LAT, None)
        lon = item.pop(N.LON, None) or item.pop(N.C_LON, None)

        if lat and lon:
            point = geojson.Point((lat, lon))
            features.append(geojson.Feature(geometry=point, properties=item))

    return make_response(jsonify(geojson.FeatureCollection(features)))


def format_result_json(name, result, fmt, iterable_result):
    """Toma el resultado de una consulta, y la devuelve con una estructura
    apropiada para ser convertida a JSON.

    Args:
        name (str): Nombre de la entidad consultada.
        result (list, dict): Entidad o lista de entidades.
        fmt (dict): Parámetros de formato.
        iterable_result (bool): Verdadero si el resultado es iterable.

    Returns:
        dict: Resultados con esctructura y formato apropiados.

    """
    if fmt.get(N.FLATTEN, False):
        if iterable_result:
            for match in result:
                flatten_dict(match, max_depth=2)
        else:
            flatten_dict(result, max_depth=2)

    return {name: result}


def create_json_response_single(name, result, fmt, iterable_result):
    """Toma un resultado de una consulta, y devuelve una respuesta
    HTTP 200 con el resultado en formato JSON.

    Args:
        name (str): Nombre de la entidad consultada.
        result (list, dict): Entidad o lista de entidades.
        fmt (dict): Parámetros de formato.
        iterable_result (bool): Verdadero si el resultado es iterable.

    Returns:
        flask.Response: Respuesta HTTP con contenido JSON.

    """
    json_response = format_result_json(name, result, fmt, iterable_result)
    return make_response(jsonify(json_response))


def create_json_response_bulk(name, results, formats, iterable_result):
    """Toma una lista de resultados de una consulta o más, y devuelve una
    respuesta HTTP 200 con los resultados en formato JSON.

    Args:
        name (str): Nombre de la entidad consultada.
        results (list): Lista de resultados.
        formats (list): Lista de parámetros de formato por consulta.
        iterable_result (bool): Verdadero si todos los resultados son
            iterables.

    Returns:
        flask.Response: Respuesta HTTP con contenido JSON.

    """
    json_results = [
        format_result_json(name, result, fmt, iterable_result)
        for result, fmt in zip(results, formats)
    ]

    return make_response(jsonify({
        N.RESULTS: json_results
    }))


def filter_result_fields(result, fields_dict, max_depth=3):
    """Remueve campos de un resultado recursivamente de acuerdo a las
    especificaciones de un diccionario de campos.

    Args:
        result (dict): Resultado con valores a filtrar.
        fields_dict (dict): Diccionario especificando cuáles campos mantener.
    """
    if max_depth <= 0:
        raise RuntimeError('Profundidad máxima alcanzada.')

    for key in list(result.keys()):
        value = result[key]
        field = fields_dict.get(key)

        if not field:
            del result[key]
        elif isinstance(field, dict):
            if not isinstance(value, dict):
                raise RuntimeError(
                    'No se puede especificar la presencia de sub-campos ' +
                    'para valores no diccionarios.')

            filter_result_fields(value, fields_dict[key], max_depth - 1)


def format_result_fields(result, fmt, iterable_result):
    """Aplica el parámetro de formato 'campos' a un resultado.

    Args:
        result (dict): Resultado con valores a filtrar.
        fmt (dict): Parámetros de formato.
        iterable_result (bool): Verdadero si el resultado es iterable.

    """
    fields_dict = fields_list_to_dict(fmt[N.FIELDS])
    if iterable_result:
        for item in result:
            filter_result_fields(item, fields_dict)
    else:
        filter_result_fields(result, fields_dict)


def format_results_fields(results, formats, iterable_result):
    """Aplica el parámetro de formato 'campos' a varios resultados.

    Args:
        results (list): Resultados con valores a filtrar.
        formats (list): Lista de parámetros de formato.
        iterable_result (bool): Verdadero si todos los resultados son
            iterables.

    """
    for result, fmt in zip(results, formats):
        format_result_fields(result, fmt, iterable_result)


def fields_list_to_dict(fields):
    """Convierte una lista de campos (potencialmente, campos anidados separados
    con puntos) en un diccionario de uno o más niveles conteniendo 'True' por
    cada campo procesado.

    Args:
        fields (dict): Lista de campos.

    Returns:
        dict: Diccionario de campos.

    """
    fields_dict = {}
    for field in fields:
        parts = field.split('.')
        current = fields_dict
        for part in parts[:-1]:
            current = current.setdefault(part, {})

        current[parts[-1]] = True

    return fields_dict


def create_ok_response(name, result, fmt, iterable_result=True):
    """Toma un resultado de una consulta, y devuelve una respuesta
    HTTP 200 con el resultado en el formato especificado.

    Args:
        name (str): Nombre de la entidad consultada.
        result (list, dict): Entidad o lista de entidades.
        fmt (dict): Parámetros de formato.
        iterable_result (bool): Verdadero si el resultado es iterable.

    Returns:
        flask.Response: Respuesta HTTP 200.

    """
    format_result_fields(result, fmt, iterable_result)

    if fmt[N.FORMAT] == 'json':
        return create_json_response_single(name, result, fmt, iterable_result)
    elif fmt[N.FORMAT] == 'csv':
        if not iterable_result:
            raise RuntimeError(
                'Se requieren datos iterables para crear una respuesta CSV.')

        return create_csv_response(name, result, fmt)
    elif fmt[N.FORMAT] == 'geojson':
        return create_geojson_response(result, iterable_result)


def create_ok_response_bulk(name, results, formats, iterable_result=True):
    """Toma una lista de resultados de una consulta o más, y devuelve una
    respuesta HTTP 200 con los resultados en formato JSON.

    Args:
        name (str): Nombre de la entidad consultada.
        results (list): Lista de resultados.
        formats (list): Lista de parámetros de formato por consulta.
        iterable_result (bool): Verdadero si todos los resultados son
            iterables.

    Returns:
        flask.Response: Respuesta HTTP 200.

    """
    format_results_fields(results, formats, iterable_result)
    return create_json_response_bulk(name, results, formats, iterable_result)
