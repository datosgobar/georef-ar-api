"""Módulo 'normalizer' de georef-ar-api

Contiene funciones que manejan la lógica de procesamiento
de los recursos que expone la API.
"""

import logging
from flask import current_app
from service import data, params, formatter, addresses, constants
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


def translate_keys(d, translations, ignore=None):
    """Cambia las keys del diccionario 'd', utilizando las traducciones
    especificadas en 'translations'. Devuelve los resultados en un nuevo
    diccionario.

    Args:
        d (dict): Diccionario a modificar.
        translations (dict): Traducciones de keys (key anterior => key nueva.)
        ignore (list): Keys de 'd' a no agregar al nuevo diccionario devuelto.

    Returns:
        dict: Diccionario con las keys modificadas.

    """
    if not ignore:
        ignore = []

    return {
        translations.get(key, key): value
        for key, value in d.items()
        if key not in ignore
    }


def process_entity_single(request, name, param_parser, key_translations):
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
    except params.ParameterParsingException as e:
        return formatter.create_param_error_response_single(e.errors, e.fmt)

    # Construir query a partir de parámetros
    query = translate_keys(qs_params, key_translations,
                           ignore=[N.FLATTEN, N.FORMAT])

    # Construir reglas de formato a partir de parámetros
    fmt = {
        key: qs_params[key]
        for key in [N.FLATTEN, N.FIELDS, N.FORMAT]
        if key in qs_params
    }

    expand_geometries = fmt[N.FORMAT] == 'shp'
    if expand_geometries:
        query['fields'] += (N.GEOM,)

    es = get_elasticsearch()
    result = data.search_entities(es, name, [query], expand_geometries)[0]

    source = constants.INDEX_SOURCES[name]
    for match in result.hits:
        match[N.SOURCE] = source

    query_result = QueryResult.from_entity_list(result.hits, result.total,
                                                result.offset)

    return formatter.create_ok_response(name, query_result, fmt)


def process_entity_bulk(request, name, param_parser, key_translations):
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
    except params.ParameterParsingException as e:
        return formatter.create_param_error_response_bulk(e.errors)

    queries = []
    formats = []
    for parsed_params in body_params:
        # Construir query a partir de parámetros
        query = translate_keys(parsed_params, key_translations,
                               ignore=[N.FLATTEN, N.FORMAT])

        # Construir reglas de formato a partir de parámetros
        fmt = {
            key: parsed_params[key]
            for key in [N.FLATTEN, N.FIELDS]
            if key in parsed_params
        }

        queries.append(query)
        formats.append(fmt)

    es = get_elasticsearch()
    results = data.search_entities(es, name, queries)

    source = constants.INDEX_SOURCES[name]
    for result in results:
        for match in result.hits:
            match[N.SOURCE] = source

    query_results = [QueryResult.from_entity_list(result.hits, result.total,
                                                  result.offset)
                     for result in results]

    return formatter.create_ok_response_bulk(name, query_results, formats)


