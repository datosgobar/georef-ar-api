"""Módulo 'params' de georef-ar-api

Contiene clases utilizadas para leer y validar parámetros recibidos en requests
HTTP.
"""

from abc import ABC, abstractmethod
import threading
import math
from enum import Enum, unique
from collections import defaultdict
from georef_ar_address import AddressParser
import service.names as N
from service import strings, constants, utils


class ParametersParseException(Exception):
    """Excepción lanzada al finalizar la recolección de errores para todos los
    parámetros.

    La variable 'self._errors' puede contener un diccionario de error por
    parámetro (GET) o una lista de diccionarios de error por parámetro (POST).

    Attributes:
        _errors (list, dict): Diccionario de errores (nombre-ParamError) para
            un conjunto de parámetros (GET), o una lista de diccionarios de
            errores (POST).
        _fmt (str): Formato a utilizar para presentar los errores.

    """

    def __init__(self, errors, fmt='json'):
        self._errors = errors
        self._fmt = fmt
        super().__init__()

    @property
    def errors(self):
        return self._errors

    @property
    def fmt(self):
        return self._fmt


class ParameterValueError(Exception):
    """Excepción lanzada durante el parseo de valores de parámetros. Puede
    incluir un objeto conteniendo información de ayuda para el usuario.

    """

    def __init__(self, message, help_data):
        self._message = message
        self._help = help_data
        super().__init__()

    @property
    def message(self):
        return self._message

    @property
    def help(self):
        return self._help


class ParameterRequiredException(Exception):
    """Excepción lanzada cuando se detecta la ausencia de un parámetro
    requerido.

    """


class InvalidChoiceException(Exception):
    """Excepción lanzada cuando un parámetro no tiene como valor uno de los
    valores permitidos.

    """


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
    INVALID_SET = 1009


class ParamError:
    """La clase ParamError representa toda la información conocida sobre un
    error de parámetro.

    """

    def __init__(self, error_type, message, source, help_data=None):
        self._error_type = error_type
        self._message = message
        self._source = source
        self._help = help_data

    @property
    def error_type(self):
        return self._error_type

    @property
    def message(self):
        return self._message

    @property
    def source(self):
        return self._source

    @property
    def help(self):
        return self._help


class Parameter(ABC):
    """Representa un parámetro cuyo valor es recibido a través de una request
    HTTP.

    La clase se encarga de validar el valor recibido vía HTTP (en forma de
    string), y retornar su valor convertido. Por ejemplo, el parámetro
    IntParameter podría recibir el valor '100' (str) y retornar 100 (int).
    La clase Parameter también se encarga de validar que los parámetros
    requeridos hayan sido envíados en la petición HTTP.

    La clase Parameter y todos sus derivadas deben definir su estado interno
    exclusivamente en el método __init__. Los métodos de validación/conversión
    'get_value', 'validate_values', etc. *no* deben modificar el estado interno
    de sus instancias. En otras palabras, la clase Parameter y sus derivadas
    deberían ser consideradas inmutables. Esto facilita el desarrollo de
    Parameter ya que el comportamiento sus métodos internos solo depende de un
    estado inicial estático.

    Attributes:
        _choices (frozenset): Lista de valores permitidos (o None si se permite
            cualquier valor).
        _required (bool): Verdadero si el parámetro es requerido.
        _default (object): Valor que debería tomar el parámetro en caso de no
            haber sido recibido.

    """

    def __init__(self, required=False, default=None, choices=None):
        """Inicializa un objeto Parameter.

        Args:
            required (bool): Verdadero si el parámetro es requerido.
            default: Valor que debería tomar el parámetro en caso de no haber
                sido recibido.
            choices (list): Lista de valores permitidos (o None si se permite
                cualquier valor).

        """
        if required and default is not None:
            raise ValueError(
                'Default values are not allowed on required parameters')

        self._choices = frozenset(choices) if choices else None
        self._required = required
        self._default = default

        if choices and default is not None:
            try:
                self._check_value_in_choices(default)
            except InvalidChoiceException:
                raise ValueError('Default value not contained in choices')

    def get_value(self, val):
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
            if self._required:
                raise ParameterRequiredException()

            return self._default

        parsed = self._parse_value(val)

        if self._choices:
            self._check_value_in_choices(parsed)

        return parsed

    def _check_value_in_choices(self, val):
        """Comprueba que un valor esté dentro de los valores permitidos del
        objeto Parameter. El valor ya debería estar parseado y tener el tipo
        apropiado.

        Args:
            val: Valor a comprobar si está contenido dentro de los valores
                permitidos.

        Raises:
            InvalidChoiceException: si el valor no está contenido dentro de los
                valores permitidos.

        """
        if val not in self._choices:
            raise InvalidChoiceException(strings.INVALID_CHOICE)

    @abstractmethod
    def _parse_value(self, val):
        """Parsea un valor de tipo string y devuelve el resultado con el tipo
        apropiado.

        Args:
            val (str): Valor a parsear.

        Returns:
            El valor parseado.

        Raises:
            ValueError, ParameterValueError: si el valor recibido no pudo ser
                interpretado como un valor válido por el parámetro.

        """
        raise NotImplementedError()

    @property
    def choices(self):
        return sorted(list(self._choices))


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


class IdsParameter(Parameter):
    """Representa un parámetro de tipo lista de IDs numéricos. Se aceptan
    listas de IDs separados por comas (esto incluye listas de longitud 1, es
    decir, un solo ID sin comas). No se aceptan IDs repetidos.

    Se heredan las propiedades y métodos de la clase Parameter, definiendo
    nuevamente el método '_parse_value' para implementar lógica de parseo y
    validación propias de IdParameter.

    Attributes:
        _id_length (int): Longitud de los IDs a aceptar/devolver.
        _padding_char (str): Caracter a utilizar para completar los IDs
            recibidos con longitud menor a _id_length.
        _min_length (int): Longitud mínima de valores str a procesar.
        _sep (str): Caracter a utilizar para separar listas de IDs.

    """

    def __init__(self, id_length, padding_char='0', padding_length=1, sep=','):
        self._id_length = id_length
        self._padding_char = padding_char
        self._min_length = self._id_length - padding_length
        self._sep = sep
        super().__init__()

    def _parse_value(self, val):
        items = val.split(self._sep)
        if len(items) > constants.MAX_RESULT_LEN:
            raise ValueError(strings.ID_PARAM_LENGTH.format(
                constants.MAX_RESULT_LEN))

        ids = set()
        for item in items:
            item = item.strip()

            if not item.isdigit() or len(item) > self._id_length or \
               len(item) < self._min_length:
                raise ValueError(strings.ID_PARAM_INVALID.format(
                    self._id_length))

            item = item.rjust(self._id_length, self._padding_char)
            if item in ids:
                raise ValueError(strings.ID_PARAM_UNIQUE.format(item))

            ids.add(item)

        return list(ids)


