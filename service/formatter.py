"""Módulo 'formatter' de georef-ar-api

Contiene funciones que establecen la presentación de los datos obtenidos desde
las consultas a los índices o a la base de datos.
"""

import csv
from flask import make_response, jsonify, Response, request
import geojson
from service import strings
from service import names as N

CSV_SEP = ','
CSV_QUOTE = '"'
CSV_NEWLINE = '\n'
FLAT_SEP = '_'

STATES_CSV_FIELDS = [
    (N.ID, [N.STATE, N.ID]),
    (N.NAME, [N.STATE, N.NAME]),
    (N.C_LAT, [N.STATE, N.CENTROID, N.LAT]),
    (N.C_LON, [N.STATE, N.CENTROID, N.LON]),
    (N.SOURCE, [N.STATE, N.SOURCE])
]

DEPARTMENTS_CSV_FIELDS = [
    (N.ID, [N.DEPT, N.ID]),
    (N.NAME, [N.DEPT, N.NAME]),
    (N.C_LAT, [N.DEPT, N.CENTROID, N.LAT]),
    (N.C_LON, [N.DEPT, N.CENTROID, N.LON]),
    (N.STATE_ID, [N.STATE, N.ID]),
    (N.STATE_NAME, [N.STATE, N.NAME]),
    (N.STATE_INTERSECTION, [N.STATE, N.INTERSECTION]),
    (N.SOURCE, [N.DEPT, N.SOURCE])
]

MUNICIPALITIES_CSV_FIELDS = [
    (N.ID, [N.MUN, N.ID]),
    (N.NAME, [N.MUN, N.NAME]),
    (N.C_LAT, [N.MUN, N.CENTROID, N.LAT]),
    (N.C_LON, [N.MUN, N.CENTROID, N.LON]),
    (N.STATE_ID, [N.STATE, N.ID]),
    (N.STATE_NAME, [N.STATE, N.NAME]),
    (N.STATE_INTERSECTION, [N.STATE, N.INTERSECTION]),
    (N.SOURCE, [N.MUN, N.SOURCE])
]

