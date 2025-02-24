"""Módulo 'strings' de georef-ar-api

Contiene mensajes de error en forma de texto para usuarios.
"""

ADDRESS_FORMAT = 'La dirección debe seguir alguno de los formatos listados \
bajo la clave \'ayuda\'.'
ADDRESS_FORMAT_HELP = [
    '<nombre de calle>',
    '<nombre de calle> <altura>'
]
STRING_EMPTY = 'El campo no tiene contenido.'
INT_VAL_ERROR = 'El parámetro no es un número entero.'
FLOAT_VAL_ERROR = 'El parámetro no es un número real.'
INVALID_CHOICE = 'El parámetro debe tomar el valor de uno de los listados \
bajo la clave \'ayuda\'.'
INVALID_BULK = 'Las operaciones deben estar contenidas en una lista no vacía \
bajo la clave \'{}\'.'
BULK_QS_INVALID = 'No se permiten parámetros vía query string en operaciones \
bulk.'
INVALID_BULK_ENTRY = 'Las operaciones bulk deben ser de tipo objeto.'
INTERNAL_ERROR = 'Ocurrió un error interno de servidor al procesar la \
petición.'
MISSING_ERROR = 'El parámetro \'{}\' es obligatorio.'
UNKNOWN_ERROR = 'El parámetro especificado no existe. Los parámetros \
aceptados están listados bajo la clave \'ayuda\'.'
REPEATED_ERROR = 'El parámetro está repetido.'
BULK_LEN_ERROR = 'El número máximo de operaciones bulk es: {}.'
INT_VAL_SMALL = 'El número debe ser igual o mayor que {}.'
INT_VAL_BIG = 'El número debe ser menor o igual que {}.'
INT_VAL_BIG_GLOBAL = 'La suma de parámetros {} debe ser menor o igual \
que {}.'
NOT_FOUND = 'No se encontró la URL especificada.'
NOT_ALLOWED = 'Método no permitido en el recurso seleccionado.'
ID_PARAM_INVALID = 'Cada ID debe ser numérico y de longitud {}.'
ID_TWO_LENGTH_PARAM_INVALID = 'Cada ID debe ser numérico y de longitud {} ó {}.'
ID_ALPHAMERIC_TWO_LENGTH_PARAM_INVALID = 'Cada ID debe ser de longitud {} ó {}.'
ID_PARAM_LENGTH = 'La cantidad de ID debe ser menor o igual que {}.'
ID_PARAM_UNIQUE = 'La lista no debe contener ID repetidos (ID repetido: {}).'
COMPOUND_PARAM_ERROR = 'El valor del parámetro no es válido.'
FIELD_LIST_EMPTY = 'La lista no contiene valores.'
FIELD_LIST_REPEATED = 'La lista contiene valores repetidos.'
FIELD_LIST_INVALID_CHOICE = 'El parámetro debe consistir en una lista de \
ítems separados por comas. Los valores posibles de los ítems se listan bajo \
la clave \'ayuda\'. Alternativamente, se pueden especificar los valores \
\'basico\', \'estandar\' o \'completo\'.'
FIELD_INTERSECTION_FORMAT = 'El parámetro debe seguir el siguiente formato: \
<tipo de entidad>:<id>, <tipo de entidad>:<id>, ... (ver ejemplos bajo la \
clave ayuda).'
FIELD_INTERSECTION_FORMAT_HELP = [
    'provincia:94:38',
    'municipio:740038, departamento:74049',
    'departamento:62035:62007:62084',
    'municipio:700070:700049, provincia:02',
    'departamento:14028'
]
