# -*- coding: utf-8 -*-
from service import app, normalizer
from flask import jsonify, make_response, request


@app.route('/api/v1.0/normalizador', methods=['GET'])
def get_normalized_data():
    if 'direccion' not in request.args:
        return make_response(jsonify(normalizer.REQUEST_INVALID), 400)
    result = normalizer.process(request)
    return jsonify(result)
