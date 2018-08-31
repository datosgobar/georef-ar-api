"""Módulo 'data' de georef-api

Contiene funciones que ejecutan consultas a índices de Elasticsearch, o a la
base de datos PostgreSQL.
"""

import elasticsearch
from elasticsearch_dsl import Search, MultiSearch
from elasticsearch_dsl.query import Match, Range, MatchPhrasePrefix, GeoShape
import logging
import psycopg2.pool
from service import names as N


MIN_AUTOCOMPLETE_CHARS = 4
DEFAULT_MAX = 10
DEFAULT_FUZZINESS = 'AUTO:4,8'

logger = logging.getLogger('georef')


class DataConnectionException(Exception):
    """Representa un error sucedido al intentar realizar una operación
    utilizando Elasticsearch o PostgreSQL.
    """

    pass


class ElasticsearchResult:
    """Representa resultados para una consulta a Elasticsearch.

    Attributes:
        _hits (list): Lista de resultados (diccionarios).
        _total (int): Total de resultados encontrados, no necesariamente
            incluidos en la respuesta.
        _offset (int): Cantidad de resultados salteados, comenzando desde el
            primero.

    """

    def __init__(self, response, offset):
        self._hits = [hit.to_dict() for hit in response.hits]
        self._total = response.hits.total
        self._offset = offset

    @property
    def hits(self):
        return self._hits

    @property
    def total(self):
        return self._total

    @property
    def offset(self):
        return self._offset

    def __len__(self):
        return len(self._hits)


def postgres_db_connection_pool(host, name, user, password, maxconn):
    """Crea una pool de conexiones a la base de datos PostgreSQL.

    Args:
        host (str): Host de la base de datos.
        name (str): Nombre de la base de datos.
        user (str): Usuario de la base de datos.
        password (str): Contraseña de la base de datos.
        maxconn (int): Número máximo de conexiones a crear.

    Raises:
        DataConnectionException: si la conexión no pudo ser establecida.

    Returns:
        psycopg2.pool.ThreadedConnectionPool: Pool de conexiones a la base de
            datos SQL.

    """
    try:
        return psycopg2.pool.ThreadedConnectionPool(1, maxconn, host=host,
                                                    dbname=name, user=user,
                                                    password=password)
    except psycopg2.Error as e:
        logger.error(
            'Error al crear pool de conexiones a la base de datos PostgreSQL:')
        logger.error(e)
        raise DataConnectionException()


def elasticsearch_connection(hosts, sniff=False, sniffer_timeout=60):
    """Crea una conexión a Elasticsearch.

    Args:
        hosts (list): Lista de nodos Elasticsearch a los cuales conectarse.
        sniff (bool): Activa la función de sniffing, la cual permite descubrir
            nuevos nodos en un cluster y conectarse a ellos.

    Raises:
        DataConnectionException: si la conexión no pudo ser establecida.

    Returns:
        Elasticsearch: Conexión a Elasticsearch.

    """
    try:
        options = {
            'hosts': hosts
        }

        if sniff:
            options['sniff_on_start'] = True
            options['sniff_on_connection_fail'] = True
            options['sniffer_timeout'] = sniffer_timeout

        return elasticsearch.Elasticsearch(**options)
    except elasticsearch.ElasticsearchException:
        raise DataConnectionException()


def run_searches(es, index, searches):
    """Ejecuta una lista de búsquedas Elasticsearch. Internamente, se utiliza
    la función MultiSearch.

    Args:
        es (Elasticsearch): Conexión a Elasticsearch.
        index (str): Nombre del índice sobre el cual se deberían ejecutar las
            queries.
        searches (list): Lista de búsquedas, de tipo Search.

    Raises:
        DataConnectionException: si ocurrió un error al ejecutar las búsquedas.

    Returns:
        list: Lista de resultados, cada resultado contiene una lista de 'hits'
            (documentos encontrados) y otros metadatos.

    """
    ms = MultiSearch(index=index, using=es)

    for search in searches:
        ms = ms.add(search)

    try:
        responses = ms.execute(raise_on_error=True)
        es_results = []

        for search, response in zip(searches, responses):
            # Incluir offset (inicio) en los resultados
            offset = search.to_dict()['from']
            es_results.append(ElasticsearchResult(response, offset))

        return es_results
    except elasticsearch.ElasticsearchException:
        raise DataConnectionException()


def search_entities(es, index, params_list):
    """Busca entidades políticas (localidades, departamentos, o provincias)
    según parámetros de una o más consultas.

    Args:
        es (Elasticsearch): Cliente de Elasticsearch.
        index (str): Nombre del índice sobre el cual realizar las búsquedas.
        params_list (list): Lista de conjuntos de parámetros de consultas. Ver
            la documentación de la función 'build_entity_search' para más
            detalles.

    Returns:
        list: Resultados de búsqueda de entidades.

    """
    searches = [build_entity_search(**params) for params in params_list]
    return run_searches(es, index, searches)


