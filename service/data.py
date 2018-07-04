# -*- coding: utf-8 -*-

"""Módulo 'data' de georef-api

Contiene funciones que procesan los parámetros de búsqueda de una consulta
e impactan dicha búsqueda contra las fuentes de datos disponibles.
"""

import os
import psycopg2
import requests
from service.parser import flatten_dict
from service.names import *

MIN_AUTOCOMPLETE_CHARS = 4
DEFAULT_MAX = 10


def query_entity(es, index, entity_id=None, name=None, state=None,
                 department=None, municipality=None, max=None, order=None,
                 fields=None, flatten=False, exact=False):
    """Busca entidades políticas (localidades, departamentos, o provincias)
        según parámetros de búsqueda de una consulta.

    Args:
        es (Elasticsearch): Cliente de Elasticsearch.
        index (str): Nombre del índice sobre el cual realizar la búsqueda.
        entity_id (str): ID de la entidad.
        name (str): Nombre del tipo de entidad (opcional).
        state (str): ID o nombre de provincia para filtrar (opcional).
        department (str): ID o nombre de departamento para filtrar (opcional).
        municipality (str): ID o nombre de municipio para filtrar (opcional).
        max (int): Limita la cantidad de resultados (opcional).
        order (str): Campo por el cual ordenar los resultados (opcional).
        fields (list): Campos a devolver en los resultados (opcional).
        flatten (bool): Bandera para habilitar que el resultado sea aplanado.
        exact (bool): Activa búsqueda por nombres exactos. (toma efecto sólo si
            se especificaron los parámetros 'name', 'department',
            'municipality' o 'state'.)

    Returns:
        list: Resultados de búsqueda de entidades.
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
    query = {
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
    
    result = es.search(index=index, body=query)
    return [parse_es(hit, flatten, index) for hit in result['hits']['hits']]


def query_streets(es, name=None, department=None, state=None, road=None,
                  max=None, fields=None, exact=False, number=None):
    """Busca calles según parámetros de búsqueda de una consulta.

    Args:
        es (Elasticsearch): Cliente de Elasticsearch.
        name (str): Nombre de la calle para filtrar (opcional).
        department (str): Nombre de departamento para filtrar (opcional).
        state (str / int): ID o nombre de provincia para filtrar (opcional).
        road (str): Nombre del tipo de camino para filtrar (opcional).
        max (int): Limita la cantidad de resultados (opcional).
        fields (list): Campos a devolver en los resultados (opcional).
        exact (bool): Activa búsqueda por nombres exactos. (toma efecto sólo si
            se especificaron los parámetros 'name', 'locality', 'state' o
            'department'.)

    Returns:
        list: Resultados de búsqueda de calles.
    """
    if not fields:
        fields = []

    index = STREETS + '-*'  # Search in all indexes by default.
    terms = []
    if name:
        condition = build_name_condition(NAME, name, exact)
        terms.append(condition)
    if road:
        condition = build_match_condition(ROAD_TYPE, road, fuzzy=True)
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

    query = {
        'query': {
            'bool': {
                'must': terms
            }
        },
        'size': max or DEFAULT_MAX,
        '_source': {
            'include': fields,
            'exclude': [TIMESTAMP]
        },
    }

    result = es.search(index=index, body=query)
    return [parse_es(hit, False, index) for hit in result['hits']['hits']]


def query_address(es, search_params):
    """Busca direcciones para los parámetros de una consulta.

    Args:
        es (Elasticsearch): Cliente de Elasticsearch.
        search_params (dict): Diccionario con parámetros de búsqueda.

    Returns:
        list: Resultados de búsqueda de una dirección.
    """
    matches = search_es(es, search_params)
    if not matches and search_params.get('source') == 'osm':
        matches = search_osm(search_params)
    return matches


def query_place(es, index, lat, lon, fields=None):
    """Busca a que entidades políticas (municipios, departamentos, o provincias)
        pertenece una ubicación según parámetros de búsqueda de una consulta.

    Args:
        es (Elasticsearch): Cliente de Elasticsearch.
        index (str): Nombre del índice sobre el cual realizar la búsqueda.
        lat (str): Latitud correspondiente a una ubicación.
        lon (str): Longitud correspondiente a una ubicación.
        fields (list): Campos a incluir en los resultados.

    Returns:
        list: Resultados de búsqueda de una ubicación.
    """
    if not fields:
        fields = []

    query = {
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

    result = es.search(index=index, body=query)
    entities = result['hits']['hits']
    if entities:
        return parse_es(entities[0], False, index, add_source=False)

    return None

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
    elif index.startswith(STREETS):
        return SOURCE_INDEC
    else:
        raise ValueError(
            'No se pudo determinar la fuente de: {}'.format(index))


def parse_es(result, flatten, index, add_source=True):
    """Procesa un resultado de ElasticSearch para modificarlo.

    Args:
        result (dict): Diccionario con resultado.
        flatten (bool): Bandera para habilitar que el resultado sea aplanado.
        index (str): Índice donde el resultado fue encontrado.
        add_source (bool): Si es verdadero, agrega la fuente a los resultados.

    Returns:
        dict: Resultado modificado.
    """
    result = result['_source']
    if flatten:
        flatten_dict(result, max_depth=2)

    if add_source:
        result[SOURCE] = get_index_source(index)

    return result


def parse_osm(result):
    """Procesa un resultado de OpenStreetMap para modificar información.

    Args:
        result (dict): Diccionario con resultado.

    Returns:
        dict: Resultados modificado.
    """
    return {
        FULL_NAME: result['display_name'],
        NAME: result['address'].get('road'),
        ROAD_TYPE: parse_osm_type(result['type']),
        LOCALITY: result['address'].get('city'),
        STATE: result['address'].get('state')
    }


def parse_osm_type(osm_type):
    """Convierte un tipo de resultado de OpenStreetMap a un tipo de georef.

    Args:
        osm_type (str): Tipo de resultado de OpenStreetMap.

    Returns:
        str: Tipo de resultado de georef.
    """
    if osm_type == 'residential':
        return 'CALLE'
    elif osm_type == 'secondary':
        return 'AVENIDA'
    elif osm_type == 'motorway':
        return 'AUTOPISTA'
    elif osm_type == 'house':
        return 'CALLE_ALTURA'
    else:
        return 'SIN_CLASIFICAR'


def search_es(es, params):
    """Busca en ElasticSearch con los parámetros de una consulta.

    Args:
        es (Elasticsearch): Cliente de Elasticsearch.
        params (dict): Diccionario con parámetros de búsqueda.

    Returns:
        list: Resultados de búsqueda de una dirección.
    """
    number = params['number']
    streets = query_streets(es, name=params['road_name'],
                            road=params['road_type'],
                            state=params['state'],
                            department=params['department'],
                            fields=params['fields'], max=params['max'],
                            exact=params['exact'], number=number)

    addresses = []
    for street in streets:
        update_result_with(street, number)

        loc = location(street[GEOM], number, street[START_R], street[END_L])

        if not loc:
            street[LOCATION] = {LAT: None, LON: None}
        else:
            street[LOCATION] = loc

        remove_spatial_data_from(street)
        if params['flatten']:
            flatten_dict(street)

        addresses.append(street)

    return addresses


def search_osm(params):
    """Busca en OpenStreetMap para los parámetros de una consulta.

    Args:
        params (dict): Diccionario con parámetros de búsqueda.

    Returns:
        list: Resultados de búsqueda de una dirección.
    """
    url = os.environ.get('OSM_API_URL')
    query = params['road_name']
    if params.get('number'):
        query += ' %s' % params['number']
    if params.get('locality'):
        query += ', %s' % params['locality']
    if params.get('state'):
        query += ', %s' % params['state']

    params = {
        'q': query,
        'format': 'json',
        'countrycodes': 'ar',
        'addressdetails': 1,
        'limit': params.get('max') or 15
    }
    try:
        result = requests.get(url, params=params).json()
    except requests.RequestException as error:
        return []

    return [parse_osm(match) for match in result
            if match['class'] == 'highway' or match['type'] == 'house']


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
