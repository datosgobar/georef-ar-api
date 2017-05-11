# -*- coding: utf-8 -*-
from flask import jsonify, make_response, request


REQUEST_INVALID = {
    'codigo': 400,
    'estado': 'INVALIDO',
    'error': 'El parámetro direccion es obligatorio'
    }


def validate(request):
    return 'direccion' in request.args

def get_response(result):
    return make_response(jsonify(result), 200)

def get_response_for_invalid(request):
    return make_response(jsonify(REQUEST_INVALID), 400)
