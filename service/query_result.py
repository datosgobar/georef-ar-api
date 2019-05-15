"""Módulo 'query_result' de georef-ar-api.

Contiene la especificación de la clase 'QueryResult' para uso durante el
proceso de normalización de datos.
"""


class QueryResult:
    """Representa el resultado de una consulta a la API. Los contenidos del
    resultado no necesariamente deben haber sido obtenidos desde Elasticsearch,
    pueden haber sido generados vía código. En ambos casos, el uso de
    QueryResult es idéntico.

    Se distinguen dos casos de resultados posibles:
        1) Resultados en forma de lista de 0 o más elementos.
        2) Resultado singular.
    Internamente, ambos casos se almacenan como una lista.

    Attributes:
        _entities (list): Lista de entidades (provincias, municipios,
            ubicaciones, calles, etc.).
        _params (dict): Parámetros de consulta que generaron este objeto
            'QueryResult'.
        _iterable (bool): Falso si el resultado representa una entidad
            singular (como en el caso de una ubicación). Verdadero cuando se
            representa una lista de entidades (como en el caso de, por ejemplo,
            provincias).
        _total (int): Total de entidades encontradas, no necesariamente
            incluidas en la respuesta. En caso de iterable == False, se utiliza
            1 como valor default, ya que el 'total' de entidades posibles a ser
            devueltas es 0 o 1, pero al contar ya con un resultado, el número
            deber ser 1.
        _offset (int): Cantidad de resultados salteados. En caso de iterable ==
            False, se establece como 0, ya que no se puede saltear el único
            posible.

    """

    __slots__ = ['_entities', '_params', '_iterable', '_total', '_offset']

    def __init__(self, entities, params, iterable=False, total=1, offset=0):
        """Inicializar una QueryResult. Se recomienda utilizar
        'from_single_entity' y 'from_entity_list' en vez de utilizar este
        método.

        Args:
            entities (list): Ver atributo '_entities'.
            params (dict): Ver atributo '_params'.
            iterable (bool): Ver atributo '_iterable'.
            total (int): Ver atributo '_total'.
            offset (int): Ver atributo '_offset'.

        """
        self._entities = entities
        self._params = params
        self._iterable = iterable
        self._total = total
        self._offset = offset

    @classmethod
    def from_single_entity(cls, entity, params):
        """Construir una QueryResult a partir de una entidad singular.

        Args:
            entity (dict): Entidad encontrada.
            params (dict): Parámetros de consulta.

        Returns:
            QueryResult: objeto construido.

        """
        return cls([entity], params)

    @classmethod
    def from_entity_list(cls, entities, params, total, offset=0):
        """Construir una QueryResult a partir de una lista de entidades de
        cualquier longitud.

        Args:
            entities (list): Lista de entidades.
            params (dict): Parámetros de consulta.
            total (int): Total de entidades encontradas, no necesariamente
                incluidas.
            offset (int): Cantidad de resultados salteados.

        Returns:
            QueryResult: objeto construido.

        """
        return cls(entities, params, iterable=True, total=total, offset=offset)

    @classmethod
    def empty(cls, params):
        """Construir una QueryResult vacía.

        Args:
            params (dict): Parámetros de consulta.

        Returns:
            QueryResult: objeto construido.

        """
        return cls.from_entity_list([], params, total=0)

    @property
    def entities(self):
        return self._entities

    @property
    def params(self):
        return self._params

    def first_entity(self):
        return self._entities[0]

    @property
    def total(self):
        return self._total

    @property
    def offset(self):
        return self._offset

    @property
    def iterable(self):
        return self._iterable
