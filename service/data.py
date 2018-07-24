"""Módulo 'data' de georef-api

Contiene funciones que ejecutan consultas a índices de Elasticsearch, o a la
base de datos PostgreSQL.
"""

import os
import elasticsearch
import logging
import psycopg2
import psycopg2.extras
from service import names as N


MIN_AUTOCOMPLETE_CHARS = 4
DEFAULT_MAX = 10

logger = logging.getLogger('georef')


class DataConnectionException(Exception):
    """Representa un error sucedido al intentar realizar una operación
    utilizando Elasticsearch o PostgreSQL.
    """

    pass


def postgres_db_connection():
    """Crea una conexión a la base de datos PostgreSQL.

    Raises:
        DataConnectionException: si la conexión no pudo ser establecida.

    Returns:
        psycopg2.connection: Conexión a la base de datos SQL.

    """
    try:
        db = psycopg2.connect(
            connection_factory=psycopg2.extras.LoggingConnection,
            host=os.environ.get('GEOREF_API_DB_HOST'),
            dbname=os.environ.get('GEOREF_API_DB_NAME'),
            user=os.environ.get('GEOREF_API_DB_USER'),
            password=os.environ.get('GEOREF_API_DB_PASS'))

        db.initialize(logging.getLogger('psycopg2'))
        return db
    except psycopg2.Error as e:
        logger.error('Error al conectarse a la base de datos PostgreSQL:')
        logger.error(e)
        raise DataConnectionException()


def elasticsearch_connection():
    """Crea una conexión a Elasticsearch.

    Raises:
        DataConnectionException: si la conexión no pudo ser establecida.

    Returns:
        Elasticsearch: Conexión a Elasticsearch.

    """
    try:
        return elasticsearch.Elasticsearch()
    except elasticsearch.ElasticsearchException:
        raise DataConnectionException()


def run_dsl_queries(es, index, dsl_queries):
    """Ejecuta una lista de queries Elasticsearch en formato Elasticsearch
    Query DSL. Internamente, se utiliza la función MultiSearch.

    Args:
        es (Elasticsearch): Conexión a Elasticsearch.
        index (str): Nombre del índice sobre el cual se deberían ejecutar las
            queries.
        dsl_queries (list): Lista de queries en formato Query DSL.

    Raises:
        DataConnectionException: si ocurrió un error al ejecutar las queries.

    Returns:
        Elasticsearch: Conexión a Elasticsearch.

    """
    body = []
    for query in dsl_queries:
        # No es necesario especificar el índice por
        # query ya que se ejecutan todas en el mismo
        # índice.
        body.append({})
        body.append(query)

    try:
        results = es.msearch(body=body, index=index)
    except elasticsearch.ElasticsearchException:
        raise DataConnectionException()

    responses = []
    for response in results['responses']:
        error = response.get('error')
        if error:
            logger.error('Ocurrió un error en la query Elasticsearch.msearch:')
            logger.error('Tipo: {}, causa: {}'.format(error['type'],
                                                      error['reason']))
            raise DataConnectionException()

        hits = [hit['_source'] for hit in response['hits']['hits']]
        responses.append(hits)

    return responses


def query_entities(es, index, queries):
    """Busca entidades políticas (localidades, departamentos, o provincias)
    según parámetros de una o más consultas.

    Args:
        es (Elasticsearch): Cliente de Elasticsearch.
        index (str): Nombre del índice sobre el cual realizar las búsquedas.
        queries (list): Lista de conjuntos de parámetros de consultas. Ver
            la documentación de la función 'build_entity_dsl_query' para más
            detalles.

    Returns:
        list: Resultados de búsqueda de entidades.

    """
    dsl_queries = (build_entity_dsl_query(**query) for query in queries)
    return run_dsl_queries(es, index, dsl_queries)


