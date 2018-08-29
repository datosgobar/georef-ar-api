"""Módulo 'names' de georef-api

Declara los nombres que usa la API para campos,
parámetros, y otras claves que se usan frecuentemente.
"""

# Endpoints
ADDRESSES = 'direcciones'
STREETS = 'calles'
LOCALITIES = 'localidades'
DEPARTMENTS = 'departamentos'
MUNICIPALITIES = 'municipios'
STATES = 'provincias'
PLACES = 'ubicaciones'

# Fields
ID = 'id'
DOOR_NUM = 'altura'
CODE = 'codigo'
ROAD_TYPE = 'tipo'
NAME = 'nombre'
FULL_NAME = 'nomenclatura'
STATE = 'provincia'
DEPT = 'departamento'
MUN = 'municipio'
LOCALITY = 'localidad'
STREET = 'calle'
GEOM = 'geometria'
LAT = 'lat'
LON = 'lon'
C_LAT = 'centroide.lat'
C_LON = 'centroide.lon'
CENTROID = 'centroide'
END_R = 'altura.fin.derecha'
END_L = 'altura.fin.izquierda'
START_R = 'altura.inicio.derecha'
START_L = 'altura.inicio.izquierda'
START = 'inicio'
END = 'fin'
RIGHT = 'derecha'
LEFT = 'izquierda'
SOURCE = 'fuente'
TIMESTAMP = 'timestamp'
LOCALITY_TYPE = 'tipo'
LOCATION = 'ubicacion'
LOCATION_LAT = 'ubicacion.lat'
LOCATION_LON = 'ubicacion.lon'

# Parameters
ADDRESS = 'direccion'
PLACE = 'ubicacion'
ORDER = 'orden'
FIELDS = 'campos'
CSV_FIELDS = 'campos_csv'
FLATTEN = 'aplanar'
MAX = 'max'
OFFSET = 'inicio'
FORMAT = 'formato'
EXACT = 'exacto'

# Results
RESULTS = 'resultados'
TOTAL = 'total'
RETURNED = 'devueltos'

# Elasticsearch
STATE_ID = 'provincia.id'
STATE_NAME = 'provincia.nombre'
DEPT_ID = 'departamento.id'
DEPT_NAME = 'departamento.nombre'
MUN_ID = 'municipio.id'
MUN_NAME = 'municipio.nombre'
EXACT_SUFFIX = '.exacto'

# Fuentes
SOURCE_INDEC = 'INDEC'
SOURCE_BAHRA = 'BAHRA'
SOURCE_IGN = 'IGN'