def search_places(es, index, params_list):
    """Busca entidades políticas que contengan un punto dato, según
    parámetros de una o más consultas.

    Args:
        es (Elasticsearch): Cliente de Elasticsearch.
        index (str): Nombre del índice sobre el cual realizar las búsquedas.
        params_list (list): Lista de conjuntos de parámetros de consultas. Ver
            la documentación de la función 'build_place_search' para más
            detalles.

    Returns:
        list: Resultados de búsqueda de entidades.

    """
    searches = [build_place_search(**params) for params in params_list]
    return run_searches(es, index, searches)


def search_streets(es, params_list):
    """Busca vías de circulación según parámetros de una o más consultas.

    Args:
        es (Elasticsearch): Cliente de Elasticsearch.
        params_list (list): Lista de conjuntos de parámetros de consultas. Ver
            la documentación de la función 'build_streets_search' para más
            detalles.

    Returns:
        list: Resultados de búsqueda de vías de circulación.

    """
    searches = [build_streets_search(**params) for params in params_list]
    return run_searches(es, N.STREETS, searches)


def build_entity_search(entity_id=None, name=None, state=None,
                        department=None, municipality=None, max=None,
                        order=None, fields=None, exact=False, offset=0):
    """Construye una búsqueda con Elasticsearch DSL para entidades políticas
    (localidades, departamentos, o provincias) según parámetros de búsqueda
    de una consulta.

    Args:
        entity_id (str): ID de la entidad (opcional).
        name (str): Nombre del tipo de entidad (opcional).
        state (str): ID o nombre de provincia para filtrar (opcional).
        department (str): ID o nombre de departamento para filtrar (opcional).
        municipality (str): ID o nombre de municipio para filtrar (opcional).
        max (int): Limita la cantidad de resultados (opcional).
        order (str): Campo por el cual ordenar los resultados (opcional).
        fields (list): Campos a devolver en los resultados (opcional).
        exact (bool): Activa búsqueda por nombres exactos. (toma efecto sólo si
            se especificaron los parámetros 'name', 'department',
            'municipality' o 'state'.) (opcional).
        offset (int): Retornar resultados comenenzando desde los 'offset'
            primeros resultados obtenidos.

    Returns:
        Search: Búsqueda de tipo Search.

    """
    if not fields:
        fields = []

    s = Search()

    if entity_id:
        s = s.query(build_match_query(N.ID, entity_id))

    if name:
        s = s.query(build_name_query(N.NAME, name, exact))

    if municipality:
        if municipality.isdigit():
            s = s.query(build_match_query(N.MUN_ID, municipality))
        else:
            s = s.query(build_name_query(N.MUN_NAME, municipality, exact))

    if department:
        if department.isdigit():
            s = s.query(build_match_query(N.DEPT_ID, department))
        else:
            s = s.query(build_name_query(N.DEPT_NAME, department, exact))

    if state:
        if state.isdigit():
            s = s.query(build_match_query(N.STATE_ID, state))
        else:
            s = s.query(build_name_query(N.STATE_NAME, state, exact))

    if order:
        if order == N.NAME:
            order += N.EXACT_SUFFIX
        s = s.sort(order)

    s = s.source(include=fields)
    return s[offset: offset + (max or DEFAULT_MAX)]


def build_streets_search(street_id=None, road_name=None, department=None,
                         state=None, road_type=None, max=None, fields=None,
                         exact=False, number=None, offset=0):
    """Construye una búsqueda con Elasticsearch DSL para vías de circulación
    según parámetros de búsqueda de una consulta.

    Args:
        es (Elasticsearch): Cliente de Elasticsearch.
        street_id (str): ID de la calle a buscar (opcional).
        road_name (str): Nombre de la calle para filtrar (opcional).
        department (str): ID o nombre de departamento para filtrar (opcional).
        state (str): ID o nombre de provincia para filtrar (opcional).
        road_type (str): Nombre del tipo de camino para filtrar (opcional).
        max (int): Limita la cantidad de resultados (opcional).
        fields (list): Campos a devolver en los resultados (opcional).
        exact (bool): Activa búsqueda por nombres exactos. (toma efecto sólo si
            se especificaron los parámetros 'name', 'locality', 'state' o
            'department'.) (opcional).
        offset (int): Retornar resultados comenenzando desde los 'offset'
            primeros resultados obtenidos.

    Returns:
        Search: Búsqueda de tipo Search.

    """
    if not fields:
        fields = []

    s = Search()

    if street_id:
        s = s.query(build_match_query(N.ID, street_id))

    if road_name:
        s = s.query(build_name_query(N.NAME, road_name, exact))

    if road_type:
        s = s.query(build_match_query(N.ROAD_TYPE, road_type, fuzzy=True))

    if number:
        s = s.query(build_range_query(N.START_R, '<=', number))
        s = s.query(build_range_query(N.END_L, '>=', number))

    if department:
        if department.isdigit():
            s = s.query(build_match_query(N.DEPT_ID, department))
        else:
            s = s.query(build_name_query(N.DEPT_NAME, department, exact))

    if state:
        if state.isdigit():
            s = s.query(build_match_query(N.STATE_ID, state))
        else:
            s = s.query(build_name_query(N.STATE_NAME, state, exact))

    s = s.source(include=fields)
    return s[offset: offset + (max or DEFAULT_MAX)]


