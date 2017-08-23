# -*- coding: utf-8 -*-

"""Módulo 'data' de georef-api

Contiene funciones que procesan los parámetros de búsqueda de una consulta
e impactan dicha búsqueda contra las fuentes de datos disponibles.
"""

import os
import psycopg2
import requests
from elasticsearch import Elasticsearch
from service.parser import get_abbreviated


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


def query_streets(name=None, locality=None, state=None, road=None, max=None):
    """Busca calles según parámetros de búsqueda de una consulta.

    Args:
        name (str): Nombre de la calle para filtrar (opcional).
        locality (str): Nombre de la localidad para filtrar (opcional).
        department (str): ID o nombre de departamento para filtrar (opcional).
        state (str): ID o nombre de provincia para filtrar (opcional).
        road_type (str): Nombre del tipo de camino para filtrar (opcional).
        max (int): Limita la cantidad de resultados (opcional)

    Returns:
        list: Resultados de búsqueda de calles.
    """
    terms = []
    if name:
        condition = build_condition('nombre', get_abbreviated(name), fuzzy=True)
        terms.append(condition)
    if locality:
        condition = build_condition('localidad', locality, fuzzy=True)
        terms.append(condition)
    if state:
        condition = build_condition('provincia', state, fuzzy=True)
        terms.append(condition)
    if road:
        condition = build_condition('tipo', road, fuzzy=True)
        terms.append(condition)
    query = {'query': {'bool': {'must': terms}} if terms else {"match_all": {}},
             'size': max or 10}
    result = Elasticsearch().search(doc_type='calle', body=query)
    return [parse_es(hit) for hit in result['hits']['hits']]


def query_entity(index, name=None, department=None, state=None, max=None):
    """Busca entidades políticas (localidades, departamentos, o provincias)
        según parámetros de búsqueda de una consulta.

    Args:
        index (str): Nombre del índice sobre el cual realizar la búsqueda.
        name (str): Nombre del tipo de entidad (opcional).
        department (str): ID o nombre de departamento para filtrar (opcional).
        state (str): ID o nombre de provincia para filtrar (opcional).
        max (int): Limita la cantidad de resultados (opcional)

    Returns:
        list: Resultados de búsqueda de entidades.
    """
    terms = []
    if name:
        condition = build_condition('nombre', name, fuzzy=True)
        terms.append(condition)
    if department:
        if department.isdigit():
            condition = build_condition('departamento.id', department)
        else:
            condition = build_condition(
                'departamento.nombre', department, fuzzy=True)
        terms.append(condition)
    if state:
        if state.isdigit():
            condition = build_condition('provincia.id', state)
        else:
            condition = build_condition(
                'provincia.nombre', state, fuzzy=True)
        terms.append(condition)
    query = {'query': {'bool': {'must': terms}} if terms else {"match_all": {}},
             'size': max or 10}
    result = Elasticsearch().search(index=index, body=query)
    return [hit['_source'] for hit in result['hits']['hits']]


def search_es(params):
    """Busca en ElasticSearch para los parámetros de una consulta.

    Args:
        params (dict): Diccionario con parámetros de búsqueda.

    Returns:
        list: Resultados de búsqueda de una dirección.
    """
    road_name = params['road_name']
    road_type = params['road_type']
    number = params['number']
    locality = params['locality']
    state = params['state']
    max = params['max']
    addresses = query_streets(road_name, locality, state, road_type, max)
    if addresses:
        addresses = process_door(number, addresses)
    return addresses


def build_condition(field, value, fuzzy=False):
    """Crea una condición para Elasticsearch.

    Args:
        field (str): Campo de la condición.
        value (str): Valor de comparación.
        fuzzy (bool): Bandera para habilitar tolerancia a errores.

    Returns:
        dict: Condición para Elasticsearch.
    """
    if fuzzy:
        query = {field: {'query': value, 'fuzziness': 1}}
    else:
        query = {field: value}
    return {'match': query}


def parse_es(result):
    """Procesa un resultado de ElasticSearch para modificar información.

    Args:
        result (dict): Diccionario con resultado.

    Returns:
        dict: Resultados modificado.
    """
    obs = {'fuente': 'INDEC'}
    result['_source'].update(observaciones=obs)
    return result['_source']


def process_door(number, addresses):
    """Procesa direcciones para verificar el número de puerta
        y agregar información relacionada.

    Args:
        number (int or None): Número de puerta o altura.
        addresses (list): Lista de direcciones.

    Returns:
        list: Lista de direcciones procesadas.
    """
    for address in addresses:
        if number:
            address['altura'] = None
            info = 'Se procesó correctamente la dirección buscada.'
            street_start = address.get('inicio_derecha')
            street_end = address.get('fin_izquierda')
            if street_start and street_end:
                if street_start <= number <= street_end:
                    search_location_for(address, number)
                    update_result_with(address, number)
                else:
                    info = 'La altura buscada está fuera del rango conocido.'
            else:
                info = 'La calle no tiene numeración en la base de datos.'
            address['observaciones']['info'] = info
        remove_spatial_data_from(address)
    return addresses


def search_location_for(address, number):
    """Procesa los tramos de calle para obtener
        las coordenadas del número de puerta.

    Args:
        address (dict): Dirección.
        number (int): Número de puerta o altura.
    """
    if address.get('geometria'):
        address['ubicacion'] = location(
            address['geometria'], number,
            address['inicio_derecha'], address['fin_izquierda'])


def update_result_with(address, number):
    """Agrega la altura a la dirección y a la nomenclatura.

    Args:
        address (dict): Dirección.
        number (int): Número de puerta o altura.
    """
    parts = address['nomenclatura'].split(',')
    parts[0] += ' %s' % str(number)
    address['nomenclatura'] = ','.join(parts)
    address['altura'] = number


def remove_spatial_data_from(address):
    """Remueve los campos de límites y geometría de una dirección procesada.

    Args:
        address (dict): Dirección.
    """
    address.pop('inicio_derecha', None)
    address.pop('inicio_izquierda', None)
    address.pop('fin_derecha', None)
    address.pop('fin_izquierda', None)
    if address.get('ubicacion'):
        address.pop('centroide', None)


def search_osm(params):
    """Busca en OpenStreetMap para los parámetros de una consulta.

    Args:
        params (dict): Diccionario con parámetros de búsqueda.

    Returns:
        list: Resultados de búsqueda de una dirección.
    """
    url = os.environ.get('OSM_API_URL')
    query = params['road']
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
    result = requests.get(url, params=params).json()
    return [parse_osm(match) for match in result
            if match['class'] == 'highway' or match['type'] == 'house']


def parse_osm(result):
    """Procesa un resultado de OpenStreetMap para modificar información.

    Args:
        result (dict): Diccionario con resultado.

    Returns:
        dict: Resultados modificado.
    """
    return {
        'nomenclatura': result['display_name'],
        'nombre': result['address'].get('road'),
        'tipo': parse_osm_type(result['type']),
        'localidad': result['address'].get('city'),
        'provincia': result['address'].get('state'),
        'observaciones': {'fuente': 'OSM'}
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
        location = cursor.fetchall()[0][0] # Query returns single row and col.
    lat, lon = location.split(',')
    return {'lat': lat, 'lon': lon}


def get_db_connection():
    """Se conecta a una base de datos especificada en variables de entorno.

    Returns:
        connection: Conexión a base de datos.
    """
    return psycopg2.connect(
        dbname=os.environ.get('POSTGRES_DBNAME'),
        user=os.environ.get('POSTGRES_USER'),
        password=os.environ.get('POSTGRES_PASSWORD'))


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
