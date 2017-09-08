# -*- coding: utf-8 -*-

"""Módulo 'fields' de georef-api

Declara de los nombres que usa la API para
los campos, parámetros, y otras claves que se usan frecuentemente.
"""

# Endpoints
ADDRESSES = 'direcciones'
STREETS = 'calles'
LOCALITIES = 'localidades'
DEPARTMENTS = 'departamentos'
STATES = 'provincias'

# Fields
ID = 'id'
DOOR_NUM = 'altura'
CODE = 'codigo'
ROAD_TYPE = 'tipo'
NAME = 'nombre'
FULL_NAME = 'nomenclatura'
POSTAL_CODE = 'codigo_postal'
LOCALITY = 'localidad'
DEPT = 'departamento'
STATE = 'provincia'
GEOM = 'geometria'
LOCATION = 'ubicacion'
LAT = 'lat'
LON = 'lon'
END_R = 'fin_derecha'
END_L = 'fin_izquierda'
START_R = 'inicio_derecha'
START_L = 'inicio_izquierda'
OBS = 'observaciones'
SOURCE = 'fuente'
INFO = 'info'
ERROR = 'error'
MESSAGE = 'mensaje'
STATUS = 'estado'
NO_RESULTS = 'SIN_RESULTADOS'

# Parameters
ADDRESS = 'direccion'
ORDER = 'orden'
FIELDS = 'campos'
MAX = 'max'

# Elasticsearch
ID_KEYWORD = 'id.keyword'
NAME_KEYWORD = 'nombre.keyword'
DEPT_ID = 'departamento.id'
DEPT_NAME = 'departamento.nombre'
STATE_ID = 'provincia.id'
STATE_NAME = 'provincia.nombre'

# Messages
ADDRESS_PROCESSED_OK = 'Se procesó correctamente la dirección buscada.'
ADDRESS_OUT_OF_RANGE = 'La altura buscada está fuera del rango conocido.'
UNKNOWN_STREET_RANGE = 'La calle no tiene numeración en la base de datos.'
CANNOT_GEOCODE_ADDRESS = 'La altura buscada no puede ser geocodificada.'
CANNOT_INTERPOLATE_ADDRESS = 'No se pudo realizar la interpolación.'
