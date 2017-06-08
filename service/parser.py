# -*- coding: utf-8 -*-
from flask import jsonify, make_response, request
import re


REQUEST_INVALID = {
    'codigo': 400,
    'estado': 'INVALIDO',
    'error': {
        'codigo_interno': None,
        'causa': 'El Request tiene parámetros inválidos o está incompleto.',
        'mensaje': 'El Request tiene parámetros inválidos o está incompleto.',
        'info': 'https://github.com/datosgobar/georef-api'
        }
    }


def validate(request):
    return True # pending until API keys are implemented.


def get_from_string(address_str):
    return build_search_from({'direccion': address_str})


def build_search_from(params):
    address = params.get('direccion').split(',')
    road, number = get_road_and_number(address[0].strip())
    locality = params.get('localidad')
    state = params.get('provincia')
    if len(address) > 1:
        locality = address[1].strip()
    return {
        'number': number,
        'road': road,
        'locality': locality,
        'state': state   
    }


def get_road_and_number(address):
    match = re.search(r'(\s[0-9]+?)$', address)
    number = int(match.group(1)) if match else None
    address = re.sub(r'(\s[0-9]+?)$', r'', address)
    return address.strip(), number


def get_response(result):
    return make_response(jsonify(result), 200)


def get_response_for_invalid(request, message=None):
    if message is not None:
        REQUEST_INVALID['error']['mensaje'] = message
    return make_response(jsonify(REQUEST_INVALID), 400)
