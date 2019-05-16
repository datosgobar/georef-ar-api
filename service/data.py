"""Módulo 'data' de georef-ar-api

Contiene funciones que ejecutan consultas a índices de Elasticsearch.
"""

from abc import ABC, abstractmethod
import elasticsearch
from elasticsearch_dsl import Search, MultiSearch
from elasticsearch_dsl.query import Match, Range, MatchPhrasePrefix, GeoShape
from elasticsearch_dsl.query import MatchNone, Terms, Prefix, Bool
from service import names as N
from service import constants, utils
from service.management import es_config

INTERSECTION_PARAM_TYPES = {
    N.STATES,
    N.DEPARTMENTS,
    N.MUNICIPALITIES,
    N.STREETS
}


class DataConnectionException(Exception):
    """Representa un error sucedido al intentar realizar una operación
    utilizando Elasticsearch.

    """


def elasticsearch_connection(hosts, sniff=False, sniffer_timeout=60):
    """Crea una conexión a Elasticsearch.

    Args:
        hosts (list): Lista de nodos Elasticsearch a los cuales conectarse.
        sniff (bool): Activa la función de sniffing, la cual permite descubrir
            nuevos nodos en un cluster y conectarse a ellos.

    Raises:
        DataConnectionException: si la conexión no pudo ser establecida.

    Returns:
        Elasticsearch: Conexión a Elasticsearch.

    """
    try:
        options = {
            'hosts': hosts
        }

        if sniff:
            options['sniff_on_start'] = True
            options['sniff_on_connection_fail'] = True
            options['sniffer_timeout'] = sniffer_timeout

        return elasticsearch.Elasticsearch(**options)
    except elasticsearch.ElasticsearchException as e:
        raise DataConnectionException from e


def _run_multisearch(es, searches):
    """Ejecuta una lista de búsquedas Elasticsearch utilizando la función
    MultiSearch. La cantidad de búsquedas que se envían a la vez es
    configurable vía la variable ES_MULTISEARCH_MAX_LEN.

    Args:
        es (Elasticsearch): Conexión a Elasticsearch.
        searches (list): Lista de elasticsearch_dsl.Search.

    Raises:
        DataConnectionException: Si ocurrió un error al ejecutar las búsquedas.

    Returns:
        list: Lista de respuestas a cada búsqueda.

    """
    step_size = constants.ES_MULTISEARCH_MAX_LEN
    responses = []

    # Partir las búsquedas en varios baches si es necesario.
    for i in range(0, len(searches), step_size):
        end = min(i + step_size, len(searches))
        ms = MultiSearch(using=es)

        for j in range(i, end):
            ms = ms.add(searches[j])

        try:
            responses.extend(ms.execute(raise_on_error=True))
        except elasticsearch.ElasticsearchException as e:
            raise DataConnectionException() from e

    return responses


