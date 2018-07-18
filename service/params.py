import service.names as N
from service import strings

import re
from enum import Enum, unique
from collections import namedtuple

# TODO: Mover a archivo de configuración
MAX_BULK_LEN = 100


class ParameterRequiredException(Exception):
    pass


class InvalidChoiceException(Exception):
    pass


class InvalidLocationException(Exception):
    pass


@unique
class ParamErrorType(Enum):
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


class Parameter:
    def __init__(self, required=False, default=None, choices=None,
                 source='any'):
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
        return val in self.choices

    def _parse_value(self, val):
        raise NotImplementedError()


class StrParameter(Parameter):
    def _parse_value(self, val):
        if not val:
            raise ValueError(strings.STRING_EMPTY)

        return val


class BoolParameter(Parameter):
    def __init__(self, required=False, default=False):
        super().__init__(required, default, [True, False])

    def _parse_value(self, val):
        # Cualquier valor recibido (no nulo) es verdadero
        return val is not None


class StrListParameter(Parameter):
    def __init__(self, required=False, constants=None, optionals=None):
        self.constants = set(constants) if constants else set()

        optionals = set(optionals) if optionals else set()

        super().__init__(required, [], self.constants | optionals)

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
    def _parse_value(self, val):
        try:
            return int(val)
        except ValueError:
            raise ValueError(strings.INT_VAL_ERROR)


class FloatParameter(Parameter):
    def _parse_value(self, val):
        try:
            return float(val)
        except ValueError:
            raise ValueError(strings.FLOAT_VAL_ERROR)


class AddressParameter(Parameter):
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
    def __init__(self, params):
        self.params = params

    def parse_params_dict(self, received, from_source):
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
        return self.parse_params_dict(qs_params, 'querystring')


PARAMS_STATES = ParameterSet({
    N.ID: StrParameter(),
    N.NAME: StrParameter(),
    N.ORDER: StrParameter(choices=[N.ID, N.NAME]),
    N.FIELDS: StrListParameter(constants=[N.ID, N.NAME, N.SOURCE],
                               optionals=[N.LAT, N.LON]),
    N.MAX: IntParameter(default=24),
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
                               optionals=[N.LAT, N.LON, N.STATE]),
    N.MAX: IntParameter(default=10),
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
                               optionals=[N.LAT, N.LON, N.STATE, N.DEPT]),
    N.MAX: IntParameter(default=10),
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
                               optionals=[N.LAT, N.LON, N.STATE, N.DEPT, N.MUN,
                                          N.LOCALITY_TYPE]),
    N.MAX: IntParameter(default=10),
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
    N.FIELDS: StrListParameter(constants=[N.ID, N.NAME, N.LOCATION,
                                          N.DOOR_NUM, N.SOURCE],
                               optionals=[N.STATE, N.DEPT, N.ROAD_TYPE,
                                          N.FULL_NAME]),
    N.MAX: IntParameter(default=10),
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
                                          N.END_L, N.STATE, N.DEPT,
                                          N.FULL_NAME, N.ROAD_TYPE]),
    N.MAX: IntParameter(default=10),
    N.EXACT: BoolParameter(),
    N.FORMAT: StrParameter(default='json', choices=['json', 'csv'],
                           source='querystring')
})

PARAMS_PLACE = ParameterSet({
    N.LAT: FloatParameter(required=True),
    N.LON: FloatParameter(required=True),
    N.FLATTEN: BoolParameter(),
    N.FIELDS: StrListParameter(constants=[N.STATE, N.SOURCE],
                               optionals=[N.DEPT, N.MUN, N.LAT, N.LON]),
    N.FORMAT: StrParameter(default='json', choices=['json', 'geojson'],
                           source='querystring')
})