LOCALITIES_CSV_FIELDS = [
    (N.ID, [N.LOCALITY, N.ID]),
    (N.NAME, [N.LOCALITY, N.NAME]),
    (N.C_LAT, [N.LOCALITY, N.CENTROID, N.LAT]),
    (N.C_LON, [N.LOCALITY, N.CENTROID, N.LON]),
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
    (N.START_R, [N.STREET, N.DOOR_NUM, N.START, N.RIGHT]),
    (N.START_L, [N.STREET, N.DOOR_NUM, N.START, N.LEFT]),
    (N.END_R, [N.STREET, N.DOOR_NUM, N.END, N.RIGHT]),
    (N.END_L, [N.STREET, N.DOOR_NUM, N.END, N.LEFT]),
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


ENDPOINT_CSV_FIELDS = {
    N.STATES: STATES_CSV_FIELDS,
    N.DEPARTMENTS: DEPARTMENTS_CSV_FIELDS,
    N.MUNICIPALITIES: MUNICIPALITIES_CSV_FIELDS,
    N.LOCALITIES: LOCALITIES_CSV_FIELDS,
    N.STREETS: STREETS_CSV_FIELDS,
    N.ADDRESSES: ADDRESSES_CSV_FIELDS
}


class CSVLineWriter:
    """La clase CSVWriter permite escribir contenido CSV de a líneas, sin la
    necesidad de un objeto file-like como intermediario.

    Attributes:
        _dummy_writer (CSVLineWriter.DummyWriter): Objeto file-like utilizado
            como parámetro 'csvfile' para el csv.writer interno.
        _csv_writer (csv.writer): Objeto writer utilizado para darle formato a
            las filas provistas.

    """

    class DummyWriter:
        """La clase DummyWriter simplemente implementa el método write() como
        una asignación a una variable interna. Esto permite leer el contenido
        escrito en cualquier momento.

        """

        def __init__(self):
            self._content = None

        def write(self, content):
            self._content = content

        def getvalue(self):
            return self._content

    def __init__(self, *args, **kwargs):
        """Construye un objeto CSVLineWriter.

        Los argumentos recibidos se envían a el objeto csv.writer interno.

        """
        self._dummy_writer = CSVLineWriter.DummyWriter()
        self._csv_writer = csv.writer(self._dummy_writer, *args, **kwargs)

    def row_to_str(self, row, quote_positions=None):
        """Retorna una fila de valores como string en formato CSV.

        Args:
            row (list): Lista de valores.
            quote_positions (list): Lista de posiciones (índices) de 'row' que
                se deben entrecomillar obligatoriamente.

        Returns:
            str: Valores como fila en formato CSV.

        """
        self._csv_writer.writerow(row)
        row = self._dummy_writer.getvalue()

        if quote_positions:
            parts = row.split(CSV_SEP)

            for index in quote_positions:
                parts[index] = '{quot}{val}{quot}'.format(quot=CSV_QUOTE,
                                                          val=parts[index])

            row = CSV_SEP.join(parts)

        return row


def flatten_dict(d, max_depth=3, sep=FLAT_SEP):
    """Aplana un diccionario recursivamente. Modifica el diccionario original.
    Lanza un RuntimeError si no se pudo aplanar el diccionario
    con el número especificado de profundidad.

    Args:
        d (dict): Diccionario a aplanar.
        max_depth (int): Profundidad máxima a alcanzar.

    Raises:
        RuntimeError: cuando se alcanza la profundidad máxima. Se agrega esta
            medida de seguridad en caso de tener un diccionario demasiado
            profundo, o un diccionario con referencias cíclicas.

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
        error = {
            'nombre_parametro': param_name,
            'codigo_interno': param_error.error_type.value,
            'mensaje': param_error.message,
            'ubicacion': param_error.source
        }

        if param_error.help:
            error['ayuda'] = param_error.help

        results.append(error)

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
            'mensaje': strings.NOT_FOUND,
            # El listado de recursos podría utilizar app.url_map, pero es mejor
            # listar los elementos más importantes manualmente para que la
            # respuesta sea de mayor utilidad para el usuario.
            'recursos_disponibles': [
                '/api/provincias',
                '/api/departamentos',
                '/api/municipios',
                '/api/localidades',
                '/api/calles',
                '/api/direcciones',
                '/api/ubicacion'
            ]
        }
    ]

    return make_response(jsonify({
        'errores': errors
    }), 404)


def create_405_error_response(url_map):
    """Retorna un error HTTP con código 405.

    Args:
        url_map (werkzeug.routing.Map): Mapa de URLs de la aplicación Flask.

    Returns:
        flask.Response: Respuesta HTTP con error 405.

    """
    methods = {
        rule.rule: (list(rule.methods.difference({'HEAD', 'OPTIONS'})))
        for rule
        in url_map.iter_rules()
    }

    errors = [
        {
            'mensaje': strings.NOT_ALLOWED,
            'metodos_disponibles': methods[request.path]
        }
    ]

    return make_response(jsonify({
        'errores': errors
    }), 405)


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
        result (QueryResult): Resultado de una consulta (con iterable==True).
        fmt (dict): Parámetros de formato.

    Returns:
        flask.Response: Respuesta HTTP con contenido CSV.

    """
    def csv_generator():
        csv_writer = CSVLineWriter(delimiter=CSV_SEP,
                                   lineterminator=CSV_NEWLINE,
                                   quotechar=CSV_QUOTE)

        keys = []
        field_names = []
        for original_field, csv_field_name in fmt[N.CSV_FIELDS]:
            if original_field in fmt[N.FIELDS]:
                keys.append(original_field.replace('.', FLAT_SEP))
                field_names.append(FLAT_SEP.join(csv_field_name))

        yield csv_writer.row_to_str(field_names)

        for match in result.entities:
            flatten_dict(match, max_depth=3)
            values = [match[key] for key in keys]

            yield csv_writer.row_to_str(values, quote_positions=[0])

    resp = Response(csv_generator(), mimetype='text/csv')
    return make_response((resp, {
        'Content-Disposition': 'attachment; filename={}.csv'.format(
            name.lower())
    }))


def create_geojson_response(result, fmt):
    """Toma un resultado de una consulta, y devuelve una respuesta
    HTTP 200 con el resultado en formato GeoJSON.

    Args:
        result (QueryResult): Resultado de una consulta.
        fmt (dict): Parámetros de formato.

    Returns:
        flask.Response: Respuesta HTTP con contenido GeoJSON.

    """
    features = []
    for item in result.entities:
        lat, lon = None, None
        if N.LAT in item and N.LON in item:
            lat = item.pop(N.LAT)
            lon = item.pop(N.LON)
        elif N.CENTROID in item or N.LOCATION in item:
            loc = item.pop(N.CENTROID, None) or item.pop(N.LOCATION)
            lat = loc[N.LAT]
            lon = loc[N.LON]

        if lat and lon:
            if fmt.get(N.FLATTEN, False):
                flatten_dict(item, max_depth=3)

            point = geojson.Point((lon, lat))
            features.append(geojson.Feature(geometry=point, properties=item))

    return make_response(jsonify(geojson.FeatureCollection(features)))


def format_result_json(name, result, fmt):
    """Toma el resultado de una consulta, y la devuelve con una estructura
    apropiada para ser convertida a JSON.

    Args:
        name (str): Nombre de la entidad consultada.
        result (QueryResult): Resultado de una consulta.
        fmt (dict): Parámetros de formato.

    Returns:
        dict: Resultados con esctructura y formato apropiados.

    """
    if fmt.get(N.FLATTEN, False):
        if result.iterable:
            for match in result.entities:
                flatten_dict(match, max_depth=3)
        else:
            flatten_dict(result.first_entity(), max_depth=3)

    if result.iterable:
        return {
            name: result.entities,
            N.QUANTITY: len(result.entities),
            N.TOTAL: result.total,
            N.OFFSET: result.offset
        }

    return {name: result.first_entity()}


def create_json_response_single(name, result, fmt):
    """Toma un resultado de una consulta, y devuelve una respuesta
    HTTP 200 con el resultado en formato JSON.

    Args:
        name (str): Nombre de la entidad consultada.
        result (QueryResult): Resultado de una consulta.
        fmt (dict): Parámetros de formato.

    Returns:
        flask.Response: Respuesta HTTP con contenido JSON.

    """
    json_response = format_result_json(name, result, fmt)
    return make_response(jsonify(json_response))


def create_json_response_bulk(name, results, formats):
    """Toma una lista de resultados de una consulta o más, y devuelve una
    respuesta HTTP 200 con los resultados en formato JSON.

    Args:
        name (str): Nombre de la entidad consultada.
        results (list): Lista de resultados.
        formats (list): Lista de parámetros de formato por consulta.

    Returns:
        flask.Response: Respuesta HTTP con contenido JSON.

    """
    json_results = [
        format_result_json(name, result, fmt)
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


def format_result_fields(result, fmt):
    """Aplica el parámetro de formato 'campos' a un resultado.

    Args:
        result (QueryResult): Resultado con valores a filtrar.
        fmt (dict): Parámetros de formato.

    """
    fields_dict = fields_list_to_dict(fmt[N.FIELDS])
    if result.iterable:
        for item in result.entities:
            filter_result_fields(item, fields_dict)
    else:
        filter_result_fields(result.first_entity(), fields_dict)


def format_results_fields(results, formats):
    """Aplica el parámetro de formato 'campos' a varios resultados.

    Args:
        results (list): Resultados con valores a filtrar.
        formats (list): Lista de parámetros de formato.

    """
    for result, fmt in zip(results, formats):
        format_result_fields(result, fmt)


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


def create_ok_response(name, result, fmt):
    """Toma un resultado de una consulta, y devuelve una respuesta
    HTTP 200 con el resultado en el formato especificado.

    Args:
        name (str): Nombre de la entidad consultada.
        result (QueryResult): Resultado de una consulta.
        fmt (dict): Parámetros de formato.

    Returns:
        flask.Response: Respuesta HTTP 200.

    Raises:
        RuntimeError: Si se especifica un formato desconocido, o si se
            especifica formato CSV para datos no iterables.

    """
    format_result_fields(result, fmt)

    if fmt[N.FORMAT] == 'json':
        return create_json_response_single(name, result, fmt)

    if fmt[N.FORMAT] == 'csv':
        if not result.iterable:
            raise RuntimeError(
                'Se requieren datos iterables para crear una respuesta CSV.')

        return create_csv_response(name, result, fmt)

    if fmt[N.FORMAT] == 'geojson':
        return create_geojson_response(result, fmt)

    raise RuntimeError('Formato desconocido.')


def create_ok_response_bulk(name, results, formats):
    """Toma una lista de resultados de una consulta o más, y devuelve una
    respuesta HTTP 200 con los resultados en formato JSON.

    Args:
        name (str): Nombre de la entidad consultada.
        results (list): Lista de resultados QueryResult.
        formats (list): Lista de parámetros de formato por consulta.

    Returns:
        flask.Response: Respuesta HTTP 200.

    """
    format_results_fields(results, formats)
    # El valor FMT de cada elemento de formats es 'json' (ya que en modo bulk
    # solo se permiten respuestas JSON).
    return create_json_response_bulk(name, results, formats)
