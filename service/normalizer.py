"""Módulo 'normalizer' de georef-ar-api

Contiene funciones que manejan la lógica de procesamiento
de los recursos que expone la API.
"""

import logging
from flask import current_app
from service import data, params, formatter, address, location, utils, street
from service import names as N
from service.query_result import QueryResult

logger = logging.getLogger('georef')


def get_elasticsearch():
    """Devuelve la conexión a Elasticsearch activa para la sesión
    de flask. La conexión es creada si no existía.

    Returns:
        Elasticsearch: conexión a Elasticsearch.

    Raises:
        data.DataConnectionException: En caso de ocurrir un error de
            conexión con la capa de manejo de datos.

    """
    if not hasattr(current_app, 'elasticsearch'):
        current_app.elasticsearch = data.elasticsearch_connection(
            hosts=current_app.config['ES_HOSTS'],
            sniff=current_app.config['ES_SNIFF'],
            sniffer_timeout=current_app.config['ES_SNIFFER_TIMEOUT']
        )

    return current_app.elasticsearch


def _process_entity_single(request, name, param_parser, key_translations):
    """Procesa una request GET para consultar datos de una entidad.
    En caso de ocurrir un error de parseo, se retorna una respuesta HTTP 400.

    Args:
        request (flask.Request): Request GET de flask.
        name (str): Nombre de la entidad.
        param_parser (ParameterSet): Objeto utilizado para parsear los
            parámetros.
        key_translations (dict): Traducciones de keys a utilizar para convertir
            el diccionario de parámetros del usuario a un diccionario
            representando una query a Elasticsearch.

    Raises:
        data.DataConnectionException: En caso de ocurrir un error de
            conexión con la capa de manejo de datos.

    Returns:
        flask.Response: respuesta HTTP

    """
    try:
        qs_params = param_parser.parse_get_params(request.args)
    except params.ParametersParseException as e:
        return formatter.create_param_error_response_single(e.errors, e.fmt)

    # Construir query a partir de parámetros
    query = utils.translate_keys(qs_params.values, key_translations,
                                 ignore=[N.FLATTEN, N.FORMAT])

    # Construir reglas de formato a partir de parámetros
    fmt = {
        key: qs_params.values[key]
        for key in [N.FLATTEN, N.FIELDS, N.FORMAT]
        if key in qs_params.values
    }

    if fmt[N.FORMAT] == 'shp':
        query['fields'] += (N.GEOM,)

    es = get_elasticsearch()
    search_class = data.entity_search_class(name)
    search = search_class(query)

    data.ElasticsearchSearch.run_searches(es, [search])

    query_result = QueryResult.from_entity_list(search.result.hits,
                                                qs_params.received_values(),
                                                search.result.total,
                                                search.result.offset)

    return formatter.create_ok_response(name, query_result, fmt)


def _process_entity_bulk(request, name, param_parser, key_translations):
    """Procesa una request POST para consultar datos de una lista de entidades.
    En caso de ocurrir un error de parseo, se retorna una respuesta HTTP 400.

    Args:
        request (flask.Request): Request POST de flask.
        name (str): Nombre de la entidad.
        param_parser (ParameterSet): Objeto utilizado para parsear los
            parámetros.
        key_translations (dict): Traducciones de keys a utilizar para convertir
            los diccionarios de parámetros del usuario a una lista de
            diccionarios representando las queries a Elasticsearch.

    Raises:
        data.DataConnectionException: En caso de ocurrir un error de
            conexión con la capa de manejo de datos.

    Returns:
        flask.Response: respuesta HTTP

    """
    try:
        body_params = param_parser.parse_post_params(
            request.args, request.json, name)
    except params.ParametersParseException as e:
        return formatter.create_param_error_response_bulk(e.errors)

    queries = []
    formats = []
    for parsed_params in body_params:
        # Construir query a partir de parámetros
        query = utils.translate_keys(parsed_params.values, key_translations,
                                     ignore=[N.FLATTEN, N.FORMAT])

        # Construir reglas de formato a partir de parámetros
        fmt = {
            key: parsed_params.values[key]
            for key in [N.FLATTEN, N.FIELDS]
            if key in parsed_params.values
        }

        queries.append(query)
        formats.append(fmt)

    es = get_elasticsearch()
    search_class = data.entity_search_class(name)
    searches = [search_class(query) for query in queries]

    data.ElasticsearchSearch.run_searches(es, searches)

    query_results = [
        QueryResult.from_entity_list(search.result.hits,
                                     params.received_values(),
                                     search.result.total,
                                     search.result.offset)
        for search, params in zip(searches, body_params)
    ]

    return formatter.create_ok_response_bulk(name, query_results, formats)


