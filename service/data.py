"""Módulo 'data' de georef-ar-api

Contiene funciones que ejecutan consultas a índices de Elasticsearch.
"""

import elasticsearch
from elasticsearch_dsl import Search, MultiSearch
from elasticsearch_dsl.query import Match, Range, MatchPhrasePrefix, GeoShape
from elasticsearch_dsl.query import MatchNone, Terms, Prefix, Bool
from service import names as N
from service import constants
from service.management import es_config

INTERSECTION_PARAM_TYPES = (
    N.STATES, N.DEPARTMENTS, N.MUNICIPALITIES, N.STREETS
)


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
        _offset (int): Cantidad de resultados a saltear, comenzando desde el
            primero (0). El offset de la búsqueda es almacenado por separado
            para evitar tener que buscar el valor dentro del diccionario de
            _es_search.
        _result (ElasticsearchResult): Resultados de la búsqueda, luego de ser
            ejecutada.

    """

    def __init__(self, es_search, offset=0):
        """Inicializa un objeto de tipo ElasticsearchSearch.

        Args:
            es_search (elasticsearch_dsl.Search): Ver atributo '_es_search'.
            offset (int): Ver atributo '_offset'.

        """
        self._es_search = es_search
        self._offset = offset
        self._result = None

    @property
    def es_search(self):
        return self._es_search

    @property
    def offset(self):
        return self._offset

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

        step_size = constants.ES_MULTISEARCH_MAX_LEN

        # Partir las búsquedas en varios baches si es necesario.
        for i in range(0, len(searches), step_size):
            part = searches[i:i + step_size]
            ms = MultiSearch(using=es)

            for search in part:
                ms = ms.add(search.es_search)

            try:
                responses = ms.execute(raise_on_error=True)

                for search, response in zip(part, responses):
                    # Por cada objeto ElasticsearchSearch, establecer su objeto
                    # ElasticsearchResult conteniendo los documentos
                    # resultantes de la búsqueda ejecutada.
                    search.set_result(ElasticsearchResult(response,
                                                          search.offset))

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
    'interseccion' y comprueba que los IDs listados internamente apunten a
    entidades existentes. Esto se hace para poder utilizar más adelante los IDs
    ya validados en las consultas de tipo GeoShape con geometrías
    pre-indexadas, que requieren IDs de documentos existentes. La función se
    asegura de que incluso si hay varios parámetros de tipo 'intersección',
    se haga una sola consulta a Elasticsearch.

    Args:
        es (Elasticsearch): Cliente de Elasticsearch.
        params_list (list): Lista de conjuntos de parámetros de consultas.

    """
    searches = []

    for params in params_list:
        ids = params.get('intersection_ids')
        if not ids:
            continue

        for entity_type in INTERSECTION_PARAM_TYPES:
            entity_ids = list(ids[entity_type]) if entity_type in ids else None

            if entity_ids:
                ids[entity_type] = build_entity_search(entity_type,
                                                       entity_ids=entity_ids,
                                                       fields=[N.ID])

                searches.append(ids[entity_type])

    if not searches:
        return

    ElasticsearchSearch.run_searches(es, searches)

    for params in params_list:
        ids = params.get('intersection_ids')
        if not ids:
            continue

        for entity_type in INTERSECTION_PARAM_TYPES:
            if entity_type in ids:
                ids[entity_type] = [
                    hit['id']
                    for hit in ids[entity_type].result.hits
                ]


