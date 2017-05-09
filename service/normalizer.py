# -*- coding: utf-8 -*-
REQUEST_INVALID = {
    'codigo': 400,
    'estado': 'INVALIDO',
    'error': 'El parámetro direccion es obligatorio'
    }


def process(request):
    params = request.args
    return {
        'estado': 'OK',
        'direcciones': [],
        }