def _process_entity(request, name, param_parser, key_translations):
    """Procesa una request GET o POST para consultar datos de una entidad.
    En caso de ocurrir un error de parseo, se retorna una respuesta HTTP 400.
    En caso de ocurrir un error interno, se retorna una respuesta HTTP 500.

    Args:
        request (flask.Request): Request GET o POST de flask.
        name (str): Nombre de la entidad.
        param_parser (ParameterSet): Objeto utilizado para parsear los
            parámetros.
        key_translations (dict): Traducciones de keys a utilizar para convertir
            los diccionarios de parámetros del usuario a una lista de
            diccionarios representando las queries a Elasticsearch.

    Returns:
        flask.Response: respuesta HTTP

    """
    try:
        if request.method == 'GET':
            return _process_entity_single(request, name, param_parser,
                                          key_translations)

        return _process_entity_bulk(request, name, param_parser,
                                    key_translations)
    except data.DataConnectionException:
        logger.exception(
            'Excepción en manejo de consulta para recurso: {}'.format(name))
        return formatter.create_internal_error_response()


def process_state(request):
    """Procesa una request GET o POST para consultar datos de provincias.
    En caso de ocurrir un error de parseo, se retorna una respuesta HTTP 400.

    Args:
        request (flask.Request): Request GET o POST de flask.

    Returns:
        flask.Response: respuesta HTTP

    """
    return _process_entity(request, N.STATES, params.PARAMS_STATES, {
        N.ID: 'ids',
        N.NAME: 'name',
        N.INTERSECTION: 'geo_shape_ids',
        N.EXACT: 'exact',
        N.ORDER: 'order',
        N.FIELDS: 'fields',
        N.OFFSET: 'offset',
        N.MAX: 'size'
    })


def process_department(request):
    """Procesa una request GET o POST para consultar datos de departamentos.
    En caso de ocurrir un error de parseo, se retorna una respuesta HTTP 400.

    Args:
        request (flask.Request): Request GET o POST de flask.

    Returns:
        flask.Response: respuesta HTTP

    """
    return _process_entity(
        request, N.DEPARTMENTS,
        params.PARAMS_DEPARTMENTS, {
            N.ID: 'ids',
            N.NAME: 'name',
            N.INTERSECTION: 'geo_shape_ids',
            N.STATE: 'state',
            N.EXACT: 'exact',
            N.ORDER: 'order',
            N.FIELDS: 'fields',
            N.OFFSET: 'offset',
            N.MAX: 'size'
        })


def process_municipality(request):
    """Procesa una request GET o POST para consultar datos de municipios.
    En caso de ocurrir un error de parseo, se retorna una respuesta HTTP 400.

    Args:
        request (flask.Request): Request GET o POST de flask.

    Returns:
        flask.Response: respuesta HTTP

    """
    return _process_entity(
        request, N.MUNICIPALITIES,
        params.PARAMS_MUNICIPALITIES, {
            N.ID: 'ids',
            N.NAME: 'name',
            N.INTERSECTION: 'geo_shape_ids',
            N.STATE: 'state',
            N.EXACT: 'exact',
            N.ORDER: 'order',
            N.FIELDS: 'fields',
            N.OFFSET: 'offset',
            N.MAX: 'size'
        })


def process_census_locality(request):
    """Procesa una request GET o POST para consultar datos de localidades
    censales. En caso de ocurrir un error de parseo, se retorna una respuesta
    HTTP 400.

    Args:
        request (flask.Request): Request GET o POST de flask.

    Returns:
        flask.Response: respuesta HTTP

    """
    return _process_entity(
        request, N.CENSUS_LOCALITIES,
        params.PARAMS_CENSUS_LOCALITIES, {
            N.ID: 'ids',
            N.NAME: 'name',
            N.STATE: 'state',
            N.DEPT: 'department',
            N.MUN: 'municipality',
            N.EXACT: 'exact',
            N.ORDER: 'order',
            N.FIELDS: 'fields',
            N.OFFSET: 'offset',
            N.MAX: 'size'
        })