def expand_geometry_searches(es, index, params_list, searches):
    """Dada una lista de búsquedas *ya ejecutadas*, se asegura que las
    búsquedas que incluyen 'geometria' en su lista de campos efectivamente
    traigan las geometrías en sus resultados.

    Esta función es necesaria ya que los índices de entidades no cuentan con
    las versiones originales de las geometrías, por razones de performance (ver
    comentario en archivo es_config.py). Entonces, es necesario buscar las
    geometrías en índices separados, utilizando los IDs de los resultados
    encontrados en la primera búsqueda. Todo esto debe hacerse de forma
    amigable a las consultas bulk: se debe hacer una sola consulta a
    Elasticsearch incluso si se hicieron varias consultas a la API. Por esta
    razón se crean todas las ElasticsearchSearch necesarias y luego se las
    ejecuta con 'ElasticsearchSearch.run_searches'.

    Args:
        es (Elasticsearch): Cliente de Elasticsearch.
        index (str): Nombre del índice sobre el cual fueron ejecutadas las
            consultas originales.
        params_list (list): Lista de conjuntos de parámetros de consultas. Ver
            la documentación de la función 'build_entity_search' para más
            detalles.
        searches (list): Lista de ElasticsearchSearch ya ejecutadas, que
            potencialmente incluyen 'geometria' en su lista de campos
            requeridos.

    """
    geometry_searches = []
    for params, search in zip(params_list, searches):
        fields = params['fields']
        if search.result and N.GEOM in fields and N.ID in fields:
            # La búsqueda pidió la geometría de la entidad y se encontró una o
            # más entidades. Crear una nueva ElasticsearchSearch para buscar la
            # geometría utilizando el índice que corresponda (provincias ->
            # provincias-geometria).
            ids = [hit['id'] for hit in search.result.hits]
            geom_index = es_config.geom_index_for(index)

            geometry_search = build_entity_search(geom_index, entity_ids=ids,
                                                  fields=[N.ID, N.GEOM],
                                                  max=len(ids))

            # Agregar la búsqueda de geometría y la búsqueda original a la
            # lista geometry_searches
            geometry_searches.append((geometry_search, search))

    if not geometry_searches:
        return

    # Ejecutar las búsquedas de geometrías
    ElasticsearchSearch.run_searches(
        es,
        [searches[0] for searches in geometry_searches]
    )

    for geometry_search, search in geometry_searches:
        # Transformar resultados originales a diccionario de ID-entidad
        original_hits = {hit[N.ID]: hit for hit in search.result.hits}

        for hit in geometry_search.result.hits:
            # Agregar campo geometría a los resultados originales
            original_hits[hit[N.ID]][N.GEOM] = hit[N.GEOM]


def search_entities(es, index, params_list, expand_geometries=False):
    """Busca entidades políticas (localidades, departamentos, provincias o
    municipios) según parámetros de una o más consultas.

    Args:
        es (Elasticsearch): Cliente de Elasticsearch.
        index (str): Nombre del índice sobre el cual realizar las búsquedas.
        params_list (list): Lista de conjuntos de parámetros de consultas. Ver
            la documentación de la función 'build_entity_search' para más
            detalles.
        expand_geometries (bool): Si es verdadero, se analizan las búsquedas
            realizadas para ver si incluyen geometrías en sus listas de campos
            requeridos. Como la mayoría de las búsquedas no las incluyen, se
            desactiva la opción por defecto como una optimización.

    Returns:
        list: Resultados de búsqueda de entidades.

    """
    expand_intersection_parameters(es, params_list)

    searches = [build_entity_search(index, **params) for params in params_list]
    ElasticsearchSearch.run_searches(es, searches)

    if expand_geometries and index != es_config.geom_index_for(index):
        expand_geometry_searches(es, index, params_list, searches)

    return [search.result for search in searches]


def search_locations(es, index, params_list):
    """Busca entidades políticas que contengan un punto dato, según
    parámetros de una o más consultas.

    Args:
        es (Elasticsearch): Cliente de Elasticsearch.
        index (str): Nombre del índice sobre el cual realizar las búsquedas.
        params_list (list): Lista de conjuntos de parámetros de consultas. Ver
            la documentación de la función 'build_location_search' para más
            detalles.

    Returns:
        list: Resultados de búsqueda de entidades.

    """
    searches = [
        build_location_search(index, **params)
        for params in params_list
    ]

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
    searches = [build_streets_search(**params) for params in params_list]

    ElasticsearchSearch.run_searches(es, searches)
    return [search.result for search in searches]


def search_intersections(es, params_list):
    searches = [build_intersections_search(**params) for params in params_list]

    ElasticsearchSearch.run_searches(es, searches)
    return [search.result for search in searches]


