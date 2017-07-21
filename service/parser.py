# -*- coding: utf-8 -*-

"""Módulo 'parser' de georef-api

Contiene funciones que manipulan los distintos objetos
con los que operan los módulos de la API.
"""

from flask import jsonify, make_response, request
import re


REQUEST_INVALID = {
    'codigo': 400,
    'estado': 'INVALIDO',
    'error': {
        'codigo_interno': None,
        'causa': 'El Request tiene parámetros inválidos o está incompleto.',
        'mensaje': 'El Request tiene parámetros inválidos o está incompleto.',
        'info': 'https://github.com/datosgobar/georef-api'
        }
    }

ROAD_TYPES_MAP = {
    'ACCESO': 'ACC',
    'AUTOPISTA': 'AUT',
    'AVENIDA': 'AV',
    'BARRIO': 'BO',
    'BOULEVARD': 'BV',
    'CALLEJON': 'CJON',
    'CAMINO': 'CNO',
    'DEPARTAMENTO': 'DEP',
    'DIAGONAL': 'DIAG',
    'EMPALME': 'EMP',
    'KILOMETRO': 'KM',
    'MANZANA': 'MANZ',
    'NACIONAL': 'NAC',
    'NAVIO': 'NAV',
    'PASAJE': 'PJE',
    'PASILLO': 'PAS',
    'PEATONAL': 'PEAT',
    'PICADA': 'PCDA',
    'PROLONGACION': 'PROL',
    'PROVINCIA': 'PCIA',
    'PROVINCIAL': 'PCIAL',
    'PUERTO': 'PT',
    'REGIMIENTO': 'RGTO',
    'REPUBLICA': 'RCA'
    }


def validate(request):
    """Controla que una consulta sea válida para procesar.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        bool: Si una consulta es válida o no.
    """
    return True # pending until API keys are implemented.


def get_from_string(address_str):
    """Procesa los componentes de una dirección en una cadena de texto.

    Args:
        address_str (str): Texto que representa una dirección.

    Returns:
        bool: Si una consulta es válida o no.
    """
    return build_search_from({'direccion': address_str})


def build_search_from(params):
    """Arma un diccionario con los parámetros de búsqueda de una consulta.

    Args:
        params (dict): Parámetros de la consulta HTTP.

    Returns:
        dict: Parámetros de búsqueda.
    """

    address = params.get('direccion').split(',')
    road_type = get_road_type(address[0])
    road, number = get_road_and_number(address[0].strip())
    locality = params.get('localidad')
    state = params.get('provincia')
    max = params.get('max')
    source = params.get('fuente')
    if len(address) > 1:
        locality = address[1].strip()
    return {
        'number': number,
        'road': road,
        'road_type': road_type,
        'locality': locality,
        'state': state,
        'max': max,
        'source': source,
        'text': params.get('direccion')
    }


def get_abbr(name, collection):
    """Buscar y devuelve la abreviatura de un nombre en una collección

    Args:
        name (str): Texto con el nombre a buscar
        collection (dict): Collección donde buscar el nombre

    Returns:
        str or None: Nombre abreviado.

    """
    name = name.upper()
    for word in name.split():
        if word in name:
            return collection[word.upper()]
    return None


def get_road_type(address):
    """Analiza una dirección para obtener el tipo de camino si existe.

    Args:
        address (str): Texto con la calle y altura de una dirección.

    Returns:
        str or None: Tipo de camino (abreviado).
    """
    for word in address.split():
        if word.upper() in ROAD_TYPES_MAP:
            return ROAD_TYPES_MAP[word.upper()]
    return None


def get_road_and_number(address):
    """Analiza una dirección para separar en calle y altura.

    Args:
        address (str): Texto con la calle y altura de una dirección.

    Returns:
        tuple: Tupla con calle y altura de una dirección.
    """
    match = re.search(r'(\s[0-9]+?)$', address)
    number = int(match.group(1)) if match else None
    address = re.sub(r'(\s[0-9]+?)$', r'', address)
    return address.strip(), number


def get_response(result):
    """Genera una respuesta de la API.

    Args:
        result (dict): Diccionario con resultados de una consulta.

    Returns:
        flask.Response: Respuesta de la API en formato JSON.
    """
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
        REQUEST_INVALID['error']['mensaje'] = message
    return make_response(jsonify(REQUEST_INVALID), 400)
