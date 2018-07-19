# -*- coding: utf-8 -*-

"""Módulo 'normalizer' de georef-api

Contiene funciones que manejan la lógica de procesamiento
de los recursos que expone la API.
"""

from service import data, params, formatter
from service.names import *
from flask import g


def get_elasticsearch():
    if 'elasticsearch' not in g:
        g.elasticsearch = data.elasticsearch_connection()

    return g.elasticsearch


def get_postgres_db():
    if 'postgres' not in g:
        g.postgres = data.postgres_db_connection()

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


def process_entity_single(request, name, param_parser, key_translations,
                          index):
    qs_params, errors = param_parser.parse_get_params(request.args)

    if errors:
        return formatter.create_param_error_response_single(errors)

    # Construir query a partir de parámetros
    query = translate_keys(qs_params, key_translations,
                           ignore=[FLATTEN, FORMAT])

    # Construir reglas de formato a partir de parámetros
    fmt = {
        key: qs_params[key]
        for key in [FLATTEN, FIELDS, FORMAT]
        if key in qs_params
    }

    es = get_elasticsearch()
    result = data.query_entities(es, index, [query])[0]

    source = get_index_source(index)
    for match in result:
        match[SOURCE] = source

    return formatter.create_ok_response(name, result, fmt)


def process_entity_bulk(request, name, param_parser, key_translations, index):
    body_params, errors = param_parser.parse_post_params(
        request.args, request.json and request.json.get(name))

    if any(errors):
        return formatter.create_param_error_response_bulk(errors)

    queries = []
    formats = []
    for parsed_params in body_params:
        # Construir query a partir de parámetros
        query = translate_keys(parsed_params, key_translations,
                               ignore=[FLATTEN, FORMAT])

        # Construir reglas de formato a partir de parámetros
        fmt = {
            key: parsed_params[key]
            for key in [FLATTEN, FIELDS]
            if key in parsed_params
        }

        queries.append(query)
        formats.append(fmt)

    es = get_elasticsearch()
    results = data.query_entities(es, index, queries)

    source = get_index_source(index)
    for result in results:
        for match in result:
            match[SOURCE] = source

    return formatter.create_ok_response_bulk(name, results, formats)


def process_entity(request, name, param_parser, key_translations, index=None):
    if not index:
        index = name

    try:
        if request.method == 'GET':
            return process_entity_single(request, name, param_parser,
                                         key_translations, index)
        else:
            return process_entity_bulk(request, name, param_parser,
                                       key_translations, index)
    except data.DataConnectionException:
        return formatter.create_internal_error_response(request)


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


def build_street_query_format(parsed_params):
    # Construir query a partir de parámetros
    query = translate_keys(parsed_params, {
        ID: 'street_id',
        NAME: 'road_name',
        STATE: 'state',
        DEPT: 'department',
        EXACT: 'exact',
        FIELDS: 'fields',
        ROAD_TYPE: 'road_type'
    }, ignore=[FLATTEN, FORMAT])

    query['excludes'] = [GEOM]

    # Construir reglas de formato a partir de parámetros
    fmt = {
        key: parsed_params[key]
        for key in [FLATTEN, FIELDS, FORMAT]
        if key in parsed_params
    }

    return query, fmt


def process_street_single(request):
    qs_params, errors = params.PARAMS_STREETS.parse_get_params(request.args)

    if errors:
        return formatter.create_param_error_response_single(errors)

    query, fmt = build_street_query_format(qs_params)

    es = get_elasticsearch()
    result = data.query_streets(es, [query])[0]

    source = get_index_source(STREETS)
    for match in result:
        match[SOURCE] = source

    return formatter.create_ok_response(STREETS, result, fmt)


def process_street_bulk(request):
    body_params, errors = params.PARAMS_STREETS.parse_post_params(
        request.args, request.json and request.json.get(STREETS))

    if any(errors):
        return formatter.create_param_error_response_bulk(errors)

    queries = []
    formats = []
    for parsed_params in body_params:
        query, fmt = build_street_query_format(parsed_params)
        queries.append(query)
        formats.append(fmt)

    es = get_elasticsearch()
    results = data.query_streets(es, queries)

    source = get_index_source(STREETS)
    for result in results:
        for match in result:
            match[SOURCE] = source

    return formatter.create_ok_response_bulk(STREETS, results, formats)


