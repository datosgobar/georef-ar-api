"""Módulo 'formatter' de georef-ar-api

Contiene funciones que establecen la presentación de los datos obtenidos desde
las consultas a los índices o a la base de datos.
"""

import csv
import io
import zipfile
import shutil
from xml.etree import ElementTree
from flask import make_response, jsonify, Response, request, send_file
import geojson
import shapefile
from service import strings, constants
from service import names as N


CSV_SEP = ','
CSV_QUOTE = '"'
CSV_NEWLINE = '\n'
FLAT_SEP = '_'
_SHP_MAX_FIELD_CONTENT_LEN = 128
_SHP_MAX_FIELD_NAME_LEN = 11
_SHP_PRJ = ('GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378'
            '137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.0174532'
            '92519943295]]')

_STATES_CSV_FIELDS = [
    (N.ID, [N.STATE, N.ID]),
    (N.NAME, [N.STATE, N.NAME]),
    (N.COMPLETE_NAME, [N.STATE, N.COMPLETE_NAME]),
    (N.ISO_ID, [N.STATE, N.ISO_ID]),
    (N.ISO_NAME, [N.STATE, N.ISO_NAME]),
    (N.C_LAT, [N.STATE, N.CENTROID, N.LAT]),
    (N.C_LON, [N.STATE, N.CENTROID, N.LON]),
    (N.SOURCE, [N.STATE, N.SOURCE]),
    (N.CATEGORY, [N.STATE, N.CATEGORY])
]

_DEPARTMENTS_CSV_FIELDS = [
    (N.ID, [N.DEPT, N.ID]),
    (N.NAME, [N.DEPT, N.NAME]),
    (N.COMPLETE_NAME, [N.DEPT, N.COMPLETE_NAME]),
    (N.C_LAT, [N.DEPT, N.CENTROID, N.LAT]),
    (N.C_LON, [N.DEPT, N.CENTROID, N.LON]),
    (N.STATE_ID, [N.STATE, N.ID]),
    (N.STATE_NAME, [N.STATE, N.NAME]),
    (N.STATE_INTERSECTION, [N.STATE, N.INTERSECTION]),
    (N.SOURCE, [N.DEPT, N.SOURCE]),
    (N.CATEGORY, [N.DEPT, N.CATEGORY])
]

_MUNICIPALITIES_CSV_FIELDS = [
    (N.ID, [N.MUN, N.ID]),
    (N.NAME, [N.MUN, N.NAME]),
    (N.COMPLETE_NAME, [N.MUN, N.COMPLETE_NAME]),
    (N.C_LAT, [N.MUN, N.CENTROID, N.LAT]),
    (N.C_LON, [N.MUN, N.CENTROID, N.LON]),
    (N.STATE_ID, [N.STATE, N.ID]),
    (N.STATE_NAME, [N.STATE, N.NAME]),
    (N.STATE_INTERSECTION, [N.STATE, N.INTERSECTION]),
    (N.SOURCE, [N.MUN, N.SOURCE]),
    (N.CATEGORY, [N.MUN, N.CATEGORY])
]

_CENSUS_LOCALITIES_CSV_FIELDS = [
    (N.ID, [N.CENSUS_LOCALITY, N.ID]),
    (N.NAME, [N.CENSUS_LOCALITY, N.NAME]),
    (N.C_LAT, [N.CENSUS_LOCALITY, N.CENTROID, N.LAT]),
    (N.C_LON, [N.CENSUS_LOCALITY, N.CENTROID, N.LON]),
    (N.STATE_ID, [N.STATE, N.ID]),
    (N.STATE_NAME, [N.STATE, N.NAME]),
    (N.DEPT_ID, [N.DEPT, N.ID]),
    (N.DEPT_NAME, [N.DEPT, N.NAME]),
    (N.MUN_ID, [N.MUN, N.ID]),
    (N.MUN_NAME, [N.MUN, N.NAME]),
    (N.SOURCE, [N.CENSUS_LOCALITY, N.SOURCE]),
    (N.FUNCTION, [N.CENSUS_LOCALITY, N.FUNCTION]),
    (N.CATEGORY, [N.CENSUS_LOCALITY, N.CATEGORY])
]

