"""Módulo 'normalizer' de georef-api

Contiene funciones que manejan la lógica de procesamiento
de los recursos que expone la API.
"""

from service import data, params, formatter
from service.names import *
from flask import g


def get_elasticsearch():
    """Devuelve la conexión a Elasticsearch activa para la sesión
    de flask. La conexión es creada si no existía.

    Returns:
        Elasticsearch: conexión a Elasticsearch.

    Raises:
        data.DataConnectionException: En caso de ocurrir un error de
            conexión con la capa de manejo de datos.

    """
    if 'elasticsearch' not in g:
        g.elasticsearch = data.elasticsearch_connection()

    return g.elasticsearch


def get_postgres_db():
    """Devuelve la conexión a PostgreSQL activa para la sesión
    de flask. La conexión es creada si no existía.

    Returns:
        psycopg2.connection: conexión a PostgreSQL.

    Raises:
        data.DataConnectionException: En caso de ocurrir un error de
            conexión con la capa de manejo de datos.

    """
    if 'postgres' not in g:
        g.postgres = data.postgres_db_connection()

    return g.postgres


def get_index_source(index):
    """Devuelve la fuente para un índice dado.

    Args:
        index (str): Nombre del índice.

    Returns:
        str: Nombre de la fuente.

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


def process_entity_single(request, name, param_parser, key_translations,
                          index):
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
        index (str): Nombre del índice a consultar.

    Raises:
        data.DataConnectionException: En caso de ocurrir un error de
            conexión con la capa de manejo de datos.

    Returns:
        flask.Response: respuesta HTTP
    """
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
    result = data.search_entities(es, index, [query])[0]

    source = get_index_source(index)
    for match in result:
        match[SOURCE] = source

    return formatter.create_ok_response(name, result, fmt)


def process_entity_bulk(request, name, param_parser, key_translations, index):
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
        index (str): Nombre del índice a consultar.

    Raises:
        data.DataConnectionException: En caso de ocurrir un error de
            conexión con la capa de manejo de datos.

    Returns:
        flask.Response: respuesta HTTP
    """
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
    results = data.search_entities(es, index, queries)

    source = get_index_source(index)
    for result in results:
        for match in result:
            match[SOURCE] = source

    return formatter.create_ok_response_bulk(name, results, formats)


def process_entity(request, name, param_parser, key_translations, index=None):
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
        index (str): Nombre del índice a consultar. Por defecto, se utiliza
            el nombre de la entidad.

    Returns:
        flask.Response: respuesta HTTP
    """
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
        return formatter.create_internal_error_response()


def process_state(request):
    """Procesa una request GET o POST para consultar datos de provincias.
    En caso de ocurrir un error de parseo, se retorna una respuesta HTTP 400.

    Args:
        request (flask.Request): Request GET o POST de flask.

    Returns:
        flask.Response: respuesta HTTP
    """
    return process_entity(request, STATES, params.PARAMS_STATES, {
            ID: 'entity_id',
            NAME: 'name',
            EXACT: 'exact',
            ORDER: 'order',
            FIELDS: 'fields'
    })