class IdsTwoLengthParameter(IdsParameter):

    def __init__(self, *two_length, padding_char='0', sep=','):
        max_length = max(two_length)
        min_length = min(two_length)
        super().__init__(max_length, padding_char=padding_char, padding_length=max_length - min_length, sep=sep)
        self._max_length = max_length
        self._min_length = min_length

    def _parse_value(self, val):
        items = val.split(self._sep)
        if len(items) > constants.MAX_RESULT_LEN:
            raise ValueError(strings.ID_PARAM_LENGTH.format(
                constants.MAX_RESULT_LEN))

        ids = set()
        for item in items:
            item = item.strip()

            if not item.isdigit() or len(item) > self._id_length:
                raise ValueError(strings.ID_TWO_LENGTH_PARAM_INVALID.format(
                    self._min_length, self._max_length))

            id_length = self._id_length if len(item) > self._min_length else self._min_length
            item = item.rjust(id_length, self._padding_char)
            if item in ids:
                raise ValueError(strings.ID_PARAM_UNIQUE.format(item))

            ids.add(item)

        return list(ids)


class IdsAlphamericTwoLengthParameter(IdsTwoLengthParameter):

    def _parse_value(self, val):
        items = val.split(self._sep)
        if len(items) > constants.MAX_RESULT_LEN:
            raise ValueError(strings.ID_PARAM_LENGTH.format(
                constants.MAX_RESULT_LEN))

        ids = set()
        for item in items:
            item = item.strip()

            if len(item) > self._id_length:
                raise ValueError(strings.ID_ALPHAMERIC_TWO_LENGTH_PARAM_INVALID.format(
                    self._min_length, self._id_length))

            id_length = self._id_length if len(item) > self._min_length else self._min_length
            item = item.rjust(id_length, self._padding_char)
            if item in ids:
                raise ValueError(strings.ID_PARAM_UNIQUE.format(item))

            ids.add(item)

        return list(ids)


class CompoundParameter(Parameter):
    """Representa un parámetro que puede tomar distintos valores, representados
    por una lista de objetos 'Parameter'.

    Se heredan las propiedades y métodos de la clase Parameter, definiendo
    nuevamente el método '_parse_value' para implementar lógica de parseo y
    validación propias de CompoundParameter.

    Attributes:
        _parameters (tuple): Lista de 'Parameter'. Se intenta parsear el valor
            recibido con cada uno, en orden, hasta que uno retorne un valor.

    """

    def __init__(self, parameters, *args, **kwargs):
        self._parameters = tuple(parameters)
        super().__init__(*args, **kwargs)

    def _parse_value(self, val):
        for param in self._parameters:
            try:
                return param.get_value(val)
            except ValueError:
                # Probar cada Parameter interno hasta agotar la lista
                pass

        raise ValueError(strings.COMPOUND_PARAM_ERROR)


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


class FieldListParameter(Parameter):
    """Representa un parámetro de tipo lista de campos.

    Se heredan las propiedades y métodos de la clase Parameter, definiendo
    nuevamente el método '_parse_value' para implementar lógica de parseo y
    validación propias de FieldListParameter. Se define también el método
    _check_value_in_choices para modificar su comportamiento original.

    Attributes:
        self._basic (frozenset): Conjunto de campos mínimos, siempre son
            incluídos en cualquier lista de campos, incluso si el usuario no
            los especificó.
        self._standard (frozenset): Conjunto de campos estándar. Se retorna
            este conjunto de parámetros como default cuando no se especifica
            ningún conjunto de parámetros.
        self._complete (frozenset): Conjunto de campos completos. Este conjunto
            contiene todos los campos posibles a especificar.

    """

    def __init__(self, basic=None, standard=None, complete=None):
        self._basic = frozenset(basic or [])
        self._standard = frozenset(standard or []) | self._basic
        self._complete = frozenset(complete or []) | self._standard

        super().__init__(False, tuple(self._standard), self._complete)

    def _check_value_in_choices(self, val):
        """Comprueba que un valor representando un conjunto de campos sea
        válido. Cada campo debe estar contenido en 'self._complete'.

        Args:
            val (tuple): Campos recibidos.

        Raises:
            InvalidChoiceException: si alguno de los valores de 'val' no está
                contenido en 'self._complete'.

        """
        # La variable val es de tipo tuple, self._complete es de tipo
        # frozenset: Convertir val a un set, y comprobar que todos sus campos
        # están contenidos en self._complete.
        if set(val) - self._complete:
            raise InvalidChoiceException(strings.FIELD_LIST_INVALID_CHOICE)

    def _expand_prefixes(self, received):
        """Dada un conjunto de campos recibidos, expande los campos con valores
        prefijos de otros.

        Por ejemplo, el valor 'provincia' se expande a 'provincia.id' y
        'provincia.nombre'. 'altura' se expande a 'altura.fin.derecha',
        'altura.fin.izquierda', etc.

        Args:
            received (set): Campos recibidos.

        Returns:
            set: Conjunto de campos con campos prefijos expandidos.

        """
        expanded = set()
        prefixes = set()

        for part in received:
            for field in self._complete:
                field_prefix = '.'.join(field.split('.')[:-1]) + '.'

                if field_prefix.startswith(part + '.'):
                    expanded.add(field)
                    prefixes.add(part)

        # Resultado: campos recibidos, menos los prefijos, con los campos
        # expandidos.
        return (received - prefixes) | expanded

    def _parse_value(self, val):
        if not val:
            raise ValueError(strings.FIELD_LIST_EMPTY)

        parts = [part.strip() for part in val.split(',')]

        # Manejar casos especiales: basico, estandar y completo
        if len(parts) == 1 and parts[0] in [N.BASIC, N.STANDARD, N.COMPLETE]:
            if parts[0] == N.BASIC:
                return tuple(self._basic)
            if parts[0] == N.STANDARD:
                return tuple(self._standard)
            if parts[0] == N.COMPLETE:
                return tuple(self._complete)

        received = set(parts)
        if len(parts) != len(received):
            raise ValueError(strings.FIELD_LIST_REPEATED)

        received = self._expand_prefixes(received)

        # Siempre se agregan los valores básicos
        return tuple(self._basic | received)


