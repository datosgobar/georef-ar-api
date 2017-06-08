# -*- coding: utf-8 -*-
from service import data, parser


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
    if not request.args.get('direccion'):
        return parser.get_response_for_invalid(request,
        message='El parámetro "direccion" es obligatorio.')
    search = parser.build_search_from(request.args)
    matches = data.query(search)
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
            parsed_address = parser.get_from_string(address)
            matches.append({
                'original': address,
                'normalizadas': data.query(parsed_address)
                })
    result = build_result_from(matches)
    return parser.get_response(result)
