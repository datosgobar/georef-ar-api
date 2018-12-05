"""Módulo 'data' de georef-ar-api

Contiene funciones que ejecutan consultas a índices de Elasticsearch.
"""

import logging
import elasticsearch
import shapely.ops
import shapely.geometry
import shapely.wkb
from elasticsearch_dsl import Search, MultiSearch
from elasticsearch_dsl.query import Match, Range, MatchPhrasePrefix, GeoShape
from elasticsearch_dsl.query import MatchNone, Term, Prefix
from service import names as N
from service import constants
from service.management import es_config


logger = logging.getLogger('georef')


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


class ElasticsearchSearch:
    """Representa una búsqueda Elasticsearch y potencialmente sus
    resultados.

    Attributes:
        _es_search (elasticsearch_dsl.Search): Búsqueda Elasticsearch a
            ejecutar.
        _result (ElasticsearchResult): Resultados de la búsqueda, luego de ser
            ejecutada.

    """

    def __init__(self, es_search):
        """Inicializa un objeto de tipo ElasticsearchSearch.

        Args:
            es_search (elasticsearch_dsl.Search): Ver atributo '_es_search'.

        """
        self._es_search = es_search
        self._result = None

    @property
    def es_search(self):
        return self._es_search

    @property
    def result(self):
        if self._result is None:
            raise ValueError('Search has not been executed yet.')

        return self._result

    def set_result(self, result):
        if self._result is not None:
            raise ValueError('Search has already been executed.')

        self._result = result

    @staticmethod
    def run_searches(es, searches):
        """Ejecuta una lista de búsquedas ElasticsearchSearch. Internamente, se
        utiliza la función MultiSearch para ejecutarlas. Los resultados de cada
        búsqueda se almacenan en el objeto representando la búsqueda en sí
        (campo 'result').

        Args:
            es (Elasticsearch): Conexión a Elasticsearch.
            searches (list): Lista de búsquedas, de tipo ElasticsearchSearch.

        Raises:
            DataConnectionException: si ocurrió un error al ejecutar las
                búsquedas.

        """
        if not searches:
            return

        ms = MultiSearch(using=es)

        for search in searches:
            ms = ms.add(search.es_search)

        try:
            responses = ms.execute(raise_on_error=True)

            for search, response in zip(searches, responses):
                # Incluir offset (inicio) en los resultados
                offset = search.es_search.to_dict()['from']
                search.set_result(ElasticsearchResult(response, offset))

        except elasticsearch.ElasticsearchException:
            raise DataConnectionException()


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


def expand_intersection_parameters(es, params_list):
    """Dada una lista de conjuntos de parámetros, encuentra parámetros de tipo
    'interseccion' y reemplaza los listados de IDs por búsquedas Elasticsearch
    de esos IDs. Esto se hace para poder utilizar más adelante los IDs ya
    validados en las consultas de tipo GeoShape con geometrías pre-indexadas,
    que requieren IDs de documentos existentes.

    Args:
        es (Elasticsearch): Cliente de Elasticsearch.
        params_list (list): Lista de conjuntos de parámetros de consultas.

    """
    sub_queries = {
        N.STATES: [],
        N.DEPARTMENTS: [],
        N.MUNICIPALITIES: []
    }

    for params in params_list:
        ids = params.get('intersection')
        if not ids:
            continue

        for entity_type in sub_queries:
            ids[entity_type] = [
                ElasticsearchSearch(build_entity_search(entity_type,
                                                        entity_id=i,
                                                        fields=[N.ID]))
                for i in ids[entity_type]
            ]

            sub_queries[entity_type].extend(ids[entity_type])

    for queries in sub_queries.values():
        ElasticsearchSearch.run_searches(es, queries)


def search_entities(es, index, params_list):
    """Busca entidades políticas (localidades, departamentos, provincias o
    municipios) según parámetros de una o más consultas.

    Args:
        es (Elasticsearch): Cliente de Elasticsearch.
        index (str): Nombre del índice sobre el cual realizar las búsquedas.
        params_list (list): Lista de conjuntos de parámetros de consultas. Ver
            la documentación de la función 'build_entity_search' para más
            detalles.

    Returns:
        list: Resultados de búsqueda de entidades.

    """
    expand_intersection_parameters(es, params_list)

    searches = [ElasticsearchSearch(build_entity_search(index, **params))
                for params in params_list]

    ElasticsearchSearch.run_searches(es, searches)
    return [search.result for search in searches]


def search_places(es, index, params_list):
    """Busca entidades políticas que contengan un punto dato, según
    parámetros de una o más consultas.

    Args:
        es (Elasticsearch): Cliente de Elasticsearch.
        index (str): Nombre del índice sobre el cual realizar las búsquedas.
        params_list (list): Lista de conjuntos de parámetros de consultas. Ver
            la documentación de la función 'build_place_search' para más
            detalles.

    Returns:
        list: Resultados de búsqueda de entidades.

    """
    searches = [ElasticsearchSearch(build_place_search(index, **params))
                for params in params_list]

    ElasticsearchSearch.run_searches(es, searches)
    return [search.result for search in searches]


