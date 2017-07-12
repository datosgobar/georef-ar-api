# -*- coding: utf-8 -*-

"""Módulo 'routes' de georef-api

Declara las rutas de los recursos que expone la API e
invoca las funciones que procesan dichos recursos.
"""

from flask import request, Blueprint
from flask_jwt import jwt_required

from service import normalizer

api = Blueprint('api', __name__, url_prefix='/api/v1.0/')


@api.route('direcciones', methods=['GET', 'POST'])
@jwt_required()
def get_addresses():
    return normalizer.process_address(request)


@api.route('calles', methods=['GET'])
@jwt_required()
def get_streets():
    return normalizer.process_street(request)


@api.route('localidades', methods=['GET'])
@jwt_required()
def get_localities():
    return normalizer.process_locality(request)


@api.route('departamentos', methods=['GET'])
@jwt_required()
def get_departments():
    return normalizer.process_department(request)


@api.route('provincias', methods=['GET'])
@jwt_required()
def get_states():
    return normalizer.process_state(request)
