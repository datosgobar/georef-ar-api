"""Módulo '__init__' de georef-api

Crea la aplicación Flask de la API de Georef.
"""

from flask import Flask

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['JSON_AS_ASCII'] = False

import service.routes