def query_places(es, index, queries):
    """Busca entidades políticas que contengan un punto dato, según
    parámetros de una o más consultas.

    Args:
        es (Elasticsearch): Cliente de Elasticsearch.
        index (str): Nombre del índice sobre el cual realizar las búsquedas.
        queries (list): Lista de conjuntos de parámetros de consultas. Ver
            la documentación de la función 'build_place_dsl_query' para más
            detalles.

    Returns:
        list: Resultados de búsqueda de entidades.

    """
    index += '-' + N.GEOM  # Utilizar índices con geometrías
    dsl_queries = (build_place_dsl_query(**query) for query in queries)
    results = run_dsl_queries(es, index, dsl_queries)

    # Ya que solo puede existir una entidad por punto (para un tipo dado
    # de entidad), modificar los resultados para que el resultado de cada
    # consulta esté compuesto de exactamente una entidad, o el valor None.
    return [
        result[0] if result else None
        for result in results
    ]


def query_streets(es, queries):
    """Busca vías de circulación según parámetros de una o más consultas.

    Args:
        es (Elasticsearch): Cliente de Elasticsearch.
        queries (list): Lista de conjuntos de parámetros de consultas. Ver
            la documentación de la función 'build_streets_dsl_query' para más
            detalles.

    Returns:
        list: Resultados de búsqueda de entidades.

    """
    dsl_queries = (build_streets_dsl_query(**query) for query in queries)
    return run_dsl_queries(es, N.STREETS, dsl_queries)


def build_entity_dsl_query(entity_id=None, name=None, state=None,
                           department=None, municipality=None, max=None,
                           order=None, fields=None, exact=False):
    """Construye una query con Elasticsearch DSL para entidades políticas
    (localidades, departamentos, o provincias) según parámetros de búsqueda
    de una consulta.

    Args:
        entity_id (str): ID de la entidad.
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

    Returns:
        dict: Query construida para Elasticsearch.

    """
    if not fields:
        fields = []

    terms = []
    sorts = {}

    if entity_id:
        condition = build_match_condition(N.ID, entity_id)
        terms.append(condition)
    if name:
        condition = build_name_condition(N.NAME, name, exact)
        terms.append(condition)
    if municipality:
        if municipality.isdigit():
            condition = build_match_condition(N.MUN_ID, municipality)
        else:
            condition = build_name_condition(N.MUN_NAME, municipality, exact)
        terms.append(condition)
    if department:
        if department.isdigit():
            condition = build_match_condition(N.DEPT_ID, department)
        else:
            condition = build_name_condition(N.DEPT_NAME, department, exact)
        terms.append(condition)
    if state:
        if state.isdigit():
            condition = build_match_condition(N.STATE_ID, state)
        else:
            condition = build_name_condition(N.STATE_NAME, state, exact)
        terms.append(condition)
    if order:
        if N.ID in order:
            sorts[N.ID] = {'order': 'asc'}

        if N.NAME in order:
            sorts[N.NAME + N.EXACT_SUFFIX] = {'order': 'asc'}

    return {
        'query': {
            'bool': {
                'must': terms
            }
        },
        'size': max or DEFAULT_MAX,
        'sort': sorts,
        '_source': {
            'include': fields,
            'exclude': [N.TIMESTAMP]
        }
    }


def build_streets_dsl_query(street_id=None, road_name=None, department=None,
                            state=None, road_type=None, max=None, fields=None,
                            exact=False, number=None, excludes=None):
    """Construye una query con Elasticsearch DSL para vías de circulación
    según parámetros de búsqueda de una consulta.

    Args:
        es (Elasticsearch): Cliente de Elasticsearch.
        street_id (str): ID de la calle a buscar.
        road_name (str): Nombre de la calle para filtrar (opcional).
        department (str): ID o nombre de departamento para filtrar (opcional).
        state (str): ID o nombre de provincia para filtrar (opcional).
        road_type (str): Nombre del tipo de camino para filtrar (opcional).
        max (int): Limita la cantidad de resultados (opcional).
        fields (list): Campos a devolver en los resultados (opcional).
        excludes (list): Campos a no incluir en los resultados (opcional).
        exact (bool): Activa búsqueda por nombres exactos. (toma efecto sólo si
            se especificaron los parámetros 'name', 'locality', 'state' o
            'department'.) (opcional).

    Returns:
        dict: Query construida para Elasticsearch.

    """
    if not fields:
        fields = []

    if not excludes:
        excludes = []

    if N.TIMESTAMP not in excludes:
        excludes.append(N.TIMESTAMP)

    terms = []
    if street_id:
        condition = build_match_condition(N.ID, street_id)
        terms.append(condition)
    if road_name:
        condition = build_name_condition(N.NAME, road_name, exact)
        terms.append(condition)
    if road_type:
        condition = build_match_condition(N.ROAD_TYPE, road_type, fuzzy=True)
        terms.append(condition)
    if number:
        terms.append(build_range_condition(N.START_R, '<=', number))
        terms.append(build_range_condition(N.END_L, '>=', number))
    if department:
        if department.isdigit():
            condition = build_match_condition(N.DEPT_ID, department)
        else:
            condition = build_name_condition(N.DEPT_NAME, department, exact)
        terms.append(condition)
    if state:
        if state.isdigit():
            condition = build_match_condition(N.STATE_ID, state)
        else:
            condition = build_name_condition(N.STATE_NAME, state, exact)
        terms.append(condition)

    return {
        'query': {
            'bool': {
                'must': terms
            }
        },
        'size': max or DEFAULT_MAX,
        '_source': {
            'include': fields,
            'exclude': excludes
        }
    }


