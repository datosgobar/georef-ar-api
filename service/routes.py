# -*- coding: utf-8 -*-
from service import app, normalizer
from flask import request


@app.route('/api/v1.0/normalizador', methods=['GET', 'POST'])
def get_normalized_data():
    return normalizer.process(request)
