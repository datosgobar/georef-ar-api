# -*- coding: utf-8 -*-

"""Módulo 'names' de georef-api

Declara los nombres que usa la API para campos,
parámetros, y otras claves que se usan frecuentemente.
"""

# Endpoints
ADDRESSES = 'direcciones'
STREETS = 'calles'
SETTLEMENTS = 'bahra'
LOCALITIES = 'localidades'
DEPARTMENTS = 'departamentos'
MUNICIPALITIES = 'municipios'
STATES = 'provincias'
PLACE = 'ubicacion'
PLACES = 'ubicaciones'

# Fields
ID = 'id'
DOOR_NUM = 'altura'
CODE = 'codigo'
ROAD_TYPE = 'tipo'
NAME = 'nombre'
FULL_NAME = 'nomenclatura'
POSTAL_CODE = 'codigo_postal'
STATE = 'provincia'
DEPT = 'departamento'
MUN = 'municipio'
LOCALITY = 'localidad'
GEOM = 'geometria'
LOCATION = 'ubicacion'
LAT = 'lat'
LON = 'lon'
END_R = 'fin_derecha'
END_L = 'fin_izquierda'
START_R = 'inicio_derecha'
START_L = 'inicio_izquierda'
SOURCE = 'fuente'
INFO = 'info'
ERROR = 'error'
MESSAGE = 'mensaje'
TIMESTAMP = 'timestamp'
LOCALITY_TYPE = 'tipo'

# Parameters
ADDRESS = 'direccion'
ORDER = 'orden'
FIELDS = 'campos'
FLATTEN = 'aplanar'
MAX = 'max'
FORMAT = 'formato'
EXACT = 'exacto'

# Results
RESULTS = 'resultados'

# Elasticsearch
STATE_ID = 'provincia.id'
STATE_NAME = 'provincia.nombre'
DEPT_ID = 'departamento.id'
DEPT_NAME = 'departamento.nombre'
MUN_ID = 'municipio.id'
MUN_NAME = 'municipio.nombre'

EXACT_SUFFIX = '.exacto'

# Messages
WRONG_QUERY = 'El request tiene parámetros inválidos o está incompleto.'
ADDRESS_REQUIRED = 'El parámetro \'direccion\' es obligatorio.'
ADDRESS_PROCESSED_OK = '¡Encontramos la dirección!'
CANNOT_GEOCODE_ADDRESS = 'Esta altura no puede ser geocodificada.'
NUMBER_REQUIRED = 'Falta la altura en el parámetro \'direccion\'.'
EMPTY_DATA = 'No hay direcciones en el cuerpo del request.'
INVALID_PARAM = 'El parámetro \'{param}\' no es válido para el recurso /{res}.'
EMPTY_PARAM = 'El parámetro \'{param}\' no puede estar vacío.'
LAT_REQUIRED = 'El parámetro \'lat\' es obligatorio.'
LON_REQUIRED = 'El parámetro \'lon\' es obligatorio.'

# Fuentes
SOURCE_INDEC = 'INDEC'
SOURCE_BAHRA = 'BAHRA'
SOURCE_IGN = 'IGN'