def process_entity(request, name, param_parser, key_translations):
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
            return process_entity_single(request, name, param_parser,
                                         key_translations)

        return process_entity_bulk(request, name, param_parser,
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
    return process_entity(request, N.STATES, params.PARAMS_STATES, {
        N.ID: 'entity_ids',
        N.NAME: 'name',
        N.INTERSECTION: 'intersection_ids',
        N.EXACT: 'exact',
        N.ORDER: 'order',
        N.FIELDS: 'fields',
        N.OFFSET: 'offset'
    })


def process_department(request):
    """Procesa una request GET o POST para consultar datos de departamentos.
    En caso de ocurrir un error de parseo, se retorna una respuesta HTTP 400.

    Args:
        request (flask.Request): Request GET o POST de flask.

    Returns:
        flask.Response: respuesta HTTP

    """
    return process_entity(request, N.DEPARTMENTS,
                          params.PARAMS_DEPARTMENTS, {
                              N.ID: 'entity_ids',
                              N.NAME: 'name',
                              N.INTERSECTION: 'intersection_ids',
                              N.STATE: 'state',
                              N.EXACT: 'exact',
                              N.ORDER: 'order',
                              N.FIELDS: 'fields',
                              N.OFFSET: 'offset'
                          })


def process_municipality(request):
    """Procesa una request GET o POST para consultar datos de municipios.
    En caso de ocurrir un error de parseo, se retorna una respuesta HTTP 400.

    Args:
        request (flask.Request): Request GET o POST de flask.

    Returns:
        flask.Response: respuesta HTTP

    """
    return process_entity(request, N.MUNICIPALITIES,
                          params.PARAMS_MUNICIPALITIES, {
                              N.ID: 'entity_ids',
                              N.NAME: 'name',
                              N.INTERSECTION: 'intersection_ids',
                              N.STATE: 'state',
                              N.EXACT: 'exact',
                              N.ORDER: 'order',
                              N.FIELDS: 'fields',
                              N.OFFSET: 'offset'
                          })


def process_locality(request):
    """Procesa una request GET o POST para consultar datos de localidades.
    En caso de ocurrir un error de parseo, se retorna una respuesta HTTP 400.

    Args:
        request (flask.Request): Request GET o POST de flask.

    Returns:
        flask.Response: respuesta HTTP

    """
    return process_entity(request, N.LOCALITIES, params.PARAMS_LOCALITIES, {
        N.ID: 'entity_ids',
        N.NAME: 'name',
        N.STATE: 'state',
        N.DEPT: 'department',
        N.MUN: 'municipality',
        N.EXACT: 'exact',
        N.ORDER: 'order',
        N.FIELDS: 'fields',
        N.OFFSET: 'offset'
    })


def build_street_query_format(parsed_params):
    """Construye dos diccionarios a partir de parámetros de consulta
    recibidos, el primero representando la query a Elasticsearch a
    realizar y el segundo representando las propiedades de formato
    (presentación) que se le debe dar a los datos obtenidos de la misma.

    Args:
        parsed_params (dict): Parámetros de una consulta para el índice de
            calles.

    Returns:
        tuple: diccionario de query y diccionario de formato

    """
    # Construir query a partir de parámetros
    query = translate_keys(parsed_params, {
        N.ID: 'street_ids',
        N.NAME: 'name',
        N.INTERSECTION: 'intersection_ids',
        N.STATE: 'state',
        N.DEPT: 'department',
        N.EXACT: 'exact',
        N.FIELDS: 'fields',
        N.TYPE: 'street_type',
        N.OFFSET: 'offset',
        N.ORDER: 'order'
    }, ignore=[N.FLATTEN, N.FORMAT])

    # Construir reglas de formato a partir de parámetros
    fmt = {
        key: parsed_params[key]
        for key in [N.FLATTEN, N.FIELDS, N.FORMAT]
        if key in parsed_params
    }

    return query, fmt


def process_street_single(request):
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
    except params.ParameterParsingException as e:
        return formatter.create_param_error_response_single(e.errors, e.fmt)

    query, fmt = build_street_query_format(qs_params)

    if fmt[N.FORMAT] == 'shp':
        query['fields'] += (N.GEOM,)

    es = get_elasticsearch()
    result = data.search_streets(es, [query])[0]

    source = constants.INDEX_SOURCES[N.STREETS]
    for match in result.hits:
        match[N.SOURCE] = source

    query_result = QueryResult.from_entity_list(result.hits, result.total,
                                                result.offset)

    return formatter.create_ok_response(N.STREETS, query_result, fmt)


def process_street_bulk(request):
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
    except params.ParameterParsingException as e:
        return formatter.create_param_error_response_bulk(e.errors)

    queries = []
    formats = []
    for parsed_params in body_params:
        query, fmt = build_street_query_format(parsed_params)
        queries.append(query)
        formats.append(fmt)

    es = get_elasticsearch()
    results = data.search_streets(es, queries)

    source = constants.INDEX_SOURCES[N.STREETS]
    for result in results:
        for match in result.hits:
            match[N.SOURCE] = source

    query_results = [QueryResult.from_entity_list(result.hits, result.total,
                                                  result.offset)
                     for result in results]

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
            return process_street_single(request)

        return process_street_bulk(request)
    except data.DataConnectionException:
        logger.exception(
            'Excepción en manejo de consulta para recurso: calles')
        return formatter.create_internal_error_response()


def build_address_query_format(parsed_params):
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
    query = translate_keys(parsed_params, {
        N.DEPT: 'department',
        N.STATE: 'state',
        N.EXACT: 'exact',
        N.OFFSET: 'offset',
        N.ORDER: 'order'
    }, ignore=[N.FLATTEN, N.FORMAT, N.FIELDS])

    # Construir reglas de formato a partir de parámetros
    fmt = {
        key: parsed_params[key]
        for key in [N.FLATTEN, N.FIELDS, N.FORMAT]
        if key in parsed_params
    }

    return query, fmt


def process_address_queries(params_list):
    """Ejecuta una lista de consultas de direcciones, partiendo desde los
    parámetros recibidos del usuario.

    Args:
        params_list (list): Lista de dict, cada dict conteniendo los parámetros
            de una consulta al recurso de direcciones de la API.

    Returns:
        tuple: Tupla de (list, list), donde la primera lista contiene una
            instancia de QueryResult por cada consulta, y la segunda lista
            contiene una instancia de dict utilizada para darle formato al
            resultado más tarde.

    """
    queries = []
    formats = []
    for parsed_params in params_list:
        query, fmt = build_address_query_format(parsed_params)
        queries.append(query)
        formats.append(fmt)

    es = get_elasticsearch()
    query_results = addresses.run_address_queries(es, queries, formats)

    return query_results, formats


def process_address_single(request):
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
    except params.ParameterParsingException as e:
        return formatter.create_param_error_response_single(e.errors, e.fmt)

    query_results, formats = process_address_queries([qs_params])

    return formatter.create_ok_response(N.ADDRESSES, query_results[0],
                                        formats[0])


def process_address_bulk(request):
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
    except params.ParameterParsingException as e:
        return formatter.create_param_error_response_bulk(e.errors)

    query_results, formats = process_address_queries(body_params)

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
            return process_address_single(request)

        return process_address_bulk(request)
    except data.DataConnectionException:
        logger.exception(
            'Excepción en manejo de consulta para recurso: direcciones')
        return formatter.create_internal_error_response()


def build_location_result(query, state, dept, muni):
    """Construye un resultado para una consulta al endpoint de ubicación.

    Args:
        query (dict): Query utilizada para obtener los resultados.
        state (dict): Provincia encontrada en la ubicación especificada.
            Puede ser None.
        dept (dict): Departamento encontrado en la ubicación especificada.
            Puede ser None.
        muni (dict): Municipio encontrado en la ubicación especificada. Puede
            ser None.

    Returns:
        dict: Resultado de ubicación con los campos apropiados

    """
    empty_entity = {
        N.ID: None,
        N.NAME: None
    }

    if not state:
        # El punto no está en la República Argentina
        state = empty_entity.copy()
        dept = empty_entity.copy()
        muni = empty_entity.copy()
        source = None
    else:
        dept = dept or empty_entity.copy()
        muni = muni or empty_entity.copy()
        # TODO: Cambiar a 'fuentes'?
        source = constants.INDEX_SOURCES[N.STATES]

    return {
        N.STATE: state,
        N.DEPT: dept,
        N.MUN: muni,
        N.LAT: query['lat'],
        N.LON: query['lon'],
        N.SOURCE: source
    }


def build_location_query_format(parsed_params):
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
    query = translate_keys(parsed_params, {}, ignore=[N.FLATTEN, N.FORMAT])

    # Construir reglas de formato a partir de parámetros
    fmt = {
        key: parsed_params[key]
        for key in [N.FLATTEN, N.FIELDS, N.FORMAT]
        if key in parsed_params
    }

    return query, fmt


def process_location_queries(es, queries):
    """Dada una lista de queries de ubicación, construye las queries apropiadas
    a índices de departamentos y municipios, y las ejecuta utilizando
    Elasticsearch.

    Args:
        es (Elasticsearch): Conexión a Elasticsearch.
        queries (list): Lista de queries de ubicación

    Returns:
        list: Resultados de ubicaciones con los campos apropiados

    """

    # TODO:
    # Por problemas con los datos de origen, se optó por utilizar una
    # implementación simple para la la funcion 'process_location_queries'.
    # Cuando los datos de departamentos cubran todo el departamento nacional,
    # se podría modificar la función para que funcione de la siguiente forma:
    #
    # (Recordar que las provincias y departamentos cubren todo el territorio
    # nacional, pero no los municipios.)
    #
    # 1) Tomar las N consultas recibidas y enviar todas al índice de
    #    departamentos.
    # 2) Tomar las consultas *que retornaron una entidad*, y re-enviarlas pero
    #    esta vez al índice de municipios. Las consultas que *no* retornaron
    #    una entidad (es decir, no cayeron dentro de un depto.) quedan marcadas
    #    como nulas.
    # 3) Combinar los resultados de los pasos 1 y 2: Si la consulta no tiene
    #    depto. asociado, su resultado es nulo. Si tiene depto., entonces
    #    también tiene provincia. Si la consulta tiene municipio, entonces
    #    tiene provincia, departamento y municipio.

    state_queries = []
    for query in queries:
        state_queries.append({
            'lat': query['lat'],
            'lon': query['lon'],
            'fields': [N.ID, N.NAME]
        })

    state_results = data.search_locations(es, N.STATES, state_queries)

    dept_queries = []
    for query in queries:
        dept_queries.append({
            'lat': query['lat'],
            'lon': query['lon'],
            'fields': [N.ID, N.NAME, N.STATE]
        })

    dept_results = data.search_locations(es, N.DEPARTMENTS, dept_queries)

    muni_queries = []
    for query in queries:
        muni_queries.append({
            'lat': query['lat'],
            'lon': query['lon'],
            'fields': [N.ID, N.NAME]
        })

    muni_results = data.search_locations(es, N.MUNICIPALITIES, muni_queries)

    locations = []
    for query, state_result, dept_result, muni_result in zip(queries,
                                                             state_results,
                                                             dept_results,
                                                             muni_results):
        # Ya que la query de tipo location retorna una o cero entidades,
        # extraer la primera entidad de los resultados, o tomar None si
        # no hay resultados.
        state = state_result.hits[0] if state_result else None
        dept = dept_result.hits[0] if dept_result else None
        muni = muni_result.hits[0] if muni_result else None
        locations.append(build_location_result(query, state, dept, muni))

    return locations


def process_location_single(request):
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
    except params.ParameterParsingException as e:
        return formatter.create_param_error_response_single(e.errors, e.fmt)

    query, fmt = build_location_query_format(qs_params)

    es = get_elasticsearch()
    location = process_location_queries(es, [query])[0]

    query_result = QueryResult.from_single_entity(location)

    return formatter.create_ok_response(N.LOCATION, query_result, fmt)


def process_location_bulk(request):
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
    except params.ParameterParsingException as e:
        return formatter.create_param_error_response_bulk(e.errors)

    queries = []
    formats = []
    for parsed_params in body_params:
        query, fmt = build_location_query_format(parsed_params)
        queries.append(query)
        formats.append(fmt)

    es = get_elasticsearch()
    locations = process_location_queries(es, queries)
    query_results = [
        QueryResult.from_single_entity(location)
        for location in locations
    ]

    return formatter.create_ok_response_bulk(N.LOCATION, query_results,
                                             formats)


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
            return process_location_single(request)

        return process_location_bulk(request)
    except data.DataConnectionException:
        logger.exception(
            'Excepción en manejo de consulta para recurso: ubicacion')
        return formatter.create_internal_error_response()
