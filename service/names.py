"""Módulo 'names' de georef-ar-api

Declara los nombres que usa la API para campos,
parámetros, y otras claves que se usan frecuentemente.

Se utilizan variables globales (constantes) para permitir escribir código en
inglés (e.g. FLOOR) con contenido real en español ('piso'). Esto es necesario
ya que los datos producidos por georef-ar-etl están en español, así como la
interfaz externa de georef-ar-api que consumen los usuarios. El uso de
variables también permite que herramientas como jedi/pylint/flake8 detecten
errores de uso de variables inexistentes estáticamente (en comparación a
utilizar un diccionario de str-str).
"""

FIELDS_SEP = '.'


def join(*words):
    return FIELDS_SEP.join(words)


##########################
#    Valores simples     #
##########################

# Entidades y recursos
STATE = 'provincia'
STATES = 'provincias'
DEPARTMENTS = 'departamentos'
DEPT = 'departamento'
MUN = 'municipio'
MUNICIPALITIES = 'municipios'
CENSUS_LOCALITIES = 'localidades_censales'
CENSUS_LOCALITY = 'localidad_censal'
SETTLEMENTS = 'asentamientos'
SETTLEMENT = 'asentamiento'
LOCALITIES = 'localidades'
LOCALITY = 'localidad'
STREET = 'calle'
STREET_A = 'calle_a'
STREET_B = 'calle_b'
STREET_X1 = 'calle_cruce_1'
STREET_X2 = 'calle_cruce_2'
STREETS = 'calles'
STREET_BLOCKS = 'cuadras'
INTERSECTION = 'interseccion'
INTERSECTIONS = 'intersecciones'
ADDRESS = 'direccion'
ADDRESSES = 'direcciones'
LOCATION = 'ubicacion'
LOCATIONS = 'ubicaciones'
RESULT = 'resultado'
RESULTS = 'resultados'

# Campos, parámetros, etc.
BASIC = 'basico'
CENTROID = 'centroide'
COMPLETE = 'completo'
DOOR_NUM = 'altura'
END = 'fin'
ISO_ID = 'iso_id'
ISO_NAME = 'iso_nombre'
COMPLETE_NAME = 'nombre_completo'
EXACT = 'exacto'
FIELDS = 'campos'
ERROR = 'error'
ERRORS = 'errores'
FLATTEN = 'aplanar'
FLOOR = 'piso'
FORMAT = 'formato'
FUNCTION = 'funcion'
FULL_NAME = 'nomenclatura'
GEOM = 'geometria'
HELP = 'ayuda'
CATEGORY = 'categoria'
ID = 'id'
ITEM = 'item'
LAT = 'lat'
LEFT = 'izquierda'
LON = 'lon'
MAX = 'max'
NAME = 'nombre'
OFFSET = 'inicio'
ORDER = 'orden'
PARAMETERS = 'parametros'
QUANTITY = 'cantidad'
RIGHT = 'derecha'
SOURCE = 'fuente'
STANDARD = 'estandar'
START = 'inicio'
TOTAL = 'total'
TYPE = 'tipo'
UNIT = 'unidad'
VALUE = 'valor'

##########################
#    Valores compuestos  #
##########################

# Campos de entidades
STATE_ID = join(STATE, ID)
STATE_INTERSECTION = join(STATE, INTERSECTION)
STATE_NAME = join(STATE, NAME)
STATE_SOURCE = join(STATE, SOURCE)
DEPT_ID = join(DEPT, ID)
DEPT_NAME = join(DEPT, NAME)
DEPT_SOURCE = join(DEPT, SOURCE)
CENSUS_LOCALITY_ID = join(CENSUS_LOCALITY, ID)
CENSUS_LOCALITY_NAME = join(CENSUS_LOCALITY, NAME)
MUN_ID = join(MUN, ID)
MUN_NAME = join(MUN, NAME)
MUN_SOURCE = join(MUN, SOURCE)
EXACT_SUFFIX = join('{}', EXACT)
C_LAT = join(CENTROID, LAT)
C_LON = join(CENTROID, LON)
LOCATION_LAT = join(LOCATION, LAT)
LOCATION_LON = join(LOCATION, LON)

# Campos de altura
START_L = join(DOOR_NUM, START, LEFT)
START_R = join(DOOR_NUM, START, RIGHT)
END_L = join(DOOR_NUM, END, LEFT)
END_R = join(DOOR_NUM, END, RIGHT)
DOOR_NUM_UNIT = join(DOOR_NUM, UNIT)
DOOR_NUM_VAL = join(DOOR_NUM, VALUE)

# Campos de calles
STREET_ID = join(STREET, ID)
STREET_NAME = join(STREET, NAME)
STREET_CATEGORY = join(STREET, CATEGORY)
STREET_X1_ID = join(STREET_X1, ID)
STREET_X1_NAME = join(STREET_X1, NAME)
STREET_X1_CATEGORY = join(STREET_X1, CATEGORY)
STREET_X2_ID = join(STREET_X2, ID)
STREET_X2_NAME = join(STREET_X2, NAME)
STREET_X2_CATEGORY = join(STREET_X2, CATEGORY)

##########################
#        Plurales        #
##########################

_PLURALS = {
    STATE: STATES,
    DEPT: DEPARTMENTS,
    MUN: MUNICIPALITIES,
    CENSUS_LOCALITY: CENSUS_LOCALITIES,
    SETTLEMENT: SETTLEMENTS,
    LOCALITY: LOCALITIES,
    STREET: STREETS,
    ADDRESS: ADDRESSES,
    LOCATION: LOCATIONS,
    RESULT: RESULTS,
    ERROR: ERRORS,
    INTERSECTION: INTERSECTIONS
}

_SINGULARS = {value: key for key, value in _PLURALS.items()}


def plural(word):
    if word not in _PLURALS:
        raise RuntimeError('No plural defined for: {}'.format(word))

    return _PLURALS[word]


def singular(word):
    if word not in _SINGULARS:
        raise RuntimeError('No singular defined for: {}'.format(word))

    return _SINGULARS[word]