class IntParameter(Parameter):
    """Representa un parámetro de tipo entero.

    Se heredan las propiedades y métodos de la clase Parameter, definiendo
    nuevamente el método '_parse_value' para implementar lógica de parseo y
    validación propias de IntParameter, y 'valid_values' para validar uno
    o más parámetros 'max' recibidos en conjunto.

    Attributes:
        _lower_limit (int): Valor mínimo int a aceptar.
        _upper_limit (int): Valor máximo int a aceptar.

    """

    def __init__(self, required=False, default=0, choices=None,
                 lower_limit=None, upper_limit=None):
        self._lower_limit = lower_limit
        self._upper_limit = upper_limit
        super().__init__(required, default, choices)

    def _parse_value(self, val):
        try:
            int_val = int(val)
        except ValueError:
            raise ValueError(strings.INT_VAL_ERROR)

        if self._lower_limit is not None and int_val < self._lower_limit:
            raise ValueError(strings.INT_VAL_SMALL.format(self._lower_limit))

        if self._upper_limit is not None and int_val > self._upper_limit:
            raise ValueError(strings.INT_VAL_BIG.format(self._upper_limit))

        return int_val


class FloatParameter(Parameter):
    """Representa un parámetro de tipo float.

    Se heredan las propiedades y métodos de la clase Parameter, definiendo
    nuevamente el método '_parse_value' para implementar lógica de parseo y
    validación propias de FloatParameter.

    """

    def _parse_value(self, val):
        try:
            num = float(val)
            if not math.isfinite(num):
                raise ValueError()

            return num
        except ValueError:
            raise ValueError(strings.FLOAT_VAL_ERROR)


class AddressParameter(Parameter):
    """Representa un parámetro de tipo dirección de calle (nombre y altura).

    Se heredan las propiedades y métodos de la clase Parameter, definiendo
    nuevamente el método '_parse_value' para implementar lógica de parseo y
    validación propias de AddressParameter.

    Attributes:
        _parser (AddressParser): Parser de direcciones de la librería
            georef-ar-address.
        _parser_lock (threading.Lock): Mutex utilizado para sincronizar el uso
            de '_parser' (ver comentario en '__init__').

    """

    def __init__(self):
        # Se crea el Lock 'self._parser_lock' para evitar problemas con
        # 'self._parser' en contextos de ejecución donde se usen threads, ya
        # que el parser cuenta con un estado interno mutable (su propiedad
        # '_cache'). Si se utilizan threads o no depende de la configuración
        # que se esté usando para los workers de Gunicorn. Por defecto los
        # workers son de tipo 'sync', por lo que se crea un proceso separado
        # por worker (no se usan threads).
        self._parser_lock = threading.Lock()

        cache = utils.LFUDict(constants.ADDRESS_PARSER_CACHE_SIZE)
        self._parser = AddressParser(cache=cache)
        super().__init__(required=True)

    def _parse_value(self, val):
        if not val:
            raise ValueError(strings.STRING_EMPTY)

        with self._parser_lock:
            return self._parser.parse(val)


class IntersectionParameter(Parameter):
    """Representa un parámetro utilizado para especificar búsqueda de entidades
    por intersección geográfica.

    Se heredan las propiedades y métodos de la clase Parameter, definiendo
    nuevamente el método '_parse_value' para implementar lógica de parseo y
    validación propias de IntersectionParameter.

    Attributes:
        _id_params (dict): Diccionario de tipo de entidad a objeto
            IdsParameter.

    """

    def __init__(self, entities, required=False):
        """Inicializa un objeto de tipo IntersectionParameter.

        Args:
            entities (list): Lista de tipos de entidades que debería aceptar el
                parámetro a inicializar.
            required (bool): Indica si el parámetro HTTP debería ser
                obligatorio.

        """
        id_lengths = {
            N.STATE: constants.STATE_ID_LEN,
            N.DEPT: constants.DEPT_ID_LEN,
            N.MUN: constants.MUNI_ID_LEN,
            N.STREET: constants.STREET_ID_LEN
        }

        if any(e not in id_lengths for e in entities):
            raise ValueError('Unknown entity type')

        self._id_params = {}

        for entity in entities:
            self._id_params[entity] = IdsParameter(
                id_length=id_lengths[entity], sep=':')

        super().__init__(required)

    def _parse_value(self, val):
        """Toma un string con una lista de tipos de entidades con IDs, y
        retorna un diccionario con los IDs asociados a los tipos.

        El formato del string debe ser el siguiente:

            <tipo 1>:<ID 1>[:<ID 2>...][,<tipo 2>:<ID 1>[:<ID 2>...]...]

        Ejemplos:

            provincia:02,departamento:90098:02007
            provincia:14,02,06,54
            departamento:02007

        Args:
            val (str): Valor del parámetro recibido vía HTTP.

        Raises:
            ValueError: En caso de que el string recibido no tenga el formato
                adecuado.

        Returns:
            dict: Tipos de entidades asociados a conjuntos de IDs

        """
        if not val:
            raise ValueError(strings.STRING_EMPTY)

        ids = defaultdict(set)

        for part in [p.strip() for p in val.split(',')]:
            sections = [s.strip() for s in part.split(':')]
            if len(sections) < 2:
                raise ParameterValueError(
                    strings.FIELD_INTERSECTION_FORMAT,
                    strings.FIELD_INTERSECTION_FORMAT_HELP)

            entity = sections[0]
            if entity not in self._id_params:
                raise ParameterValueError(
                    strings.FIELD_INTERSECTION_FORMAT,
                    strings.FIELD_INTERSECTION_FORMAT_HELP)

            entity_ids_str = ':'.join(sections[1:])
            entity_ids = self._id_params[entity].get_value(entity_ids_str)

            entity_plural = N.plural(entity)
            ids[entity_plural].update(entity_ids)

        return ids if any(list(ids.values())) else {}


