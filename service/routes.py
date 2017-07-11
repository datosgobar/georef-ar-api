# -*- coding: utf-8 -*-

"""Módulo 'routes' de georef-api

Declara las rutas de los recursos que expone la API e
invoca las funciones que procesan dichos recursos.
"""

from service import normalizer
from flask import request, Blueprint
api = Blueprint('api', __name__, url_prefix='/api/v1.0/')


@api.route('direcciones', methods=['GET', 'POST'])
def get_addresses():
    return normalizer.process_address(request)


@api.route('calles', methods=['GET'])
def get_streets():
    return normalizer.process_street(request)


@api.route('localidades', methods=['GET'])
def get_localities():
    return normalizer.process_locality(request)


@api.route('departamentos', methods=['GET'])
def get_departments():
    return normalizer.process_department(request)


@api.route('provincias', methods=['GET'])
def get_states():
    return normalizer.process_state(request)