class ElasticsearchSearch(ABC):
    """Representa una búsqueda a realizar utilizando Elasticsearch. Dependiendo
    de los parámetros de búsqueda, se puede llegar a necesitar más de una
    consulta a Elasticsearch para completar la misma.

    Attributes:
        _search (elasticsearch_dsl.Search): Búsqueda principal a envíar a
            Elasticsearch.
        _index (str): Índice sobre el cual realizar la búsqueda principal.
        _offset (int): Cantidad de resultados a saltear ('from').
        _result (ElasticsearchResult): Resultado de la búsqueda.

    """

    __slots__ = ['_search', '_index', '_offset', '_result']

    def __init__(self, index, query):
        """Inicializa un objeto de tipo ElasticsearchSearch.

        Args:
            index (str): Ver atributo '_index'.
            query (dict): Parámetros de la búsqueda. Ver el método
                '_read_query' para tomar nota de los valores permitidos
                dentro del diccionario.

        """
        self._search = Search(index=index)
        if constants.ES_TRACK_TOTAL_HITS:
            # Configurar la cantidad máxima de hits con los que se pueden
            # calcular total de hits precisos (nuevo en Elasticsearch 7.0.0).
            self._search = self._search.extra(
                track_total_hits=constants.ES_TRACK_TOTAL_HITS)

        self._index = index
        self._offset = query.get('offset', 0)
        self._result = None

        self._read_query(**query)

    @abstractmethod
    def search_steps(self):
        """Devuelve un iterador de búsquedas elasticsearch_dsl.Search, cada una
        representando un paso requerido para completar la búsqueda
        ElasticsearchSearch.

        Cuando el iterador finaliza, el valor de 'self._result' contiene el
        resultado final de la búsqueda.

        Yields:
            elasticsearch_dsl.Search: Búsqueda DSL que se desea ejecutar. Sus
                resultados deberían ser devueltos por el invocador de
                'next()/send()'.

        """
        raise NotImplementedError()

    def _read_query(self, fields=None, size=constants.DEFAULT_SEARCH_SIZE,
                    offset=0):
        """Lee los parámetros de búsqueda recibidos y los agrega al atributo
        'self._search'.

        Args:
            fields (list): Lista de campos a incluir en los resultados de la
                búsqueda.
            size (int): Tamaño máximo de resultados a devolver.
            offset (int): Cantidad de resultados a saltear.

        """
        if fields:
            self._search = self._search.source(includes=fields)

        self._search = self._search[offset:offset + size]

    def _expand_intersection_query(self, geo_shape_ids):
        """Expande (comprueba) que los IDs contenidos en geo_shape_ids sean
        válidos y referencien a entidades existentes. Los IDs inválidos son
        removidos.

        Este paso es necesario ya que la búsqueda por geometrías pre-indexadas
        de Elasticsearch no acepta IDs de documentos no existentes. Si se
        intenta utilizar un ID inválido, retorna HTTP 400.

        Para realizar la búsqueda, se retorna un iterador de
        elasticsearch_dsl.Search. De esta forma, se puede utilizar este método
        desde 'search_steps', agregando instancias de elasticsearch_dsl.Search
        que deben ser ejecutadas para completar los resultados de la instancia
        de ElasticsearchSearch.

        Yields:
            elasticsearch_dsl.Search: Búsqueda DSL necesaria para completar el
                chequeo de IDs.

        Args:
            geo_shape_ids (dict): Diccionario de str - list, las keys siendo
                tipos de entidades, y los valores siendo listas de IDs para el
                tipo de entidad.

        """
        checked_ids = {}

        for entity_type in INTERSECTION_PARAM_TYPES:
            if entity_type not in geo_shape_ids:
                continue

            entity_ids = list(geo_shape_ids[entity_type])
            search_class = entity_search_class(entity_type)
            search = search_class({
                'ids': entity_ids,
                'size': len(entity_ids),
                'fields': [N.ID]
            })

            yield from search.search_steps()

            checked_ids[entity_type] = [
                hit[N.ID] for hit in search.result.hits
            ]

        self._search = self._search.query(_build_geo_query(
            N.GEOM,
            ids=checked_ids
        ))

    def _expand_geometry_query(self, search_class):
        """Expande (completa) una búsqueda que incluye 'geometria' en sus
        campos. Para lograr esto, crea búsquedas elasticsearch_dsl.Search
        a los índices correspondientes que incluyen geometrías.

        Este método es necesario ya que los índices de entidades no cuentan
        con las versiones originales de las geometrías, por razones de
        performance (ver comentario en archivo es_config.py). Entonces, es
        necesario buscar las geometrías en índices separados, utilizando los
        IDs de los resultados encontrados en la búsqueda principal
        ('self._search').

        Para realizar la búsqueda de geometrías, se retorna un iterador de
        elasticsearch_dsl.Search. De esta forma, se puede utilizar este método
        desde 'search_steps', agregando instancias de elasticsearch_dsl.Search
        que deben ser ejecutadas para completar los resultados de la instancia
        de ElasticsearchSearch.

        Args:
            search_class (type): Clase a utilizar para crear el iterador de
                búsquedas.

        Yields:
            elasticsearch_dsl.Search: Búsqueda DSL necesaria para obtener las
                geometrías.

        """
        ids = [hit['id'] for hit in self._result.hits]

        geom_search = search_class({
            'ids': ids,
            'fields': [N.ID, N.GEOM],
            'size': len(ids)
        })

        yield from geom_search.search_steps()

        original_hits = {hit[N.ID]: hit for hit in self._result.hits}

        for hit in geom_search.result.hits:
            # Agregar campo geometría a los resultados originales
            original_hits[hit[N.ID]][N.GEOM] = hit[N.GEOM]

    @property
    def result(self):
        """Devuelve el resultado de la búsqueda, si esta fue ejecutada.

        Raises:
            RuntimeError: Si la búsqueda no fue ejecutada.

        Returns:
            ElasticsearchResult: Resultado de la búsqueda.

        """
        if self._result is None:
            raise RuntimeError('Search has not been executed yet')

        return self._result

    @staticmethod
    def run_searches(es, searches):
        """Ejecuta una lista de búsquedas ElasticsearchSearch.

        Para ejecutar las búsquedas, se obtiene un iterador de búsquedas
        elasticsearch_dsl.Search por cada elemento de 'searches'. Utilizando
        los iteradores, se construyen listas de elasticsearch_dsl.Search, que
        son luego ejecutadas utilizando '_run_multisearch'. Después, los
        resultados son devueltos a cada iterador, que pueden o no generar una
        nueva búsqueda elasticsearch_dsl.Search. El proceso se repite hasta que
        todos los iteradores hayan finalizado. Con todo este proceso se logra:

            1) Ejecutar cualquier tipo de búsquedas bajo una mismas interfaz.
            2) Ejecutar búsquedas que requieren distintas cantides de pasos
               bajo una misma interfaz.
            3) Utilizar la funcionalidad de MultiSearch para hacer la menor
               cantidad de consultas posible a Elasticsearch.

        Los resultados de cada búsqueda pueden ser accedidos vía el campo
        '.result' de cada una.

        Args:
            es (Elasticsearch): Conexión a Elasticsearch.
            searches (list): Lista de búsquedas ElasticsearchSearch o
                derivados. La lista puede ser de cualquier largo ya que sus
                contenidos son fraccionados por '_run_multisearch' para evitar
                consultas demasiado extensas a Elasticsearch.

        """
        iterators = [search.search_steps() for search in searches]
        iteration_data = []
        for iterator in iterators:
            search = utils.step_iterator(iterator)

            if search:
                iteration_data.append((iterator, search))

        while iteration_data:
            responses = _run_multisearch(es, [
                search for _, search in iteration_data
            ])

            iterators = (iterator for iterator, _ in iteration_data)
            iteration_data = []

            for iterator, response in zip(iterators, responses):
                search = utils.step_iterator(iterator, response)
                if search:
                    iteration_data.append((iterator, search))