def process_settlement(request):
    """Procesa una request GET o POST para consultar datos de asentamientos
    (base BAHRA). En caso de ocurrir un error de parseo, se retorna una
    respuesta HTTP 400.

    Args:
        request (flask.Request): Request GET o POST de flask.

    Returns:
        flask.Response: respuesta HTTP

    """
    return _process_entity(request, N.SETTLEMENTS, params.PARAMS_SETTLEMENTS, {
        N.ID: 'ids',
        N.NAME: 'name',
        N.STATE: 'state',
        N.DEPT: 'department',
        N.MUN: 'municipality',
        N.CENSUS_LOCALITY: 'census_locality',
        N.EXACT: 'exact',
        N.ORDER: 'order',
        N.FIELDS: 'fields',
        N.OFFSET: 'offset',
        N.MAX: 'size'
    })


def process_locality(request):
    """Procesa una request GET o POST para consultar datos de localidades.
    En caso de ocurrir un error de parseo, se retorna una respuesta HTTP 400.

    Args:
        request (flask.Request): Request GET o POST de flask.

    Returns:
        flask.Response: respuesta HTTP

    """
    return _process_entity(request, N.LOCALITIES, params.PARAMS_LOCALITIES, {
        N.ID: 'ids',
        N.NAME: 'name',
        N.STATE: 'state',
        N.DEPT: 'department',
        N.MUN: 'municipality',
        N.CENSUS_LOCALITY: 'census_locality',
        N.EXACT: 'exact',
        N.ORDER: 'order',
        N.FIELDS: 'fields',
        N.OFFSET: 'offset',
        N.MAX: 'size'
    })


def _build_street_query_format(parsed_params):
    """Construye dos diccionarios a partir de parámetros de consulta
    recibidos, el primero representando la query a Elasticsearch a
    realizar y el segundo representando las propiedades de formato
    (presentación) que se le debe dar a los datos obtenidos de la misma.

    Args:
        parsed_params (dict): Parámetros de una consulta para el recurso de
            calles.

    Returns:
        tuple: diccionario de query y diccionario de formato

    """
    # Construir query a partir de parámetros
    query = utils.translate_keys(parsed_params, {
        N.ID: 'ids',
        N.NAME: 'name',
        N.INTERSECTION: 'geo_shape_ids',
        N.STATE: 'state',
        N.DEPT: 'department',
        N.CENSUS_LOCALITY: 'census_locality',
        N.EXACT: 'exact',
        N.FIELDS: 'fields',
        N.CATEGORY: 'category',
        N.OFFSET: 'offset',
        N.ORDER: 'order',
        N.MAX: 'size'
    }, ignore=[N.FLATTEN, N.FORMAT])

    # Construir reglas de formato a partir de parámetros
    fmt = {
        key: parsed_params[key]
        for key in [N.FLATTEN, N.FIELDS, N.FORMAT]
        if key in parsed_params
    }

    return query, fmt


def _process_street_queries(params_list):
    """Ejecuta una lista de consultas de calles, partiendo desde los parámetros
    recibidos del usuario.

    Args:
        params_list (list): Lista de ParametersParseResult, cada uno
            conteniendo los parámetros de una consulta al recurso de calles de
            la API.

    Returns:
        tuple: Tupla de (list, list), donde la primera lista contiene una
            instancia de QueryResult por cada consulta, y la segunda lista
            contiene una instancia de dict utilizada para darle formato al
            resultado más tarde.

    """
    queries = []
    formats = []
    for parsed_params in params_list:
        query, fmt = _build_street_query_format(parsed_params.values)
        if fmt.get(N.FORMAT) == 'shp':
            query['fields'] += (N.GEOM,)

        queries.append(query)
        formats.append(fmt)

    es = get_elasticsearch()
    query_results = street.run_street_queries(es, params_list, queries,
                                              formats)

    return query_results, formats


def _process_street_single(request):
    """Procesa una request GET para consultar datos de calles.
    En caso de ocurrir un error de parseo, se retorna una respuesta HTTP 400.

    Args:
        request (flask.Request): Request GET de flask.

    Raises:
        data.DataConnectionException: En caso de ocurrir un error de
            conexión con la capa de manejo de datos.

    Returns:
        flask.Response: respuesta HTTP

    """
    try:
        qs_params = params.PARAMS_STREETS.parse_get_params(request.args)
    except params.ParametersParseException as e:
        return formatter.create_param_error_response_single(e.errors, e.fmt)

    query_results, formats = _process_street_queries([qs_params])
    return formatter.create_ok_response(N.STREETS, query_results[0],
                                        formats[0])


