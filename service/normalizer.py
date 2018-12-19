"""Módulo 'normalizer' de georef-ar-api

Contiene funciones que manejan la lógica de procesamiento
de los recursos que expone la API.
"""

import logging
from flask import current_app
from service import data, params, formatter
from service import names as N

logger = logging.getLogger('georef')

INDEX_SOURCES = {
    N.STATES: N.SOURCE_IGN,
    N.DEPARTMENTS: N.SOURCE_IGN,
    N.MUNICIPALITIES: N.SOURCE_IGN,
    N.LOCALITIES: N.SOURCE_BAHRA,
    N.STREETS: N.SOURCE_INDEC
}


class QueryResult:
    """Representa el resultado de una consulta a la API.

    Se distinguen dos casos de resultados posibles:
        1) Resultados en forma de lista de 0 o más elementos.
        2) Resultado singular.
    Internamente, ambos casos se almacenan como una lista.

    Attributes:
        _entities (list): Lista de entidades (provincias, municipios,
            ubicaciones, calles, etc.).
        _iterable (bool): Falso si el resultado representa una entidad
            singular (como en el caso de una ubicación). Verdadero cuando se
            representa una lista de entidades (como en el caso de, por ejemplo,
            provincias).
        _total (int): Total de entidades encontradas, no necesariamente
            incluidas en la respuesta. En caso de iterable == False, se utiliza
            1 como valor default, ya que el 'total' de entidades posibles a ser
            devueltas es 0 o 1, pero al contar ya con un resultado, el número
            deber ser 1.
        _offset (int): Cantidad de resultados salteados. En caso de iterable ==
            False, se establece como 0, ya que no se puede saltear el único
            posible.

    """

    def __init__(self, entities, iterable=False, total=1, offset=0):
        """Inicializar una QueryResult. Se recomienda utilizar
        'from_single_entity' y 'from_entity_list' en vez de utilizar este
        método.

        """
        self._entities = entities
        self._iterable = iterable
        self._total = total
        self._offset = offset

    @classmethod
    def from_single_entity(cls, entity):
        """Construir una QueryResult a partir de una entidad singular.

        Args:
            entity (dict): Entidad encontrada.

        """
        return cls([entity])

    @classmethod
    def from_entity_list(cls, entities, total, offset=0):
        """Construir una QueryResult a partir de una lista de entidades de
        cualquier longitud.

        Args:
            entities (list): Lista de entidades.
            total (int): Total de entidades encontradas, no necesariamente
                incluidas.
            offset (int): Cantidad de resultados salteados.

        """
        return cls(entities, iterable=True, total=total, offset=offset)

    @property
    def entities(self):
        return self._entities

    def first_entity(self):
        return self._entities[0]

    @property
    def total(self):
        return self._total

    @property
    def offset(self):
        return self._offset

    @property
    def iterable(self):
        return self._iterable


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
    fmt[N.CSV_FIELDS] = formatter.ENDPOINT_CSV_FIELDS[name]

    es = get_elasticsearch()
    result = data.search_entities(es, name, [query])[0]

    source = INDEX_SOURCES[name]
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

    source = INDEX_SOURCES[name]
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
        N.INTERSECTION: 'intersection',
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
                              N.INTERSECTION: 'intersection',
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
                              N.INTERSECTION: 'intersection',
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
        N.NAME: 'road_name',
        N.STATE: 'state',
        N.DEPT: 'department',
        N.EXACT: 'exact',
        N.FIELDS: 'fields',
        N.ROAD_TYPE: 'road_type',
        N.OFFSET: 'offset',
        N.ORDER: 'order'
    }, ignore=[N.FLATTEN, N.FORMAT])

    # Construir reglas de formato a partir de parámetros
    fmt = {
        key: parsed_params[key]
        for key in [N.FLATTEN, N.FIELDS, N.FORMAT]
        if key in parsed_params
    }
    fmt[N.CSV_FIELDS] = formatter.STREETS_CSV_FIELDS

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

    es = get_elasticsearch()
    result = data.search_streets(es, [query])[0]

    source = INDEX_SOURCES[N.STREETS]
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

    source = INDEX_SOURCES[N.STREETS]
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