class TerritoriesSearch(ElasticsearchSearch):
    """Representa una búsqueda de entidades territoriales (provincias,
    departamentos, etc.).

    Attributes:
        _geo_shape_ids (dict): Diccionario de str - list, las keys siendo
            tipos de entidades, y los valores siendo listas de IDs para el
            tipo de entidad. Se separa este atributo de los parámetros de
            búsqueda ya que requiere un manejo especial (requiere realizar
            consultas adicionales a otros índices).
        _geom_search_class (type): Clase que debería utilizarse para buscar
            geometrías para entidades de este TerritoriesSearch. Si es 'None',
            las geometrías simplemente pueden ser obtenidas agregando
            'geometria' a la lista de campos.
        _fetch_geoms (bool): Verdadero si es necesario realizar consultas
            adicionales para obtener geometrías.

    """

    __slots__ = ['_geo_shape_ids', '_geom_search_class', '_fetch_geoms']

    def __init__(self, index, query, geom_search_class=None):
        """Inicializa un objeto de tipo TerritoriesSearch.

        Args:
            index (str): Ver atributo '_index'.
            query (dict): Parámetros de la búsqueda. Ver el método
                '_read_query' para tomar nota de los valores permitidos
                dentro del diccionario.
            geom_search_class (type): Ver atributo '_geom_search_class'.

        """
        self._geo_shape_ids = query.pop('geo_shape_ids', None)
        self._geom_search_class = geom_search_class

        fields = query.get('fields')

        if fields and self._geom_search_class:
            # Se pidieron geometrías, pero este índice no las contiene,
            # es necesario buscarlas en el índice de geometrías
            # correspondiente.
            self._fetch_geoms = N.GEOM in fields and N.ID in fields
        else:
            # Las geometrías están contenidas en este índice. Si se pidieron en
            # 'fields', serán devueltas por la consulta a Elasticsearch.
            self._fetch_geoms = False

        super().__init__(index, query)

    def _read_query(self, ids=None, name=None, census_locality=None,
                    municipality=None, department=None, state=None,
                    exact=False, geo_shape_geoms=None, order=None, **kwargs):
        """Lee los parámetros de búsqueda recibidos y los agrega al atributo
        'self._search'. Luego, invoca al método '_read_query' de la superclase
        con los parámetros que no fueron procesados.

        Args:
            ids (list): Filtrar por IDs de entidades.
            name (str): Filtrar por nombre de entidades.
            census_locality (list, str): Filtrar por nombre o IDs de
                localidades censales.
            municipality (list, str): Filtrar por nombre o IDs de municipios.
            department (list, str): Filtrar por nombre o IDs de departamentos.
            state (list, str): Filtrar por nombre o IDs de provincias.
            exact (bool): Si es verdadero, desactivar la búsqueda fuzzy para
                todos los parámetros de texto siendo utilizados (nombre,
                provincia, etc.).
            geo_shape_geoms (list): Lista de geometrías GeoJSON a utilizar para
                filtrar por intersección con geometrías.
            order (str): Campo a utilizar para ordenar los resultados.
            kwargs (dict): Parámetros a delegar a la superclase.

        """
        super()._read_query(**kwargs)

        if ids:
            self._search = self._search.filter(_build_terms_query(N.ID, ids))

        if name:
            self._search = self._search.query(_build_name_query(N.NAME, name,
                                                                exact))

        if geo_shape_geoms:
            self._search = self._search.query(_build_geo_query(
                N.GEOM,
                geoms=geo_shape_geoms
            ))

        if census_locality:
            self._search = self._search.query(_build_subentity_query(
                N.CENSUS_LOCALITY_ID,
                N.CENSUS_LOCALITY_NAME,
                census_locality,
                exact
            ))

        if municipality:
            self._search = self._search.query(_build_subentity_query(
                N.MUN_ID,
                N.MUN_NAME,
                municipality,
                exact
            ))

        if department:
            self._search = self._search.query(_build_subentity_query(
                N.DEPT_ID,
                N.DEPT_NAME,
                department,
                exact
            ))

        if state:
            self._search = self._search.query(_build_subentity_query(
                N.STATE_ID,
                N.STATE_NAME,
                state,
                exact
            ))

        if order:
            if order == N.NAME:
                order = N.EXACT_SUFFIX.format(order)
            self._search = self._search.sort(order)

    def search_steps(self):
        """Ver documentación de 'ElasticsearchSearch.search_steps'.

        Pasos requeridos:
            1) Expandir parámetros 'geo_shape_ids'. (opcional)
            2) Buscar la entidad principal.
            3) Obtener geometrías. (opcional)

        """
        if self._geo_shape_ids:
            yield from self._expand_intersection_query(self._geo_shape_ids)

        response = yield self._search
        self._result = ElasticsearchResult(response, self._offset)

        if self._fetch_geoms:
            yield from self._expand_geometry_query(self._geom_search_class)


