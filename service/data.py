# -*- coding: utf-8 -*-

"""Módulo 'data' de georef-api

Contiene funciones que procesan los parámetros de búsqueda de una consulta
e impactan dicha búsqueda contra las fuentes de datos disponibles.
"""

import os
import psycopg2
import requests
from collections import defaultdict
from elasticsearch import Elasticsearch, ElasticsearchException
from service.parser import get_abbreviated, get_flatten_result
from service.names import *


def query_entity(index, entity_id=None, name=None, department=None, state=None,
                 max=None, order=None, fields=[], flatten=False):
    """Busca entidades políticas (localidades, departamentos, o provincias)
        según parámetros de búsqueda de una consulta.

    Args:
        index (str): Nombre del índice sobre el cual realizar la búsqueda.
        entity_id (int): ID de la entidad.
        name (str): Nombre del tipo de entidad (opcional).
        department (str): ID o nombre de departamento para filtrar (opcional).
        state (str): ID o nombre de provincia para filtrar (opcional).
        max (int): Limita la cantidad de resultados (opcional).
        order (str): Campo por el cual ordenar los resultados (opcional).
        fields (list): Campos a devolver en los resultados (opcional).
        flatten (bool): Bandera para habilitar que el resultado sea aplanado.

    Returns:
        list: Resultados de búsqueda de entidades.
    """
    fields_excludes = ['geometry']
    terms = []
    sorts = {}
    if entity_id:
        condition = build_condition(ID, entity_id)
        terms.append(condition)
    if name:
        condition = build_condition(NAME, name, fuzzy=True)
        terms.append(condition)
    if department:
        if department.isdigit():
            condition = build_condition(DEPT_ID, department)
        else:
            condition = build_condition(DEPT_NAME, department, fuzzy=True)
        terms.append(condition)
    if state:
        if state.isdigit():
            condition = build_condition(STATE_ID, state)
        else:
            condition = build_condition(STATE_NAME, state, fuzzy=True)
        terms.append(condition)
    if order:
        if ID in order: sorts[ID_KEYWORD] = {'order': 'asc'}
        if NAME in order: sorts[NAME_KEYWORD] = {'order': 'asc'}
    query = {'query': {'bool': {'must': terms}} if terms else {"match_all": {}},
             'size': max or 10, 'sort': sorts, '_source': {
                                                    'include': fields,
                                                    'excludes': fields_excludes
        }}
    try:
        result = Elasticsearch().search(index=index, body=query)
    except ElasticsearchException as error:
        return []

    return [parse_entity(hit, flatten) for hit in result['hits']['hits']]


def query_streets(name=None, locality=None, department=None, state=None,
                  road=None, max=None, fields=[]):
    """Busca calles según parámetros de búsqueda de una consulta.

    Args:
        name (str): Nombre de la calle para filtrar (opcional).
        locality (str): Nombre de la localidad para filtrar (opcional).
        department (str): Nombre de departamento para filtrar (opcional).
        state (str): ID o nombre de provincia para filtrar (opcional).
        road (str): Nombre del tipo de camino para filtrar (opcional).
        max (int): Limita la cantidad de resultados (opcional).
        fields (list): Campos a devolver en los resultados (opcional).

    Returns:
        list: Resultados de búsqueda de calles.
    """
    index = STREETS + '-*'  # Search in all indexes by default.
    terms = []
    if name:
        condition = build_condition(NAME, get_abbreviated(name), fuzzy=True)
        terms.append(condition)
    if road:
        condition = build_condition(ROAD_TYPE, road, fuzzy=True)
        terms.append(condition)
    if locality:
        condition = build_condition(LOCALITY, locality, fuzzy=True)
        terms.append(condition)
    if department:
        condition = build_condition(DEPT, department, fuzzy=True)
        terms.append(condition)
    if state:
        if state.isdigit():
            target_state = query_entity(STATES, entity_id=state, max=1)
        else:
            target_state = query_entity(STATES, name=state, max=1)

        if target_state:  # Narrows search to specific index.
            index = '-'.join([STREETS, target_state[0][ID]])
    if LOCATION in fields:
        fields.extend([GEOM, START_R, START_L, END_R, END_L, FULL_NAME])

    query = {'query': {'bool': {'must': terms}} if terms else {"match_all": {}},
             'size': max or 10, '_source': fields}
    try:
        result = Elasticsearch().search(index=index, body=query)
    except ElasticsearchException as error:
        return []

    return [parse_es(hit) for hit in result['hits']['hits']]


def query_address(search_params):
    """Busca direcciones para los parámetros de una consulta.

    Args:
        search_params (dict): Diccionario con parámetros de búsqueda.

    Returns:
        list: Resultados de búsqueda de una dirección.
    """
    matches = search_es(search_params)
    if not matches and search_params.get('source') == 'osm':
        matches = search_osm(search_params)
    return matches