_SETTLEMENTS_CSV_FIELDS = [
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
    (N.CENSUS_LOCALITY_ID, [N.CENSUS_LOCALITY, N.ID]),
    (N.CENSUS_LOCALITY_NAME, [N.CENSUS_LOCALITY, N.NAME]),
    (N.SOURCE, [N.LOCALITY, N.SOURCE]),
    (N.CATEGORY, [N.LOCALITY, N.CATEGORY])
]

_LOCALITIES_CSV_FIELDS = _SETTLEMENTS_CSV_FIELDS

_STREETS_CSV_FIELDS = [
    (N.ID, [N.STREET, N.ID]),
    (N.NAME, [N.STREET, N.NAME]),
    (N.START_R, [N.STREET, N.DOOR_NUM, N.START, N.RIGHT]),
    (N.START_L, [N.STREET, N.DOOR_NUM, N.START, N.LEFT]),
    (N.END_R, [N.STREET, N.DOOR_NUM, N.END, N.RIGHT]),
    (N.END_L, [N.STREET, N.DOOR_NUM, N.END, N.LEFT]),
    (N.FULL_NAME, [N.STREET, N.FULL_NAME]),
    (N.CATEGORY, [N.STREET, N.CATEGORY]),
    (N.STATE_ID, [N.STATE, N.ID]),
    (N.STATE_NAME, [N.STATE, N.NAME]),
    (N.DEPT_ID, [N.DEPT, N.ID]),
    (N.DEPT_NAME, [N.DEPT, N.NAME]),
    (N.CENSUS_LOCALITY_ID, [N.CENSUS_LOCALITY, N.ID]),
    (N.CENSUS_LOCALITY_NAME, [N.CENSUS_LOCALITY, N.NAME]),
    (N.SOURCE, [N.STREET, N.SOURCE])
]

_ADDRESSES_CSV_FIELDS = [
    (N.FULL_NAME, [N.ADDRESS, N.FULL_NAME]),
    (N.STREET_NAME, [N.STREET, N.NAME]),
    (N.STREET_ID, [N.STREET, N.ID]),
    (N.STREET_CATEGORY, [N.STREET, N.CATEGORY]),
    (N.DOOR_NUM_VAL, [N.DOOR_NUM, N.VALUE]),
    (N.DOOR_NUM_UNIT, [N.DOOR_NUM, N.UNIT]),
    (N.STREET_X1_NAME, [N.STREET_X1, N.NAME]),
    (N.STREET_X1_ID, [N.STREET_X1, N.ID]),
    (N.STREET_X1_CATEGORY, [N.STREET_X1, N.CATEGORY]),
    (N.STREET_X2_NAME, [N.STREET_X2, N.NAME]),
    (N.STREET_X2_ID, [N.STREET_X2, N.ID]),
    (N.STREET_X2_CATEGORY, [N.STREET_X2, N.CATEGORY]),
    (N.FLOOR, [N.FLOOR]),
    (N.STATE_ID, [N.STATE, N.ID]),
    (N.STATE_NAME, [N.STATE, N.NAME]),
    (N.DEPT_ID, [N.DEPT, N.ID]),
    (N.DEPT_NAME, [N.DEPT, N.NAME]),
    (N.CENSUS_LOCALITY_ID, [N.CENSUS_LOCALITY, N.ID]),
    (N.CENSUS_LOCALITY_NAME, [N.CENSUS_LOCALITY, N.NAME]),
    (N.LOCATION_LAT, [N.ADDRESS, N.LAT]),
    (N.LOCATION_LON, [N.ADDRESS, N.LON]),
    (N.SOURCE, [N.ADDRESS, N.SOURCE])
]