class StreetsSearch(ElasticsearchSearch):
    """Representa una búsqueda de calles.

    Attributes:
        _geo_shape_ids (dict): Diccionario de str - list, las keys siendo
            tipos de entidades, y los valores siendo listas de IDs para el
            tipo de entidad. Se separa este atributo de los parámetros de
            búsqueda ya que requiere un manejo especial (requiere realizar
            consultas adicionales a otros índices).

    """

    __slots__ = ['_geo_shape_ids']

    def __init__(self, query):
        """Inicializa un objeto de tipo StreetsSearch.

        Args:
            query (dict): Parámetros de la búsqueda. Ver el método
                '_read_query' para tomar nota de los valores permitidos
                dentro del diccionario.

        """
        self._geo_shape_ids = query.pop('geo_shape_ids', None)
        super().__init__(N.STREETS, query)

    def _read_query(self, ids=None, name=None, census_locality=None,
                    department=None, state=None, category=None, order=None,
                    exact=False, **kwargs):
        """Lee los parámetros de búsqueda recibidos y los agrega al atributo
        'self._search'. Luego, invoca al método '_read_query' de la superclase
        con los parámetros que no fueron procesados.

        Args:
            ids (list): Filtrar por IDs de calles.
            name (str): Filtrar por nombre de calles.
            census_locality (list, str): Filtrar por nombre o IDs de
                localidades censales.
            department (list, str): Filtrar por nombre o IDs de departamentos.
            state (list, str): Filtrar por nombre o IDs de provincias.
            category (str): Filtrar por tipo de calle.
            exact (bool): Si es verdadero, desactivar la búsqueda fuzzy para
                todos los parámetros de texto siendo utilizados (nombre,
                provincia, etc.).
            order (str): Campo a utilizar para ordenar los resultados.
            kwargs (dict): Parámetros a delegar a la superclase.

        """
        super()._read_query(**kwargs)

        if ids:
            self._search = self._search.filter(_build_terms_query(
                N.ID,
                ids
            ))

        if name:
            self._search = self._search.query(_build_name_query(
                N.NAME,
                name,
                exact
            ))

        if category:
            self._search = self._search.query(_build_match_query(
                N.CATEGORY,
                category,
                fuzzy=True
            ))

        if census_locality:
            self._search = self._search.query(_build_subentity_query(
                N.CENSUS_LOCALITY_ID,
                N.CENSUS_LOCALITY_NAME,
                census_locality,
                exact
            ))

        if department:
            self._search = self._search.query(_build_subentity_query(
                N.DEPT_ID,
                N.DEPT_NAME,
                department,
                exact
            ))

        if state:
            self._search = self._search.query(_build_subentity_query(
                N.STATE_ID,
                N.STATE_NAME,
                state,
                exact
            ))

        if order:
            if order == N.NAME:
                order = N.EXACT_SUFFIX.format(order)
            self._search = self._search.sort(order)

    def search_steps(self):
        """Ver documentación de 'ElasticsearchSearch.search_steps'.

        Pasos requeridos:
            1) Expandir parámetros 'geo_shape_ids'. (opcional)
            2) Buscar calles.

        """
        if self._geo_shape_ids:
            yield from self._expand_intersection_query(self._geo_shape_ids)

        response = yield self._search
        self._result = ElasticsearchResult(response, self._offset)


