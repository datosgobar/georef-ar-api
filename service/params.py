"""Módulo 'params' de georef-api

Contiene clases utilizadas para leer y validar parámetros recibidos en requests
HTTP.
"""

import service.names as N
from service import strings

import re
from enum import Enum, unique
from collections import namedtuple

# TODO: Mover a archivo de configuración
MAX_BULK_LEN = 100


class ParameterRequiredException(Exception):
    """Excepción lanzada cuando se detecta la ausencia de un parámetro
    requerido.

    """

    pass


class InvalidChoiceException(Exception):
    """Excepción lanzada cuando un parámetro no tiene como valor uno de los
    valores permitidos.

    """

    pass


class InvalidLocationException(Exception):
    """Excepción lanzada cuando se recibe un parámetro en la parte incorrecta de
    una request HTTP (por ejemplo, query string en vez de body).

    """

    pass


@unique
class ParamErrorType(Enum):
    """Códigos de error para cada tipo de error de parámetro.

    Nota: En caso de agregar un nuevo error, no reemplazar un valor existente,
    crear uno nuevo.

    """

    UNKNOWN_PARAM = 1000
    VALUE_ERROR = 1001
    INVALID_CHOICE = 1002
    PARAM_REQUIRED = 1003
    INVALID_BULK = 1004
    INVALID_LOCATION = 1005
    REPEATED = 1006
    INVALID_BULK_ENTRY = 1007
    INVALID_BULK_LEN = 1008


ParamError = namedtuple('ParamError', ['error_type', 'message', 'source'])
"""La clase ParamError representa toda la información conocida sobre un error
de parámetro.
"""


class Parameter:
    """Representa un parámetro cuyo valor es recibido a través de una request
    HTTP.

    La clase se encarga de validar el valor recibido vía HTTP (en forma de
    string), comprobando también que el valor haya sido recibido (en caso de
    ser un parámetro requerido).

    Attributes:
        choices (list): Lista de valores permitidos (o None si se permite
            cualquier valor).
        required (bool): Verdadero si el parámetro es requerido.
        default: Valor que debería tomar el parámetro en caso de no haber sido
            recibido.
        source (str): Ubicación permitida del parámetro en el request HTTP.

    """

    def __init__(self, required=False, default=None, choices=None,
                 source='any'):
        """Inicializa un objeto Parameter.

        Args:
            choices (list): Lista de valores permitidos (o None si se permite
                cualquier valor).
            required (bool): Verdadero si el parámetro es requerido.
            default: Valor que debería tomar el parámetro en caso de no haber
                sido recibido.
            source (str): Ubicación permitida del parámetro en el request HTTP
                (querystring, body o any).

        """
        if required and default is not None:
            raise ValueError(strings.OBLIGATORY_NO_DEFAULT)

        self.choices = choices
        self.required = required
        self.default = default
        self.source = source

        if choices and \
           default is not None \
           and not self._value_in_choices(default):
            raise ValueError(strings.DEFAULT_INVALID_CHOICE)

    def get_value(self, val, from_source):
        """Toma un valor 'val' recibido desde una request HTTP, y devuelve el
        verdadero valor (con tipo apropiado) resultante de acuerdo a las
        propiedades del objeto Parameter.

        Args:
            val (str): String recibido desde la request HTTP, o None si no se
                recibió un valor.
            from_source (str): Ubicación de la request HTTP donde se recibió el
                valor.

        Returns:
            El valor del parámetro resultante, cuyo tipo depende de las reglas
            definidas por el objeto Parameter y sus subclases.

        """
        if val is None:
            if self.required:
                raise ParameterRequiredException()
            else:
                return self.default
        else:
            if self.source != 'any' and from_source != self.source:
                raise InvalidLocationException(strings.INVALID_LOCATION.format(
                    self.source))

        parsed = self._parse_value(val)

        if self.choices and not self._value_in_choices(parsed):
            raise InvalidChoiceException(
                strings.INVALID_CHOICE.format(', '.join(self.choices)))

        return parsed

    def _value_in_choices(self, val):
        """Comprueba que un valor esté dentro de los valores permitidos del
        objeto Parameter. El valor ya debería estar parseado y tener el tipo
        apropiado.

        Args:
            val: Valor a comprobar si está contenido dentro de los valores
                permitidos.

        Returns:
            bool: Verdadero si el valor está contenido dentro de los valores
                permitidos

        """
        return val in self.choices

    def _parse_value(self, val):
        """Parsea un valor de tipo string y devuelve el resultado con el tipo
        apropiado.

        Args:
            val (str): Valor a parsear.

        Returns:
            El valor parseado.

        """
        raise NotImplementedError()