_ENDPOINT_CSV_FIELDS = {
    N.STATES: _STATES_CSV_FIELDS,
    N.DEPARTMENTS: _DEPARTMENTS_CSV_FIELDS,
    N.MUNICIPALITIES: _MUNICIPALITIES_CSV_FIELDS,
    N.CENSUS_LOCALITIES: _CENSUS_LOCALITIES_CSV_FIELDS,
    N.SETTLEMENTS: _SETTLEMENTS_CSV_FIELDS,
    N.LOCALITIES: _LOCALITIES_CSV_FIELDS,
    N.STREETS: _STREETS_CSV_FIELDS,
    N.ADDRESSES: _ADDRESSES_CSV_FIELDS
}


_SHP_SHORT_FIELD_NAMES = {
    key.replace(N.FIELDS_SEP, FLAT_SEP): value
    for key, value in
    {
        N.STATE_NAME: 'prov_nombre',
        N.STATE_ID: 'prov_id',
        N.STATE_INTERSECTION: 'prov_intscn',
        N.DEPT_NAME: 'dpto_nombre',
        N.DEPT_ID: 'dpto_id',
        N.CENSUS_LOCALITY_ID: 'lcen_id',
        N.CENSUS_LOCALITY_NAME: 'lcen_nombre',
        N.MUN_NAME: 'muni_nombre',
        N.MUN_ID: 'muni_id',
        N.C_LAT: 'centr_lat',
        N.C_LON: 'centr_lon',
        N.FULL_NAME: 'nomencla',
        N.COMPLETE_NAME: 'nombre_comp',
        N.START_R: 'alt_ini_der',
        N.START_L: 'alt_ini_izq',
        N.END_R: 'alt_fin_der',
        N.END_L: 'alt_fin_izq'
    }.items()
}
"""dict: El formato Shapefile no permite campos cuyos nombres tengan más de 11
caracteres, por lo que es necesario especificar abreviaciones para campos que
maneje la API que sean demasiado largos."""


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

    def row_to_str(self, row):
        """Retorna una fila de valores como string en formato CSV.

        Args:
            row (list): Lista de valores.

        Returns:
            str: Valores como fila en formato CSV.

        """
        self._csv_writer.writerow(row)
        return self._dummy_writer.getvalue()


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
        raise RuntimeError("Maximum depth reached")

    for key in list(d.keys()):
        v = d[key]
        if isinstance(v, dict):
            flatten_dict(v, max_depth - 1, sep)

            for subkey, subval in v.items():
                flat_key = sep.join([key, subkey])
                d[flat_key] = subval

            del d[key]


def _create_xml_element(tag, content=None):
    """Crea un elemento XML con un contenido interno opcional.

    Args:
        tag (str): Tag del elemento XML.
        content (object): Contenido opcional del elemento (se lo convierte a
            str).

    Returns:
        ElementTree.Element: elemento XML.

    """
    element = ElementTree.Element(tag)
    if content is not None:
        element.text = str(content)
    return element


def _xml_flask_response(element, status=200):
    """Crea una respuesta HTTP con contenido XML.

    Args:
        element (ElementTree.Element): Elemento XML raíz a retornar en la
            respuesta HTTP.
        status (int): Código de respuesta HTTP a utilizar.

    Returns:
        flask.Response: Respuesta HTTP con el contenido especificado.

    """
    contents = io.StringIO()
    root = _create_xml_element(constants.API_NAME)
    root.append(element)

    ElementTree.ElementTree(root).write(contents, encoding='unicode',
                                        xml_declaration=True)

    return Response(contents.getvalue(), mimetype='application/xml',
                    status=status)