class IntersectionsSearch(ElasticsearchSearch):
    """Representa una búsqueda de intersecciones de calles. Utiliza el índice
    'intersecciones' para buscar datos.

    """

    def __init__(self, query):
        """Inicializa un objeto de tipo IntersectionsSearch.

        Args:
            query (dict): Parámetros de la búsqueda. Ver el método
                '_read_query' para tomar nota de los valores permitidos
                dentro del diccionario.

        """
        super().__init__(N.INTERSECTIONS, query)

    def _read_query(self, ids=None, geo_shape_geoms=None, census_locality=None,
                    department=None, state=None, exact=False, **kwargs):
        """Lee los parámetros de búsqueda recibidos y los agrega al atributo
        'self._search'. Luego, invoca al método '_read_query' de la superclase
        con los parámetros que no fueron procesados.

        Args:
            ids (tuple): Filtrar por IDs de intersecciones. La tupla debe
                contener exactamente dos listas de IDs: se buscan
                intersecciones donde la calle A pertenezca a la primera lista,
                y donde la calle B pertenezca a la segunda (o vice versa).
            geo_shape_geoms (list): Lista de geometrías GeoJSON a utilizar para
                filtrar por intersección con geometrías.
            census_locality (list, str, tuple): Filtrar por nombre o IDs de
                localidades censales.
            department (list, str): Filtrar por nombre o IDs de departamentos.
            state (list, str): Filtrar por nombre o IDs de provincias.
            exact (bool): Si es verdadero, desactivar la búsqueda fuzzy para
                todos los parámetros de texto siendo utilizados (nombre,
                provincia, etc.).
            kwargs (dict): Parámetros a delegar a la superclase.

        """
        super()._read_query(**kwargs)

        if ids:
            query_1 = (
                _build_terms_query(N.join(N.STREET_A, N.ID), ids[0]) &
                _build_terms_query(N.join(N.STREET_B, N.ID), ids[1])
            )

            query_2 = (
                _build_terms_query(N.join(N.STREET_A, N.ID), ids[1]) &
                _build_terms_query(N.join(N.STREET_B, N.ID), ids[0])
            )

            self._search = self._search.query(query_1 | query_2)

        if geo_shape_geoms:
            self._search = self._search.query(_build_geo_query(
                N.GEOM,
                geoms=geo_shape_geoms
            ))

        if census_locality:
            for side in [N.STREET_A, N.STREET_B]:
                self._search = self._search.query(_build_subentity_query(
                    N.join(side, N.CENSUS_LOCALITY_ID),
                    N.join(side, N.CENSUS_LOCALITY_NAME),
                    census_locality,
                    exact
                ))

        if department:
            for side in [N.STREET_A, N.STREET_B]:
                self._search = self._search.query(_build_subentity_query(
                    N.join(side, N.DEPT_ID),
                    N.join(side, N.DEPT_NAME),
                    department,
                    exact
                ))

        if state:
            for side in [N.STREET_A, N.STREET_B]:
                self._search = self._search.query(_build_subentity_query(
                    N.join(side, N.STATE_ID),
                    N.join(side, N.STATE_NAME),
                    state,
                    exact
                ))

    def search_steps(self):
        """Ver documentación de 'ElasticsearchSearch.search_steps'.

        Pasos requeridos:
            1) Buscar intersecciones de calles.

        """
        response = yield self._search
        self._result = ElasticsearchResult(response, self._offset)


class StreetBlocksSearch(ElasticsearchSearch):
    """Representa una búsqueda de cuadras de calles. Utiliza el índice
    'cuadras' para buscar datos.

    """

    def __init__(self, query):
        """Inicializa un objeto de tipo StreetBlocksSearch.

        Args:
            query (dict): Parámetros de la búsqueda. Ver el método
                '_read_query' para tomar nota de los valores permitidos
                dentro del diccionario.

        """
        super().__init__(N.STREET_BLOCKS, query)

    def _read_query(self, name=None, category=None, census_locality=None,
                    department=None, state=None, number=None, exact=False,
                    order=None, **kwargs):
        """Lee los parámetros de búsqueda recibidos y los agrega al atributo
        'self._search'. Luego, invoca al método '_read_query' de la superclase
        con los parámetros que no fueron procesados.

        Args:
            name (str): Filtrar por nombre de calles.
            category (str): Filtrar por tipo de calle.
            census_locality (list, str, tuple): Filtrar por nombre o IDs de
                localidades censales.
            department (list, str): Filtrar por nombre o IDs de departamentos.
            state (list, str): Filtrar por nombre o IDs de provincias.
            number (int): Filtrar por altura de calle. El valor debe estar
                contenido en los extremos inicio-fin de alturas de la cuadra.
            exact (bool): Si es verdadero, desactivar la búsqueda fuzzy para
                todos los parámetros de texto siendo utilizados (nombre,
                provincia, etc.).
            order (str): Campo a utilizar para ordenar los resultados.
            kwargs (dict): Parámetros a delegar a la superclase.

        """
        super()._read_query(**kwargs)

        if name:
            self._search = self._search.query(_build_name_query(
                N.join(N.STREET, N.NAME),
                name,
                exact
            ))

        if category:
            self._search = self._search.query(_build_match_query(
                N.join(N.STREET, N.CATEGORY),
                category,
                fuzzy=True
            ))

        if census_locality:
            self._search = self._search.query(_build_subentity_query(
                N.join(N.STREET, N.CENSUS_LOCALITY_ID),
                N.join(N.STREET, N.CENSUS_LOCALITY_NAME),
                census_locality,
                exact
            ))

        if department:
            self._search = self._search.query(_build_subentity_query(
                N.join(N.STREET, N.DEPT_ID),
                N.join(N.STREET, N.DEPT_NAME),
                department,
                exact
            ))

        if state:
            self._search = self._search.query(_build_subentity_query(
                N.join(N.STREET, N.STATE_ID),
                N.join(N.STREET, N.STATE_NAME),
                state,
                exact
            ))

        if number is not None:
            right_condition = (
                _build_range_query(N.START_R, '<=', number) &
                _build_range_query(N.END_R, '>=', number)
            )

            left_condition = (
                _build_range_query(N.START_L, '<=', number) &
                _build_range_query(N.END_L, '>=', number)
            )

            # El número debe estar contenido del lado derecho o del izquierdo
            self._search = self._search.query(right_condition | left_condition)

        if order:
            if order == N.NAME:
                order = N.EXACT_SUFFIX.format(order)
            self._search = self._search.sort(N.join(N.STREET, order))

    def search_steps(self):
        """Ver documentación de 'ElasticsearchSearch.search_steps'.

        Pasos requeridos:
            1) Buscar cuadras.

        """
        response = yield self._search
        self._result = ElasticsearchResult(response, self._offset)