class StrParameter(Parameter):
    """Representa un parámetro de tipo string no vacío.

    Se heredan las propiedades y métodos de la clase Parameter, definiendo
    nuevamente el método '_parse_value' para implementar lógica de parseo y
    validación propias de StrParameter.

    """

    def _parse_value(self, val):
        if not val:
            raise ValueError(strings.STRING_EMPTY)

        return val


class BoolParameter(Parameter):
    """Representa un parámetro de tipo booleano.

    Se heredan las propiedades y métodos de la clase Parameter, definiendo
    nuevamente el método '_parse_value' para implementar lógica de parseo y
    validación propias de BoolParameter.

    """

    def __init__(self):
        super().__init__(False, False, [True, False])

    def _parse_value(self, val):
        # Cualquier valor recibido (no nulo) es verdadero
        return val is not None


class StrListParameter(Parameter):
    """Representa un parámetro de tipo lista de strings.

    Se heredan las propiedades y métodos de la clase Parameter, definiendo
    nuevamente el método '_parse_value' para implementar lógica de parseo y
    validación propias de StrListParameter. Se define también el método
    _value_in_choices para modificar su comportamiento original.

    """

    def __init__(self, required=False, constants=None, optionals=None):
        self.constants = set(constants) if constants else set()
        optionals = set(optionals) if optionals else set()
        all_values = self.constants | optionals

        super().__init__(required, list(all_values), all_values)

    def _value_in_choices(self, val):
        # La variable val es de tipo set o list, self.choices es de tipo set:
        # devolver falso si existen elementos en val que no están en
        # self.choices.
        return not (set(val) - self.choices)

    def _parse_value(self, val):
        if not val:
            raise ValueError(strings.STRLIST_EMPTY)

        received = set(part.strip() for part in val.split(','))
        # Siempre se agregan los valores constantes
        return list(self.constants | received)


class IntParameter(Parameter):
    """Representa un parámetro de tipo entero.

    Se heredan las propiedades y métodos de la clase Parameter, definiendo
    nuevamente el método '_parse_value' para implementar lógica de parseo y
    validación propias de IntParameter.

    """
    def __init__(self, required=False, default=None, choices=None,
                 source='any', lower_limit=None):
        self.lower_limit = lower_limit
        super().__init__(required, default, choices, source)

    def _parse_value(self, val):
        try:
            int_val = int(val)
        except ValueError:
            raise ValueError(strings.INT_VAL_ERROR)

        if self.lower_limit is not None and int_val < self.lower_limit:
            raise ValueError(
                strings.INT_VAL_SMALL.format(self.lower_limit))

        return int_val


class FloatParameter(Parameter):
    """Representa un parámetro de tipo float.

    Se heredan las propiedades y métodos de la clase Parameter, definiendo
    nuevamente el método '_parse_value' para implementar lógica de parseo y
    validación propias de FloatParameter.

    """

    def _parse_value(self, val):
        try:
            return float(val)
        except ValueError:
            raise ValueError(strings.FLOAT_VAL_ERROR)


class AddressParameter(Parameter):
    """Representa un parámetro de tipo dirección de calle.

    Se heredan las propiedades y métodos de la clase Parameter, definiendo
    nuevamente el método '_parse_value' para implementar lógica de parseo y
    validación propias de AddressParameter.

    """

    def __init__(self):
        super().__init__(required=True)

    def _parse_value(self, val):
        # TODO: Revisar expresiones regulares
        match = re.search(r'(\s[0-9]+?)$', val)
        number = int(match.group(1)) if match else None
        if not number:
            raise ValueError(strings.ADDRESS_NO_NUM)

        road_name = re.sub(r'(\s[0-9]+?)$', r'', val)

        if not road_name:
            raise ValueError(strings.ADDRESS_NO_NAME)

        return road_name.strip(), number