def _process_street_bulk(request):
    """Procesa una request POST para consultar datos de calles.
    En caso de ocurrir un error de parseo, se retorna una respuesta HTTP 400.

    Args:
        request (flask.Request): Request POST de flask.

    Raises:
        data.DataConnectionException: En caso de ocurrir un error de
            conexión con la capa de manejo de datos.

    Returns:
        flask.Response: respuesta HTTP

    """
    try:
        body_params = params.PARAMS_STREETS.parse_post_params(
            request.args, request.json, N.STREETS)
    except params.ParametersParseException as e:
        return formatter.create_param_error_response_bulk(e.errors)

    query_results, formats = _process_street_queries(body_params)
    return formatter.create_ok_response_bulk(N.STREETS, query_results, formats)


def process_street(request):
    """Procesa una request GET o POST para consultar datos de calles.
    En caso de ocurrir un error de parseo, se retorna una respuesta HTTP 400.
    En caso de ocurrir un error interno, se retorna una respuesta HTTP 500.

    Args:
        request (flask.Request): Request GET o POST de flask.

    Returns:
        flask.Response: respuesta HTTP

    """
    try:
        if request.method == 'GET':
            return _process_street_single(request)

        return _process_street_bulk(request)
    except data.DataConnectionException:
        logger.exception(
            'Excepción en manejo de consulta para recurso: calles')
        return formatter.create_internal_error_response()


def _build_address_query_format(parsed_params):
    """Construye dos diccionarios a partir de parámetros de consulta
    recibidos, el primero representando la query a Elasticsearch a
    realizar y el segundo representando las propiedades de formato
    (presentación) que se le debe dar a los datos obtenidos de la misma.

    Args:
        parsed_params (dict): Parámetros de una consulta normalización de
            una dirección.

    Returns:
        tuple: diccionario de query y diccionario de formato

    """
    # Construir query a partir de parámetros
    query = utils.translate_keys(parsed_params, {
        N.DEPT: 'department',
        N.STATE: 'state',
        N.CENSUS_LOCALITY: 'census_locality',
        N.EXACT: 'exact',
        N.OFFSET: 'offset',
        N.ORDER: 'order',
        N.MAX: 'size'
    }, ignore=[N.FLATTEN, N.FORMAT, N.FIELDS])

    # Construir reglas de formato a partir de parámetros
    fmt = {
        key: parsed_params[key]
        for key in [N.FLATTEN, N.FIELDS, N.FORMAT]
        if key in parsed_params
    }

    return query, fmt


def _process_address_queries(params_list):
    """Ejecuta una lista de consultas de direcciones, partiendo desde los
    parámetros recibidos del usuario.

    Args:
        params_list (list): Lista de ParametersParseResult, cada uno
            conteniendo los parámetros de una consulta al recurso de
            direcciones de la API.

    Returns:
        tuple: Tupla de (list, list), donde la primera lista contiene una
            instancia de QueryResult por cada consulta, y la segunda lista
            contiene una instancia de dict utilizada para darle formato al
            resultado más tarde.

    """
    queries = []
    formats = []
    for parsed_params in params_list:
        query, fmt = _build_address_query_format(parsed_params.values)
        queries.append(query)
        formats.append(fmt)

    es = get_elasticsearch()
    query_results = address.run_address_queries(es, params_list, queries,
                                                formats)

    return query_results, formats


def _process_address_single(request):
    """Procesa una request GET para normalizar una dirección.
    En caso de ocurrir un error de parseo, se retorna una respuesta HTTP 400.

    Args:
        request (flask.Request): Request GET de flask.

    Raises:
        data.DataConnectionException: En caso de ocurrir un error de
            conexión con la capa de manejo de datos.

    Returns:
        flask.Response: respuesta HTTP

    """
    try:
        qs_params = params.PARAMS_ADDRESSES.parse_get_params(request.args)
    except params.ParametersParseException as e:
        return formatter.create_param_error_response_single(e.errors, e.fmt)

    query_results, formats = _process_address_queries([qs_params])

    return formatter.create_ok_response(N.ADDRESSES, query_results[0],
                                        formats[0])


