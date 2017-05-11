# -*- coding: utf-8 -*-
from flask import jsonify, make_response, request


REQUEST_INVALID = {
    'codigo': 400,
    'estado': 'INVALIDO',
    'error': 'El Request tiene parámetros inválidos o está incompleto.'
    }


def validate(request):
    return True # pending until API keys are implemented.

def get_response(result):
    return make_response(jsonify(result), 200)

def get_response_for_invalid(request, message=None):
    if message is not None:
        REQUEST_INVALID['error'] = message
    return make_response(jsonify(REQUEST_INVALID), 400)
