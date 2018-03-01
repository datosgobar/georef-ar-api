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

# Parameters
ADDRESS = 'direccion'
ORDER = 'orden'
FIELDS = 'campos'
FLATTEN = 'aplanar'
MAX = 'max'
FORMAT = 'formato'

# Elasticsearch
ID_KEYWORD = 'id.keyword'
NAME_KEYWORD = 'nombre.keyword'
DEPT_ID = 'departamento.id'
DEPT_NAME = 'departamento.nombre'
STATE_ID = 'provincia.id'
STATE_NAME = 'provincia.nombre'

# Messages
WRONG_QUERY = 'El request tiene parámetros inválidos o está incompleto.'
ADDRESS_REQUIRED = 'El parámetro {direccion} es obligatorio.'
ADDRESS_PROCESSED_OK = '¡Encontramos la dirección!'
ADDRESS_OUT_OF_RANGE = 'Esta altura está fuera del rango conocido.'
UNKNOWN_STREET_RANGE = 'La calle no tiene numeración en la base de datos.'
CANNOT_GEOCODE_ADDRESS = 'Esta altura no puede ser geocodificada.'
CANNOT_INTERPOLATE_ADDRESS = 'Falló la interpolación.'
NUMBER_REQUIRED = 'Falta la altura en el parámetro {direccion}.'
EMPTY_DATA = 'No hay direcciones en el cuerpo del request.'
INVALID_PARAM = 'El parámetro {%s} no es válido para el recurso /%s.'
LAT_REQUIRED = 'El parámetro {lat} es obligatorio.'
LON_REQUIRED = 'El parámetro {lon} es obligatorio.'