def search_streets(es, params_list):
    """Busca vías de circulación según parámetros de una o más consultas.

    Args:
        es (Elasticsearch): Cliente de Elasticsearch.
        params_list (list): Lista de conjuntos de parámetros de consultas. Ver
            la documentación de la función 'build_streets_search' para más
            detalles.

    Returns:
        list: Resultados de búsqueda de vías de circulación.

    """
    searches = [ElasticsearchSearch(build_streets_search(**params))
                for params in params_list]

    ElasticsearchSearch.run_searches(es, searches)
    return [search.result for search in searches]


def build_entity_search(index, entity_id=None, name=None, state=None,
                        department=None, municipality=None, max=None,
                        order=None, fields=None, exact=False, offset=0,
                        intersection=None):
    """Construye una búsqueda con Elasticsearch DSL para entidades políticas
    (localidades, departamentos, o provincias) según parámetros de búsqueda
    de una consulta.

    Args:
        index (str): Índice sobre el cual se debería ejecutar la búsqueda.
        entity_id (str): ID de la entidad (opcional).
        name (str): Nombre del tipo de entidad (opcional).
        state (str): ID o nombre de provincia para filtrar (opcional).
        department (str): ID o nombre de departamento para filtrar (opcional).
        municipality (str): ID o nombre de municipio para filtrar (opcional).
        max (int): Limita la cantidad de resultados (opcional).
        order (str): Campo por el cual ordenar los resultados (opcional).
        fields (list): Campos a devolver en los resultados (opcional).
        exact (bool): Activa búsqueda por nombres exactos. (toma efecto sólo si
            se especificaron los parámetros 'name', 'department',
            'municipality' o 'state'.) (opcional).
        offset (int): Retornar resultados comenenzando desde los 'offset'
            primeros resultados obtenidos.

    Returns:
        Search: Búsqueda de tipo Search.

    """
    if not fields:
        fields = []

    s = Search(index=index)

    if entity_id:
        s = s.filter(build_term_query(N.ID, entity_id))

    if name:
        s = s.query(build_name_query(N.NAME, name, exact))

    if intersection:
        s = s.query(build_intersection_query(N.GEOM, intersection))

    if municipality:
        if municipality.isdigit():
            s = s.filter(build_term_query(N.MUN_ID, municipality))
        else:
            s = s.query(build_name_query(N.MUN_NAME, municipality, exact))

    if department:
        if department.isdigit():
            s = s.filter(build_term_query(N.DEPT_ID, department))
        else:
            s = s.query(build_name_query(N.DEPT_NAME, department, exact))

    if state:
        if state.isdigit():
            s = s.filter(build_term_query(N.STATE_ID, state))
        else:
            s = s.query(build_name_query(N.STATE_NAME, state, exact))

    if order:
        if order == N.NAME:
            order += N.EXACT_SUFFIX
        s = s.sort(order)

    s = s.source(include=fields)
    return s[offset: offset + (max or constants.DEFAULT_SEARCH_SIZE)]


def build_streets_search(street_id=None, road_name=None, department=None,
                         state=None, road_type=None, max=None, order=None,
                         fields=None, exact=False, number=None, offset=0):
    """Construye una búsqueda con Elasticsearch DSL para vías de circulación
    según parámetros de búsqueda de una consulta.

    Args:
        street_id (str): ID de la calle a buscar (opcional).
        road_name (str): Nombre de la calle para filtrar (opcional).
        department (str): ID o nombre de departamento para filtrar (opcional).
        state (str): ID o nombre de provincia para filtrar (opcional).
        road_type (str): Nombre del tipo de camino para filtrar (opcional).
        max (int): Limita la cantidad de resultados (opcional).
        order (str): Campo por el cual ordenar los resultados (opcional).
        fields (list): Campos a devolver en los resultados (opcional).
        number (int): Altura de la dirección (opcional).
        exact (bool): Activa búsqueda por nombres exactos. (toma efecto sólo si
            se especificaron los parámetros 'name', 'locality', 'state' o
            'department'.) (opcional).
        offset (int): Retornar resultados comenenzando desde los 'offset'
            primeros resultados obtenidos.

    Returns:
        Search: Búsqueda de tipo Search.

    """
    if not fields:
        fields = []

    s = Search(index=N.STREETS)

    if street_id:
        s = s.filter(build_term_query(N.ID, street_id))

    if road_name:
        s = s.query(build_name_query(N.NAME, road_name, exact))

    if road_type:
        s = s.query(build_match_query(N.ROAD_TYPE, road_type, fuzzy=True))

    if number:
        s = s.query(build_range_query(N.START_R, '<=', number) |
                    build_range_query(N.START_L, '<=', number))
        s = s.query(build_range_query(N.END_L, '>=', number) |
                    build_range_query(N.END_R, '>=', number))

    if department:
        if department.isdigit():
            s = s.filter(build_term_query(N.DEPT_ID, department))
        else:
            s = s.query(build_name_query(N.DEPT_NAME, department, exact))

    if state:
        if state.isdigit():
            s = s.filter(build_term_query(N.STATE_ID, state))
        else:
            s = s.query(build_name_query(N.STATE_NAME, state, exact))

    if order:
        if order == N.NAME:
            order += N.EXACT_SUFFIX
        s = s.sort(order)

    s = s.source(include=fields)
    return s[offset: offset + (max or constants.DEFAULT_SEARCH_SIZE)]


