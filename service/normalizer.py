# -*- coding: utf-8 -*-

"""Módulo 'normalizer' de georef-api

Contiene funciones que manejan la lógica de procesamiento
de los recursos que expone la API.
"""

from service import data, parser
from service.names import *


def build_result_for(entity, matches):
    """Arma un diccionario con la lista de resultados para una entidad.

    Args:
        entity (str): Nombre de la entidad de la que se retornan resulados.
        matches (list): Lista con los resultados.

    Returns:
        dict: Resultados e información de estado asociada.
    """
    return {entity: matches}


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
            message='El parámetro "direccion" es obligatorio.')
    search = parser.build_search_from(request.args)
    if search['number'] is None:
        return parser.get_response_for_invalid(request,
            message='Debe ingresar una altura.')
    data.save_address(search)
    matches = data.query_address(search)
    result = build_result_for(ADDRESSES, matches)
    return parser.get_response(result)


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
            return parser.get_response_for_invalid(request,
            message='No hay datos de direcciones para procesar.')
        for address in addresses:
            parsed_address = parser.get_from_string(address)
            matches.append({
                'original': address,
                'normalizadas': data.query_address(parsed_address)
                })
    result = build_result_for(ADDRESSES, matches)
    return parser.get_response(result)


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
    result = build_result_for(STREETS, matches)
    return parser.get_response(result)


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
    matches = data.query_entity(LOCALITIES, name, department, state,
                                max, order, fields, flatten)
    result = build_result_for(LOCALITIES, matches)
    return parser.get_response(result)


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
    result = build_result_for(DEPARTMENTS, matches)
    return parser.get_response(result)


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
    result = build_result_for(STATES, matches)
    return parser.get_response(result)
