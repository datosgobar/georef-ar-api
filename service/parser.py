# -*- coding: utf-8 -*-

"""Módulo 'parser' de georef-api

Contiene funciones que manipulan los distintos objetos
con los que operan los módulos de la API.
"""

from flask import jsonify, make_response, request, Response
from geojson import Feature, FeatureCollection, Point, Polygon
from service.abbreviations import ABBR_STREETS, ROAD_TYPES
from service.names import *
import re
import os


REQUEST_INVALID = {
    'codigo': 400,
    'error': {
        'codigo_interno': None,
        'mensaje': WRONG_QUERY,
        'info': 'https://github.com/datosgobar/georef-api'
    }
}


ENDPOINT_PARAMS = {
    PLACE: [LAT, LON, FLATTEN],
    ADDRESSES: [ADDRESS, LOCALITY, DEPT, STATE, FIELDS, MAX],
    STREETS: [NAME, ROAD_TYPE, LOCALITY, DEPT, STATE, FIELDS, MAX],
    SETTLEMENTS: [ID, NAME, DEPT, STATE, ORDER, FIELDS, FLATTEN, MAX, FORMAT],
    MUNICIPALITIES: [ID, NAME, DEPT, STATE, ORDER, FIELDS, FLATTEN, MAX, FORMAT],
    DEPARTMENTS: [ID, NAME, STATE, ORDER, FIELDS, FLATTEN, MAX, FORMAT],
    STATES: [ID, NAME, ORDER, FIELDS, FLATTEN, MAX, FORMAT]
}


def validate_params(request, resource):
    """Controla que una consulta sea válida para procesar.
 
    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.
 
    Returns:
        (bool, str): Si una consulta es válida o no, y un mensaje si hay error.
    """
    for param in request.args:
        if param not in ENDPOINT_PARAMS[resource]:
            return False, INVALID_PARAM % (param, resource)
    return True, ''


def get_url_rule(request):
    """Analiza la URL y devuelve un diccionario con el formato solicitado.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        (bool, dict, str): Si una consulta es válida o no, un diccionario con
        los valores del formato solicitado y un mensaje si hay error.
    """
    format_request = {'convert': True, 'max': 10000, 'type': 'api'}
    path = str(request.url_rule)
    rule = os.path.split(path)

    if '.' in rule[1]:
        if len(request.args) > 0:
            return False, '', WRONG_QUERY
        for word in rule:
            if '.csv' in word:
                format_request['type'] = 'csv'
            elif '.geojson' in word:
                format_request['type'] = 'geojson'
            else:
                format_request['convert'] = False
    else:
        if request.args.get(FORMAT) == 'csv':
            format_request['type'] = 'csv'
        elif request.args.get(FORMAT) == 'geojson':
            format_request['type'] = 'geojson'
        else:
            format_request['convert'] = False
        format_request['max'] = request.args.get(MAX)
    return True, format_request, ''


def get_fields(args):
    """Devuelve los campos a mostrar pedidos en la consulta.

    Args:
        args (str or None): valores del parámetro "campos".

    Returns:
        list: campos para filtrar la búsqueda.
    """
    return args.split(',') if args else []


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
    road_type, road_name, number = get_parts_from(address[0].strip())
    locality = params.get(LOCALITY)
    department = params.get(DEPT)
    state = params.get(STATE)
    max = params.get(MAX)
    source = params.get(SOURCE)
    fields = get_fields(params.get(FIELDS))
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
        'source': source,
        'fields': fields,
        'text': params.get(ADDRESS)  # Raw user input.
    }


def get_abbreviated(name):
    """Busca y devuelve la abreviatura de un nombre en una collección

    Args:
        name (str): Texto con el nombre a buscar.

    Returns:
        str: Nombre abreviado si hubo coincidencias.
    """
    name = name.upper()
    for word in name.split():
        if word in ABBR_STREETS:
            name = name.replace(word, ABBR_STREETS[word.upper()])

    return name


def get_parts_from(address):
    """Analiza una dirección para separar en calle y altura.

    Args:
        address (str): Texto con la calle y altura de una dirección.

    Returns:
        tuple: Tupla con calle y altura de una dirección.
    """
    road_type = None
    for word in address.split():
        if word.upper() in ROAD_TYPES:
            road_type = ROAD_TYPES[word.upper()]
            address = address.replace(word, '')
            break

    match = re.search(r'(\s[0-9]+?)$', address)
    number = int(match.group(1)) if match else None
    road_name = re.sub(r'(\s[0-9]+?)$', r'', address)

    return road_type, road_name.strip(), number


def get_response(result, format_request={}):
    """Genera una respuesta de la API.

    Args:
        result (dict): Diccionario con resultados de una consulta.
        format_request (dict): Diccionario con los valores del formato.

    Returns:
        flask.Response: Respuesta de la API en formato CSV o JSON
    """
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
                    point = Point((entity['lat'], entity['lon']))
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


def get_flatten_result(result):
    """ Devuelve datos aplanados
    Args:
        result (dict): Diccionario con resultados de una consulta.
    """
    for field in list(result):
        if isinstance(result[field], dict):
            for key, value in result[field].items():
                result['_'.join([field, key])] = value
            del result[field]

    return result