class ParamValidator:
    """Interfaz para realizar una validación de valores de parámetros HTTP.

    Los validadores deben definir un solo método, 'validate_values'.

    """

    def validate_values(self, param_names, values):
        """Realizar una validación de parámetros.

        El método 'validate_values' puede ser llamado en dos contextos:

        1) Al momento de validar valores para un conjunto de parámetros
            distintos. Por ejemplo, el valor de 'max' e 'inicio'. En este caso,
            param_names es un listado de todos los parámetros a validar.

        2) Al momento de validar varios valores para un mismo parámetro (por
            ejemplo, varios valores de 'max' en una request POST). En este
            caso, el valor de param_names es una lista de un solo nombre de
            parámetro.

        Args:
            param_names (list): Lista de nombres de parámetros.
            values (list): Lista de valores leídos y convertidos.

        Raises:
            ValueError: En caso de fallar la validación.

        """
        raise NotImplementedError()


class IntSetSumValidator(ParamValidator):
    """Implementa una validación de parámetros que comprueba que uno o más
    valores sumados no superen un cierto valor.

    Ver la documentación de 'ParamValidator' para detalles de uso.

    Attributes:
        _upper_limit (int): Suma máxima permitida.

    """

    def __init__(self, upper_limit):
        self._upper_limit = upper_limit

    def validate_values(self, param_names, values):
        if sum(values) > self._upper_limit:
            names = ', '.join('\'{}\''.format(name) for name in param_names)
            raise ValueError(
                strings.INT_VAL_BIG_GLOBAL.format(names, self._upper_limit))


class ParametersParseResult:
    """Representa el resultado de parsear un conjunto de parámetros (de un
    endpoint).

    Attributes:
        _values (dict): Valor parseado por cada parámetro.
        _received (set): Conjunto de parámetros que fueron recibidos. Los
            parámetros no incluidos en este conjunto tomaron obligatoriamente
            su valor default. Se usta este atributo para determinar cuáles
            parámetros deben mostrarse al usuario bajo el campo 'params'.

    """

    __slots__ = ['_values', '_received']

    def __init__(self):
        """Inicializa un objeto de tipo 'ParametersParseResult'.

        """
        self._values = {}
        self._received = set()

    def add_value(self, param_name, value):
        """Agrega el valor de un parámetro parseado.

        Args:
            param_name (str): Nombre del parámetro.
            value (object): Valor parseado (no el string recibido).

        """
        self._values[param_name] = value

    def mark_received(self, param_name):
        """Marca un parámetro como recibido externamente.

        Args:
            param_name (str): Nombre del parámetro recibido.

        """
        self._received.add(param_name)

    @property
    def values(self):
        return self._values

    def received_values(self):
        """Retorna un diccionario conteniendo solo los parámetros recibidos.

        Returns:
            dict: Diccionario de nombre de parámetro-valor, solo conteniendo
                parámetros recibidos externamente (no defaults).

        """
        return {name: self._values[name] for name in self._received}


