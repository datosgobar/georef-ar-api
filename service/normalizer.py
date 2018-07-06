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

    params = {
        'entity_id': request.args.get(ID),
        'name': request.args.get(NAME),
        'max': request.args.get(MAX) or 24,
        'exact': EXACT in request.args,
        'order': request.args.get(ORDER),
        'fields': parser.get_fields(request.args.get(FIELDS), STATES)
    }

    try:
        es = get_elasticsearch()
        matches = data.query_entities(es, STATES, [params])[0]
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

    params = {
        'entity_id': request.args.get(ID),
        'name': request.args.get(NAME),
        'state': request.args.get(STATE),
        'max': request.args.get(MAX) or format_request['max'],
        'exact': EXACT in request.args,
        'order': request.args.get(ORDER),
        'fields': parser.get_fields(request.args.get(FIELDS), DEPARTMENTS),
        # 'flatten': FLATTEN in request.args or format_request['convert']
    }

    try:
        es = get_elasticsearch()
        matches = data.query_entities(es, DEPARTMENTS, [params])[0]
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

    params = {
        'entity_id': request.args.get(ID),
        'name': request.args.get(NAME),
        'department': request.args.get(DEPT),
        'state': request.args.get(STATE),
        'max': request.args.get(MAX) or format_request['max'],
        'exact': EXACT in request.args,
        'order': request.args.get(ORDER),
        'fields': parser.get_fields(request.args.get(FIELDS), MUNICIPALITIES),
        # 'flatten': FLATTEN in request.args or format_request['convert']
    }

    try:
        es = get_elasticsearch()
        matches = data.query_entities(es, MUNICIPALITIES, [params])[0]
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

    params = {
        'entity_id': request.args.get(ID),
        'name': request.args.get(NAME),
        'state': request.args.get(STATE),
        'department': request.args.get(DEPT),
        'municipality': request.args.get(MUN),
        'exact': EXACT in request.args,
        'order': request.args.get(ORDER),
        'fields': parser.get_fields(request.args.get(FIELDS), SETTLEMENTS),
        # 'flatten': FLATTEN in request.args or format_request['convert'],
        'max': request.args.get(MAX) or format_request['max']
    }

    try:
        es = get_elasticsearch()
        matches = data.query_entities(es, SETTLEMENTS, [params])[0]
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

    params = {
        'road_name': request.args.get(NAME),
        'department': request.args.get(DEPT),
        'state': request.args.get(STATE),
        'road_type': request.args.get(ROAD_TYPE),
        'max': request.args.get(MAX),
        'exact': EXACT in request.args,
        # 'flatten': FLATTEN in request.args,
        'fields': parser.get_fields(request.args.get(FIELDS), STREETS)
    }

    try:
        es = get_elasticsearch()
        matches = data.query_streets(es, [params])[0]
    except ElasticsearchException:
        abort(500)

    for street in matches:
        street.pop(GEOM, None)

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
                search = parser.build_search_from({
                    ADDRESS: address
                })

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
        params = {
            'lat': lat,
            'lon': lon,
            'fields': [ID, NAME, STATE]
        }
        dept = data.query_places(es, DEPARTMENTS, [params])[0]

        if dept:
            params = {
                'lat': lat,
                'lon': lon,
                'fields': [ID, NAME]
            }
            muni = data.query_places(es, MUNICIPALITIES, [params])[0]
            # Remover la provincia del departamento y colocarla directamente
            # en el resultado. Haciendo esto se logra evitar una consulta
            # al índice de provincias.
            state = dept.pop(STATE)
            place = {}

            if muni:
                place[SOURCE] = data.get_index_source(MUNICIPALITIES)
            else:
                # Si la municipalidad no fue encontrada, mantener la misma
                # estructura de datos en la respuesta.
                muni = {
                    ID: None,
                    NAME: None
                }
                place[SOURCE] = data.get_index_source(DEPARTMENTS)

            place[MUN] = muni
            place[DEPT] = dept
            place[STATE] = state
            place[LAT] = lat
            place[LON] = lon

            if flatten:
                flatten_dict(place, max_depth=2)
        else:
            place = {}

    except ElasticsearchException:
        abort(500)

    return parser.get_response({PLACE: place})