def value_to_xml(tag, val, *, list_item_names=None, list_item_default=None,
                 max_depth=5):
    """Dado un valor dict, list, str, None o numérico, lo convierte
    recursivamentea su equivalente en XML y retorna el nodo raíz resultante.

    Args:
        tag (str): Valor a utilizar como el tag del elemento XML raíz.
        val (dict, list, int, float, NoneType, str): Valor a convertir a XML.
            En caso de dict y list, se convierten también los valores
            contenidos internamente, y se contruye un árbol XML con los
            resultados.
        list_item_names (dict): Valores a utilizar como tags en caso de tener
            que convertir listas a XML. Por ejemplo, si tag == 'libros' y val
            es de tipo list, entonces list_item_names podría contener el mapeo
            'libros' -> 'libro'. De esta forma, se crearía un elemento XML con
            tag 'libros', e internamente cada elemento de la lista estaría
            dentro de un tag 'libro'. Notar que el parámetro se utiliza también
            en las llamadas recursivas a 'value_to_xml', por lo que se pueden
            especificar los tags de elementos de listas para cualquier nivel de
            profundidad del valor a convertir. En caso de no encontrar un valor
            plural en el diccionario, se intenta utilizar el valor en
            'list_item_default'. Si su valor es None, se utiliza en cambio la
            función 'names.singular()' para buscar el singular de la palabra.
        list_item_default (str): Ver explicación bajo parámetro
            'list_item_names'.
        max_depth (int): Profundidad máxima a alcanzar.

    Raises:
        RuntimeError: cuando se alcanza la profundidad máxima. Se agrega esta
            medida de seguridad en caso de tener un diccionario demasiado
            profundo, o un diccionario con referencias cíclicas.

    Returns:
        ElementTree.Element: valor convertido a su equivalente en XML.

    """
    if max_depth <= 0:
        raise RuntimeError("Maximum depth reached")

    root = _create_xml_element(tag)

    if isinstance(val, dict):
        for key in sorted(val):
            elem = value_to_xml(key, val[key], list_item_names=list_item_names,
                                list_item_default=list_item_default,
                                max_depth=max_depth - 1)
            root.append(elem)
    elif isinstance(val, (list, set)):
        for value in val:
            list_item_name = None

            if list_item_names:
                # Intentar utilizar list_item_names primero
                list_item_name = list_item_names.get(tag)

            if not list_item_name:
                # Utilizar list_item_default o names.singular() si el singular
                # no fue especificado
                if list_item_default:
                    list_item_name = list_item_default
                else:
                    list_item_name = N.singular(tag)

            elem = value_to_xml(list_item_name, value,
                                list_item_names=list_item_names,
                                list_item_default=list_item_default,
                                max_depth=max_depth - 1)
            root.append(elem)
    elif val is not None:
        root.text = str(val)

    return root


def _format_params_error_dict(error_dict):
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
            error[N.HELP] = param_error.help

        results.append(error)

    return results


