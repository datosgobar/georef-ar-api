# -*- coding: utf-8 -*-

"""Módulo 'data' de georef-api

Contiene funciones que procesan los parámetros de búsqueda de una consulta
e impactan dicha búsqueda contra las fuentes de datos disponibles.
"""

import os
import psycopg2
from service.parser import flatten_dict
from service.names import *

MIN_AUTOCOMPLETE_CHARS = 4
DEFAULT_MAX = 10


def run_queries(es, index, queries):
    """TODO: Docs
    """
    body = []
    for query in queries:
        # No es necesario especificar el índice por
        # query ya que se ejecutan todas en el mismo
        # índice.
        body.append({})
        body.append(query)

    results = es.msearch(body=body, index=index)

    responses = []
    for response in results['responses']:
        hits = [hit['_source'] for hit in response['hits']['hits']]
        responses.append(hits)

    return responses


def query_entities(es, index, params_list):
    """Busca entidades políticas (localidades, departamentos, o provincias)
    según parámetros de una o más consultas.

    Args:
        es (Elasticsearch): Cliente de Elasticsearch.
        index (str): Nombre del índice sobre el cual realizar las búsquedas.
        params_list (list): Lista de conjuntos de parámetros de consultas. Ver
            la documentación de la función 'build_entity_query' para más
            detalles.

    Returns:
        list: Resultados de búsqueda de entidades.
    """

    queries = (build_entity_query(**params) for params in params_list)
    return run_queries(es, index, queries)


def query_streets(es, params_list):
    """Busca vías de circulación según parámetros de una o más consultas.

    Args:
        es (Elasticsearch): Cliente de Elasticsearch.
        params_list (list): Lista de conjuntos de parámetros de consultas. Ver
            la documentación de la función 'build_streets_query' para más
            detalles.

    Returns:
        list: Resultados de búsqueda de entidades.
    """

    queries = (build_streets_query(**params) for params in params_list)
    return run_queries(es, STREETS, queries)


def query_places(es, index, params_list):
    """Busca entidades políticas que contengan un punto dato, según
    parámetros de una o más consultas.

    Args:
        es (Elasticsearch): Cliente de Elasticsearch.
        index (str): Nombre del índice sobre el cual realizar las búsquedas.
        params_list (list): Lista de conjuntos de parámetros de consultas. Ver
            la documentación de la función 'build_places_query' para más
            detalles.

    Returns:
        list: Resultados de búsqueda de entidades.
    """

    index += '-' + GEOM # Utilizar índices con geometrías
    queries = (build_places_query(**params) for params in params_list)
    results = run_queries(es, index, queries)

    # Ya que solo puede existir una entidad por punto (para un tipo dado
    # de entidad), modificar los resultados para que el resultado de cada
    # consulta esté compuesto de exactamente una entidad, o el valor None.
    return [
        result[0] if result else None
        for result in results
    ]


def build_entity_query(entity_id=None, name=None, state=None,
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
        condition = build_match_condition(ID, entity_id)
        terms.append(condition)
    if name:
        condition = build_name_condition(NAME, name, exact)
        terms.append(condition)
    if municipality:
        if municipality.isdigit():
            condition = build_match_condition(MUN_ID, municipality)
        else:
            condition = build_name_condition(MUN_NAME, municipality, exact)
        terms.append(condition)
    if department:
        if department.isdigit():
            condition = build_match_condition(DEPT_ID, department)
        else:
            condition = build_name_condition(DEPT_NAME, department, exact)
        terms.append(condition)
    if state:
        if state.isdigit():
            condition = build_match_condition(STATE_ID, state)
        else:
            condition = build_name_condition(STATE_NAME, state, exact)
        terms.append(condition)
    if order:
        if ID in order: sorts[ID] = {'order': 'asc'}
        if NAME in order: sorts[NAME + EXACT_SUFFIX] = {'order': 'asc'}

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
            'exclude': [TIMESTAMP]
        }
    }


