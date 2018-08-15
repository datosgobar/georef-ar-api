"""Módulo '__init__' de georef-api

Crea la aplicación Flask de la API de Georef.
"""

from flask import Flask

app = Flask('georef')
app.config.from_envvar('GEOREF_CONFIG')

import service.routes  # noqa: E402,F401
