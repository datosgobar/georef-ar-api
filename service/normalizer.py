# -*- coding: utf-8 -*-
from service import parser


def process(request):
    if not parser.validate(request):
        return parser.get_response_for_invalid(request)
    if request.method == 'GET':
        return parser.get_response({'estado': 'OK', 'direcciones': [] })    
    return parser.get_response({
        'estado': 'OK',
        'direcciones': [],
        'originales': []
        })
