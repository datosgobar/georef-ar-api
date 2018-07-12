# -*- coding: utf-8 -*-

"""Módulo 'normalizer' de georef-api

Contiene funciones que manejan la lógica de procesamiento
de los recursos que expone la API.
"""

from service import data, params, formatter
from service.names import *
from elasticsearch import Elasticsearch, ElasticsearchException
from flask import g
import os
import psycopg2


def get_elasticsearch():
    if 'elasticsearch' not in g:
        g.elasticsearch = Elasticsearch()

    return g.elasticsearch


def get_postgres_db():
    if 'postgres' not in g:
        g.postgres = psycopg2.connect(
            host=os.environ.get('GEOREF_API_DB_HOST'),
            dbname=os.environ.get('GEOREF_API_DB_NAME'),
            user=os.environ.get('GEOREF_API_DB_USER'),
            password=os.environ.get('GEOREF_API_DB_PASS'))

    return g.postgres


def get_index_source(index):
    """Devuelve la fuente para un índice dado.

    Args:
        index (str): Nombre del índice.
    """
    if index in [STATES, DEPARTMENTS, MUNICIPALITIES]:
        return SOURCE_IGN
    elif index in [SETTLEMENTS, LOCALITIES]:
        return SOURCE_BAHRA
    elif index == STREETS:
        return SOURCE_INDEC
    else:
        raise ValueError(
            'No se pudo determinar la fuente de: {}'.format(index))


def translate_keys(d, translations, ignore=None):
    if not ignore:
        ignore = []

    return {
        translations.get(key, key): value
        for key, value in d.items()
        if key not in ignore
    }


def parse_params(request, name, param_parser):
    if request.method == 'GET':
        params_list = [request.args]
        param_source = 'querystring'
    else:
        params_list = request.json.get(name)
        param_source = 'body'

    return param_parser.parse_params_dict_list(params_list, param_source)


def process_entity(request, name, param_parser, key_translations, index=None):
    if not index:
        index = name

    parse_results, errors = parse_params(request, name, param_parser)

    if any(errors):
        return formatter.create_param_error_response(request, errors)

    queries = []

    for parsed_params in parse_results:
        query = translate_keys(parsed_params, key_translations,
                               ignore=[FLATTEN, FORMAT])
        queries.append(query)

    try:
        es = get_elasticsearch()
        responses = data.query_entities(es, index, queries)
    except ElasticsearchException:
        return formatter.create_internal_error_response(request)

    source = get_index_source(index)
    for response in responses:
        for match in response:
            match[SOURCE] = source

    return formatter.create_ok_response(request, parse_results, name,
                                        responses)


def process_state(request):
    """Procesa una consulta de tipo GET para normalizar provincias.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objeto flask.Response.
    """
    return process_entity(request, STATES, params.PARAMS_STATES, {
            ID: 'entity_id',
            NAME: 'name',
            EXACT: 'exact',
            ORDER: 'order',
            FIELDS: 'fields'
    })


def process_department(request):
    """Procesa una consulta de tipo GET para normalizar provincias.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objeto flask.Response.
    """
    return process_entity(request, DEPARTMENTS, params.PARAMS_DEPARTMENTS, {
            ID: 'entity_id',
            NAME: 'name',
            STATE: 'state',
            EXACT: 'exact',
            ORDER: 'order',
            FIELDS: 'fields'
    })


def process_municipality(request):
    """Procesa una consulta de tipo GET para normalizar municipios.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objeto flask.Response.
    """
    return process_entity(request, MUNICIPALITIES, params.PARAMS_MUNICIPALITIES, {
            ID: 'entity_id',
            NAME: 'name',
            STATE: 'state',
            DEPT: 'department',
            EXACT: 'exact',
            ORDER: 'order',
            FIELDS: 'fields'
    })


def process_locality(request):
    """Procesa una consulta de tipo GET para normalizar localidades.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objeto flask.Response.
    """
    return process_entity(request, LOCALITIES, params.PARAMS_LOCALITIES, {
            ID: 'entity_id',
            NAME: 'name',
            STATE: 'state',
            DEPT: 'department',
            MUN: 'municipality',
            EXACT: 'exact',
            ORDER: 'order',
            FIELDS: 'fields'
    }, index=SETTLEMENTS)