class ParameterSet():
    """Representa un conjunto de parámetros HTTP.

    Se utiliza para representar todos los parámetros aceptados por un cierto
    endpoint HTTP.

    Attributes:
        params (dict): Diccionario de parámetros aceptados, siendo las keys
            los nombres de los parámetros que se debe usar al especificarlos, y
            los valores objetos de tipo Parameter.

    """

    def __init__(self, params):
        """Inicializa un objeto de tipo ParameterSet.

        Args:
            params (dict): Ver atributo 'params'.

        """
        self.params = params

    def parse_params_dict(self, received, from_source):
        """Parsea parámetros (clave-valor) recibidos en una request HTTP,
        utilizando el conjunto de parámetros internos.

        Args:
            received (dict): Parámetros recibidos sin procesar.
            from_source (str): Ubicación dentro de la request HTTP donde fueron
                recibidos los parámetros.

        Returns:
            tuple: Tupla de resultados y errores. Los resultados consisten de
                un diccionario conteniendo como clave el nombre del parámetro,
                y como valor el valor parseado y validado, con su tipo
                apropiado. Los errores consisten de un diccionario conteniendo
                como clave el nombre del parámetro recibido, y como valor un
                objeto de tipo ParamError, especificando el error.
        """
        parsed, errors = {}, {}
        is_multi_dict = hasattr(received, 'getlist')

        for param_name, param in self.params.items():
            if is_multi_dict:
                received_vals = received.getlist(param_name)
            else:
                received_vals = [received.get(param_name)]

            # Comprobar que ningún parámetro esté repetido
            if not received_vals:
                received_val = None
            elif len(received_vals) > 1:
                errors[param_name] = ParamError(ParamErrorType.REPEATED,
                                                strings.REPEATED_ERROR,
                                                from_source)
                continue
            else:
                received_val = received_vals[0]

            try:
                parsed_val = param.get_value(received_val, from_source)
                parsed[param_name] = parsed_val
            except ParameterRequiredException:
                errors[param_name] = ParamError(ParamErrorType.PARAM_REQUIRED,
                                                strings.MISSING_ERROR,
                                                from_source)
            except ValueError as e:
                errors[param_name] = ParamError(ParamErrorType.VALUE_ERROR,
                                                str(e), from_source)
            except InvalidLocationException as e:
                errors[param_name] = ParamError(
                    ParamErrorType.INVALID_LOCATION, str(e), from_source)
            except InvalidChoiceException as e:
                errors[param_name] = ParamError(ParamErrorType.INVALID_CHOICE,
                                                str(e), from_source)

        for param_name in received:
            if param_name not in self.params:
                errors[param_name] = ParamError(ParamErrorType.UNKNOWN_PARAM,
                                                strings.UNKNOWN_ERROR,
                                                from_source)

        return parsed, errors

    def parse_post_params(self, qs_params, body_params):
        """Parsea parámetros (clave-valor) recibidos en una request HTTP
        POST utilizando el conjunto de parámetros internos.

        Args:
            qs_params (dict): Parámetros recibidos en el query string.
            body_params (list): Lista de diccionarios, cada uno representando
                un conjunto de parámetros recibidos en el body del request
                HTTP.

        Returns:
            tuple: Tupla de dos listas: una lista de conjuntos de parámetros
                parseados, y una lista de conjuntos de errores de parseo. Los
                elementos de ambas listas provinenen de 'parse_param_dict'.

        """
        if qs_params:
            # No aceptar parámetros de querystring en bulk
            return [], [
                {'querystring': ParamError(ParamErrorType.INVALID_LOCATION,
                                           strings.BULK_QS_INVALID,
                                           'querystring')}
            ]

        if not body_params or not isinstance(body_params, list):
            # No aceptar operaciones bulk que no sean listas, y no
            # aceptar listas vacías.
            return [], [
                {'body': ParamError(ParamErrorType.INVALID_BULK,
                                    strings.INVALID_BULK, 'body')}
            ]

        if len(body_params) > MAX_BULK_LEN:
            return [], [
                {'body': ParamError(
                    ParamErrorType.INVALID_BULK_LEN,
                    strings.BULK_LEN_ERROR.format(MAX_BULK_LEN), 'body')}
            ]

        results, errors_list = [], []
        for param_dict in body_params:
            if not hasattr(param_dict, 'get'):
                parsed, errors = {}, {
                    'body': ParamError(ParamErrorType.INVALID_BULK_ENTRY,
                                       strings.INVALID_BULK_ENTRY,
                                       'body')
                }
            else:
                parsed, errors = self.parse_params_dict(param_dict, 'body')

            results.append(parsed)
            errors_list.append(errors)

        return results, errors_list

    def parse_get_params(self, qs_params):
        """Parsea parámetros (clave-valor) recibidos en una request HTTP GET
        utilizando el conjunto de parámetros internos.

        Args:
            qs_params (dict): Parámetros recibidos en el query string.

        Returns:
            tuple: Valor de retorno de 'parse_dict_params'.

        """
        return self.parse_params_dict(qs_params, 'querystring')


PARAMS_STATES = ParameterSet({
    N.ID: StrParameter(),
    N.NAME: StrParameter(),
    N.ORDER: StrParameter(choices=[N.ID, N.NAME]),
    N.FIELDS: StrListParameter(constants=[N.ID, N.NAME, N.SOURCE],
                               optionals=[N.LAT, N.LON]),
    N.MAX: IntParameter(default=24, lower_limit=1),
    N.EXACT: BoolParameter(),
    N.FORMAT: StrParameter(default='json', choices=['json', 'csv', 'geojson'],
                           source='querystring')
})