class EndpointParameters:
    """Representa un conjunto de parámetros para un endpoint HTTP.

    Attributes:
        _get_qs_params (dict): Diccionario de parámetros aceptados vía
            querystring en requests GET, siendo las keys los nombres de los
            parámetros que se debe usar al especificarlos, y los valores
            objetos de tipo Parameter.

        _shared_params (dict): Similar a 'get_qs_params', pero contiene
            parámetros aceptados vía querystring en requests GET Y parámetros
            aceptados vía body en requests POST (compartidos).

        _cross_validators (list): Lista de tuplas (validador, [nombres]), que
            representa los validadores utilizados para validar distintos
            parámetros como conjuntos. Por ejemplo, los parámetros 'max' e
            'inicio' deben cumplir, en conjunto, la condición de no sumar
            más de un valor específico.

        _set_validators (dict): Diccionario de (nombre de parámetro -
            validador), utilizado para realizar validaciones sobre conjuntos de
            valores para un mismo parámetro. Este tipo de validaciones es
            utilizado cuando se procesan los requests POST, donde el usuario
            puede enviar varias consultas, con parámetros repetidos entre
            consultas.

    """

    def __init__(self, shared_params=None, get_qs_params=None):
        """Inicializa un objeto de tipo EndpointParameters.

        Args:
            get_qs_params (dict): Ver atributo 'get_qs_params'.
            shared_params (dict): Ver atributo 'shared_params'.

        """
        shared_params = shared_params or {}
        get_qs_params = get_qs_params or {}

        self._get_qs_params = {**get_qs_params, **shared_params}
        self._post_body_params = shared_params

        self._cross_validators = []
        self._set_validators = defaultdict(list)

    def with_cross_validator(self, param_names, validator):
        """Agrega un validador a la lista de validadores para grupos de
        parámetros.

        Args:
            param_names (list): Lista de nombres de parámetros sobre los cuales
                ejecutar el validador.
            validator (ParamValidator): Validador de valores.

        """
        self._cross_validators.append((validator, param_names))
        return self

    def with_set_validator(self, param_name, validator):
        """Agrega un validador a la lista de validadores para conjuntos de
        valores para un parámetro.

        Args:
            param_name (str): Nombre del parámetro a utilizar en la validación
                de conjuntos de valores.
            validator (ParamValidator): Validador de valores.

        """
        self._set_validators[param_name].append(validator)
        return self

    def _parse_params_dict(self, params, received, from_source):
        """Parsea parámetros (clave-valor) recibidos en una request HTTP,
        utilizando el conjunto 'params' de parámetros.

        Args:
            params (dict): Diccionario de objetos Parameter (nombre-Parameter).
            received (dict): Parámetros recibidos sin procesar (nombre-valor).
            from_source (str): Ubicación dentro de la request HTTP donde fueron
                recibidos los parámetros.

        Returns:
            ParametersParseResult: Objeto con la información de todos los
                parámetros recibidos, con sus valores.

        Raises:
            ParametersParseException: Excepción con errores de parseo
                de parámetros.

        """
        results = ParametersParseResult()
        errors = {}
        # Cuando ser reciben parámetros vía querystring, se pueden llegar a
        # tener varios valores bajo una misma key (ver clase
        # werkzeug.MultiDict).
        is_multi_dict = hasattr(received, 'getlist')

        for param_name, param in params.items():
            received_val = received.get(param_name)

            if is_multi_dict and len(received.getlist(param_name)) > 1:
                errors[param_name] = ParamError(ParamErrorType.REPEATED,
                                                strings.REPEATED_ERROR,
                                                from_source)
                continue

            try:
                parsed = param.get_value(received_val)
                results.add_value(param_name, parsed)
            except ParameterRequiredException:
                errors[param_name] = ParamError(ParamErrorType.PARAM_REQUIRED,
                                                strings.MISSING_ERROR.format(
                                                    param_name),
                                                from_source)
            except ValueError as e:
                errors[param_name] = ParamError(ParamErrorType.VALUE_ERROR,
                                                str(e), from_source)
            except ParameterValueError as e:
                errors[param_name] = ParamError(ParamErrorType.VALUE_ERROR,
                                                e.message, from_source, e.help)
            except InvalidChoiceException as e:
                errors[param_name] = ParamError(ParamErrorType.INVALID_CHOICE,
                                                str(e), from_source,
                                                param.choices)

        for param_name in received:
            if param_name not in params:
                errors[param_name] = ParamError(ParamErrorType.UNKNOWN_PARAM,
                                                strings.UNKNOWN_ERROR,
                                                from_source,
                                                list(params.keys()))
            else:
                results.mark_received(param_name)

        if errors:
            # Si no se especificó un formato válido, utilizar JSON para mostrar
            # los errores.
            fmt = results.values.get(N.FORMAT, 'json')
            raise ParametersParseException(errors, fmt)

        self._cross_validate_params(results, from_source)
        return results

    def _cross_validate_params(self, parsed, from_source):
        """Ejecuta las validaciones de conjuntos de parámetros distintos. Por
        ejemplo, un validador puede comprobar que la suma de los parámetros
        'max' e 'inicio' no superen un cierto valor.

        Args:
            parsed (ParametersParseResult): Objeto donde se almacenan los
                resultados del parseo de argumentos para una consulta.
            from_source (str): Ubicación dentro de la request HTTP donde fueron
                recibidos los parámetros.

        Raises:
            ParametersParseException: Se lanza la excepción si no se pasó una
                validación instalada para conjuntos de parámetros.

        """
        errors = {}

        for validator, param_names in self._cross_validators:
            values = [parsed.values[name] for name in param_names]
            try:
                validator.validate_values(param_names, values)
            except ValueError as e:
                for param in param_names:
                    errors[param] = ParamError(ParamErrorType.INVALID_SET,
                                               str(e), from_source)

                # Si se encontraron errores al validar uno o más parámetros,
                # utilizar el primer error encontrado.
                break

        if errors:
            raise ParametersParseException(errors)

    def _validate_param_sets(self, results):
        """Ejecuta las validaciones de conjuntos de valores para un parámetro.
        Por ejemplo, un validador puede comprobar que la suma de todos los
        parámetros 'max' en una request POST no supere un cierto valor. Notar
        que esta validación solo se utiliza en requests POST ya que es el único
        contexto donde se pueden recibir varios valores de un mismo parámetro
        (ya que se repiten parámetros entre consultas recibidas).

        Args:
            results (list): Lista de ParametersParseResult, cada uno contiene
                los resultados de parsear los parámetros de una consulta.

        Raises:
            ParametersParseException: Se lanza la excepción si no se pasó una
                validación instalada para conjuntos de valores.

        """
        # Comenzar con un diccionario de errores vacío por cada consulta.
        errors_list = [{} for _ in range(len(results))]

        for name in self._post_body_params.keys():
            validators = self._set_validators[name]

            for validator in validators:
                try:
                    # Validar conjuntos de valores de parámetros bajo el
                    # mismo nombre
                    validator.validate_values([name],
                                              (result.values[name]
                                               for result in results))
                except ValueError as e:
                    error = ParamError(ParamErrorType.INVALID_SET, str(e),
                                       'body')

                    # Si la validación no fue exitosa, crear un error y
                    # agregarlo al conjunto de errores de cada consulta que lo
                    # utilizó.
                    for errors in errors_list:
                        errors[name] = error

                    # Se muestra solo el error de la primera validación
                    # fallida.
                    break

        # Luego de validar conjuntos, lanzar una excepción si se generaron
        # errores nuevos
        if any(errors_list):
            raise ParametersParseException(errors_list)

    def parse_post_params(self, qs_params, body, body_key):
        """Parsea parámetros (clave-valor) recibidos en una request HTTP
        POST utilizando el conjunto de parámetros internos. Se parsean por
        separado los parámetros querystring y los parámetros de body.

        Args:
            qs_params (dict): Parámetros recibidos en el query string.
            body_params (dict): Datos JSON recibidos vía POST.
            body_key (str): Nombre de la key bajo donde debería estar la lista
                de consultas recibias vía POST, en 'body_params'.

        Returns:
            list: lista de ParametersParseResult.

        Raises:
            ParametersParseException: Excepción con errores de parseo
                de parámetros.

        """
        if qs_params:
            # No aceptar parámetros de querystring en bulk
            raise ParametersParseException([
                {'querystring': ParamError(ParamErrorType.INVALID_LOCATION,
                                           strings.BULK_QS_INVALID,
                                           'querystring')}
            ])

        body_params = body.get(body_key) if isinstance(body, dict) else None

        if not body_params or not isinstance(body_params, list):
            # No aceptar operaciones bulk que no sean listas, y no
            # aceptar listas vacías.
            raise ParametersParseException([
                {body_key: ParamError(ParamErrorType.INVALID_BULK,
                                      strings.INVALID_BULK.format(body_key),
                                      'body')}
            ])

        if len(body_params) > constants.MAX_BULK_LEN:
            raise ParametersParseException([
                {body_key: ParamError(
                    ParamErrorType.INVALID_BULK_LEN,
                    strings.BULK_LEN_ERROR.format(constants.MAX_BULK_LEN),
                    'body')}
            ])

        results, errors_list = [], []
        for param_dict in body_params:
            parsed = None
            errors = {}
            if hasattr(param_dict, 'get'):
                try:
                    parsed = self._parse_params_dict(self._post_body_params,
                                                     param_dict, 'body')
                except ParametersParseException as e:
                    errors = e.errors
            else:
                errors[body_key] = ParamError(
                    ParamErrorType.INVALID_BULK_ENTRY,
                    strings.INVALID_BULK_ENTRY, 'body')

            results.append(parsed)
            errors_list.append(errors)

        if any(errors_list):
            raise ParametersParseException(errors_list)

        self._validate_param_sets(results)
        return results

    def parse_get_params(self, qs_params):
        """Parsea parámetros (clave-valor) recibidos en una request HTTP GET
        utilizando el conjunto de parámetros internos.

        Args:
            qs_params (dict): Parámetros recibidos en el query string.

        Returns:
            ParametersParseResult: Valor de retorno de 'parse_dict_params'.

        Raises:
            ParametersParseException: Excepción con errores de parseo
                de parámetros.

        """
        return self._parse_params_dict(self._get_qs_params, qs_params,
                                       'querystring')


