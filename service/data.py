# -*- coding: utf-8 -*-

"""Módulo 'data' de georef-api

Contiene funciones que procesan los parámetros de búsqueda de una consulta
e impactan dicha búsqueda contra las fuentes de datos disponibles.
"""

import os
import psycopg2
import requests
from elasticsearch import Elasticsearch


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


def query_entity(index, name=None, department=None, state=None, max=None):
    """Busca entidades (localidades, departamentos, o provincias)
        según parámetros de búsqueda de una consulta.

    Args:
        index (str): Nombre del índice sobre el cual realizar la búsqueda.
        name (str): Nombre del tipo de entidad (opcional).
        department (str): ID o nombre de departamento para filtrar (opcional).
        state (str): ID o nombre de provincia para filtrar (opcional).

    Returns:
        list: Resultados de búsqueda de entidades.
    """
    terms = []
    if name:
        condition = {'nombre': {'query': name, 'fuzziness': 'AUTO'}}
        terms.append({'match': condition})
    if department:
        if department.isdigit():
            condition = {'departamento.id': department}
        else:
            condition = {'departamento.nombre': {
                    'query': department, 'fuzziness': 'AUTO'}}
        terms.append({'match': condition})
    if state:
        if state.isdigit():
            condition = {'provincia.id': state}
        else:
            condition = {'provincia.nombre': {
                    'query': state, 'fuzziness': 'AUTO'}}
        terms.append({'match': condition})
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
    terms = []
    query = {'query': {'bool': {'must': terms}}, 'size': params['max'] or 10}
    road = params['road']
    number = params['number']
    terms.append(
        {'match': {'nomenclatura': {'query': road, 'fuzziness': 'AUTO'}}})
    locality = params['locality']
    state = params['state']
    if locality:
        terms.append(
            {'match': {'localidad': {'query': locality, 'fuzziness': 'AUTO'}}})
    if state:
        terms.append(
            {'match': {'provincia': {'query': state, 'fuzziness': 'AUTO'}}})
    result = Elasticsearch().search(index='sanluis', body=query)
    addresses = [parse_es(hit) for hit in result['hits']['hits']]
    if addresses:
        addresses = process_door(number, addresses)
    return addresses


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


def parse_es(result):
    """Procesa un resultado de ElasticSearch para modificar información.

    Args:
        result (dict): Diccionario con resultado.

    Returns:
        dict: Resultados modificado.
    """
    obs = {
        'fuente': 'INDEC',
        #'info': 'Se procesó correctamente la dirección buscada.'
        }
    result['_source'].update(observaciones=obs)
    return result['_source']


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
        'altura_inicial': None,
        'altura_final': None,
        'localidad': result['address'].get('city'),
        'provincia': result['address'].get('state'),
        'observaciones': {
            'fuente': 'OSM'
            }
        }


def process_door(number, addresses):
    """Procesa direcciones para verificar el número de puerta
        y agregar información relacionada.

    Args:
        number (int or None): Número de puerta.
        addresses (list): Lista de direcciones.

    Returns:
        list: Lista de direcciones procesadas.
    """
    for address in addresses:
        if number:
            address['altura'] = None
            info = 'Se procesó correctamente la dirección buscada.'
            st_start = address.get('altura_inicial')
            st_end = address.get('altura_final')
            if st_start and st_end:
                if st_start <= number <= st_end:
                    update_result_with(address, number)
                    search_street_section_for(address, number)
                else:
                    info = 'La altura buscada está fuera del rango conocido.'
            else:
                info = 'La calle no tiene numeración en la base de datos.'
            address['observaciones']['info'] = info
        del address['altura_inicial']
        del address['altura_final']
        del address['tramos']
    return addresses


def update_result_with(address, number):
    """Agrega la altura a la dirección y a la nomenclatura.

    Args:
        address (dict): Dirección.
        number (int): Número de puerta.

    Returns:
        list: Lista de direcciones procesadas.
    """
    parts = address['nomenclatura'].split(',')
    parts[0] += ' %s' % str(number)
    address['nomenclatura'] = ', '.join(parts)
    address['altura'] = number


def search_street_section_for(address, number):
    """Procesa los tramos de calle para obtener
        las coordenadas del número de puerta.

    Args:
        address (dict): Dirección.
        number (int): Número de puerta.
    """
    for section in address.get('tramos'):
        if (section['inicio_derecha'] <= number <= section['fin_izquierda']):
            address['ubicacion'] = location(section['geometria'], number,
                section['inicio_derecha'], section['fin_izquierda'])
            del address['centroide']
            return


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
