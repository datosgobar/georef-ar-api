# -*- coding: utf-8 -*-
import os
import requests
from elasticsearch import Elasticsearch


def query(address):
    matches = search_es(address)
    if not matches and address.get('source') == 'osm':
        matches = search_osm(address)
    return matches


def query_entity(name, index):
    fuzzy_match = {'match': {'nombre': {'query': name, 'fuzziness': 'AUTO'}}}
    query = {'query': fuzzy_match if name else {"match_all": {}}}
    result = Elasticsearch().search(index=index, body=query)
    return [hit['_source'] for hit in result['hits']['hits']]


def search_es(address):
    terms = []
    query = {'query': {'bool': {'must': terms}}, 'size': address['max'] or 10}
    road = address['road']
    number = address['number']
    terms.append(
        {'match': {'nomenclatura': {'query': road, 'fuzziness': 'AUTO'}}})
    locality = address['locality']
    state = address['state']
    if locality:
        terms.append(
            {'match': {'localidad': {'query': locality, 'fuzziness': 'AUTO'}}})
    if state:
        terms.append(
            {'match': {'provincia': {'query': state, 'fuzziness': 'AUTO'}}})
    result = Elasticsearch().search(body=query)
    addresses = [parse_es(hit) for hit in result['hits']['hits']]
    if addresses and number:
        addresses = process_door(number, addresses)
    return addresses


def search_osm(address):
    url = os.environ.get('OSM_API_URL')
    query = address['road']
    if address.get('number'):
        query += ' %s' % address['number']
    if address.get('locality'):
        query += ', %s' % address['locality']
    if address.get('state'):
        query += ', %s' % address['state']
    params = {
        'q': query,
        'format': 'json',
        'countrycodes': 'ar',
        'addressdetails': 1,
        'limit': address.get('max') or 15
    }
    result = requests.get(url, params=params).json()
    return [parse_osm(match) for match in result
            if match['class'] == 'highway' or match['type'] == 'house']


def parse_es(result):
    obs = {
        'fuente': 'INDEC',
        'info': 'Se procesó correctamente la dirección buscada.'
        }
    result['_source'].update(observaciones=obs)
    return result['_source']


def parse_osm(result):
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
    for address in addresses:
        info = address['observaciones']['info']
        st_start = address.get('altura_inicial')
        st_end = address.get('altura_final')
        if st_start and st_end:
            if st_start <= number and number <= st_end:
                parts = address['nomenclatura'].split(',')
                parts[0] += ' %s' % str(number)
                address['nomenclatura'] = ', '.join(parts)
            else:
                info = 'La altura buscada está fuera del rango conocido.'
        else:
            info = 'La calle no tiene numeración en la base de datos.'
        address['observaciones']['info'] = info
    return addresses


def parse_osm_type(osm_type):
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