def build_entity_search(index, entity_ids=None, name=None, state=None,
                        department=None, municipality=None, max=None,
                        order=None, fields=None, exact=False,
                        intersection_ids=None, offset=0):
    """Construye una búsqueda con Elasticsearch DSL para entidades políticas
    (localidades, departamentos, o provincias) según parámetros de búsqueda
    de una consulta.

    Args:
        index (str): Índice sobre el cual se debería ejecutar la búsqueda.
        entity_ids (list): IDs de entidades (opcional).
        name (str): Nombre del tipo de entidad (opcional).
        state (list, str): Lista de IDs o nombre de provincia para filtrar
            (opcional).
        department (list, str): Lista de IDs o nombre de departamento para
            filtrar (opcional).
        municipality (list, str): Lista de IDs o nombre de municipio para
            filtrar (opcional).
        max (int): Limita la cantidad de resultados (opcional).
        order (str): Campo por el cual ordenar los resultados (opcional).
        fields (list): Campos a devolver en los resultados (opcional).
        exact (bool): Activa búsqueda por nombres exactos. (toma efecto sólo si
            se especificaron los parámetros 'name', 'department',
            'municipality' o 'state'.) (opcional).
        intersection_ids (dict): Diccionario de tipo de entidad - lista de IDs
            a utilizar para filtrar por intersecciones con geometrías
            pre-indexadas (opcional).
        offset (int): Retornar resultados comenenzando desde los 'offset'
            primeros resultados obtenidos.

    Returns:
        Search: Búsqueda de tipo ElasticsearchSearch.

    """
    if not fields:
        fields = []

    s = Search(index=index)

    if entity_ids:
        s = s.filter(build_terms_query(N.ID, entity_ids))

    if name:
        s = s.query(build_name_query(N.NAME, name, exact))

    if intersection_ids:
        s = s.query(build_intersection_query(N.GEOM, ids=intersection_ids))

    if municipality:
        s = s.query(build_subentity_query(N.MUN_ID, N.MUN_NAME, municipality,
                                          exact))

    if department:
        s = s.query(build_subentity_query(N.DEPT_ID, N.DEPT_NAME, department,
                                          exact))

    if state:
        s = s.query(build_subentity_query(N.STATE_ID, N.STATE_NAME, state,
                                          exact))

    if order:
        if order == N.NAME:
            order = N.EXACT_SUFFIX.format(order)
        s = s.sort(order)

    s = s.source(include=fields)
    s = s[offset: offset + (max or constants.DEFAULT_SEARCH_SIZE)]

    return ElasticsearchSearch(s, offset)


def build_streets_search(street_ids=None, name=None, department=None,
                         state=None, street_type=None, max=None, order=None,
                         fields=None, exact=False, number=None,
                         intersection_ids=None, offset=0):
    """Construye una búsqueda con Elasticsearch DSL para vías de circulación
    según parámetros de búsqueda de una consulta.

    Args:
        street_ids (list): IDs de calles a buscar (opcional).
        name (str): Nombre de la calle para filtrar (opcional).
        department (str): ID o nombre de departamento para filtrar (opcional).
        state (str): ID o nombre de provincia para filtrar (opcional).
        street_type (str): Nombre del tipo de camino para filtrar (opcional).
        max (int): Limita la cantidad de resultados (opcional).
        order (str): Campo por el cual ordenar los resultados (opcional).
        fields (list): Campos a devolver en los resultados (opcional).
        number (int): Altura de la dirección (opcional).
        exact (bool): Activa búsqueda por nombres exactos. (toma efecto sólo si
            se especificaron los parámetros 'name', 'locality', 'state' o
            'department'.) (opcional).
        intersection_ids (dict): Diccionario de tipo de entidad - lista de IDs
            a utilizar para filtrar por intersecciones con geometrías
            pre-indexadas (opcional).
        offset (int): Retornar resultados comenenzando desde los 'offset'
            primeros resultados obtenidos.

    Returns:
        Search: Búsqueda de tipo ElasticsearchSearch.

    """
    if not fields:
        fields = []

    s = Search(index=N.STREETS)

    if street_ids:
        s = s.filter(build_terms_query(N.ID, street_ids))

    if intersection_ids:
        s = s.query(build_intersection_query(N.GEOM, ids=intersection_ids))

    if name:
        s = s.query(build_name_query(N.NAME, name, exact))

    if street_type:
        s = s.query(build_match_query(N.TYPE, street_type, fuzzy=True))

    if number:
        s = s.query(build_range_query(N.START_R, '<=', number) |
                    build_range_query(N.START_L, '<=', number))
        s = s.query(build_range_query(N.END_L, '>=', number) |
                    build_range_query(N.END_R, '>=', number))

    if department:
        s = s.query(build_subentity_query(N.DEPT_ID, N.DEPT_NAME, department,
                                          exact))

    if state:
        s = s.query(build_subentity_query(N.STATE_ID, N.STATE_NAME, state,
                                          exact))

    if order:
        if order == N.NAME:
            order = N.EXACT_SUFFIX.format(order)
        s = s.sort(order)

    s = s.source(include=fields)
    s = s[offset: offset + (max or constants.DEFAULT_SEARCH_SIZE)]

    return ElasticsearchSearch(s, offset)


