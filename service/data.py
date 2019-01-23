"""Módulo 'data' de georef-ar-api

Contiene funciones que ejecutan consultas a índices de Elasticsearch.
"""

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

    pass


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
    except elasticsearch.ElasticsearchException:
        raise DataConnectionException()


def run_multisearch(es, searches):
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
        except elasticsearch.ElasticsearchException:
            raise DataConnectionException()

    return responses


class ElasticsearchSearch:
    def __init__(self, index, query):
        self._search = Search(index=index)
        self._index = index
        self._offset = query.get('offset', 0)
        self._result = None

        self._read_query(**query)

    def search_steps(self):
        raise NotImplementedError()

    def _read_query(self, fields=None, size=constants.DEFAULT_SEARCH_SIZE,
                    offset=0):
        if fields:
            self._search = self._search.source(include=fields)

        self._search = self._search[offset:offset + size]

    def _expand_intersection_query(self, geo_shape_ids):
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

        self._search = self._search.query(build_geo_query(
            N.GEOM,
            ids=checked_ids
        ))

    def _expand_geometry_query(self, search_class):
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
        if self._result is None:
            raise RuntimeError('Search has not been executed yet')

        return self._result

    def set_result(self, result):
        if self._result is not None:
            raise RuntimeError('Search has already been executed')

        self._result = result

    @staticmethod
    def run_searches(es, searches):
        iterators = [search.search_steps() for search in searches]
        iteration_data = []
        for iterator in iterators:
            search = utils.step_iterator(iterator)

            if search:
                iteration_data.append((iterator, search))

        while iteration_data:
            responses = run_multisearch(es, [
                search for _, search in iteration_data
            ])

            iterators = (iterator for iterator, _ in iteration_data)
            iteration_data = []

            for iterator, response in zip(iterators, responses):
                search = utils.step_iterator(iterator, response)
                if search:
                    iteration_data.append((iterator, search))