PARAMS_STATES = EndpointParameters(shared_params={
    N.ID: IdsParameter(id_length=constants.STATE_ID_LEN),
    N.NAME: StrParameter(),
    N.INTERSECTION: IntersectionParameter(entities=[N.DEPT, N.MUN, N.STREET]),
    N.ORDER: StrParameter(choices=[N.ID, N.NAME]),
    N.FLATTEN: BoolParameter(),
    N.FIELDS: FieldListParameter(basic=[N.ID, N.NAME],
                                 standard=[N.C_LAT, N.C_LON],
                                 complete=[N.SOURCE, N.COMPLETE_NAME, N.ISO_ID,
                                           N.ISO_NAME, N.CATEGORY]),
    N.MAX: IntParameter(default=24, lower_limit=1,
                        upper_limit=constants.MAX_RESULT_LEN),
    N.OFFSET: IntParameter(lower_limit=0,
                           upper_limit=constants.MAX_RESULT_WINDOW),
    N.EXACT: BoolParameter()
}, get_qs_params={
    N.FORMAT: StrParameter(default='json',
                           choices=['json', 'csv', 'geojson', 'xml', 'shp'])
}).with_set_validator(
    N.MAX,
    IntSetSumValidator(upper_limit=constants.MAX_RESULT_LEN)
).with_cross_validator(
    [N.MAX, N.OFFSET],
    IntSetSumValidator(upper_limit=constants.MAX_RESULT_WINDOW)
)

PARAMS_DEPARTMENTS = EndpointParameters(shared_params={
    N.ID: IdsParameter(id_length=constants.DEPT_ID_LEN),
    N.NAME: StrParameter(),
    N.INTERSECTION: IntersectionParameter(entities=[N.STATE, N.MUN, N.STREET]),
    N.STATE: CompoundParameter([IdsParameter(constants.STATE_ID_LEN),
                                StrParameter()]),
    N.ORDER: StrParameter(choices=[N.ID, N.NAME]),
    N.FLATTEN: BoolParameter(),
    N.FIELDS: FieldListParameter(basic=[N.ID, N.NAME],
                                 standard=[N.C_LAT, N.C_LON, N.STATE_ID,
                                           N.STATE_NAME],
                                 complete=[N.SOURCE, N.STATE_INTERSECTION,
                                           N.COMPLETE_NAME, N.CATEGORY]),
    N.MAX: IntParameter(default=10, lower_limit=1,
                        upper_limit=constants.MAX_RESULT_LEN),
    N.OFFSET: IntParameter(lower_limit=0,
                           upper_limit=constants.MAX_RESULT_WINDOW),
    N.EXACT: BoolParameter()
}, get_qs_params={
    N.FORMAT: StrParameter(default='json',
                           choices=['json', 'csv', 'geojson', 'xml', 'shp'])
}).with_set_validator(
    N.MAX,
    IntSetSumValidator(upper_limit=constants.MAX_RESULT_LEN)
).with_cross_validator(
    [N.MAX, N.OFFSET],
    IntSetSumValidator(upper_limit=constants.MAX_RESULT_WINDOW)
)

PARAMS_MUNICIPALITIES = EndpointParameters(shared_params={
    N.ID: IdsParameter(id_length=constants.MUNI_ID_LEN),
    N.NAME: StrParameter(),
    N.INTERSECTION: IntersectionParameter(entities=[N.DEPT, N.STATE,
                                                    N.STREET]),
    N.STATE: CompoundParameter([IdsParameter(constants.STATE_ID_LEN),
                                StrParameter()]),
    N.ORDER: StrParameter(choices=[N.ID, N.NAME]),
    N.FLATTEN: BoolParameter(),
    N.FIELDS: FieldListParameter(basic=[N.ID, N.NAME],
                                 standard=[N.C_LAT, N.C_LON, N.STATE_ID,
                                           N.STATE_NAME],
                                 complete=[N.SOURCE, N.STATE_INTERSECTION,
                                           N.CATEGORY, N.COMPLETE_NAME]),
    N.MAX: IntParameter(default=10, lower_limit=1,
                        upper_limit=constants.MAX_RESULT_LEN),
    N.OFFSET: IntParameter(lower_limit=0,
                           upper_limit=constants.MAX_RESULT_WINDOW),
    N.EXACT: BoolParameter()
}, get_qs_params={
    N.FORMAT: StrParameter(default='json',
                           choices=['json', 'csv', 'geojson', 'xml', 'shp'])
}).with_set_validator(
    N.MAX,
    IntSetSumValidator(upper_limit=constants.MAX_RESULT_LEN)
).with_cross_validator(
    [N.MAX, N.OFFSET],
    IntSetSumValidator(upper_limit=constants.MAX_RESULT_WINDOW)
)