def create_param_error_response_single(errors, fmt):
    """Toma un diccionario de errores de parámetros y devuelve una respuesta
    HTTP 400 detallando los errores.

    Args:
        errors (dict): Diccionario de errores.
        fmt (str): Formato de datos a utilizar en la respuesta.

    Returns:
        flask.Response: Respuesta HTTP con errores.

    """
    errors_fmt = _format_params_error_dict(errors)

    if fmt == 'xml':
        root = value_to_xml('errores', errors_fmt,
                            list_item_names={N.HELP: N.ITEM})
        return _xml_flask_response(root, status=400)

    # Para cualquier formato que no sea XML, utilizar JSON para devolver
    # los errores.
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
    errors_fmt = [_format_params_error_dict(d) for d in errors]

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
            # La variable 'app.url_map' contiene una lista de todos los
            # recursos de la app Flask, sin embargo es mejor listarlos
            # manualmente para evitar incluir los que comienzan con /api/v1.0.
            'recursos_disponibles': [
                '/api/provincias',
                '/api/departamentos',
                '/api/municipios',
                '/api/localidades-censales',
                '/api/asentamientos',
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


def _format_result_xml(name, result, fmt):
    """Toma el resultado de una consulta y la convierte a su equivalente en
    XML.

    Args:
        name (str): Nombre de la entidad consultada.
        result (QueryResult): Resultado de una consulta.
        fmt (dict): Parámetros de formato.

    Returns:
        ElementTree.Element: Resultados con estructura XML.

    """
    # Remover campos no especificados por el usuario.
    _format_result_fields(result, fmt)

    root = _create_xml_element(N.RESULT)
    root.append(value_to_xml(N.PARAMETERS, result.params,
                             list_item_default=N.ITEM))

    if result.iterable:
        root.append(value_to_xml(name, result.entities))
        root.append(_create_xml_element(N.QUANTITY, len(result.entities)))
        root.append(_create_xml_element(N.TOTAL, result.total))
        root.append(_create_xml_element(N.OFFSET, result.offset))
    else:
        root.append(value_to_xml(name, result.first_entity()))

    return root


def _create_xml_response_single(name, result, fmt):
    """Toma un resultado de una consulta, y devuelve una respuesta
    HTTP 200 con el resultado en formato XML.

    Args:
        name (str): Nombre de la entidad consultada.
        result (QueryResult): Resultado de una consulta.
        fmt (dict): Parámetros de formato.

    Returns:
        flask.Response: Respuesta HTTP 200 con contenido XML.

    """
    root = _format_result_xml(name, result, fmt)
    return _xml_flask_response(root)


def _create_shp_response_single(name, result, fmt):
    """Toma un resultado de una consulta, y devuelve una respuesta HTTP 200 con
    el resultado en formato SHP (Shapefile), comprimido en formato ZIP.

    Args:
        name (str): Nombre de la entidad que fue consultada.
        result (QueryResult): Resultado de una consulta.
        fmt (dict): Parámetros de formato.

    Returns:
        flask.Response: Respuesta HTTP con contenido SHP.

    """
    if not result.iterable:
        raise ValueError('SHP: Result must be iterable')

    contents = io.BytesIO()
    zip_file = zipfile.ZipFile(contents, mode='w')

    # El formato SHP exige la presencia de los siguientes 3 archivos:
    shp = io.BytesIO()
    shx = io.BytesIO()
    dbf = io.BytesIO()
    # Y opcionalmente:
    prj = io.BytesIO(_SHP_PRJ.encode('utf-8'))

    writer = shapefile.Writer(shp=shp, shx=shx, dbf=dbf)
    keys = [field.replace(N.FIELDS_SEP, FLAT_SEP) for field in fmt[N.FIELDS]]

    for key in keys:
        if len(key) > _SHP_MAX_FIELD_NAME_LEN:
            key = _SHP_SHORT_FIELD_NAMES[key]
        writer.field(key, 'C', _SHP_MAX_FIELD_CONTENT_LEN)

    for entity in result.entities:
        writer.shape(entity[N.GEOM])

        flatten_dict(entity, max_depth=3)
        record = []
        for key in keys:
            value = str(entity[key])
            if len(value) > _SHP_MAX_FIELD_CONTENT_LEN:
                value = value[:_SHP_MAX_FIELD_CONTENT_LEN]

            record.append(value)

        writer.record(*record)

    writer.close()

    files = [(shp, 'shp'), (shx, 'shx'), (dbf, 'dbf'), (prj, 'prj')]
    for fp, extension in files:
        with zip_file.open('{}.{}'.format(name, extension), mode='w') as f:
            # Escribir cada archivo al comprimido ZIP.
            fp.seek(0)
            shutil.copyfileobj(fp, f)

    zip_file.close()

    contents.seek(0)
    return send_file(contents, attachment_filename='{}.zip'.format(name),
                     as_attachment=True)


def _create_csv_response_single(name, result, fmt):
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
                                   quotechar=CSV_QUOTE,
                                   quoting=csv.QUOTE_NONNUMERIC)

        keys = []
        field_names = []
        csv_fields = _ENDPOINT_CSV_FIELDS[name]

        for original_field, csv_field_name in csv_fields:
            if original_field in fmt[N.FIELDS]:
                keys.append(original_field.replace(N.FIELDS_SEP, FLAT_SEP))
                field_names.append(FLAT_SEP.join(csv_field_name))

        yield csv_writer.row_to_str(field_names)

        for match in result.entities:
            flatten_dict(match, max_depth=3)
            values = [match[key] for key in keys]

            yield csv_writer.row_to_str(values)

    resp = Response(csv_generator(), mimetype='text/csv')
    return make_response((resp, {
        'Content-Disposition': 'attachment; filename={}.csv'.format(
            name.lower())
    }))