def street_extents(door_nums, number):
    """Dados los datos de alturas de una calle, y una altura recibida en una
    consulta, retorna los extremos de la calle que contienen la altura.
    Idealmente, se utilizaría siempre start_r y end_l, pero al contar a veces
    con datos incompletos, se flexibiliza la elección de extremos para poder
    geolocalizar más direcciones.

    Args:
        door_nums (dict): Datos de alturas de la calle.
        number (int): Altura recibida en una consulta.

    Returns:
        tuple (int, int): Altura inicial y final de la calle que contienen la
            altura especificada.

    Raises:
        ValueError: Si la altura no está contenida dentro de ninguna
            combinación de extremos.

    """
    start_r = door_nums[N.START][N.RIGHT]
    start_l = door_nums[N.START][N.LEFT]
    end_r = door_nums[N.END][N.RIGHT]
    end_l = door_nums[N.END][N.LEFT]

    combinations = [(start_r, end_l), (start_l, end_r), (start_r, end_r),
                    (start_l, end_l)]

    for start, end in combinations:
        if start <= number <= end:
            return start, end

    raise ValueError('Street number out of range')


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

    for street in result.hits:
        if number and N.FULL_NAME in fields:
            parts = street[N.FULL_NAME].split(',')
            parts[0] += ' {}'.format(number)
            street[N.FULL_NAME] = ','.join(parts)

        door_nums = street.pop(N.DOOR_NUM)
        geom = street.pop(N.GEOM)

        if N.DOOR_NUM in fields:
            street[N.DOOR_NUM] = number

        if N.LOCATION_LAT in fields or N.LOCATION_LON in fields:
            if number:
                # El llamado a street_extents() no puede lanzar una excepción
                # porque los resultados de Elasticsearch aseguran que 'number'
                # está dentro de alguna combinación de extremos de la calle.
                start, end = street_extents(door_nums, number)
                loc = data.street_number_location(geom, number, start, end)
            else:
                loc = {
                    N.LAT: None,
                    N.LON: None
                }

            street[N.LOCATION] = loc

        street[N.SOURCE] = source


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
    road_name, number = parsed_params.pop(N.ADDRESS)
    parsed_params['road_name'] = road_name
    parsed_params['number'] = number

    query = translate_keys(parsed_params, {
        N.DEPT: 'department',
        N.STATE: 'state',
        N.EXACT: 'exact',
        N.ROAD_TYPE: 'road_type',
        N.OFFSET: 'offset',
        N.ORDER: 'order'
    }, ignore=[N.FLATTEN, N.FORMAT, N.FIELDS])

    query['fields'] = parsed_params[N.FIELDS] + [N.GEOM, N.START_R, N.END_L]

    # Construir reglas de formato a partir de parámetros
    fmt = {
        key: parsed_params[key]
        for key in [N.FLATTEN, N.FIELDS, N.FORMAT]
        if key in parsed_params
    }
    fmt[N.CSV_FIELDS] = formatter.ADDRESSES_CSV_FIELDS

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
    try:
        qs_params = params.PARAMS_ADDRESSES.parse_get_params(request.args)
    except params.ParameterParsingException as e:
        return formatter.create_param_error_response_single(e.errors, e.fmt)

    query, fmt = build_address_query_format(qs_params)

    es = get_elasticsearch()
    result = data.search_streets(es, [query])[0]

    source = INDEX_SOURCES[N.STREETS]
    build_addresses_result(result, query, source)

    query_result = QueryResult.from_entity_list(result.hits, result.total,
                                                result.offset)

    return formatter.create_ok_response(N.ADDRESSES, query_result, fmt)


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

    queries = []
    formats = []
    for parsed_params in body_params:
        query, fmt = build_address_query_format(parsed_params)
        queries.append(query)
        formats.append(fmt)

    es = get_elasticsearch()
    results = data.search_streets(es, queries)

    source = INDEX_SOURCES[N.STREETS]
    for result, query in zip(results, queries):
        build_addresses_result(result, query, source)

    query_results = [QueryResult.from_entity_list(result.hits, result.total,
                                                  result.offset)
                     for result in results]

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


def build_place_result(query, state, dept, muni):
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
        source = INDEX_SOURCES[N.STATES]

    place = {
        N.STATE: state,
        N.DEPT: dept,
        N.MUN: muni,
        N.LAT: query['lat'],
        N.LON: query['lon'],
        N.SOURCE: source
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
    query = translate_keys(parsed_params, {}, ignore=[N.FLATTEN, N.FORMAT])

    # Construir reglas de formato a partir de parámetros
    fmt = {
        key: parsed_params[key]
        for key in [N.FLATTEN, N.FIELDS, N.FORMAT]
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

    # TODO:
    # Por problemas con los datos de origen, se optó por utilizar una
    # implementación simple para la la funcion 'process_place_queries'.
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

    state_results = data.search_places(es, N.STATES, state_queries)

    dept_queries = []
    for query in queries:
        dept_queries.append({
            'lat': query['lat'],
            'lon': query['lon'],
            'fields': [N.ID, N.NAME, N.STATE]
        })

    dept_results = data.search_places(es, N.DEPARTMENTS, dept_queries)

    muni_queries = []
    for query in queries:
        muni_queries.append({
            'lat': query['lat'],
            'lon': query['lon'],
            'fields': [N.ID, N.NAME]
        })

    muni_results = data.search_places(es, N.MUNICIPALITIES, muni_queries)

    places = []
    for query, state_result, dept_result, muni_result in zip(queries,
                                                             state_results,
                                                             dept_results,
                                                             muni_results):
        # Ya que la query de tipo place retorna una o cero entidades,
        # extraer la primera entidad de los resultados, o tomar None si
        # no hay resultados.
        state = state_result.hits[0] if state_result else None
        dept = dept_result.hits[0] if dept_result else None
        muni = muni_result.hits[0] if muni_result else None
        places.append(build_place_result(query, state, dept, muni))

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
    try:
        qs_params = params.PARAMS_PLACE.parse_get_params(request.args)
    except params.ParameterParsingException as e:
        return formatter.create_param_error_response_single(e.errors, e.fmt)

    query, fmt = build_place_query_format(qs_params)

    es = get_elasticsearch()
    place = process_place_queries(es, [query])[0]

    query_result = QueryResult.from_single_entity(place)

    return formatter.create_ok_response(N.PLACE, query_result, fmt)


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
    try:
        body_params = params.PARAMS_PLACE.parse_post_params(
            request.args, request.json, N.PLACES)
    except params.ParameterParsingException as e:
        return formatter.create_param_error_response_bulk(e.errors)

    queries = []
    formats = []
    for parsed_params in body_params:
        query, fmt = build_place_query_format(parsed_params)
        queries.append(query)
        formats.append(fmt)

    es = get_elasticsearch()
    places = process_place_queries(es, queries)
    query_results = [QueryResult.from_single_entity(place) for place in places]

    return formatter.create_ok_response_bulk(N.PLACE, query_results, formats)


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

        return process_place_bulk(request)
    except data.DataConnectionException:
        logger.exception(
            'Excepción en manejo de consulta para recurso: ubicacion')
        return formatter.create_internal_error_response()
