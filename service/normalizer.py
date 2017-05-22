# -*- coding: utf-8 -*-
from service import parser, persistence


def build_dict_from(row):
    full_address = ' '.join(row[:2]) + ', ' + ', '.join(row[4:])
    return {
        'descripcion': full_address,
        'tipo': row[0],
        'nombre': row[1],
        'altura_inicial': row[2],
        'altura_final': row[3],
        'localidad': row[4],
        'provincia': row[5]
    }


def build_results_from(matched_addresses, addresses=None):
    results = {
        'estado': 'OK' if matched_addresses else 'SIN_RESULTADOS',
        'direcciones': [build_dict_from(row) for row in matched_addresses]
        }
    if addresses:
        results.update(originales=[{'nombre': addr} for addr in addresses])
    return results


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
    results = build_results_from(matches)
    return parser.get_response(results)


def process_post(request):
    matches = []
    json_data = request.get_json()
    if json_data:
        addresses = json_data.get('direcciones')
        if not addresses:
            return parser.get_response_for_invalid(request,
            message='No hay datos de direcciones para procesar.')
        for address in addresses:
            matches.extend(persistence.query(address))
    results = build_results_from(matches, addresses)
    return parser.get_response(results)