PARAMS_DEPARTMENTS = ParameterSet({
    N.ID: StrParameter(),
    N.NAME: StrParameter(),
    N.STATE: StrParameter(),
    N.ORDER: StrParameter(choices=[N.ID, N.NAME]),
    N.FLATTEN: BoolParameter(),
    N.FIELDS: StrListParameter(constants=[N.ID, N.NAME, N.SOURCE],
                               optionals=[N.LAT, N.LON, N.STATE_ID,
                                          N.STATE_NAME]),
    N.MAX: IntParameter(default=10, lower_limit=1),
    N.EXACT: BoolParameter(),
    N.FORMAT: StrParameter(default='json', choices=['json', 'csv', 'geojson'],
                           source='querystring')
})

PARAMS_MUNICIPALITIES = ParameterSet({
    N.ID: StrParameter(),
    N.NAME: StrParameter(),
    N.STATE: StrParameter(),
    N.DEPT: StrParameter(),
    N.ORDER: StrParameter(choices=[N.ID, N.NAME]),
    N.FLATTEN: BoolParameter(),
    N.FIELDS: StrListParameter(constants=[N.ID, N.NAME, N.SOURCE],
                               optionals=[N.LAT, N.LON, N.STATE_ID,
                                          N.STATE_NAME, N.DEPT_ID,
                                          N.DEPT_NAME]),
    N.MAX: IntParameter(default=10, lower_limit=1),
    N.EXACT: BoolParameter(),
    N.FORMAT: StrParameter(default='json', choices=['json', 'csv', 'geojson'],
                           source='querystring')
})

PARAMS_LOCALITIES = ParameterSet({
    N.ID: StrParameter(),
    N.NAME: StrParameter(),
    N.STATE: StrParameter(),
    N.DEPT: StrParameter(),
    N.MUN: StrParameter(),
    N.ORDER: StrParameter(choices=[N.ID, N.NAME]),
    N.FLATTEN: BoolParameter(),
    N.FIELDS: StrListParameter(constants=[N.ID, N.NAME, N.SOURCE],
                               optionals=[N.LAT, N.LON, N.STATE_ID,
                                          N.STATE_NAME, N.DEPT_ID, N.DEPT_NAME,
                                          N.MUN_ID, N.MUN_NAME,
                                          N.LOCALITY_TYPE]),
    N.MAX: IntParameter(default=10, lower_limit=1),
    N.EXACT: BoolParameter(),
    N.FORMAT: StrParameter(default='json', choices=['json', 'csv', 'geojson'],
                           source='querystring')
})

PARAMS_ADDRESSES = ParameterSet({
    N.ADDRESS: AddressParameter(),
    N.ROAD_TYPE: StrParameter(),
    N.STATE: StrParameter(),
    N.DEPT: StrParameter(),
    N.FLATTEN: BoolParameter(),
    N.FIELDS: StrListParameter(constants=[N.ID, N.NAME, N.DOOR_NUM,
                                          N.SOURCE],
                               optionals=[N.STATE_ID, N.STATE_NAME, N.DEPT_ID,
                                          N.DEPT_NAME, N.ROAD_TYPE,
                                          N.FULL_NAME, N.LOCATION_LAT,
                                          N.LOCATION_LON]),
    N.MAX: IntParameter(default=10, lower_limit=1),
    N.EXACT: BoolParameter(),
    N.FORMAT: StrParameter(default='json', choices=['json', 'csv'],
                           source='querystring')
})

PARAMS_STREETS = ParameterSet({
    N.ID: StrParameter(),
    N.NAME: StrParameter(),
    N.ROAD_TYPE: StrParameter(),
    N.STATE: StrParameter(),
    N.DEPT: StrParameter(),
    N.FLATTEN: BoolParameter(),
    N.FIELDS: StrListParameter(constants=[N.ID, N.NAME, N.SOURCE],
                               optionals=[N.START_R, N.START_L, N.END_R,
                                          N.END_L, N.STATE_ID, N.STATE_NAME,
                                          N.DEPT_ID, N.DEPT_NAME, N.FULL_NAME,
                                          N.ROAD_TYPE]),
    N.MAX: IntParameter(default=10, lower_limit=1),
    N.EXACT: BoolParameter(),
    N.FORMAT: StrParameter(default='json', choices=['json', 'csv'],
                           source='querystring')
})

PARAMS_PLACE = ParameterSet({
    N.LAT: FloatParameter(required=True),
    N.LON: FloatParameter(required=True),
    N.FLATTEN: BoolParameter(),
    N.FIELDS: StrListParameter(constants=[N.STATE_ID, N.STATE_NAME, N.SOURCE],
                               optionals=[N.DEPT_ID, N.DEPT_NAME, N.MUN_ID,
                                          N.MUN_NAME, N.LAT, N.LON]),
    N.FORMAT: StrParameter(default='json', choices=['json', 'geojson'],
                           source='querystring')
})
