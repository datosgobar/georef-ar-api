# -*- coding: utf-8 -*-

"""Módulo 'normalizer' de georef-api

Contiene funciones que manejan la lógica de procesamiento
de los recursos que expone la API.
"""

from service import data, parser
from service.names import *


def process_address(request):
    """Procesa una consulta para normalizar direcciones.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de una de las funciones invocadas según el tipo de Request.
    """
    if request.method == 'GET':
        return address_get(request)
    return address_post(request)


def address_get(request):
    """Procesa una consulta de tipo GET para normalizar direcciones.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objecto flask.Response.
    """
    if not request.args.get(ADDRESS):
        return parser.get_response_for_invalid(request,
                                               message=ADDRESS_REQUIRED)

    search = parser.build_search_from(request.args)
    if search['number'] is None:
        return parser.get_response_for_invalid(request, message=NUMBER_REQUIRED)

    data.save_address(search)
    matches = data.query_address(search)
    return parser.get_response({ADDRESSES: matches})


def address_post(request):
    """Procesa una consulta de tipo POST para normalizar direcciones.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objecto flask.Response.
    """
    matches = []
    json_data = request.get_json()

    if json_data:
        addresses = json_data.get(ADDRESSES)
        if not addresses:
            return parser.get_response_for_invalid(request, message=EMPTY_DATA)
        for address in addresses:
            search = parser.get_search_from_string(address)
            matches.append({
                'original': address,
                'normalizadas': data.query_address(search)
            })

    return parser.get_response({ADDRESSES: matches})


def process_street(request):
    """Procesa una consulta de tipo GET para normalizar calles.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objecto flask.Response.
    """
    name = request.args.get(NAME)
    locality = request.args.get(LOCALITY)
    state = request.args.get(STATE)
    road_type = request.args.get(ROAD_TYPE)
    max = request.args.get(MAX)
    fields = parser.get_fields(request.args.get(FIELDS))

    matches = data.query_streets(name, locality, state, road_type, max, fields)
    for street in matches: street.pop(GEOM, None)

    return parser.get_response({STREETS: matches})


def process_locality(request):
    """Procesa una consulta de tipo GET para normalizar localidades.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objecto flask.Response.
    """
    name = request.args.get(NAME)
    department = request.args.get(DEPT)
    state = request.args.get(STATE)
    max = request.args.get(MAX)
    order = request.args.get(ORDER)
    fields = parser.get_fields(request.args.get(FIELDS))
    flatten = FLATTEN in request.args

    matches = data.query_entity(SETTLEMENTS, name, department, state,
                                max, order, fields, flatten)

    return parser.get_response({LOCALITIES: matches})


def process_department(request):
    """Procesa una consulta de tipo GET para normalizar departamentos.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objecto flask.Response.
    """
    name = request.args.get(NAME)
    state = request.args.get(STATE)
    max = request.args.get(MAX)
    order = request.args.get(ORDER)
    fields = parser.get_fields(request.args.get(FIELDS))
    flatten = FLATTEN in request.args

    matches = data.query_entity(DEPARTMENTS, name, state=state, max=max,
                                order=order, fields=fields, flatten=flatten)

    return parser.get_response({DEPARTMENTS: matches})


def process_municipality(request):
    """Procesa una consulta de tipo GET para normalizar municipios.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objecto flask.Response.
    """
    name = request.args.get(NAME)
    state = request.args.get(STATE)
    max = request.args.get(MAX)
    order = request.args.get(ORDER)
    fields = parser.get_fields(request.args.get(FIELDS))
    flatten = FLATTEN in request.args

    matches = data.query_entity(MUNICIPALITIES, name, state=state, max=max,
                                order=order, fields=fields, flatten=flatten)

    return parser.get_response({MUNICIPALITIES: matches})


def process_state(request):
    """Procesa una consulta de tipo GET para normalizar provincias.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objecto flask.Response.
    """
    name = request.args.get(NAME)
    max = request.args.get(MAX) or 24
    order = request.args.get(ORDER)
    fields = parser.get_fields(request.args.get(FIELDS))

    matches = data.query_entity(STATES, name, max=max,
                                order=order, fields=fields)

    return parser.get_response({STATES: matches})
