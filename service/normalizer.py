# -*- coding: utf-8 -*-

"""Módulo 'normalizer' de georef-api

Contiene funciones que manejan la lógica de procesamiento
de los recursos que expone la API.
"""

from service import data, parser
from service.names import *


def process_place(request):
    """Procesa una consulta para georreferenciar una ubicación.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de una de las funciones invocadas según el tipo de Request.
    """
    valid_request, error = parser.validate_params(request, PLACE)
    if not valid_request:
        return parser.get_response_for_invalid(request, message=error)
    if not request.args.get(LAT):
        return parser.get_response_for_invalid(request, message=LAT_REQUIRED)
    if not request.args.get(LON):
        return parser.get_response_for_invalid(request, message=LON_REQUIRED)

    lat = request.args.get(LAT)
    lon = request.args.get(LON)
    flatten = FLATTEN in request.args
    matches = data.query_place(MUNICIPALITIES, lat, lon, flatten)
    if not matches:
        matches = data.query_place(DEPARTMENTS, lat, lon, flatten)

    return parser.get_response({PLACE: matches})


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
    valid_request, error = parser.validate_params(request, ADDRESSES)
    if not valid_request:
        return parser.get_response_for_invalid(request, message=error)
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
    valid_request, error = parser.validate_params(request, STREETS)
    if not valid_request:
        return parser.get_response_for_invalid(request, message=error)

    name = request.args.get(NAME)
    locality = request.args.get(LOCALITY)
    department = request.args.get(DEPT)
    state = request.args.get(STATE)
    road_type = request.args.get(ROAD_TYPE)
    max = request.args.get(MAX)
    fields = parser.get_fields(request.args.get(FIELDS))

    matches = data.query_streets(name, locality, department, state,
                                 road_type, max, fields)
    for street in matches: street.pop(GEOM, None)

    return parser.get_response({STREETS: matches})


def process_locality(request):
    """Procesa una consulta de tipo GET para normalizar localidades.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objecto flask.Response.
    """
    valid_rule, format_request, error = parser.get_url_rule(request)
    if not valid_rule:
        return parser.get_response_for_invalid(request, message=error)
    valid_request, error = parser.validate_params(request, SETTLEMENTS)
    if not valid_request:
        return parser.get_response_for_invalid(request, message=error)

    locality_id = request.args.get(ID)
    name = request.args.get(NAME)
    department = request.args.get(DEPT)
    state = request.args.get(STATE)
    max = request.args.get(MAX) or format_request['max']
    order = request.args.get(ORDER)
    fields = parser.get_fields(request.args.get(FIELDS))
    flatten = FLATTEN in request.args or format_request['convert']

    matches = data.query_entity(SETTLEMENTS, entity_id=locality_id, name=name,
                                department=department, state=state, max=max,
                                order=order, fields=fields, flatten=flatten)

    return parser.get_response({LOCALITIES: matches}, format_request)


def process_department(request):
    """Procesa una consulta de tipo GET para normalizar departamentos.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objecto flask.Response.
    """
    valid_rule, format_request, error = parser.get_url_rule(request)
    if not valid_rule:
        return parser.get_response_for_invalid(request, message=error)
    valid_request, error = parser.validate_params(request, DEPARTMENTS)
    if not valid_request:
        return parser.get_response_for_invalid(request, message=error)

    dept_id = request.args.get(ID)
    name = request.args.get(NAME)
    state = request.args.get(STATE)
    max = request.args.get(MAX) or format_request['max']
    order = request.args.get(ORDER)
    fields = parser.get_fields(request.args.get(FIELDS))
    flatten = FLATTEN in request.args or format_request['convert']

    matches = data.query_entity(DEPARTMENTS, entity_id=dept_id, name=name,
                                state=state, flatten=flatten,
                                order=order, fields=fields, max=max)

    return parser.get_response({DEPARTMENTS: matches}, format_request)


def process_municipality(request):
    """Procesa una consulta de tipo GET para normalizar municipios.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objecto flask.Response.
    """
    valid_rule, format_request, error = parser.get_url_rule(request)
    if not valid_rule:
        return parser.get_response_for_invalid(request, message=error)
    valid_request, error = parser.validate_params(request, MUNICIPALITIES)
    if not valid_request:
        return parser.get_response_for_invalid(request, message=error)

    municipality_id = request.args.get(ID)
    name = request.args.get(NAME)
    department = request.args.get(DEPT)
    state = request.args.get(STATE)
    max = request.args.get(MAX) or format_request['max']
    order = request.args.get(ORDER)
    fields = parser.get_fields(request.args.get(FIELDS))
    flatten = FLATTEN in request.args or format_request['convert']

    matches = data.query_entity(MUNICIPALITIES, entity_id=municipality_id,
                                name=name, department=department, state=state,
                                flatten=flatten, order=order, fields=fields,
                                max=max)

    return parser.get_response({MUNICIPALITIES: matches}, format_request)


def process_state(request):
    """Procesa una consulta de tipo GET para normalizar provincias.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objecto flask.Response.
    """
    valid_rule, format_request, error = parser.get_url_rule(request)
    if not valid_rule:
        return parser.get_response_for_invalid(request, message=error)
    valid_request, error = parser.validate_params(request, STATES)
    if not valid_request:
        return parser.get_response_for_invalid(request, message=error)

    state_id = request.args.get(ID)
    name = request.args.get(NAME)
    max = request.args.get(MAX) or 24
    order = request.args.get(ORDER)
    fields = parser.get_fields(request.args.get(FIELDS))
    matches = data.query_entity(STATES, entity_id=state_id, name=name,
                                order=order, fields=fields, max=max)
    return parser.get_response({STATES: matches}, format_request)
