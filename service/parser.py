# -*- coding: utf-8 -*-

"""Módulo 'parser' de georef-api

Contiene funciones que manipulan los distintos objetos
con los que operan los módulos de la API.
"""

from flask import jsonify, make_response, request, Response
from geojson import Feature, FeatureCollection, Point, Polygon
from service.names import *
import re
import os


DEFAULT_MAX_FMT = 10000

REQUEST_INVALID = {
    'codigo': 400,
    'error': {
        'codigo_interno': None,
        'mensaje': WRONG_QUERY,
        'info': 'https://github.com/datosgobar/georef-api'
    }
}


ENDPOINT_PARAMS = {
    STATES: [ID, NAME, ORDER, FIELDS, MAX, FORMAT, EXACT],
    DEPARTMENTS: [ID, NAME, STATE, ORDER, FIELDS, FLATTEN, MAX, FORMAT, EXACT],
    MUNICIPALITIES: [ID, NAME, DEPT, STATE, ORDER, FIELDS, FLATTEN, MAX, 
                     FORMAT, EXACT],
    SETTLEMENTS: [ID, NAME, DEPT, STATE, ORDER, FIELDS, MUN, FLATTEN, MAX,
                  FORMAT, EXACT],
    ADDRESSES: [ADDRESS, ROAD_TYPE, DEPT, STATE, FIELDS, MAX, EXACT],
    STREETS: [NAME, ROAD_TYPE, DEPT, STATE, FIELDS, MAX, EXACT],
    PLACE: [LAT, LON, FLATTEN]
}

ENDPOINT_OBLIGATORY_FIELDS = {
    STATES: [ID, NAME],
    DEPARTMENTS: [ID, NAME],
    MUNICIPALITIES: [ID, NAME],
    SETTLEMENTS: [ID, NAME],
    STREETS: [ID, NAME],
    ADDRESSES: [ID, NAME, DOOR_NUM, GEOM, START_R, START_L, END_R, END_L,
        LOCATION]
}

NONEMPTY_PARAMS = set([ID, NAME, ORDER, FIELDS, MAX, FORMAT, STATE, DEPT, MUN,
    LOCALITY, ADDRESS, ROAD_TYPE, LAT, LON, SOURCE])


def validate_params(request, resource):
    """Controla que una consulta sea válida para procesar.
 
    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.
        resource: (str): Nombre del recurso a validar.
 
    Returns:
        (bool, str): Si una consulta es válida o no, y un mensaje si hay error.
    """
    for param in request.args:
        if param not in ENDPOINT_PARAMS[resource]:
            return False, INVALID_PARAM.format(param=param, res=resource)

        if param in NONEMPTY_PARAMS and not request.args[param]:
            return False, EMPTY_PARAM.format(param=param) 

    return True, None


def get_url_rule(request):
    """Analiza la URL y devuelve un diccionario con el formato solicitado.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        (bool, dict, str): Si una consulta es válida o no, un diccionario con
        los valores del formato solicitado y un mensaje si hay error.
    """
    format_request = {'convert': True, 'max': DEFAULT_MAX_FMT, 'type': 'json'}
    path = str(request.url_rule)
    rule = os.path.split(path)
    endpoint = rule[1]  # request endpoint

    if '.' in endpoint:
        if len(request.args) > 0:
            return False, '', WRONG_QUERY
        if '.csv' in endpoint:
            format_request['type'] = 'csv'
        elif '.geojson' in endpoint:
            format_request['type'] = 'geojson'
        else:
            format_request['convert'] = False
    else:
        if request.args.get(FORMAT):
            if request.args.get(FORMAT) == 'csv':
                format_request['type'] = 'csv'
            elif request.args.get(FORMAT) == 'geojson':
                format_request['type'] = 'geojson'
            elif request.args.get(FORMAT) != 'json':
                return False, '', WRONG_QUERY
        else:
            format_request['convert'] = False
            format_request['max'] = request.args.get(MAX)
    return True, format_request, ''