class StatesGeometrySearch(TerritoriesSearch):
    """Representa una búsqueda de geometrías de provincias.

    Reservada para uso interno en 'data.py'. Se pueden buscar geometrías
    utilizando 'StatesSearch', que internamente utilizará esta clase.

    Ver documentación de la clase 'TerritoriesSearch' para más información.

    """

    def __init__(self, query):
        super().__init__(es_config.geom_index_for(N.STATES), query)


class StatesSearch(TerritoriesSearch):
    """Representa una búsqueda de provincias.

    Ver documentación de la clase 'TerritoriesSearch' para más información.

    """

    def __init__(self, query):
        super().__init__(N.STATES, query,
                         geom_search_class=StatesGeometrySearch)


class DepartmentsGeometrySearch(TerritoriesSearch):
    """Representa una búsqueda de geometrías de departamentos.

    Reservada para uso interno en 'data.py'. Se pueden buscar geometrías
    utilizando 'DepartmentsSearch', que internamente utilizará esta clase.

    Ver documentación de la clase 'TerritoriesSearch' para más información.

    """

    def __init__(self, query):
        super().__init__(es_config.geom_index_for(N.DEPARTMENTS), query)


class DepartmentsSearch(TerritoriesSearch):
    """Representa una búsqueda de departamentos.

    Ver documentación de la clase 'TerritoriesSearch' para más información.

    """

    def __init__(self, query):
        super().__init__(N.DEPARTMENTS, query,
                         geom_search_class=DepartmentsGeometrySearch)


class MunicipalitiesGeometrySearch(TerritoriesSearch):
    """Representa una búsqueda de geometrías de municipios.

    Reservada para uso interno en 'data.py'. Se pueden buscar geometrías
    utilizando 'MunicipalitiesSearch', que internamente utilizará esta clase.

    Ver documentación de la clase 'TerritoriesSearch' para más información.

    """

    def __init__(self, query):
        super().__init__(es_config.geom_index_for(N.MUNICIPALITIES), query)


class MunicipalitiesSearch(TerritoriesSearch):
    """Representa una búsqueda de municipios.

    Ver documentación de la clase 'TerritoriesSearch' para más información.

    """

    def __init__(self, query):
        super().__init__(N.MUNICIPALITIES, query,
                         geom_search_class=MunicipalitiesGeometrySearch)


class CensusLocalitiesSearch(TerritoriesSearch):
    """Representa una búsqueda de localidades censales.

    Ver documentación de la clase 'TerritoriesSearch' para más información.

    """

    def __init__(self, query):
        super().__init__(N.CENSUS_LOCALITIES, query)


class SettlementsSearch(TerritoriesSearch):
    """Representa una búsqueda de asentamientos.

    Ver documentación de la clase 'TerritoriesSearch' para más información.

    """

    def __init__(self, query):
        super().__init__(N.SETTLEMENTS, query)


class LocalitiesSearch(TerritoriesSearch):
    """Representa una búsqueda de localidades.

    Ver documentación de la clase 'TerritoriesSearch' para más información.

    """

    def __init__(self, query):
        super().__init__(N.LOCALITIES, query)


_ENTITY_SEARCH_CLASSES = {
    N.STATES: StatesSearch,
    N.DEPARTMENTS: DepartmentsSearch,
    N.MUNICIPALITIES: MunicipalitiesSearch,
    N.CENSUS_LOCALITIES: CensusLocalitiesSearch,
    N.SETTLEMENTS: SettlementsSearch,
    N.LOCALITIES: LocalitiesSearch,
    N.STREETS: StreetsSearch
}
"""dict: Mantiene un registro de nombres de índices vs. clase a utilizar para
buscar en los mismos."""