def _create_geojson_response_single(result, fmt):
    """Toma un resultado de una consulta, y devuelve una respuesta
    HTTP 200 con el resultado en formato GeoJSON.

    Args:
        result (QueryResult): Resultado de una consulta.
        fmt (dict): Parámetros de formato.

    Returns:
        flask.Response: Respuesta HTTP con contenido GeoJSON.

    """
    # Remover campos no especificados por el usuario.
    _format_result_fields(result, fmt)

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


def _format_result_json(name, result, fmt):
    """Toma el resultado de una consulta, y la devuelve con una estructura
    apropiada para ser convertida a JSON.

    Args:
        name (str): Nombre de la entidad consultada.
        result (QueryResult): Resultado de una consulta.
        fmt (dict): Parámetros de formato.

    Returns:
        dict: Resultados con estructura y formato apropiados.

    """
    # Remover campos no especificados por el usuario.
    _format_result_fields(result, fmt)

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
            N.OFFSET: result.offset,
            N.PARAMETERS: result.params
        }

    return {
        name: result.first_entity(),
        N.PARAMETERS: result.params
    }


def _create_json_response_single(name, result, fmt):
    """Toma un resultado de una consulta, y devuelve una respuesta
    HTTP 200 con el resultado en formato JSON.

    Args:
        name (str): Nombre de la entidad consultada.
        result (QueryResult): Resultado de una consulta.
        fmt (dict): Parámetros de formato.

    Returns:
        flask.Response: Respuesta HTTP con contenido JSON.

    """
    json_response = _format_result_json(name, result, fmt)
    return jsonify(json_response)


def _create_json_response_bulk(name, results, formats):
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
        _format_result_json(name, result, fmt)
        for result, fmt in zip(results, formats)
    ]

    return jsonify({
        N.RESULTS: json_results
    })


def filter_result_fields(result, fields_dict, max_depth=3):
    """Remueve campos de un resultado recursivamente de acuerdo a las
    especificaciones de un diccionario de campos.

    Args:
        result (dict): Resultado con valores a filtrar.
        fields_dict (dict): Diccionario especificando cuáles campos mantener.

    """
    if max_depth <= 0:
        raise RuntimeError('Maximum depth reached')

    for key in list(result.keys()):
        value = result[key]
        field = fields_dict.get(key)

        if not field:
            del result[key]
        elif isinstance(field, dict):
            if not isinstance(value, dict):
                raise ValueError(
                    'Can\'t specify sub-fields for non-dict values')

            filter_result_fields(value, fields_dict[key], max_depth - 1)


def _format_result_fields(result, fmt):
    """Dada la lista de campos en fmt[N.FIELDS], remueve los campos no
    especificados en cada entidad del resultado.

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


def fields_list_to_dict(fields, sep=N.FIELDS_SEP):
    """Convierte una lista de campos (potencialmente, campos anidados separados
    con puntos) en un diccionario de uno o más niveles conteniendo 'True' por
    cada campo procesado.

    Por ejemplo, dada la siguiente lista de campos:

    ['a', 'b.c', 'd']

    Resultaría en el siguiente diccionario de campos:

    {
        'a': True,
        'b': {
            'c': True
        },
        'd': True
    }

    Args:
        fields (tuple): Lista de campos.
        sep (str): Separador de campos anidados.

    Returns:
        dict: Diccionario de campos.

    """
    fields_dict = {}
    for field in fields:
        parts = field.split(sep)
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
    if fmt[N.FORMAT] == 'json':
        return _create_json_response_single(name, result, fmt)

    if fmt[N.FORMAT] == 'csv':
        if not result.iterable:
            raise ValueError(
                'Can\'t create CSV response from non-iterable content')

        return _create_csv_response_single(name, result, fmt)

    if fmt[N.FORMAT] == 'xml':
        return _create_xml_response_single(name, result, fmt)

    if fmt[N.FORMAT] == 'geojson':
        return _create_geojson_response_single(result, fmt)

    if fmt[N.FORMAT] == 'shp':
        return _create_shp_response_single(name, result, fmt)

    raise ValueError('Unknown format')


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
    # El valor FMT de cada elemento de formats es 'json' (ya que en modo bulk
    # solo se permiten respuestas JSON).
    return _create_json_response_bulk(name, results, formats)