def build_place_search(lat, lon, fields=None):
    """Construye una búsqueda con Elasticsearch DSL para entidades en una
    ubicación según parámetros de búsqueda de una consulta.

    Args:
        lat (float): Latitud del punto.
        lon (float): Longitud del punto.
        fields (list): Campos a devolver en los resultados (opcional).

    Returns:
        Search: Búsqueda de tipo Search.

    """
    if not fields:
        fields = []

    s = Search()

    options = {
        'shape': {
            'type': 'point',
            'coordinates': [lon, lat]
        }
    }

    s = s.query(GeoShape(**{N.GEOM: options}))
    s = s.source(include=fields)
    return s[:1]


def build_name_query(field, value, exact=False):
    """Crea una condición de búsqueda por nombre para Elasticsearch.
       Las entidades con nombres son, por el momento, las provincias, los
       departamentos, los municipios, las localidades y las calles.

    Args:
        field (str): Campo de la condición.
        value (str): Valor de comparación.
        exact (bool): Activar modo de búsqueda exacta.

    Returns:
        Query: Condición para Elasticsearch.

    """
    if exact:
        field += N.EXACT_SUFFIX
        return build_match_query(field, value, False)
    else:
        match_query = build_match_query(field, value, True, operator='and')

        if len(value.strip()) >= MIN_AUTOCOMPLETE_CHARS:
            prefix_query = build_match_phrase_prefix_query(field, value)
            return prefix_query | match_query
        else:
            return match_query


def build_match_phrase_prefix_query(field, value):
    """Crea una condición 'Match Phrase Prefix' para Elasticsearch.

    Args:
        field (str): Campo de la condición.
        value (str): Valor de comparación.

    Returns:
        Query: Condición para Elasticsearch.

    """
    options = {
        'query': value
    }
    return MatchPhrasePrefix(**{field: options})


def build_range_query(field, operator, value):
    """Crea una condición 'Range' para Elasticsearch.

    Args:
        field (str): Campo de la condición.
        value (int): Número contra el que se debería comparar el campo.
        operator (str): Operador a utilizar (>, =>, <, =<)

    Returns:
        Query: Condición Range para Elasticsearch

    """
    if operator == '<':
        es_operator = 'lt'
    elif operator == '<=':
        es_operator = 'lte'
    elif operator == '>':
        es_operator = 'gt'
    elif operator == '>=':
        es_operator = 'gte'
    else:
        raise ValueError('Invalid operator.')

    options = {es_operator: value}
    return Range(**{field: options})


def build_match_query(field, value, fuzzy=False, operator='or'):
    """Crea una condición 'Match' para Elasticsearch.

    Args:
        field (str): Campo de la condición.
        value (str): Valor de comparación.
        fuzzy (bool): Bandera para habilitar tolerancia a errores.
        operator (bool): Operador a utilizar para conectar clausulas 'term'

    Returns:
        Query: Condición para Elasticsearch.

    """
    options = {
        'query': value,
        'operator': operator
    }

    if fuzzy:
        options['fuzziness'] = DEFAULT_FUZZINESS

    return Match(**{field: options})


def street_number_location(connection, geom, number, start, end):
    """Obtiene las coordenadas de un punto dentro de un tramo de calle.

    Args:
        connection (psycopg2.connection): Conexión a base de datos.
        geom (str): Geometría de un tramo de calle.
        number (int or None): Número de puerta o altura.
        start (int): Numeración inicial del tramo de calle.
        end (int): Numeración final del tramo de calle.

    Returns:
        dict: Coordenadas del punto.

    """
    args = geom, number, start, end
    query = """SELECT geocodificar('%s', %s, %s, %s);""" % args

    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            location = cursor.fetchall()[0][0]
    except psycopg2.Error as e:
        logger.error('Ocurrieron errores en la consulta SQL:')
        logger.error(e)
        raise DataConnectionException()

    if location['code']:
        parts = location['result'].split(',')
        lat, lon = float(parts[0]), float(parts[1])
    else:
        lat, lon = None, None

    return {
        N.LAT: lat,
        N.LON: lon
    }
