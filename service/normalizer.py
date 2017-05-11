# -*- coding: utf-8 -*-
from service import parser, persistence


def process(request):
    if not parser.validate(request):
        return parser.get_response_for_invalid(request)
    if request.method == 'GET':
        return process_get(request)
    return process_post(request)


def build_results_from(addresses):
    return {
        'estado': 'OK' if addresses else 'SIN_RESULTADOS',
        'direcciones': addresses
        }


def process_get(request):
    if 'direccion' not in request.args:
        return parser.get_response_for_invalid(request,
        message='El parámetro direccion es obligatorio')
    address = request.args.get('direccion')
    matches = persistence.query(address)#(request)
    results = build_results_from(matches)
    return parser.get_response(results)


def process_post(request):
    return parser.get_response({
        'estado': 'OK',
        'direcciones': [],
        'originales': []
        })
