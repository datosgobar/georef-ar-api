import service.names as N
from service import strings

import re
from enum import Enum, unique
from collections import namedtuple


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
    EMPTY_BULK = 1004
    INVALID_LOCATION = 1005


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

        for param_name, param in self.params.items():
            received_val = received.get(param_name, None)

            try:
                parsed_val = param.get_value(received_val, from_source)
                parsed[param_name] = parsed_val
            except ParameterRequiredException:
                errors[param_name] = ParamError(ParamErrorType.PARAM_REQUIRED,
                                                None, from_source)
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
                                                None, from_source)

        return parsed, errors

    def parse_params_dict_list(self, received, from_source):
        if not received and from_source == 'body':
            # No aceptar una lista vacía de operaciones bulk
            return [], [
                {'json': ParamError(ParamErrorType.EMPTY_BULK,
                                    strings.EMPTY_BULK, from_source)}
            ]

        results, results_errors = [], []
        for param_dict in received:
            parsed, errors = self.parse_params_dict(param_dict, from_source)
            results.append(parsed)
            results_errors.append(errors)

        return results, results_errors


PARAMS_STATES = ParameterSet({
    N.ID: StrParameter(),
    N.NAME: StrParameter(),
    N.ORDER: StrParameter(choices=[N.ID, N.NAME]),
    N.FIELDS: StrListParameter(constants=[N.ID, N.NAME, N.SOURCE, N.SOURCE],
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
    N.FIELDS: StrListParameter(constants=[N.ID, N.NAME, N.SOURCE,
                                          N.LOCATION, N.DOOR_NUM],
                               optionals=[N.STATE, N.DEPT, N.ROAD_TYPE,
                                          N.FULL_NAME]),
    N.MAX: IntParameter(default=10),
    N.EXACT: BoolParameter(),
    N.FORMAT: StrParameter(default='json', choices=['json', 'csv'],
                           source='querystring')
})

PARAMS_STREETS = ParameterSet({
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
    N.FIELDS: StrListParameter(constants=[N.STATE],
                               optionals=[N.DEPT, N.MUN, N.LAT, N.LON]),
    N.FORMAT: StrParameter(default='json', choices=['json', 'geojson'],
                           source='querystring')
})
