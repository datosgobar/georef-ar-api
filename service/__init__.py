"""Módulo '__init__' de georef-ar-api

Crea la aplicación Flask de la API de Georef.
"""

from flask import Flask

app = Flask('georef', static_folder=None)
app.config.from_envvar('GEOREF_CONFIG')

with app.app_context():
    # Crear parsers de parámetros utilizando configuración de Flask app
    import service.params

import service.routes  # noqa: E402,F401 pylint: disable=wrong-import-position