def build_place_search(index, lat, lon, fields=None):
    """Construye una búsqueda con Elasticsearch DSL para entidades en una
    ubicación según parámetros de búsqueda de una consulta.

    Args:
        index (str): Índice sobre el cual se debería ejecutar la búsqueda.
        lat (float): Latitud del punto.
        lon (float): Longitud del punto.
        fields (list): Campos a devolver en los resultados (opcional).

    Returns:
        Search: Búsqueda de tipo Search.

    """
    if not fields:
        fields = []

    s = Search(index=index)

    options = {
        'shape': {
            'type': 'point',
            'coordinates': [lon, lat]
        }
    }

    s = s.query(GeoShape(**{N.GEOM: options}))
    s = s.source(include=fields)
    return s[:1]


def build_intersection_query(field, ids):
    """Crea una condición de búsqueda por intersección de geometrías de una
    o más entidades, de tipos provincia/departamento/municipio.

    Args:
        field (str): Campo de la condición (debe ser de tipo 'geo_shape').
        ids (dict): Diccionario de tipo de entidad / lista de
            ElasticsearchSearch. Cada ElasticsearchSearch representa,
            potencialmente, un ID de entidad a utilizar en una GeoShape query.

    Returns:
        Query: Condición para Elasticsearch.

    """
    query = MatchNone()

    for entity_type, entity_id_searches in ids.items():
        for search in entity_id_searches:
            hits = search.result.hits

            if hits:
                # La búsqueda por ID retornó resultados, la longitud de los
                # los mismos debe ser 1.
                entity_id = hits[0]['id']
                query |= build_geo_indexed_shape_query(field, entity_type,
                                                       entity_id, N.GEOM)

    return query


def build_geo_indexed_shape_query(field, index, entity_id, entity_geom_path):
    """Crea una condición de búsqueda por intersección con una geometría
    pre-indexada. La geometría debe pertenecer a una entidad de tipo provincia,
    departamento o municipio.

    Args:
        field (str): Campo de la condición.
        index (str): Índice donde está almacenada la geometría pre-indexada.
        entity_id (str): ID del documento con la geometría a utilizar.
        entity_geom_path (str): Campo del documento donde se encuentra la
            geometría.

    Returns:
        Query: Condición para Elasticsearch.

    """
    if index not in [N.STATES, N.DEPARTMENTS, N.MUNICIPALITIES]:
        raise ValueError('Invalid entity type.')

    options = {
        'indexed_shape': {
            'index': N.GEOM_INDEX.format(index),
            'type': es_config.DOC_TYPE,
            'id': entity_id,
            'path': entity_geom_path
        }
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


def build_term_query(field, value):
    """Crea una condición de búsqueda por término exacto para Elasticsearch.

    Args:
        field (str): Campo de la condición.
        value (str): Valor de comparación.

    Returns:
        Query: Condición para Elasticsearch.

    """
    return Term(**{field: value})


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
        field += N.EXACT_SUFFIX
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
        raise ValueError('Invalid operator.')

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


def street_number_location(geom, number, start, end):
    """Obtiene las coordenadas de un punto dentro de un tramo de calle.

    Args:
        geom (str): Geometría de un tramo de calle.
        number (int or None): Número de puerta o altura.
        start (int): Numeración inicial del tramo de calle.
        end (int): Numeración final del tramo de calle.

    Returns:
        dict: Coordenadas del punto.

    """
    shape = shapely.wkb.loads(bytes.fromhex(geom))
    line = shapely.ops.linemerge(shape)
    lat, lon = None, None

    if isinstance(line, shapely.geometry.LineString):
        # Si la geometría de la calle pudo ser combinada para formar un único
        # tramo, encontrar la ubicación interpolando la altura con el inicio y
        # fin de altura de la calle.
        ip = line.interpolate((number - start) / (end - start),
                              normalized=True)
        # TODO:
        # line.interpolate retorna un shapely Point pero pylint solo mira
        # los atributos de BaseGeometry.
        lat = ip.y  # pylint: disable=no-member
        lon = ip.x  # pylint: disable=no-member

    return {
        N.LAT: lat,
        N.LON: lon
    }
