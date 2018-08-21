"""Módulo 'strings' de georef-api

Contiene mensajes de error en forma de texto para usuarios.
"""

OBLIGATORY_NO_DEFAULT = 'Los parámetros obligatorios no pueden tener valor \
default.'
DEFAULT_INVALID_CHOICE = 'El valor default no se encuentra dentro de las \
opciones de valores.'
ADDRESS_NO_NUM = 'La dirección no contiene una altura.'
ADDRESS_NO_NAME = 'La dirección no contiene un nombre de calle.'
STRING_EMPTY = 'El campo de texto no tiene contenido.'
STRLIST_EMPTY = 'La lista no contiene valores.'
STRLIST_REPEATED = 'La lista contiene valores repetidos.'
INT_VAL_ERROR = 'El parámetro no es un número entero.'
FLOAT_VAL_ERROR = 'El parámetro no es un número real.'
INVALID_CHOICE = 'El parámetro debe tomar uno de los siguientes valores: {}.'
INVALID_BULK = 'Las operaciones deben estar contenidas en una lista de \
longitud 1 o más.'
BULK_QS_INVALID = 'No se permiten parámetros vía query string en operaciones \
bulk.'
INVALID_BULK_ENTRY = 'Las operaciones bulk deben ser de tipo objeto.'
INTERNAL_ERROR = 'Ocurrió un error interno de servidor al procesar la \
petición.'
MISSING_ERROR = 'El parámetro es obligatorio.'
UNKNOWN_ERROR = 'El parámetro especificado no existe.'
REPEATED_ERROR = 'El parámetro está repetido.'
BULK_LEN_ERROR = 'El número máximo de operaciones bulk es: {}.'
INT_VAL_SMALL = 'El número debe ser igual o mayor que {}.'
INT_VAL_BIG = 'El número debe ser menor o igual que {}.'
INT_VAL_BIG_GLOBAL = 'La suma de parámetros \'max\' debe ser menor o igual \
que {}.'
NOT_FOUND = 'No se encontró la URL especificada.'
ID_PARAM_INVALID = 'El ID debe ser numérico y de longitud {}.'
