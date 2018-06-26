# -*- coding: utf-8 -*-

"""Módulo 'normalizer' de georef-api

Contiene funciones que manejan la lógica de procesamiento
de los recursos que expone la API.
"""

from service import data, parser
from service.names import *
from service.parser import flatten_dict
from elasticsearch import Elasticsearch, ElasticsearchException
from flask import g, abort


def get_elasticsearch():
    if 'elasticsearch' not in g:
        g.elasticsearch = Elasticsearch()

    return g.elasticsearch


def process_state(request):
    """Procesa una consulta de tipo GET para normalizar provincias.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objeto flask.Response.
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
    exact = EXACT in request.args
    order = request.args.get(ORDER)
    fields = parser.get_fields(request.args.get(FIELDS), STATES)

    try:
        es = get_elasticsearch()
        matches = data.query_entity(es, STATES, entity_id=state_id, name=name,
                                    order=order, fields=fields, max=max,
                                    exact=exact)
    except ElasticsearchException:
        abort(500)

    return parser.get_response({STATES: matches}, format_request)


def process_department(request):
    """Procesa una consulta de tipo GET para normalizar departamentos.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objeto flask.Response.
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
    exact = EXACT in request.args
    order = request.args.get(ORDER)
    fields = parser.get_fields(request.args.get(FIELDS), DEPARTMENTS)
    flatten = FLATTEN in request.args or format_request['convert']

    try:
        es = get_elasticsearch()
        matches = data.query_entity(es, DEPARTMENTS, entity_id=dept_id,
                                    name=name, state=state, flatten=flatten,
                                    order=order, fields=fields, max=max,
                                    exact=exact)
    except ElasticsearchException:
        abort(500)

    return parser.get_response({DEPARTMENTS: matches}, format_request)


def process_municipality(request):
    """Procesa una consulta de tipo GET para normalizar municipios.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objeto flask.Response.
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
    exact = EXACT in request.args
    order = request.args.get(ORDER)
    fields = parser.get_fields(request.args.get(FIELDS), MUNICIPALITIES)
    flatten = FLATTEN in request.args or format_request['convert']

    try:
        es = get_elasticsearch()
        matches = data.query_entity(es, MUNICIPALITIES,
                                entity_id=municipality_id, name=name,
                                department=department, state=state,
                                flatten=flatten, order=order, fields=fields,
                                max=max, exact=exact)
    except ElasticsearchException:
        abort(500)

    return parser.get_response({MUNICIPALITIES: matches}, format_request)


def process_locality(request):
    """Procesa una consulta de tipo GET para normalizar localidades.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objeto flask.Response.
    """
    valid_rule, format_request, error = parser.get_url_rule(request)
    if not valid_rule:
        return parser.get_response_for_invalid(request, message=error)
    valid_request, error = parser.validate_params(request, SETTLEMENTS)
    if not valid_request:
        return parser.get_response_for_invalid(request, message=error)

    locality_id = request.args.get(ID)
    name = request.args.get(NAME)
    state = request.args.get(STATE)
    department = request.args.get(DEPT)
    municipality = request.args.get(MUN)
    exact = EXACT in request.args
    order = request.args.get(ORDER)
    fields = parser.get_fields(request.args.get(FIELDS), SETTLEMENTS)
    flatten = FLATTEN in request.args or format_request['convert']
    max = request.args.get(MAX) or format_request['max']

    try:
        es = get_elasticsearch()
        matches = data.query_entity(es, SETTLEMENTS, entity_id=locality_id,
                                    name=name, municipality=municipality,
                                    department=department, state=state,
                                    max=max, order=order, fields=fields,
                                    flatten=flatten, exact=exact)
    except ElasticsearchException:
        abort(500)

    return parser.get_response({LOCALITIES: matches}, format_request)


def process_street(request):
    """Procesa una consulta de tipo GET para normalizar calles.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objeto flask.Response.
    """
    valid_request, error = parser.validate_params(request, STREETS)
    if not valid_request:
        return parser.get_response_for_invalid(request, message=error)

    name = request.args.get(NAME)
    department = request.args.get(DEPT)
    state = request.args.get(STATE)
    road_type = request.args.get(ROAD_TYPE)
    max = request.args.get(MAX)
    exact = EXACT in request.args
    fields = parser.get_fields(request.args.get(FIELDS), STREETS)

    try:
        es = get_elasticsearch()
        matches = data.query_streets(es, name=name, department=department,
                                     state=state, road=road_type, max=max,
                                     fields=fields, exact=exact)
    except ElasticsearchException:
        abort(500)

    for street in matches: street.pop(GEOM, None)
        
    return parser.get_response({STREETS: matches})


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
        Resultado de la consulta como objeto flask.Response.
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

    try:
        es = get_elasticsearch()
        matches = data.query_address(es, search)
    except ElasticsearchException:
        abort(500)

    return parser.get_response({ADDRESSES: matches})


def address_post(request):
    """Procesa una consulta de tipo POST para normalizar direcciones.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objeto flask.Response.
    """
    matches = []
    json_data = request.get_json()

    if json_data:
        addresses = json_data.get(ADDRESSES)
        if not addresses:
            return parser.get_response_for_invalid(request, message=EMPTY_DATA)
        try:
            es = get_elasticsearch()
            for address in addresses:
                search = parser.get_search_from_string(address)
                matches.append({
                    'original': address,
                    'normalizadas': data.query_address(es, search)
                })
        except ElasticsearchException:
            abort(500)

    return parser.get_response({ADDRESSES: matches})


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

    try:
        es = get_elasticsearch()
        muni_index = MUNICIPALITIES + '-' + GEOM
        dept_index = DEPARTMENTS + '-' + GEOM

        dept = data.query_place(es, dept_index, lat, lon, [ID, NAME, STATE])

        if dept:
            muni = data.query_place(es, muni_index, lat, lon, [ID, NAME])
            # Remover la provincia del departamento y colocarla directamente
            # en el resultado. Haciendo esto se logra evitar una consulta
            # al índice de provincias.
            state = dept.pop(STATE)

            place = {
                MUN: muni,
                DEPT: dept,
                STATE: state,
                LAT: lat,
                LON: lon
            }

            if muni:
                place[SOURCE] = data.get_index_source(MUNICIPALITIES)
            else:
                place[SOURCE] = data.get_index_source(DEPARTMENTS)

            if flatten:
                flatten_dict(place, max_depth=2)
        else:
            place = {}

    except ElasticsearchException:
        abort(500)

    return parser.get_response({PLACE: place})