def process_department(request):
    """Procesa una request GET o POST para consultar datos de departamentos.
    En caso de ocurrir un error de parseo, se retorna una respuesta HTTP 400.

    Args:
        request (flask.Request): Request GET o POST de flask.

    Returns:
        flask.Response: respuesta HTTP
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
    """Procesa una request GET o POST para consultar datos de municipios.
    En caso de ocurrir un error de parseo, se retorna una respuesta HTTP 400.

    Args:
        request (flask.Request): Request GET o POST de flask.

    Returns:
        flask.Response: respuesta HTTP
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
    """Procesa una request GET o POST para consultar datos de localidades.
    En caso de ocurrir un error de parseo, se retorna una respuesta HTTP 400.

    Args:
        request (flask.Request): Request GET o POST de flask.

    Returns:
        flask.Response: respuesta HTTP
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
    qs_params, errors = params.PARAMS_STREETS.parse_get_params(request.args)

    if errors:
        return formatter.create_param_error_response_single(errors)

    query, fmt = build_street_query_format(qs_params)

    es = get_elasticsearch()
    result = data.search_streets(es, [query])[0]

    source = get_index_source(STREETS)
    for match in result:
        match[SOURCE] = source

    return formatter.create_ok_response(STREETS, result, fmt)


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
    results = data.search_streets(es, queries)

    source = get_index_source(STREETS)
    for result in results:
        for match in result:
            match[SOURCE] = source

    return formatter.create_ok_response_bulk(STREETS, results, formats)


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
        else:
            return process_street_bulk(request)
    except data.DataConnectionException:
        return formatter.create_internal_error_response()


def build_addresses_result(result, query, source):
    """Construye resultados para una consulta al endpoint de direcciones.
    Modifica los resultados contenidos en la lista 'result', agregando
    ubicación, altura y nomenclatura con altura.

    Args:
        result (list): Resultados de una búsqueda al índice de calles.
            (lista de calles).
        query (dict): Query utilizada para obtener los resultados.
        source (str): Nombre de la fuente de los datos.

    """
    fields = query['fields']
    number = query['number']

    for street in result:
        if FULL_NAME in fields:
            parts = street[FULL_NAME].split(',')
            parts[0] += ' {}'.format(number)
            street[FULL_NAME] = ','.join(parts)

        if DOOR_NUM in fields:
            street[DOOR_NUM] = number

        start_r = street.pop(START_R)
        end_l = street.pop(END_L)
        geom = street.pop(GEOM)

        if LOCATION_LAT in fields or LOCATION_LON in fields:
            loc = data.street_number_location(get_postgres_db(), geom,
                                              number, start_r, end_l)
            street[LOCATION] = loc

        street[SOURCE] = source


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
    road_name, number = parsed_params.pop(ADDRESS)
    parsed_params['road_name'] = road_name
    parsed_params['number'] = number

    query = translate_keys(parsed_params, {
        DEPT: 'department',
        STATE: 'state',
        EXACT: 'exact',
        ROAD_TYPE: 'road_type'
    }, ignore=[FLATTEN, FORMAT, FIELDS])

    query['fields'] = parsed_params[FIELDS] + [GEOM, START_R, END_L]
    query['excludes'] = [START_L, END_R]

    # Construir reglas de formato a partir de parámetros
    fmt = {
        key: parsed_params[key]
        for key in [FLATTEN, FIELDS, FORMAT]
        if key in parsed_params
    }

    return query, fmt


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
    qs_params, errors = params.PARAMS_ADDRESSES.parse_get_params(request.args)

    if errors:
        return formatter.create_param_error_response_single(errors)

    query, fmt = build_address_query_format(qs_params)

    es = get_elasticsearch()
    result = data.search_streets(es, [query])[0]

    source = get_index_source(STREETS)
    build_addresses_result(result, query, source)

    return formatter.create_ok_response(ADDRESSES, result, fmt)


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
    results = data.search_streets(es, queries)

    source = get_index_source(STREETS)
    for result, query in zip(results, queries):
        build_addresses_result(result, query, source)

    return formatter.create_ok_response_bulk(ADDRESSES, results, formats)


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
        else:
            return process_address_bulk(request)
    except data.DataConnectionException:
        return formatter.create_internal_error_response()


def build_place_result(query, dept, muni):
    """Construye un resultado para una consulta al endpoint de ubicación.

    Args:
        query (dict): Query utilizada para obtener los resultados.
        dept (dict): Departamento encontrado en la ubicación especificada.
            Puede ser None.
        muni (dict): Municipio encontrado en la ubicación especificada. Puede
            ser None.

    Returns:
        dict: Resultado de ubicación con los campos apropiados

    """
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

    return place


def build_place_query_format(parsed_params):
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
    query = translate_keys(parsed_params, {}, ignore=[FLATTEN, FORMAT])

    # Construir reglas de formato a partir de parámetros
    fmt = {
        key: parsed_params[key]
        for key in [FLATTEN, FIELDS, FORMAT]
        if key in parsed_params
    }

    return query, fmt


def process_place_queries(es, queries):
    """Dada una lista de queries de ubicación, construye las queries apropiadas
    a índices de departamentos y municipios, y las ejecuta utilizando
    Elasticsearch.

    Args:
        es (Elasticsearch): Conexión a Elasticsearch.
        queries (list): Lista de queries de ubicación

    Returns:
        list: Resultados de ubicaciones con los campos apropiados

    """
    dept_queries = []
    for query in queries:
        dept_queries.append({
            'lat': query['lat'],
            'lon': query['lon'],
            'fields': [ID, NAME, STATE]
        })

    departments = data.search_places(es, DEPARTMENTS, dept_queries)

    muni_queries = []
    for query in queries:
        muni_queries.append({
            'lat': query['lat'],
            'lon': query['lon'],
            'fields': [ID, NAME]
        })

    munis = data.search_places(es, MUNICIPALITIES, muni_queries)

    places = []
    for query, dept, muni in zip(queries, departments, munis):
        places.append(build_place_result(query, dept, muni))

    return places


def process_place_single(request):
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
    qs_params, errors = params.PARAMS_PLACE.parse_get_params(request.args)

    if errors:
        return formatter.create_param_error_response_single(errors)

    query, fmt = build_place_query_format(qs_params)

    es = get_elasticsearch()
    result = process_place_queries(es, [query])[0]

    return formatter.create_ok_response(PLACE, result, fmt,
                                        iterable_result=False)


def process_place_bulk(request):
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
            return process_place_single(request)
        else:
            return process_place_bulk(request)
    except data.DataConnectionException:
        return formatter.create_internal_error_response()