def entity_search_class(entity):
    """Dado un nombre de entidad, retorna la clase correspondiente que debe
    ser utilizada para realizar búsquedas de la misma.

    Args:
        entity (str): Nombre de entidad (plural).

    Raises:
        ValueError: Si el nombre de la entidad no es válido.

    Returns:
        type: Clase derivada de ElasticsearchSearch a utilizar para realizar
            búsquedas de la entidad.

    """
    if entity not in _ENTITY_SEARCH_CLASSES:
        raise ValueError('Unknown entity type: {}'.format(entity))

    return _ENTITY_SEARCH_CLASSES[entity]


class ElasticsearchResult:
    """Representa resultados para una consulta a Elasticsearch.

    Attributes:
        _hits (list): Lista de resultados (diccionarios).
        _total (int): Total de resultados encontrados, no necesariamente
            incluidos en la respuesta.
        _offset (int): Cantidad de resultados salteados, comenzando desde el
            primero.

    """

    __slots__ = ['_hits', '_total', '_offset']

    def __init__(self, response, offset):
        self._hits = [hit.to_dict() for hit in response.hits]
        # En Elasticsearch 7.0.0, response.hits.total dejó de ser un int y
        # ahora es un objeto (dict). Si total.relation es 'gte', entonces el
        # total es un estimado (lower bound). Solo se hacen estimados para
        # queries que matcheen más de 10k documentos (por default).
        self._total = response.hits.total.value
        self._offset = offset

    @property
    def hits(self):
        return self._hits

    @property
    def total(self):
        return self._total

    @property
    def offset(self):
        return self._offset

    def __len__(self):
        return len(self._hits)


def _build_subentity_query(id_field, name_field, value, exact):
    """Crea una condición de búsqueda por propiedades de una subentidad. Esta
    condición se utiliza para filtrar resultados utilizando IDs o nombre de una
    subentidad contenida por otra. Por ejemplo, se pueden buscar departamentos
    filtrando por nombre de provincia, o localidades filtrando por IDS de
    municipios.

    Args:
        id_field (str): Nombre del campo de ID de la subentidad.
        name_field (str): Nombre del campo de nombre de la subentidad.
        value (list, str, tuple): Valor a buscar. En caso de ser una lista,
            representa una lista de IDs. En caso de ser un string, representa
            un nombre. En caso de ser una tupla, representa una lista de IDs y
            un nombre (buscar ambos unidos por OR).
        exact (bool): Activa la búsqueda por nombres exactos (en caso de que
            'value' sea de tipo str).

    Returns:
            Query: Condición para Elasticsearch.

    """
    if isinstance(value, list):
        return Bool(filter=[_build_terms_query(id_field, value)])
    if isinstance(value, tuple):
        ids, name = value
        return (
            _build_name_query(name_field, name, exact) |
            Bool(filter=[_build_terms_query(id_field, ids)])
        )

    return _build_name_query(name_field, value, exact)


def _build_geo_query(field, ids=None, geoms=None, relation='intersects'):
    """Crea una condición de búsqueda por propiedades de geometrías. La función
    permite especificar una o más geometrías (vía el ID de un documento, o su
    valor GeoJSON directo) y una relación (INTERSECTS, WITHIN, etc.), y luego
    construye las queries GeoShape apropiadas, una por geometría. Las queries
    son unidas con el operador lógico OR.

    Args:
        field (str): Campo de la condición (debe ser de tipo 'geo_shape').
        ids (dict): Diccionario de tipo de entidad - lista de IDs. Los
            documentos referidos deben contar con un campo 'geometria'.
        geoms (list): Lista de geometrías con formato GeoJSON.
        relation (str): Tipo de búsqueda por geometrías a realizar. Ver la
            documentación de Elasticsearch GeoShape Query para más detalles.

    Returns:
        Query: Condición para Elasticsearch.

    """
    query = MatchNone()

    if ids:
        for entity_type, id_list in ids.items():
            for entity_id in id_list:
                query |= _build_geo_indexed_shape_query(field, entity_type,
                                                        entity_id, N.GEOM,
                                                        relation)

    if geoms:
        for geom in geoms:
            query |= _build_geo_shape_query(field, geom, relation)

    return query


def _build_geo_shape_query(field, geom, relation):
    """Crea una condición de búsqueda por relación con una geometría en formato
    GeoJSON.

    Args:
        field (str): Campo de la condición.
        geom (dict): Geometría GeoJSON.
        relation (str): Tipo de búsqueda por geometrías a realizar. Ver la
            documentación de Elasticsearch GeoShape Query para más detalles.

    Returns:
        Query: Condición para Elasticsearch.

    """
    options = {
        'shape': geom,
        'relation': relation
    }

    return GeoShape(**{field: options})