def query_place(index, lat, lon, flatten=False):
    """Busca a que entidades políticas (municipios, departamentos, o provincias)
        pertenece una ubicación según parámetros de búsqueda de una consulta.

    Args:
        index (str): Nombre del índice sobre el cual realizar la búsqueda.
        lat (str): Latitud correspondiente a una ubicación.
        lon (str): Longitud correspondiente a una ubicación.
        flatten (bool): Bandera para habilitar que el resultado sea aplanado.

    Returns:
        list: Resultados de búsqueda de una ubicación.
    """
    query = {'query': {'bool': {'must': {'match_all': {}},
                                'filter': {'geo_shape': {'geometry': {'shape': {
                                        'type': 'point',
                                        'coordinates': [lon, lat]
                                    }}}}}},
             '_source': {'excludes': ['geometry']}}
    try:
        result = Elasticsearch().search(index=index, body=query)
    except ElasticsearchException as error:
        return []

    return [parse_place(hit, index, flatten) for hit in result['hits']['hits']]


def build_condition(field, value, kind='match', fuzzy=False):
    """Crea una condición para Elasticsearch.

    Args:
        field (str): Campo de la condición.
        value (str): Valor de comparación.
        fuzzy (bool): Bandera para habilitar tolerancia a errores.
        kind (str): Valor de tipo de coincidencia.
    Returns:
        dict: Condición para Elasticsearch.
    """
    if fuzzy and kind == 'match':
        query = {field: {'query': value, 'fuzziness': 1}}
    else:
        query = {field: value}
    return {kind: query}


def parse_entity(result, flatten):
    """Procesa un resultado de ElasticSearch para modificarlo.

    Args:
        result (dict): Diccionario con resultado.
        flatten (bool): Bandera para habilitar que el resultado sea aplanado.

    Returns:
        dict: Resultado modificado.
    """
    entity = result['_source']
    if flatten:
        get_flatten_result(entity)
    return entity


def parse_es(result):
    """Procesa un resultado de ElasticSearch para modificarlo.

    Args:
        result (dict): Diccionario con resultado.

    Returns:
        dict: Resultado modificado.
    """
    result = result['_source']
    obs = {SOURCE: 'INDEC'}
    result[OBS] = obs
    result.pop(POSTAL_CODE, None)
    return result


def parse_place(result, index, flatten):
    """Procesa un resultado de ElasticSearch para modificarlo.

    Args:
        result (dict): Diccionario con resultado.
        index (str): Nombre del índice sobre el cual se realizó la búsqueda.
        flatten (bool): Bandera para habilitar que el resultado sea aplanado.

    Returns:
        dict: Resultado modificado.
    """
    result = result['_source']
    result = dict(result)
    if index == MUNICIPALITIES:
        add = {'municipalidad': {'id': result[ID], 'nombre': result[NAME]}}
    else:
        add = {'departamento': {'id': result[ID], 'nombre': result[NAME]}}

    result.update(add)
    result.pop(ID)
    result.pop(NAME)

    if flatten:
        get_flatten_result(result)

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
        STATE: result['address'].get('state'),
        OBS: {SOURCE: 'OSM'}
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


def process_door(number, street):
    """Procesa una calle para verificar el número de puerta
       y agregar información relacionada.

    Args:
        number (int): Número de puerta o altura.
        street (dict): Calle a procesar.

    Returns:
        dict: Calle procesada con información de altura.
    """
    if number:
        street[DOOR_NUM] = None
        info = ADDRESS_PROCESSED_OK
        street_start = street.get(START_R)
        street_end = street.get(END_L)

        if street_start or street_end:
            if street_start == street_end:
                info = CANNOT_INTERPOLATE_ADDRESS
            elif number < street_start or number > street_end:
                info = ADDRESS_OUT_OF_RANGE
            else:
                search_location_for(street, number)
                update_result_with(street, number)
                if street[LOCATION] is None:
                    street.pop(LOCATION, None)
                    info = CANNOT_GEOCODE_ADDRESS
        else:
            info = UNKNOWN_STREET_RANGE
        street[OBS][INFO] = info

    remove_spatial_data_from(street)
    return street


def search_es(params):
    """Busca en ElasticSearch con los parámetros de una consulta.

    Args:
        params (dict): Diccionario con parámetros de búsqueda.

    Returns:
        list: Resultados de búsqueda de una dirección.
    """
    number = params['number']
    streets = query_streets(name=params['road_name'], road=params['road_type'],
                            locality=params['locality'], state=params['state'],
                            department=params['department'],
                            fields=params['fields'], max=params['max'])
    addresses = []
    for street in streets:
        address = process_door(number, street)
        if address.get(DOOR_NUM):
            addresses.append(address)

    return addresses


def search_location_for(address, number):
    """Procesa los tramos de calle para obtener
        las coordenadas del número de puerta.

    Args:
        address (dict): Dirección.
        number (int): Número de puerta o altura.
    """
    if address.get(GEOM):
        address[LOCATION] = location(address[GEOM], number,
                                     address[START_R], address[END_L])


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


def save_address(search, user=None):
    """Guarda información de una búsqueda."""
    search_data = {
        'search_text': search['text'],
        'road_type': search['road_type'],
        'road_name': search['road_name'],
        'door_number': search['number'],
        'locality': search['locality'],
        'state': search['state']
    }
    url = os.environ.get('GEOREF_URL') + 'save_address_search'
    try:
        response = requests.post(url, data=search_data)
    except requests.exceptions.RequestException:
        pass