def build_place_dsl_query(lat, lon, fields=None):
    """Construye una query con Elasticsearch DSL para entidades en una
    ubicación según parámetros de búsqueda de una consulta.

    Args:
        lat (float): Latitud del punto.
        lon (float): Longitud del punto.
        fields (list): Campos a devolver en los resultados (opcional).

    Returns:
        dict: Query construida para Elasticsearch.

    """
    if not fields:
        fields = []

    return {
        'query': {
            'bool': {
                'filter': {
                    'geo_shape': {
                        N.GEOM: {
                            'shape': {
                                'type': 'point',
                                'coordinates': [lon, lat]
                            }
                        }
                    }
                }
            }
        },
        '_source': {
            'includes': fields,
            'excludes': [N.GEOM, N.TIMESTAMP]
        },
        'size': 1
    }


def build_name_condition(field, value, exact=False):
    """Crea una condición de búsqueda por nombre para Elasticsearch.
       Las entidades con nombres son, por el momento, las provincias, los
       departamentos, los municipios, las localidades y las calles.

    Args:
        field (str): Campo de la condición.
        value (str): Valor de comparación.
        exact (bool): Activar modo de búsqueda exacta.

    Returns:
        dict: Condición para Elasticsearch.

    """
    if exact:
        field += N.EXACT_SUFFIX
        terms = [build_match_condition(field, value, False)]
    else:
        terms = [build_match_condition(field, value, True, operator='and')]
        if len(value.strip()) >= MIN_AUTOCOMPLETE_CHARS:
            terms.append(build_match_phrase_prefix_condition(field, value))

    return {
        'bool': {
            'should': terms
        }
    }


def build_match_phrase_prefix_condition(field, value):
    """Crea una condición 'Match Phrase Prefix' para Elasticsearch.

    Args:
        field (str): Campo de la condición.
        value (str): Valor de comparación.

    Returns:
        dict: Condición para Elasticsearch.

    """
    return {
        'match_phrase_prefix': {
            field: value
        }
    }


def build_range_condition(field, operator, value):
    """Crea una condición 'Range' para Elasticsearch.

    Args:
        field (str): Campo de la condición.
        value (int): Número contra el que se debería comparar el campo.
        operator (str): Operador a utilizar (>, =>, <, =<)

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

    return {
        'range': {
            field: {
                es_operator: value
            }
        }
    }


def build_match_condition(field, value, fuzzy=False, operator='or'):
    """Crea una condición 'Match' para Elasticsearch.

    Args:
        field (str): Campo de la condición.
        value (str): Valor de comparación.
        fuzzy (bool): Bandera para habilitar tolerancia a errores.
        operator (bool): Operador a utilizar para conectar clausulas 'term'

    Returns:
        dict: Condición para Elasticsearch.

    """
    query = {field: {'query': value, 'operator': operator}}
    if fuzzy:
        query[field]['fuzziness'] = 'AUTO:4,8'

    return {'match': query}


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
