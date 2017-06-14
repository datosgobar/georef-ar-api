# -*- coding: utf-8 -*-
from service import app, normalizer
from flask import request


@app.route('/api/v1.0/direcciones', methods=['GET', 'POST'])
def get_normalized_data():
    return normalizer.process_address(request)


@app.route('/api/v1.0/localidades', methods=['GET'])
def get_localities():
    return normalizer.process_locality(request)


@app.route('/api/v1.0/departamentos', methods=['GET'])
def get_departments():
    return normalizer.process_department(request)


@app.route('/api/v1.0/provincias', methods=['GET'])
def get_states():
    return normalizer.process_state(request)
