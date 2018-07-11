# -*- coding: utf-8 -*-

"""Módulo 'parser' de georef-api

Contiene funciones que manipulan los distintos objetos
con los que operan los módulos de la API.
"""

from flask import jsonify, make_response, request, Response
from geojson import Feature, FeatureCollection, Point, Polygon
from service.names import *
from service import params
import os


DEFAULT_MAX_FMT = 10000

REQUEST_INVALID = {
    'codigo': 400,
    'error': {
        'codigo_interno': None,
        'mensaje': WRONG_QUERY,
        'info': 'https://github.com/datosgobar/georef-api'
    }
}


def get_url_rule(request):
    """Analiza la URL y devuelve un diccionario con el formato solicitado.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        (bool, dict, str): Si una consulta es válida o no, un diccionario con
        los valores del formato solicitado y un mensaje si hay error.
    """
    format_request = {'convert': True, 'max': DEFAULT_MAX_FMT, 'type': 'json'}
    path = str(request.url_rule)
    rule = os.path.split(path)
    endpoint = rule[1]  # request endpoint

    if '.' in endpoint:
        if len(request.args) > 0:
            return False, '', WRONG_QUERY
        if '.csv' in endpoint:
            format_request['type'] = 'csv'
        elif '.geojson' in endpoint:
            format_request['type'] = 'geojson'
        else:
            format_request['convert'] = False
    else:
        if request.args.get(FORMAT):
            if request.args.get(FORMAT) == 'csv':
                format_request['type'] = 'csv'
            elif request.args.get(FORMAT) == 'geojson':
                format_request['type'] = 'geojson'
            elif request.args.get(FORMAT) != 'json':
                return False, '', WRONG_QUERY
        else:
            format_request['convert'] = False
            format_request['max'] = request.args.get(MAX)
    return True, format_request, ''



def get_response(result, format_request=None):
    """Genera una respuesta de la API.

    Args:
        result (dict): Diccionario con resultados de una consulta.
        format_request (dict): Diccionario con los valores del formato.

    Returns:
        flask.Response: Respuesta de la API en formato CSV o JSON
    """
    if not format_request:
        format_request = {}

    if 'type' in format_request and format_request['type'] == 'csv':
        entity = [row for row in result.keys()]
        headers = {'Content-Disposition': 'attachment; '
                                          'filename=' + entity[0] + '.csv'}
        return Response(generate_csv(result), mimetype='text/csv',
                        headers=headers)
    elif 'type' in format_request and format_request['type'] == 'geojson':
        features = []
        for key, _ in result.items():
            for entity in result[key]:
                properties = dict(entity)
                point = None
                if 'lat' and 'lon' in entity.keys():
                    properties.pop('lat')
                    properties.pop('lon')
                    point = Point((float(entity['lat']), float(entity['lon'])))
                features.append(Feature(
                    geometry=point,
                    properties=properties
                ))
            return jsonify(FeatureCollection(features))
    else:
        return make_response(jsonify(result), 200)

def generate_csv(result):
    """ Generar datos en formato CSV

    Args:
        result (dict): Diccionario con resultados de una consulta.
    """
    first = True
    for key, rows in result.items():
        for row in rows:
            if first:
                yield ';'.join(dict(row).keys()) + '\n'
            yield ';'.join(str(v) for v in dict(row).values()) + '\n'
            first = False

