"""Módulo 'utils' de georef-ar-api

Contiene funciones y clases de varias utilidades.
"""


class LRUDict:
    """Diccionario LRU ("Least Recently Used").

    Implementa un diccionario similar a dict que cuenta con un tamaño máximo de
    ítems a almacenar. Cuando se llega al tamaño máximo y se quiere insertar un
    nuevo valor, se elimina primero el ítem menos utilizado automáticamente.

    Siempre se mantiene la propiedad len(LRUDict(N)) <= N.

    Attributes:
        _size (int): Tamaño máximo a alcanzar.
        _dict (dict): Diccionario utilizado para almacenar los ítems.
        _last_new_key (object): Última clave insertada *que no haya sido
            utilizada desde su inserción*.

    """
    class LRUDictItem:
        __slots__ = ['value', 'score']

        def __init__(self, value):
            self.value = value
            self.score = 0

        def __repr__(self):
            return '{} [{}]'.format(self.value, self.score)

    def __init__(self, size):
        """Inicializa un objeto de tipo LRUDict.

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

            self._dict[key] = LRUDict.LRUDictItem(value)
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
        return 'LRUDict({})'.format(self._dict)


def step_iterator(iterator, input_data=None):
    try:
        if input_data is None:
            return next(iterator)

        return iterator.send(input_data)
    except StopIteration:
        return None
