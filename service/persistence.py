# -*- coding: utf-8 -*-
import os
import re
import requests
import json
from elasticsearch import Elasticsearch


def query(address, params=None):
    es = Elasticsearch()
    query = {'query': {'bool': {'must': []}}}
    terms = query['query']['bool']['must']
    road, _ = get_parts_from(address.split(',')[0])
    terms.append({'match_phrase_prefix': {'nomenclatura': road}})
    if params and (len(params)) > 1:
        locality = params.get('localidad')
        state = params.get('provincia')
        if locality:
            terms.append({'match': {'localidad': locality}})
        if state:
            terms.append({'match': {'provincia': state}})

    results = es.search(body=query)
    if results['hits']['total'] != 0:
        return [address['_source'] for address in results['hits']['hits']]
    else:
        url = 'http://nominatim.openstreetmap.org/search'
        params = {'q': address, 'format': 'json', 'countrycodes': 'ar', 'addressdetails': 1, 'limit': 10}
        results_osm = requests.get(url, params=params).json()
        return [build_dict_osm(res) for res in results_osm]


def build_dict_from(address, row):
    road = ' '.join(row[:2])
    place = ', '.join(row[4:])
    _, number = get_parts_from(address.split(',')[0])
    obs = 'Se procesó correctamente la dirección buscada.'
    if number and row[2] and row[3]:    # validates door number.
        if row[2] <= number and number <= row[3]:
            road += ' %s' % str(number)
        else:
            obs = 'La altura buscada está fuera del rango conocido.'
    elif number and not (row[2] or row[3]):
        obs = 'La calle no tiene numeración en la base de datos.'
    full_address = ', '.join([road, place])
    return {
        'nomenclatura': full_address,
        'tipo': row[0],
        'nombre': row[1],
        'altura_inicial': row[2],
        'altura_final': row[3],
        'localidad': row[4],
        'provincia': row[5],
        'observaciones': obs
    }


def get_parts_from(address):
    match = re.search(r'(\s[0-9]+?)$', address)
    number = int(match.group(1)) if match else None
    address = re.sub(r'(\s[0-9]+?)$', r'', address)
    return address.strip(), number


def build_dict_osm(res):
    address = {
       'nomenclatura': res['display_name'],
       'tipo': res['type'],
       'nombre': res['address']['road'],
       'localidad': '' if 'city' not in res['address'] else res['address']['city'],
       'provincia': res['address']['state'],
       'observaciones': ''
    }
    return address
