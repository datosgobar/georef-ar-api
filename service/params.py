import service.names as N
import re
from enum import Enum, auto


class ParameterRequiredException(Exception):
    pass


class InvalidChoiceException(Exception):
    pass


class ParamError(Enum):
    UNKNOWN_PARAM = auto()
    VALUE_ERROR = auto()
    INVALID_CHOICE = auto()
    PARAM_REQUIRED = auto()
    EMPTY_BULK = auto()


class Parameter:
    def __init__(self, required=False, default=None, choices=None):
        if required and default is not None:
            raise ValueError(
                'Los parámetros obligatorios no pueden tener valor default.')

        self.choices = choices
        self.required = required
        self.default = default

        if choices and \
           default is not None \
           and not self._value_in_choices(default):
            raise ValueError('El valor default no se encuentra \
                              dentro de las opciones de valores.')

    def get_value(self, val):
        if val is None:
            if self.required:
                raise ParameterRequiredException()
            else:
                return self.default

        parsed = self._parse_value(val)

        if self.choices and not self._value_in_choices(parsed):
            raise InvalidChoiceException()

        return parsed

    def _value_in_choices(self, val):
        return val in self.choices

    def _parse_value(self, val):
        raise NotImplementedError()


class StrParameter(Parameter):
    def _parse_value(self, val):
        if not val:
            raise ValueError()

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
        if val is None:
            raise ValueError()

        received = set(part.strip() for part in val.split(','))
        # Siempre se agregan los valores constantes
        return list(self.constants | received)


class IntParameter(Parameter):
    def _parse_value(self, val):
        return int(val)


class FloatParameter(Parameter):
    def _parse_value(self, val):
        return float(val)


class AddressParameter(Parameter):
    def __init__(self):
        super().__init__(required=True)

    def _parse_value(self, val):
        # TODO: Revisar expresiones regulares
        match = re.search(r'(\s[0-9]+?)$', val)
        number = int(match.group(1)) if match else None
        if not number:
            raise ValueError()

        road_name = re.sub(r'(\s[0-9]+?)$', r'', val)

        if not road_name:
            raise ValueError()

        return road_name.strip(), number


class ParameterSet():
    def __init__(self, params):
        self.params = params

    def parse_params_dict(self, received):
        parsed, errors = {}, {}

        for param_name, param in self.params.items():
            received_val = received.get(param_name, None)

            try:
                parsed_val = param.get_value(received_val)
                parsed[param_name] = parsed_val
            except ParameterRequiredException:
                errors[param_name] = ParamError.PARAM_REQUIRED
            except ValueError:
                errors[param_name] = ParamError.VALUE_ERROR
            except InvalidChoiceException:
                errors[param_name] = ParamError.INVALID_CHOICE

        for param_name in received:
            if param_name not in self.params:
                errors[param_name] = ParamError.UNKNOWN_PARAM

        return parsed, errors

    def parse_params_dict_list(self, received):
        results = []
        for param_dict in received:
            parsed, errors = self.parse_params_dict(param_dict)
            results.append((parsed, errors))

        return results


PARAMS_STATES = ParameterSet({
    N.ID: StrParameter(),
    N.NAME: StrParameter(),
    N.ORDER: StrParameter(choices=[N.ID, N.NAME]),
    N.FIELDS: StrListParameter(constants=[N.ID, N.NAME, N.SOURCE, N.SOURCE],
                               optionals=[N.LAT, N.LON]),
    N.MAX: IntParameter(default=24),
    N.EXACT: BoolParameter()
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
    N.EXACT: BoolParameter()
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
    N.EXACT: BoolParameter()
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
    N.EXACT: BoolParameter()
})

PARAMS_ADDRESSES = ParameterSet({
    N.ADDRESS: AddressParameter(),
    N.ROAD_TYPE: StrParameter(),
    N.STATE: StrParameter(),
    N.DEPT: StrParameter(),
    N.FLATTEN: BoolParameter(),
    N.FIELDS: StrListParameter(constants=[N.ID, N.NAME, N.DOOR_NUM, N.SOURCE],
                               optionals=[N.STATE, N.DEPT, N.LOCATION,
                                          N.FULL_NAME, N.ROAD_TYPE]),
    N.MAX: IntParameter(default=10),
    N.EXACT: BoolParameter()
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
    N.EXACT: BoolParameter()
})

PARAMS_PLACE = ParameterSet({
    N.LAT: FloatParameter(required=True),
    N.LON: FloatParameter(required=True),
    N.FLATTEN: BoolParameter(),
    N.FIELDS: StrListParameter(constants=[N.STATE],
                               optionals=[N.DEPT, N.MUN, N.LAT, N.LON])
})
