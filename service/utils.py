"""Módulo 'utils' de georef-ar-api

Contiene funciones y clases de varias utilidades.
"""

from flask.json import JSONEncoder
from georef_ar_address.address_data import AddressData
from service import names as N

_ADDRESS_TYPES = {
    'simple': 'simple',
    'intersection': 'interseccion',
    'between': 'entre_calles'
}


class LFUDict:
    """Diccionario LFU ("Least Frequently Used").

    Implementa un diccionario similar a dict que cuenta con un tamaño máximo de
    ítems a almacenar. Cuando se llega al tamaño máximo y se quiere insertar un
    nuevo valor, se elimina primero el ítem menos utilizado automáticamente.

    Siempre se mantiene la propiedad len(LFUDict(N)) <= N.

    Attributes:
        _size (int): Tamaño máximo a alcanzar.
        _dict (dict): Diccionario utilizado para almacenar los ítems.
        _last_new_key (object): Última clave insertada *que no haya sido
            utilizada desde su inserción*.

    """
    class LFUDictItem:
        __slots__ = ['value', 'score']

        def __init__(self, value):
            self.value = value
            self.score = 0

        def __repr__(self):
            return '{} [{}]'.format(self.value, self.score)

    def __init__(self, size):
        """Inicializa un objeto de tipo LFUDict.

        Args:
            size (int): Ver atributo '_size'.

        """
        if size < 1:
            raise ValueError('size must be 1 or larger')
        self._size = size
        self._dict = {}
        self._last_new_key = None

    def _evict_min_key(self):
        """Remueve el ítem menos utilizado del diccionario 'self._dict'.
        """
        if self._dict:
            if self._last_new_key is None:
                # Buscar la key con el puntaje más bajo
                min_item = min(self._dict.items(), key=lambda i: i[1].score)
                min_key = min_item[0]
            else:
                # Utilizar la última key insertada, si nunca fue accedida ni
                # modificada. Esto nos permite evitar tener que buscar la key
                # con menor puntuación.
                min_key = self._last_new_key
                self._last_new_key = None

            del self._dict[min_key]

    def _increase_key_score(self, key):
        """Aumenta el número de usos de una clave almacenada en 'self._dict'.

        Args:
            key (object): Clave contenida en 'self._dict'.

        """
        self._dict[key].score += 1

        if key == self._last_new_key:
            self._last_new_key = None

    def __getitem__(self, key):
        """Devuelve un ítem del diccionario.

        Args:
            key (object): Clave del ítem.

        Returns:
            object: Valor almacenado bajo 'key'.

        """
        if key is None:
            raise TypeError('Invalid key: None')

        if key in self._dict:
            self._increase_key_score(key)

        return self._dict[key].value

    def __setitem__(self, key, value):
        """Establece un ítem clave-valor del diccionario.

        Args:
            key (object): Clave del ítem.
            value (object): Valor del ítem.

        """
        if key is None:
            raise TypeError('Invalid key: None')

        if key not in self._dict:
            # El tamaño del diccionario interno llegó al máximo, remover la key
            # menos utilizada.
            if len(self._dict) == self._size:
                self._evict_min_key()

            self._dict[key] = LFUDict.LFUDictItem(value)
            self._last_new_key = key
        else:
            self._increase_key_score(key)
            self._dict[key].value = value

    def __len__(self):
        """Devuelve la cantidad de ítems en el diccionario.

        Returns:
            int: Cantidad de ítems en el diccionario.

        """
        return len(self._dict)

    def __contains__(self, key):
        """Comprueba si una clave está contenida o no en el diccionario.

        Args:
            key (object): Clave a utilizar.

        Returns:
            bool: Verdadero si la clave está contenida en el diccionario.

        """
        has_key = key in self._dict
        if has_key:
            self._increase_key_score(key)

        return has_key

    def __repr__(self):
        """Devuelve una representación textual del diccionario.

        Returns:
            str: Representación del diccionario.

        """
        return 'LFUDict({})'.format(self._dict)


def address_data_spanish(address_data):
    """Traduce al castellano los campos de un objeto 'AddressData'.

    Returns:
        dict: Datos de un 'AddressData' con campos en castellano.

    """
    return {
        N.DOOR_NUM: {
            N.UNIT: address_data['door_number']['unit'],
            N.VALUE: address_data['door_number']['value']
        },
        N.FLOOR: address_data['floor'],
        N.STREETS: address_data['street_names'],
        N.TYPE: _ADDRESS_TYPES[address_data['type']]
    }


class GeorefJSONEncoder(JSONEncoder):
    """Codificador JSON para Georef. Extiende 'JSONEncoder' para poder
    codificar valores de tipo 'set' y 'AddressData'.

    """

    # pylint: disable=method-hidden
    def default(self, o):
        """Retorna un objeto a codificar, dado un objeto recibido por el
        codificador.

        Args:
            o (object): Objeto recibido por el codificador.

        Returns:
            object: Objeto final a codificar.

        """
        if isinstance(o, set):
            return list(o)

        if isinstance(o, AddressData):
            return address_data_spanish(o.to_dict())

        return super().default(o)


def patch_json_encoder(app):
    """Modifica un app Flask para utilizar 'GeorefJSONEncoder'.

    Args:
        app (flask.app.Flask): App de Flask.

    """
    app.json_encoder = GeorefJSONEncoder


def step_iterator(iterator, input_data=None):
    """Avanza un iterador un paso, enviándole un valor si es necesario.
    El iterador *no* debe producir valores 'None' en ninguno de sus pasos.

    Args:
        iterator (iterator): Iterador a avanzar.
        input_data (object): Valor a envíar al iterador.

    Returns:
        object: Valor producido por el iterador, o 'None' si finalizó.

    """
    try:
        if input_data is None:
            return next(iterator)

        return iterator.send(input_data)
    except StopIteration:
        return None


def translate_keys(d, translations, ignore=None):
    """Cambia las keys del diccionario 'd', utilizando las traducciones
    especificadas en 'translations'. Devuelve los resultados en un nuevo
    diccionario.

    Args:
        d (dict): Diccionario a modificar.
        translations (dict): Traducciones de keys (key anterior => key nueva.)
        ignore (list): Keys de 'd' a no agregar al nuevo diccionario devuelto.

    Returns:
        dict: Diccionario con las keys modificadas.

    """
    if not ignore:
        ignore = []

    return {
        translations.get(key, key): value
        for key, value in d.items()
        if key not in ignore
    }
