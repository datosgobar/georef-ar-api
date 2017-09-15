# -*- coding: utf-8 -*-

"""Módulo 'parser' de georef-api

Contiene funciones que manipulan los distintos objetos
con los que operan los módulos de la API.
"""

from flask import jsonify, make_response, request
from service.abbreviations import ABBR_STREETS, ROAD_TYPES
from service.names import *
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


def validate(request):
    """Controla que una consulta sea válida para procesar.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        bool: Si una consulta es válida o no.
    """
    return True # pending until API keys are implemented.


def get_fields(args):
    """Devuelve los campos a mostrar pedidos en la consulta.

    Args:
        args (str or None): valores del parámetro "campos".

    Returns:
        list: campos para filtrar la búsqueda.
    """
    if args:
        return args.split(',')
    return []

def get_from_string(address_str):
    """Procesa los componentes de una dirección en una cadena de texto.

    Args:
        address_str (str): Texto que representa una dirección.

    Returns:
        bool: Si una consulta es válida o no.
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
        collection (dict): Colección donde buscar el nombre.

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
        REQUEST_INVALID[ERROR][MESSAGE] = message
    return make_response(jsonify(REQUEST_INVALID), 400)