def _process_address_bulk(request):
    """Procesa una request POST para normalizar lote de direcciones.
    En caso de ocurrir un error de parseo, se retorna una respuesta HTTP 400.

    Args:
        request (flask.Request): Request POST de flask.

    Raises:
        data.DataConnectionException: En caso de ocurrir un error de
            conexión con la capa de manejo de datos.

    Returns:
        flask.Response: respuesta HTTP

    """
    try:
        body_params = params.PARAMS_ADDRESSES.parse_post_params(
            request.args, request.json, N.ADDRESSES)
    except params.ParametersParseException as e:
        return formatter.create_param_error_response_bulk(e.errors)

    query_results, formats = _process_address_queries(body_params)

    return formatter.create_ok_response_bulk(N.ADDRESSES, query_results,
                                             formats)


def process_address(request):
    """Procesa una request GET o POST para normalizar lote de direcciones.
    En caso de ocurrir un error de parseo, se retorna una respuesta HTTP 400.
    En caso de ocurrir un error interno, se retorna una respuesta HTTP 500.

    Args:
        request (flask.Request): Request GET o POST de flask.

    Returns:
        flask.Response: respuesta HTTP

    """
    try:
        if request.method == 'GET':
            return _process_address_single(request)

        return _process_address_bulk(request)
    except data.DataConnectionException:
        logger.exception(
            'Excepción en manejo de consulta para recurso: direcciones')
        return formatter.create_internal_error_response()


def _build_location_query_format(parsed_params):
    """Construye dos diccionarios a partir de parámetros de consulta
    recibidos, el primero representando la query a Elasticsearch a
    realizar y el segundo representando las propiedades de formato
    (presentación) que se le debe dar a los datos obtenidos de la misma.

    Args:
        parsed_params (dict): Parámetros de una consulta para una ubicación.

    Returns:
        tuple: diccionario de query y diccionario de formato

    """
    # Construir query a partir de parámetros
    query = utils.translate_keys(parsed_params, {}, ignore=[N.FLATTEN,
                                                            N.FORMAT])

    # Construir reglas de formato a partir de parámetros
    fmt = {
        key: parsed_params[key]
        for key in [N.FLATTEN, N.FIELDS, N.FORMAT]
        if key in parsed_params
    }

    return query, fmt


def _process_location_single(request):
    """Procesa una request GET para obtener entidades en un punto.
    En caso de ocurrir un error de parseo, se retorna una respuesta HTTP 400.

    Args:
        request (flask.Request): Request GET de flask.

    Raises:
        data.DataConnectionException: En caso de ocurrir un error de
            conexión con la capa de manejo de datos.

    Returns:
        flask.Response: respuesta HTTP

    """
    try:
        qs_params = params.PARAMS_LOCATION.parse_get_params(request.args)
    except params.ParametersParseException as e:
        return formatter.create_param_error_response_single(e.errors, e.fmt)

    query, fmt = _build_location_query_format(qs_params.values)

    es = get_elasticsearch()
    result = location.run_location_queries(es, [qs_params], [query])[0]

    return formatter.create_ok_response(N.LOCATION, result, fmt)


def _process_location_bulk(request):
    """Procesa una request POST para obtener entidades en varios puntos.
    En caso de ocurrir un error de parseo, se retorna una respuesta HTTP 400.

    Args:
        request (flask.Request): Request POST de flask.

    Raises:
        data.DataConnectionException: En caso de ocurrir un error de
            conexión con la capa de manejo de datos.

    Returns:
        flask.Response: respuesta HTTP

    """
    try:
        body_params = params.PARAMS_LOCATION.parse_post_params(
            request.args, request.json, N.LOCATIONS)
    except params.ParametersParseException as e:
        return formatter.create_param_error_response_bulk(e.errors)

    queries = []
    formats = []
    for parsed_params in body_params:
        query, fmt = _build_location_query_format(parsed_params.values)
        queries.append(query)
        formats.append(fmt)

    es = get_elasticsearch()
    results = location.run_location_queries(es, body_params, queries)

    return formatter.create_ok_response_bulk(N.LOCATION, results, formats)


def process_location(request):
    """Procesa una request GET o POST para obtener entidades en una o varias
    ubicaciones.
    En caso de ocurrir un error de parseo, se retorna una respuesta HTTP 400.
    En caso de ocurrir un error interno, se retorna una respuesta HTTP 500.

    Args:
        request (flask.Request): Request GET o POST de flask.

    Returns:
        flask.Response: respuesta HTTP

    """
    try:
        if request.method == 'GET':
            return _process_location_single(request)

        return _process_location_bulk(request)
    except data.DataConnectionException:
        logger.exception(
            'Excepción en manejo de consulta para recurso: ubicacion')
        return formatter.create_internal_error_response()