def process_street(request):
    """Procesa una consulta de tipo GET para normalizar calles.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objeto flask.Response.
    """
    parse_results, errors = parse_params(request, STREETS,
                                         params.PARAMS_STREETS)

    if any(errors):
        return formatter.create_param_error_response(request, errors)

    queries = []
    for parsed_params in parse_results:
        query = translate_keys(parsed_params, {
            NAME: 'road_name',
            STATE: 'state',
            DEPT: 'department',
            EXACT: 'exact',
            FIELDS: 'fields',
            ROAD_TYPE: 'road_type'
        }, ignore=[FLATTEN, FORMAT])

        query['excludes'] = [GEOM]
        queries.append(query)

    try:
        es = get_elasticsearch()
        responses = data.query_streets(es, queries)
    except ElasticsearchException:
        return formatter.create_internal_error_response(request)

    source = get_index_source(STREETS)
    for response in responses:
        for match in response:
            match[SOURCE] = source

    return formatter.create_ok_response(request, parse_results, STREETS,
                                        responses)


def build_addresses_result(result, query, source):
    fields = query['fields']
    number = query['number']

    for street in result:
        if not fields or FULL_NAME in fields:
            parts = street[FULL_NAME].split(',')
            parts[0] += ' {}'.format(number)
            street[FULL_NAME] = ','.join(parts)

        if not fields or DOOR_NUM in fields:
            street[DOOR_NUM] = number

        start_r = street.pop(START_R)
        end_l = street.pop(END_L)
        geom = street.pop(GEOM)

        if not fields or LOCATION in fields:
            loc = data.street_number_location(get_postgres_db(), geom,
                                              number, start_r, end_l)
            street[LOCATION] = loc

        street[SOURCE] = source


def process_address(request):
    """Procesa una consulta para normalizar direcciones.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de una de las funciones invocadas según el tipo de Request.
    """
    parse_results, errors = parse_params(request, ADDRESSES,
                                         params.PARAMS_ADDRESSES)

    if any(errors):
        return formatter.create_param_error_response(request, errors)

    queries = []
    for parsed_params in parse_results:
        road_name, number = parsed_params.pop(ADDRESS)
        parsed_params['road_name'] = road_name
        parsed_params['number'] = number

        query = translate_keys(parsed_params, {
            DEPT: 'department',
            STATE: 'state',
            EXACT: 'exact',
            FIELDS: 'fields',
            ROAD_TYPE: 'road_type'
        }, ignore=[FLATTEN, FORMAT])

        if query['fields']:
            query['fields'].extend([GEOM, START_R, END_L])

        query['excludes'] = [START_L, END_R]
            
        queries.append(query)

    try:
        es = get_elasticsearch()
        responses = data.query_streets(es, queries)
    except ElasticsearchException:
        return formatter.create_internal_error_response(request)

    source = get_index_source(STREETS)

    for response, query in zip(responses, queries):
        build_addresses_result(response, query, source)
        
    return formatter.create_ok_response(request, parse_results, ADDRESSES,
                                        responses)


def build_place_result(query, dept, muni):
    empty_entity = {
        ID: None,
        NAME: None
    }
    
    if not dept:
        state = empty_entity.copy()
        dept = empty_entity.copy()
        muni = empty_entity.copy()
        source = None
    else:
        # Remover la provincia del departamento y colocarla directamente
        # en el resultado. Haciendo esto se logra evitar una consulta
        # al índice de provincias.
        state = dept.pop(STATE)
        muni = muni or empty_entity.copy()
        source = get_index_source(DEPARTMENTS)

    place = {
        STATE: state,
        DEPT: dept,
        MUN: muni,
        LAT: query['lat'],
        LON: query['lon'],
        SOURCE: source
    }

    if query[FIELDS]:
        place = {key: place[key] for key in place if key in query[FIELDS]}

    return place


def process_place(request):
    """Procesa una consulta para georreferenciar una ubicación.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de una de las funciones invocadas según el tipo de Request.
    """
    parse_results, errors = parse_params(request, PLACES, params.PARAMS_PLACE)

    if any(errors):
        return formatter.create_param_error_response(request, errors)

    queries = []

    for parsed_params in parse_results:
        query = translate_keys(parsed_params, {}, ignore=[FLATTEN, FORMAT])
        queries.append(query)

    try:
        es = get_elasticsearch()
        dept_queries = []
        for query in queries:
            dept_queries.append({
                'lat': query['lat'],
                'lon': query['lon'],
                'fields': [ID, NAME, STATE]
            })
            
        departments = data.query_places(es, DEPARTMENTS, dept_queries)

        muni_queries = []
        for query in queries:
            muni_queries.append({
                'lat': query['lat'],
                'lon': query['lon'],
                'fields': [ID, NAME]
            })

        munis = data.query_places(es, MUNICIPALITIES, muni_queries)

        places = []
        for query, dept, muni in zip(queries, departments, munis):
            places.append(build_place_result(query, dept, muni))

    except ElasticsearchException:
        return formatter.create_internal_error_response(request)

    return formatter.create_ok_response(request, parse_results, PLACE, places,
                                        iterable_results=False)