PARAMS_CENSUS_LOCALITIES = EndpointParameters(shared_params={
    N.ID: IdsParameter(id_length=constants.CENSUS_LOCALITY_ID_LEN),
    N.NAME: StrParameter(),
    N.STATE: CompoundParameter([IdsParameter(constants.STATE_ID_LEN),
                                StrParameter()]),
    N.DEPT: CompoundParameter([IdsParameter(constants.DEPT_ID_LEN),
                               StrParameter()]),
    N.MUN: CompoundParameter([IdsParameter(constants.MUNI_ID_LEN),
                              StrParameter()]),
    N.ORDER: StrParameter(choices=[N.ID, N.NAME]),
    N.FLATTEN: BoolParameter(),
    N.FIELDS: FieldListParameter(basic=[N.ID, N.NAME],
                                 standard=[N.C_LAT, N.C_LON, N.STATE_ID,
                                           N.STATE_NAME, N.DEPT_ID,
                                           N.DEPT_NAME, N.MUN_ID, N.MUN_NAME,
                                           N.CATEGORY, N.FUNCTION],
                                 complete=[N.SOURCE]),
    N.MAX: IntParameter(default=10, lower_limit=1,
                        upper_limit=constants.MAX_RESULT_LEN),
    N.OFFSET: IntParameter(lower_limit=0,
                           upper_limit=constants.MAX_RESULT_WINDOW),
    N.EXACT: BoolParameter()
}, get_qs_params={
    N.FORMAT: StrParameter(default='json',
                           choices=['json', 'csv', 'geojson', 'xml', 'shp'])
}).with_set_validator(
    N.MAX,
    IntSetSumValidator(upper_limit=constants.MAX_RESULT_LEN)
).with_cross_validator(
    [N.MAX, N.OFFSET],
    IntSetSumValidator(upper_limit=constants.MAX_RESULT_WINDOW)
)

PARAMS_SETTLEMENTS = EndpointParameters(shared_params={
    N.ID: IdsAlphamericTwoLengthParameter(*constants.SETTLEMENT_ID_LEN),
    N.NAME: StrParameter(),
    N.STATE: CompoundParameter([IdsParameter(constants.STATE_ID_LEN),
                                StrParameter()]),
    N.DEPT: CompoundParameter([IdsParameter(constants.DEPT_ID_LEN),
                               StrParameter()]),
    N.MUN: CompoundParameter([IdsParameter(constants.MUNI_ID_LEN),
                              StrParameter()]),
    N.CENSUS_LOCALITY: CompoundParameter([
        IdsParameter(constants.CENSUS_LOCALITY_ID_LEN),
        StrParameter()
    ]),
    N.ORDER: StrParameter(choices=[N.ID, N.NAME]),
    N.FLATTEN: BoolParameter(),
    N.FIELDS: FieldListParameter(basic=[N.ID, N.NAME],
                                 standard=[N.C_LAT, N.C_LON, N.STATE_ID,
                                           N.STATE_NAME, N.DEPT_ID,
                                           N.DEPT_NAME, N.MUN_ID, N.MUN_NAME,
                                           N.CENSUS_LOCALITY_ID,
                                           N.CENSUS_LOCALITY_NAME,
                                           N.CATEGORY],
                                 complete=[N.SOURCE]),
    N.MAX: IntParameter(default=10, lower_limit=1,
                        upper_limit=constants.MAX_RESULT_LEN),
    N.OFFSET: IntParameter(lower_limit=0,
                           upper_limit=constants.MAX_RESULT_WINDOW),
    N.EXACT: BoolParameter()
}, get_qs_params={
    N.FORMAT: StrParameter(default='json',
                           choices=['json', 'csv', 'geojson', 'xml', 'shp'])
}).with_set_validator(
    N.MAX,
    IntSetSumValidator(upper_limit=constants.MAX_RESULT_LEN)
).with_cross_validator(
    [N.MAX, N.OFFSET],
    IntSetSumValidator(upper_limit=constants.MAX_RESULT_WINDOW)
)

PARAMS_LOCALITIES = EndpointParameters(shared_params={
    N.ID: IdsTwoLengthParameter(*constants.LOCALITY_ID_LEN),
    N.NAME: StrParameter(),
    N.STATE: CompoundParameter([IdsParameter(constants.STATE_ID_LEN),
                                StrParameter()]),
    N.DEPT: CompoundParameter([IdsParameter(constants.DEPT_ID_LEN),
                               StrParameter()]),
    N.MUN: CompoundParameter([IdsParameter(constants.MUNI_ID_LEN),
                              StrParameter()]),
    N.CENSUS_LOCALITY: CompoundParameter([
        IdsParameter(constants.CENSUS_LOCALITY_ID_LEN),
        StrParameter()
    ]),
    N.ORDER: StrParameter(choices=[N.ID, N.NAME]),
    N.FLATTEN: BoolParameter(),
    N.FIELDS: FieldListParameter(basic=[N.ID, N.NAME],
                                 standard=[N.C_LAT, N.C_LON, N.STATE_ID,
                                           N.STATE_NAME, N.DEPT_ID,
                                           N.DEPT_NAME, N.MUN_ID, N.MUN_NAME,
                                           N.CENSUS_LOCALITY_ID,
                                           N.CENSUS_LOCALITY_NAME,
                                           N.CATEGORY],
                                 complete=[N.SOURCE]),
    N.MAX: IntParameter(default=10, lower_limit=1,
                        upper_limit=constants.MAX_RESULT_LEN),
    N.OFFSET: IntParameter(lower_limit=0,
                           upper_limit=constants.MAX_RESULT_WINDOW),
    N.EXACT: BoolParameter()
}, get_qs_params={
    N.FORMAT: StrParameter(default='json',
                           choices=['json', 'csv', 'geojson', 'xml', 'shp'])
}).with_set_validator(
    N.MAX,
    IntSetSumValidator(upper_limit=constants.MAX_RESULT_LEN)
).with_cross_validator(
    [N.MAX, N.OFFSET],
    IntSetSumValidator(upper_limit=constants.MAX_RESULT_WINDOW)
)