def process_street(request):
    """Procesa una consulta de tipo GET para normalizar calles.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objeto flask.Response.
    """
    try:
        if request.method == 'GET':
            return process_street_single(request)
        else:
            return process_street_bulk(request)
    except data.DataConnectionException:
        return formatter.create_internal_error_response(request)


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


def build_address_query_format(parsed_params):
    # Construir query a partir de parámetros
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

    # Construir reglas de formato a partir de parámetros
    fmt = {
        key: parsed_params[key]
        for key in [FLATTEN, FIELDS, FORMAT]
        if key in parsed_params
    }

    return query, fmt


def process_address_single(request):
    qs_params, errors = params.PARAMS_ADDRESSES.parse_get_params(request.args)

    if errors:
        return formatter.create_param_error_response_single(errors)

    query, fmt = build_address_query_format(qs_params)

    es = get_elasticsearch()
    result = data.query_streets(es, [query])[0]

    source = get_index_source(STREETS)
    build_addresses_result(result, query, source)

    return formatter.create_ok_response(ADDRESSES, result, fmt)


def process_address_bulk(request):
    body_params, errors = params.PARAMS_ADDRESSES.parse_post_params(
        request.args, request.json and request.json.get(ADDRESSES))

    if any(errors):
        return formatter.create_param_error_response_bulk(errors)

    queries = []
    formats = []
    for parsed_params in body_params:
        query, fmt = build_address_query_format(parsed_params)
        queries.append(query)
        formats.append(fmt)

    es = get_elasticsearch()
    results = data.query_streets(es, queries)

    source = get_index_source(STREETS)
    for result, query in zip(results, queries):
        build_addresses_result(result, query, source)

    return formatter.create_ok_response_bulk(ADDRESSES, results, formats)


def process_address(request):
    """Procesa una consulta de tipo GET para normalizar direcciones.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objeto flask.Response.
    """
    try:
        if request.method == 'GET':
            return process_address_single(request)
        else:
            return process_address_bulk(request)
    except data.DataConnectionException:
        return formatter.create_internal_error_response(request)


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


def build_place_query_format(parsed_params):
    # Construir query a partir de parámetros
    query = translate_keys(parsed_params, {}, ignore=[FLATTEN, FORMAT])

    # Construir reglas de formato a partir de parámetros
    fmt = {
        key: parsed_params[key]
        for key in [FLATTEN, FIELDS, FORMAT]
        if key in parsed_params
    }

    return query, fmt


def process_place_queries(es, queries):
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

    return places


def process_place_single(request):
    qs_params, errors = params.PARAMS_PLACE.parse_get_params(request.args)

    if errors:
        return formatter.create_param_error_response_single(errors)

    query, fmt = build_place_query_format(qs_params)

    es = get_elasticsearch()
    result = process_place_queries(es, [query])[0]

    return formatter.create_ok_response(PLACE, result, fmt,
                                        iterable_result=False)


def process_place_bulk(request):
    body_params, errors = params.PARAMS_PLACE.parse_post_params(
        request.args, request.json and request.json.get(PLACES))

    if any(errors):
        return formatter.create_param_error_response_bulk(errors)

    queries = []
    formats = []
    for parsed_params in body_params:
        query, fmt = build_place_query_format(parsed_params)
        queries.append(query)
        formats.append(fmt)

    es = get_elasticsearch()
    results = process_place_queries(es, queries)

    return formatter.create_ok_response_bulk(PLACE, results, formats,
                                             iterable_result=False)


def process_place(request):
    """Procesa una consulta para georreferenciar una ubicación.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de una de las funciones invocadas según el tipo de Request.
    """
    try:
        if request.method == 'GET':
            return process_place_single(request)
        else:
            return process_place_bulk(request)
    except data.DataConnectionException:
        return formatter.create_internal_error_response(request)
