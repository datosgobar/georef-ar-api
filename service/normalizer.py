# -*- coding: utf-8 -*-
from service import parser, persistence


def build_result_from(matched_addresses):
    return {
        'estado': 'OK' if matched_addresses else 'SIN_RESULTADOS',
        'direcciones': matched_addresses
        }


def process(request):
    if not parser.validate(request):
        return parser.get_response_for_invalid(request)
    if request.method == 'GET':
        return process_get(request)
    return process_post(request)


def process_get(request):
    address = request.args.get('direccion')
    if not address:
        return parser.get_response_for_invalid(request,
        message='El parámetro direccion es obligatorio')
    matches = persistence.query(address, request.args)
    result = build_result_from(matches)
    return parser.get_response(result)


def process_post(request):
    matches = []
    json_data = request.get_json()
    if json_data:
        addresses = json_data.get('direcciones')
        if not addresses:
            return parser.get_response_for_invalid(request,
            message='No hay datos de direcciones para procesar.')
        for address in addresses:
            matches.append({
                'original': address,
                'normalizadas': persistence.query(address)
                })
    result = build_result_from(matches)
    return parser.get_response(result)