def _build_geo_indexed_shape_query(field, index, entity_id, entity_geom_path,
                                   relation):
    """Crea una condición de búsqueda por relación geométrica con una geometría
    pre-indexada. La geometría debe pertenecer a una entidad de tipo provincia,
    departamento o municipio.

    Args:
        field (str): Campo de la condición.
        index (str): Índice donde está almacenada la geometría pre-indexada.
        entity_id (str): ID del documento con la geometría a utilizar.
        entity_geom_path (str): Campo del documento donde se encuentra la
            geometría.
        relation (str): Tipo de búsqueda por geometrías a realizar. Ver la
            documentación de Elasticsearch GeoShape Query para más detalles.

    Returns:
        Query: Condición para Elasticsearch.

    """
    if index not in INTERSECTION_PARAM_TYPES:
        raise ValueError('Invalid entity type')

    options = {
        'indexed_shape': {
            'index': es_config.geom_index_for(index),
            'id': entity_id,
            'path': entity_geom_path
        },
        'relation': relation
    }

    # Debido a la forma en la que Elasticsearch indexa geometrías, es posible
    # obtener falsos positivos en las búsquedas por intersección de geometrías.
    # Una forma simple de resolver este problema es agregar un filtro Prefix
    # adicional, que remueva todos los resultados que no pertenezcan a la misma
    # provincia que la entidad con ID == entity_id, ya que dos geometrías de
    # provincias distintas nunca pueden tener una intersección (sin importar el
    # tipo de entidad).
    prefix_query = Prefix(**{N.ID: entity_id[:constants.STATE_ID_LEN]})

    # En caso de estar buscando entidades en un índice utilizando geometrías de
    # entidades en el mismo índice, asegurarse de que los resultados no traigan
    # la entidad que utilizamos como geometría (el dato de que una geometría
    # intersecciona con si misma no es útil).
    exclude_self_query = ~_build_terms_query(N.ID, [entity_id])

    return GeoShape(**{field: options}) & prefix_query & exclude_self_query


def _build_terms_query(field, values):
    """Crea una condición de búsqueda por términos exactos para Elasticsearch.

    Args:
        field (str): Campo de la condición.
        value (list): Lista de valores.

    Returns:
        Query: Condición para Elasticsearch.

    """
    return Terms(**{field: values})


def _build_name_query(field, value, exact=False):
    """Crea una condición de búsqueda por nombre para Elasticsearch.
    Las entidades con nombres son, por el momento, las provincias, los
    departamentos, los municipios, las localidades y las calles.

    Args:
        field (str): Campo de la condición.
        value (str): Valor de comparación.
        exact (bool): Activar modo de búsqueda exacta.

    Returns:
        Query: Condición para Elasticsearch.

    """
    if exact:
        field = N.EXACT_SUFFIX.format(field)
        return _build_match_query(field, value, False)

    query = _build_match_query(field, value, True, operator='and')

    if len(value.strip()) >= constants.MIN_AUTOCOMPLETE_CHARS:
        query |= _build_match_phrase_prefix_query(field, value)

    query &= ~_build_match_query(
        field, value, analyzer=es_config.name_analyzer_excluding_terms)

    return query


def _build_match_phrase_prefix_query(field, value):
    """Crea una condición 'Match Phrase Prefix' para Elasticsearch.

    Args:
        field (str): Campo de la condición.
        value (str): Valor de comparación.

    Returns:
        Query: Condición para Elasticsearch.

    """
    options = {
        'query': value
    }
    return MatchPhrasePrefix(**{field: options})


def _build_range_query(field, operator, value):
    """Crea una condición 'Range' para Elasticsearch.

    Args:
        field (str): Campo de la condición.
        value (int): Número contra el que se debería comparar el campo.
        operator (str): Operador a utilizar (>, =>, <, =<)

    Returns:
        Query: Condición Range para Elasticsearch

    """
    if operator == '<':
        es_operator = 'lt'
    elif operator == '<=':
        es_operator = 'lte'
    elif operator == '>':
        es_operator = 'gt'
    elif operator == '>=':
        es_operator = 'gte'
    else:
        raise ValueError('Invalid operator')

    options = {es_operator: value}
    return Range(**{field: options})


def _build_match_query(field, value, fuzzy=False, operator='or',
                       analyzer=None):
    """Crea una condición 'Match' para Elasticsearch.

    Args:
        field (str): Campo de la condición.
        value (str): Valor de comparación.
        fuzzy (bool): Bandera para habilitar tolerancia a errores.
        operator (bool): Operador a utilizar para conectar clausulas 'term'
        analyzer (str): Analizador a utilizar para el análisis del texto de
            búsqueda.

    Returns:
        Query: Condición para Elasticsearch.

    """
    options = {
        'query': value,
        'operator': operator
    }

    if fuzzy:
        options['fuzziness'] = constants.DEFAULT_FUZZINESS

    if analyzer:
        options['analyzer'] = analyzer

    return Match(**{field: options})
