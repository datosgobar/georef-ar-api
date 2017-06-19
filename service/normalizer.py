# -*- coding: utf-8 -*-

"""Módulo 'normalizer' de georef-api

Contiene funciones que manejan la lógica de procesamiento
de los recursos que expone la API.
"""

from service import data, parser


def build_result_for(entity, matches):
    """Arma un diccionario con la lista de resultados para una entidad.

    Args:
        entity (str): Nombre de la entidad de la que se retornan resulados.
        matches (list): Lista con los resultados.

    Returns:
        dict: Resultados e información de estado asociada.
    """
    return {
        'estado': 'OK' if matches else 'SIN_RESULTADOS',
        entity: matches
        }


def process_address(request):
    """Procesa una consulta para normalizar direcciones.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de una de las funciones invocadas según el tipo de Request.
    """
    if not parser.validate(request):
        return parser.get_response_for_invalid(request)
    if request.method == 'GET':
        return address_get(request)
    return address_post(request)


def address_get(request):
    """Procesa una consulta de tipo GET para normalizar direcciones.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objecto flask.Response.
    """
    if not request.args.get('direccion'):
        return parser.get_response_for_invalid(request,
        message='El parámetro "direccion" es obligatorio.')
    search = parser.build_search_from(request.args)
    matches = data.query_address(search)
    result = build_result_for('direcciones', matches)
    return parser.get_response(result)


def address_post(request):
    """Procesa una consulta de tipo POST para normalizar direcciones.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objecto flask.Response.
    """
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
                'normalizadas': data.query_address(parsed_address)
                })
    result = build_result_for('direcciones', matches)
    return parser.get_response(result)


def process_locality(request):
    """Procesa una consulta de tipo GET para normalizar localidades.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objecto flask.Response.
    """
    name = request.args.get('nombre')
    department = request.args.get('departamento')
    state = request.args.get('provincia')
    matches = data.query_entity('localidades', name, department, state)
    result = build_result_for('localidades', matches)
    return parser.get_response(result)


def process_department(request):
    """Procesa una consulta de tipo GET para normalizar departamentos.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objecto flask.Response.
    """
    name = request.args.get('nombre')
    state = request.args.get('provincia')
    matches = data.query_entity('departamentos', name, state=state)
    result = build_result_for('departamentos', matches)
    return parser.get_response(result)


def process_state(request):
    """Procesa una consulta de tipo GET para normalizar provincias.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objecto flask.Response.
    """
    name = request.args.get('nombre')
    matches = data.query_entity('provincias', name)
    result = build_result_for('provincias', matches)
    return parser.get_response(result)