class TerritoriesSearch(ElasticsearchSearch):
    def __init__(self, index, query, geom_search_class=None):
        self._geo_shape_ids = query.pop('geo_shape_ids', None)
        self._geom_search_class = geom_search_class

        fields = query.get('fields', [])

        if self._geom_search_class:
            # Se pidieron geometrías, pero este índice no las contiene,
            # es necesario buscarlas en el índice de geometrías
            # correspondiente.
            self._fetch_geoms = N.GEOM in fields and N.ID in fields
        else:
            # Las geometrías están contenidas en este índice. Si se pidieron en
            # 'fields', serán devueltas por la consulta a Elasticsearch.
            self._fetch_geoms = False

        super().__init__(index, query)

    def _read_query(self, ids=None, name=None, municipality=None,
                    department=None, state=None, exact=False,
                    geo_shape_geoms=None, order=None, **kwargs):
        super()._read_query(**kwargs)

        if ids:
            self._search = self._search.filter(build_terms_query(N.ID, ids))

        if name:
            self._search = self._search.query(build_name_query(N.NAME, name,
                                                               exact))

        if geo_shape_geoms:
            self._search = self._search.query(build_geo_query(
                N.GEOM,
                geoms=geo_shape_geoms
            ))

        if municipality:
            self._search = self._search.query(build_subentity_query(
                N.MUN_ID,
                N.MUN_NAME,
                municipality,
                exact
            ))

        if department:
            self._search = self._search.query(build_subentity_query(
                N.DEPT_ID,
                N.DEPT_NAME,
                department,
                exact
            ))

        if state:
            self._search = self._search.query(build_subentity_query(
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
        if self._geo_shape_ids:
            yield from self._expand_intersection_query(self._geo_shape_ids)

        response = yield self._search
        self._result = ElasticsearchResult(response, self._offset)

        if self._fetch_geoms:
            yield from self._expand_geometry_query(self._geom_search_class)


class StreetsSearch(ElasticsearchSearch):
    def __init__(self, query):
        self._geo_shape_ids = query.pop('geo_shape_ids', None)
        super().__init__(N.STREETS, query)

    def _read_query(self, ids=None, name=None, department=None, state=None,
                    street_type=None, order=None, exact=False, number=None,
                    **kwargs):

        super()._read_query(**kwargs)

        if ids:
            self._search = self._search.filter(build_terms_query(
                N.ID,
                ids
            ))

        if name:
            self._search = self._search.query(build_name_query(
                N.NAME,
                name,
                exact
            ))

        if street_type:
            self._search = self._search.query(build_match_query(
                N.TYPE,
                street_type,
                fuzzy=True
            ))

        if number:
            self._search = self._search.query(
                build_range_query(N.START_R, '<=', number) |
                build_range_query(N.START_L, '<=', number)
            )

            self._search = self._search.query(
                build_range_query(N.END_L, '>=', number) |
                build_range_query(N.END_R, '>=', number)
            )

        if department:
            self._search = self._search.query(build_subentity_query(
                N.DEPT_ID,
                N.DEPT_NAME,
                department,
                exact
            ))

        if state:
            self._search = self._search.query(build_subentity_query(
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
        if self._geo_shape_ids:
            yield from self._expand_intersection_query(self._geo_shape_ids)

        response = yield self._search
        self._result = ElasticsearchResult(response, self._offset)


class IntersectionsSearch(ElasticsearchSearch):
    def __init__(self, query):
        super().__init__(N.INTERSECTIONS, query)

    def _read_query(self, ids=None, geo_shape_geoms=None, department=None,
                    state=None, exact=False, **kwargs):
        super()._read_query(**kwargs)

        if ids:
            query_1 = (
                build_terms_query(N.join(N.STREET_A, N.ID), ids[0]) &
                build_terms_query(N.join(N.STREET_B, N.ID), ids[1])
            )

            query_2 = (
                build_terms_query(N.join(N.STREET_A, N.ID), ids[1]) &
                build_terms_query(N.join(N.STREET_B, N.ID), ids[0])
            )

            self._search = self._search.query(query_1 | query_2)

        if geo_shape_geoms:
            self._search = self._search.query(build_geo_query(
                N.GEOM,
                geoms=geo_shape_geoms
            ))

        if department:
            for side in [N.STREET_A, N.STREET_B]:
                self._search = self._search.query(build_subentity_query(
                    N.join(side, N.DEPT_ID),
                    N.join(side, N.DEPT_NAME),
                    department,
                    exact
                ))

        if state:
            for side in [N.STREET_A, N.STREET_B]:
                self._search = self._search.query(build_subentity_query(
                    N.join(side, N.STATE_ID),
                    N.join(side, N.STATE_NAME),
                    state,
                    exact
                ))

    def search_steps(self):
        response = yield self._search
        self._result = ElasticsearchResult(response, self._offset)


class StatesGeometrySearch(TerritoriesSearch):
    def __init__(self, query):
        super().__init__(es_config.geom_index_for(N.STATES), query)


class StatesSearch(TerritoriesSearch):
    def __init__(self, query):
        super().__init__(N.STATES, query,
                         geom_search_class=StatesGeometrySearch)


class DepartmentsGeometrySearch(TerritoriesSearch):
    def __init__(self, query):
        super().__init__(es_config.geom_index_for(N.DEPARTMENTS), query)


class DepartmentsSearch(TerritoriesSearch):
    def __init__(self, query):
        super().__init__(N.DEPARTMENTS, query,
                         geom_search_class=DepartmentsGeometrySearch)


class MunicipalitiesGeometrySearch(TerritoriesSearch):
    def __init__(self, query):
        super().__init__(es_config.geom_index_for(N.MUNICIPALITIES), query)


class MunicipalitiesSearch(TerritoriesSearch):
    def __init__(self, query):
        super().__init__(N.MUNICIPALITIES, query,
                         geom_search_class=MunicipalitiesGeometrySearch)


class LocalitiesSearch(TerritoriesSearch):
    def __init__(self, query):
        super().__init__(N.LOCALITIES, query)


ENTITY_SEARCH_CLASSES = {
    N.STATES: StatesSearch,
    N.DEPARTMENTS: DepartmentsSearch,
    N.MUNICIPALITIES: MunicipalitiesSearch,
    N.LOCALITIES: LocalitiesSearch,
    N.STREETS: StreetsSearch
}


def entity_search_class(entity):
    if entity not in ENTITY_SEARCH_CLASSES:
        raise ValueError('Unknown entity type: {}'.format(entity))

    return ENTITY_SEARCH_CLASSES[entity]


class ElasticsearchResult:
    """Representa resultados para una consulta a Elasticsearch.

    Attributes:
        _hits (list): Lista de resultados (diccionarios).
        _total (int): Total de resultados encontrados, no necesariamente
            incluidos en la respuesta.
        _offset (int): Cantidad de resultados salteados, comenzando desde el
            primero.

    """

    def __init__(self, response, offset):
        self._hits = [hit.to_dict() for hit in response.hits]
        self._total = response.hits.total
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


def build_subentity_query(id_field, name_field, value, exact):
    """Crea una condición de búsqueda por propiedades de una subentidad. Esta
    condición se utiliza para filtrar resultados utilizando IDs o nombre de una
    subentidad contenida por otra. Por ejemplo, se pueden buscar departamentos
    filtrando por nombre de provincia, o localidades filtrando por IDS de
    municipios.

    Args:
        id_field (str): Nombre del campo de ID de la subentidad.
        name_field (str): Nombre del campo de nombre de la subentidad.
        value (list, str): Lista de IDs o nombre a utilizar para filtrar.
        exact (bool): Activa la búsqueda por nombres exactos (en caso de que
            'value' sea de tipo str).

    Returns:
            Query: Condición para Elasticsearch.

    """
    if isinstance(value, list):
        return Bool(filter=[build_terms_query(id_field, value)])

    return build_name_query(name_field, value, exact)


def build_geo_query(field, ids=None, geoms=None, relation='intersects'):
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
                query |= build_geo_indexed_shape_query(field, entity_type,
                                                       entity_id, N.GEOM,
                                                       relation)

    if geoms:
        for geom in geoms:
            query |= build_geo_shape_query(field, geom, relation)

    return query


def build_geo_shape_query(field, geom, relation):
    options = {
        'shape': geom,
        'relation': relation
    }

    return GeoShape(**{field: options})


def build_geo_indexed_shape_query(field, index, entity_id, entity_geom_path,
                                  relation):
    """Crea una condición de búsqueda por intersección con una geometría
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
            'type': es_config.DOC_TYPE,
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
    prefix_query = Prefix(id=entity_id[:constants.STATE_ID_LEN])
    return GeoShape(**{field: options}) & prefix_query


def build_terms_query(field, values):
    """Crea una condición de búsqueda por términos exactos para Elasticsearch.

    Args:
        field (str): Campo de la condición.
        value (list): Lista de valores.

    Returns:
        Query: Condición para Elasticsearch.

    """
    return Terms(**{field: values})


def build_name_query(field, value, exact=False):
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
        return build_match_query(field, value, False)

    query = build_match_query(field, value, True, operator='and')

    if len(value.strip()) >= constants.MIN_AUTOCOMPLETE_CHARS:
        query |= build_match_phrase_prefix_query(field, value)

    query &= ~build_match_query(
        field, value, analyzer=es_config.name_analyzer_excluding_terms)

    return query


def build_match_phrase_prefix_query(field, value):
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


def build_range_query(field, operator, value):
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


def build_match_query(field, value, fuzzy=False, operator='or', analyzer=None):
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