_ADDRESSES_BASIC_FIELDS = [
    N.DOOR_NUM_VAL,
    N.STREET_ID, N.STREET_NAME,
    N.STREET_X1_ID, N.STREET_X1_NAME,
    N.STREET_X2_ID, N.STREET_X2_NAME,
    N.FULL_NAME
]

_ADDRESSES_STANDARD_FIELDS = [
    N.STATE_ID, N.STATE_NAME,
    N.DEPT_ID, N.DEPT_NAME,
    N.CENSUS_LOCALITY_ID, N.CENSUS_LOCALITY_NAME,
    N.DOOR_NUM_UNIT,
    N.FLOOR,
    N.STREET_CATEGORY,
    N.STREET_X1_CATEGORY,
    N.STREET_X2_CATEGORY,
    N.LOCATION_LAT, N.LOCATION_LON
]

_ADDRESSES_COMPLETE_FIELDS = [
    N.SOURCE
]

PARAMS_ADDRESSES = EndpointParameters(shared_params={
    N.ADDRESS: AddressParameter(),
    N.STATE: CompoundParameter([IdsParameter(constants.STATE_ID_LEN),
                                StrParameter()]),
    N.DEPT: CompoundParameter([IdsParameter(constants.DEPT_ID_LEN),
                               StrParameter()]),
    N.CENSUS_LOCALITY: CompoundParameter([
        IdsParameter(constants.CENSUS_LOCALITY_ID_LEN),
        StrParameter()
    ]),
    N.LOCALITY: CompoundParameter([IdsTwoLengthParameter(*constants.LOCALITY_ID_LEN),
                                   StrParameter()]),
    N.ORDER: StrParameter(choices=[N.ID, N.NAME]),
    N.FLATTEN: BoolParameter(),
    N.FIELDS: FieldListParameter(basic=_ADDRESSES_BASIC_FIELDS,
                                 standard=_ADDRESSES_STANDARD_FIELDS,
                                 complete=_ADDRESSES_COMPLETE_FIELDS),
    N.MAX: IntParameter(default=10, lower_limit=1,
                        upper_limit=constants.MAX_RESULT_LEN),
    N.OFFSET: IntParameter(lower_limit=0,
                           upper_limit=constants.MAX_RESULT_WINDOW),
    N.EXACT: BoolParameter()
}, get_qs_params={
    N.FORMAT: StrParameter(default='json',
                           choices=['json', 'csv', 'geojson', 'xml'])
}).with_set_validator(
    N.MAX,
    IntSetSumValidator(upper_limit=constants.MAX_RESULT_LEN)
).with_cross_validator(
    [N.MAX, N.OFFSET],
    IntSetSumValidator(upper_limit=constants.MAX_RESULT_WINDOW)
)

PARAMS_STREETS = EndpointParameters(shared_params={
    N.ID: IdsParameter(id_length=constants.STREET_ID_LEN),
    N.NAME: StrParameter(),
    N.INTERSECTION: IntersectionParameter(entities=[N.STREET, N.MUN, N.DEPT,
                                                    N.STATE]),
    N.CATEGORY: StrParameter(),
    N.STATE: CompoundParameter([IdsParameter(constants.STATE_ID_LEN),
                                StrParameter()]),
    N.DEPT: CompoundParameter([IdsParameter(constants.DEPT_ID_LEN),
                               StrParameter()]),
    N.CENSUS_LOCALITY: CompoundParameter([
        IdsParameter(constants.CENSUS_LOCALITY_ID_LEN),
        StrParameter()
    ]),
    N.ORDER: StrParameter(choices=[N.ID, N.NAME]),
    N.FLATTEN: BoolParameter(),
    N.FIELDS: FieldListParameter(basic=[N.ID, N.NAME],
                                 standard=[N.START_R, N.START_L, N.END_R,
                                           N.END_L, N.STATE_ID, N.STATE_NAME,
                                           N.DEPT_ID, N.DEPT_NAME,
                                           N.CENSUS_LOCALITY_ID,
                                           N.CENSUS_LOCALITY_NAME, N.FULL_NAME,
                                           N.CATEGORY],
                                 complete=[N.SOURCE]),
    N.MAX: IntParameter(default=10, lower_limit=1,
                        upper_limit=constants.MAX_RESULT_LEN),
    N.OFFSET: IntParameter(lower_limit=0,
                           upper_limit=constants.MAX_RESULT_WINDOW),
    N.EXACT: BoolParameter()
}, get_qs_params={
    N.FORMAT: StrParameter(default='json',
                           choices=['json', 'csv', 'xml', 'shp'])
}).with_set_validator(
    N.MAX,
    IntSetSumValidator(upper_limit=constants.MAX_RESULT_LEN)
).with_cross_validator(
    [N.MAX, N.OFFSET],
    IntSetSumValidator(upper_limit=constants.MAX_RESULT_WINDOW)
)

PARAMS_LOCATION = EndpointParameters(shared_params={
    N.LAT: FloatParameter(required=True),
    N.LON: FloatParameter(required=True),
    N.FLATTEN: BoolParameter(),
    N.FIELDS: FieldListParameter(basic=[N.STATE_ID, N.STATE_NAME, N.LAT,
                                        N.LON],
                                 standard=[N.DEPT_ID, N.DEPT_NAME, N.MUN_ID,
                                           N.MUN_NAME],
                                 complete=[N.STATE_SOURCE, N.DEPT_SOURCE,
                                           N.MUN_SOURCE])
}, get_qs_params={
    N.FORMAT: StrParameter(default='json', choices=['json', 'geojson', 'xml'])
})