def build_streets_query(road_name=None, department=None, state=None, road_type=None,
                        max=None, fields=None, exact=False, number=None):
    """Construye una query con Elasticsearch DSL para vías de circulación
    según parámetros de búsqueda de una consulta.

    Args:
        es (Elasticsearch): Cliente de Elasticsearch.
        road_name (str): Nombre de la calle para filtrar (opcional).
        department (str): ID o nombre de departamento para filtrar (opcional).
        state (str): ID o nombre de provincia para filtrar (opcional).
        road_type (str): Nombre del tipo de camino para filtrar (opcional).
        max (int): Limita la cantidad de resultados (opcional).
        fields (list): Campos a devolver en los resultados (opcional).
        exact (bool): Activa búsqueda por nombres exactos. (toma efecto sólo si
            se especificaron los parámetros 'name', 'locality', 'state' o
            'department'.) (opcional).

    Returns:
        dict: Query construida para Elasticsearch.
    """
    if not fields:
        fields = []

    terms = []
    if road_name:
        condition = build_name_condition(NAME, road_name, exact)
        terms.append(condition)
    if road_type:
        condition = build_match_condition(ROAD_TYPE, road_type, fuzzy=True)
        terms.append(condition)
    if number:
        terms.append(build_range_condition(START_R, '<=', number))
        terms.append(build_range_condition(END_L, '>=', number))
    if department:
        if department.isdigit():
            condition = build_match_condition(DEPT_ID, department)
        else:
            condition = build_name_condition(DEPT_NAME, department, exact)
        terms.append(condition)
    if state:
        if state.isdigit():
            condition = build_match_condition(STATE_ID, state)
        else:
            condition = build_name_condition(STATE_NAME, state, exact)
        terms.append(condition)

    if LOCATION in fields:
        fields.extend([GEOM, START_R, START_L, END_R, END_L])

    return {
        'query': {
            'bool': {
                'must': terms
            }
        },
        'size': max or DEFAULT_MAX,
        '_source': {
            'include': fields,
            'exclude': [TIMESTAMP]
        }
    }


def build_places_query(lat, lon, fields=None):
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
                        GEOM: {
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
            'excludes': [GEOM, TIMESTAMP]
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
        field += EXACT_SUFFIX
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


def get_index_source(index):
    """Devuelve la fuente para un índice dado.

    Args:
        index (str): Nombre del índice.
    """
    if index in [STATES, DEPARTMENTS, MUNICIPALITIES]:
        return SOURCE_IGN
    elif index == SETTLEMENTS:
        return SOURCE_BAHRA
    elif index == STREETS:
        return SOURCE_INDEC
    else:
        raise ValueError(
            'No se pudo determinar la fuente de: {}'.format(index))


def query_address(es, params): # TODO: Combinar con query_streets
    """Busca en ElasticSearch con los parámetros de una consulta.

    Args:
        es (Elasticsearch): Cliente de Elasticsearch.
        params (dict): Diccionario con parámetros de búsqueda.

    Returns:
        list: Resultados de búsqueda de una dirección.
    """
    number = params['number']
    streets = query_streets(es, [params])[0]

    addresses = []
    for street in streets:
        update_result_with(street, number)

        loc = location(street[GEOM], number, street[START_R], street[END_L])

        if not loc:
            street[LOCATION] = {LAT: None, LON: None}
        else:
            street[LOCATION] = loc

        remove_spatial_data_from(street)
        # if params['flatten']:
        #     flatten_dict(street, max_depth=2)

        addresses.append(street)

    return addresses


def update_result_with(address, number):
    """Agrega la altura a la dirección y a la nomenclatura.

    Args:
        address (dict): Dirección.
        number (int): Número de puerta o altura.
    """
    if FULL_NAME in address:
        parts = address[FULL_NAME].split(',')
        parts[0] += ' %s' % str(number)
        address[FULL_NAME] = ','.join(parts)
    address[DOOR_NUM] = number


def remove_spatial_data_from(address):
    """Remueve los campos de límites y geometría de una dirección procesada.

    Args:
        address (dict): Dirección.
    """
    address.pop(START_R, None)
    address.pop(START_L, None)
    address.pop(END_R, None)
    address.pop(END_L, None)
    address.pop(GEOM, None)


def get_db_connection():
    """Se conecta a una base de datos especificada en variables de entorno.

    Returns:
        connection: Conexión a base de datos.
    """
    return psycopg2.connect(host=os.environ.get('GEOREF_API_DB_HOST'),
                            dbname=os.environ.get('GEOREF_API_DB_NAME'),
                            user=os.environ.get('GEOREF_API_DB_USER'),
                            password=os.environ.get('GEOREF_API_DB_PASS'))


def location(geom, number, start, end):
    """Obtiene las coordenadas de un punto dentro de un tramo de calle.

    Args:
        geom (str): Geometría de un tramo de calle.
        number (int or None): Número de puerta o altura.
        start (int): Numeración inicial del tramo de calle.
        end (int): Numeración final del tramo de calle.

    Returns:
        dict: Coordenadas del punto.
    """
    if not number:
        return None

    args = geom, number, start, end
    query = """SELECT geocodificar('%s', %s, %s, %s);""" % args
    connection = get_db_connection()

    with connection.cursor() as cursor:
        cursor.execute(query)
        location = cursor.fetchall()[0][0]  # Query returns single row and col.
    if location['code']:
        lat, lon = location['result'].split(',')
        return {LAT: lat, LON: lon}

    return None