def get_fields(args, resource):
    """Devuelve los campos a mostrar pedidos en la consulta.

    Args:
        args (str or None): valores del parámetro "campos".

    Returns:
        list: campos para filtrar la búsqueda.
    """
    if not args:
        return []
    
    return list(set(args.split(',') + ENDPOINT_OBLIGATORY_FIELDS[resource]))


def get_search_from_string(address_str):
    """Procesa los componentes de una dirección en una cadena de texto.

    Args:
        address_str (str): Texto que representa una dirección.

    Returns:
        dict: Parámetros de búsqueda.
    """
    return build_search_from({ADDRESS: address_str})


def build_search_from(params):
    """Arma un diccionario con los parámetros de búsqueda de una consulta.

    Args:
        params (dict): Parámetros de la consulta HTTP.

    Returns:
        dict: Parámetros de búsqueda.
    """
    address = params.get(ADDRESS).split(',')
    road_name, number = get_parts_from(address[0].strip())
    road_type = params.get(ROAD_TYPE)
    locality = params.get(LOCALITY)
    department = params.get(DEPT)
    state = params.get(STATE)
    max = params.get(MAX)
    exact = EXACT in params
    source = params.get(SOURCE)
    fields = get_fields(params.get(FIELDS), ADDRESSES)
    if len(address) > 1:
        locality = address[1].strip()

    return {
        'number': number,
        'road_name': road_name,
        'road_type': road_type,
        'locality': locality,
        'department': department,
        'state': state,
        'max': max,
        'exact': exact,
        'source': source,
        'fields': fields
    }


def get_parts_from(address):
    """Analiza una dirección para separar en calle y altura.

    Args:
        address (str): Texto con la calle y altura de una dirección.

    Returns:
        tuple: Tupla con calle y altura de una dirección.
    """
    match = re.search(r'(\s[0-9]+?)$', address)
    number = int(match.group(1)) if match else None
    if number == 0:
        number = None
    road_name = re.sub(r'(\s[0-9]+?)$', r'', address)

    return road_name.strip(), number


def get_response(result, format_request=None):
    """Genera una respuesta de la API.

    Args:
        result (dict): Diccionario con resultados de una consulta.
        format_request (dict): Diccionario con los valores del formato.

    Returns:
        flask.Response: Respuesta de la API en formato CSV o JSON
    """
    if not format_request:
        format_request = {}

    if 'type' in format_request and format_request['type'] == 'csv':
        entity = [row for row in result.keys()]
        headers = {'Content-Disposition': 'attachment; '
                                          'filename=' + entity[0] + '.csv'}
        return Response(generate_csv(result), mimetype='text/csv',
                        headers=headers)
    elif 'type' in format_request and format_request['type'] == 'geojson':
        features = []
        for key, _ in result.items():
            for entity in result[key]:
                properties = dict(entity)
                point = None
                if 'lat' and 'lon' in entity.keys():
                    properties.pop('lat')
                    properties.pop('lon')
                    point = Point((float(entity['lat']), float(entity['lon'])))
                features.append(Feature(
                    geometry=point,
                    properties=properties
                ))
            return jsonify(FeatureCollection(features))
    else:
        return make_response(jsonify(result), 200)


def get_response_for_invalid(request, message=None):
    """Genera una respuesta para consultas inválidas.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.
        message (str): Mensaje de error opcional.

    Returns:
        flask.Response: Respuesta de la API en formato JSON.
    """
    if message is not None:
        REQUEST_INVALID[ERROR][MESSAGE] = message
    return make_response(jsonify(REQUEST_INVALID), 400)


def generate_csv(result):
    """ Generar datos en formato CSV

    Args:
        result (dict): Diccionario con resultados de una consulta.
    """
    first = True
    for key, rows in result.items():
        for row in rows:
            if first:
                yield ';'.join(dict(row).keys()) + '\n'
            yield ';'.join(str(v) for v in dict(row).values()) + '\n'
            first = False


def flatten_dict(d, max_depth=4):
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