def build_location_search(index, lat, lon, fields=None):
    """Construye una búsqueda con Elasticsearch DSL para entidades en una
    ubicación según parámetros de búsqueda de una consulta.

    Args:
        index (str): Índice sobre el cual se debería ejecutar la búsqueda.
        lat (float): Latitud del punto.
        lon (float): Longitud del punto.
        fields (list): Campos a devolver en los resultados (opcional).

    Returns:
        Search: Búsqueda de tipo ElasticsearchSearch.

    """
    if not fields:
        fields = []

    s = Search(index=index)

    options = {
        # Shape en formato GeoJSON
        'shape': {
            'type': 'Point',
            'coordinates': [lon, lat]
        }
    }

    s = s.query(GeoShape(**{N.GEOM: options}))
    s = s.source(include=fields)

    return ElasticsearchSearch(s[:1])


def build_intersections_search(ids=None, names=None, department=None,
                               state=None, max=None, fields=None, exact=False,
                               offset=0):
    if not fields:
        fields = []

    s = Search(index=N.INTERSECTIONS)

    if ids:
        query_1 = (
            build_terms_query(N.join(N.STREET_A, N.ID), ids[0]) &
            build_terms_query(N.join(N.STREET_B, N.ID), ids[1])
        )

        query_2 = (
            build_terms_query(N.join(N.STREET_A, N.ID), ids[1]) &
            build_terms_query(N.join(N.STREET_B, N.ID), ids[0])
        )

        s = s.query(query_1 | query_2)

    if names:
        query_1 = (
            build_name_query(N.join(N.STREET_A, N.NAME), names[0], exact) &
            build_name_query(N.join(N.STREET_B, N.NAME), names[1], exact)
        )

        query_2 = (
            build_name_query(N.join(N.STREET_A, N.NAME), names[1], exact) &
            build_name_query(N.join(N.STREET_B, N.NAME), names[0], exact)
        )

        s = s.query(query_1 | query_2)

    if department:
        for side in [N.STREET_A, N.STREET_B]:
            s = s.query(build_subentity_query(
                N.join(side, N.DEPT_ID),
                N.join(side, N.DEPT_NAME),
                department,
                exact
            ))

    if state:
        for side in [N.STREET_A, N.STREET_B]:
            s = s.query(build_subentity_query(
                N.join(side, N.STATE_ID),
                N.join(side, N.STATE_NAME),
                state,
                exact
            ))

    s = s.source(include=fields)
    s = s[offset: offset + (max or constants.DEFAULT_SEARCH_SIZE)]

    return ElasticsearchSearch(s, offset)


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


def build_intersection_query(field, ids):
    """Crea una condición de búsqueda por intersección de geometrías de una
    o más entidades, de tipos provincia/departamento/municipio.

    Args:
        field (str): Campo de la condición (debe ser de tipo 'geo_shape').
        ids (dict): Diccionario de tipo de entidad - lista de IDs.

    Returns:
        Query: Condición para Elasticsearch.

    """
    query = MatchNone()

    for entity_type, id_list in ids.items():
        for entity_id in id_list:
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
    if index not in INTERSECTION_PARAM_TYPES:
        raise ValueError('Invalid entity type')

    options = {
        'indexed_shape': {
            'index': es_config.geom_index_for(index),
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
