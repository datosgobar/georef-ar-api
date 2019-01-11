"""Módulo 'names' de georef-ar-api

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
DOOR_NUM_VAL = 'altura.valor'
DOOR_NUM_UNIT = 'altura.unidad'
ROAD_TYPE = 'tipo'
NAME = 'nombre'
FULL_NAME = 'nomenclatura'
STATE = 'provincia'
DEPT = 'departamento'
MUN = 'municipio'
LOCALITY = 'localidad'
STREET = 'calle'
STREET_X1 = 'calle_cruce_1'
STREET_X2 = 'calle_cruce_2'
GEOM = 'geometria'
LAT = 'lat'
LON = 'lon'
VALUE = 'valor'
UNIT = 'unidad'
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
LOCALITY_TYPE = 'tipo'
LOCATION = 'ubicacion'
FLOOR = 'piso'
LOCATION_LAT = 'ubicacion.lat'
LOCATION_LON = 'ubicacion.lon'
STREET_ID = 'calle.id'
STREET_NAME = 'calle.nombre'
STREET_TYPE = 'calle.tipo'
STREET_X1_ID = 'calle_cruce_1.id'
STREET_X1_NAME = 'calle_cruce_1.nombre'
STREET_X1_TYPE = 'calle_cruce_1.tipo'
STREET_X2_ID = 'calle_cruce_2.id'
STREET_X2_NAME = 'calle_cruce_2.nombre'
STREET_X2_TYPE = 'calle_cruce_2.tipo'

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
BASIC = 'basico'
STANDARD = 'estandar'
COMPLETE = 'completo'
INTERSECTION = 'interseccion'

# Results
RESULTS = 'resultados'
RESULT = 'resultado'
TOTAL = 'total'
QUANTITY = 'cantidad'

# Elasticsearch
STATE_ID = 'provincia.id'
STATE_NAME = 'provincia.nombre'
STATE_INTERSECTION = 'provincia.interseccion'
DEPT_ID = 'departamento.id'
DEPT_NAME = 'departamento.nombre'
MUN_ID = 'municipio.id'
MUN_NAME = 'municipio.nombre'
EXACT_SUFFIX = '.exacto'

# Fuentes
SOURCE_INDEC = 'INDEC'
SOURCE_BAHRA = 'BAHRA'
SOURCE_IGN = 'IGN'

# Índices
GEOM_INDEX = '{}-geometria'

# API
API_NAME = 'georef-ar-api'
