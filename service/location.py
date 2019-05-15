"""Módulo 'location.py' de georef-ar-api.

Contiene las clases y funciones necesarias para la implementación del recurso
/ubicacion de la API.
"""

from service.data import ElasticsearchSearch, StatesSearch, DepartmentsSearch
from service.data import MunicipalitiesSearch
from service import names as N
from service.geometry import Point
from service.query_result import QueryResult


def _build_location_result(params, query, state, dept, muni):
    """Construye un resultado para una consulta al endpoint de ubicación.

    Args:
        params (dict): Parámetros recibidos.
        query (dict): Query utilizada para obtener los resultados (generada a
            partir de 'params').
        state (dict): Provincia encontrada en la ubicación especificada.
            Puede ser None.
        dept (dict): Departamento encontrado en la ubicación especificada.
            Puede ser None.
        muni (dict): Municipio encontrado en la ubicación especificada. Puede
            ser None.

    Returns:
        QueryResult: Resultado de ubicación.

    """
    empty_entity = {
        N.ID: None,
        N.NAME: None,
        N.SOURCE: None
    }

    if not state:
        # El punto no está en la República Argentina
        state = empty_entity.copy()
        dept = empty_entity.copy()
        muni = empty_entity.copy()
    else:
        dept = dept or empty_entity.copy()
        muni = muni or empty_entity.copy()

    return QueryResult.from_single_entity({
        N.STATE: state,
        N.DEPT: dept,
        N.MUN: muni,
        N.LAT: query['lat'],
        N.LON: query['lon']
    }, params)


def run_location_queries(es, params_list, queries):
    """Dada una lista de queries de ubicación, construye las queries apropiadas
    a índices de departamentos y municipios, y las ejecuta utilizando
    Elasticsearch.

    Args:
        es (Elasticsearch): Conexión a Elasticsearch.
        params_list (list): Lista de ParametersParseResult.
        queries (list): Lista de queries de ubicación, generadas a partir de
            'params_list'.

    Returns:
        list: Resultados de ubicaciones (QueryResult).

    """
    # TODO:
    # Por problemas con los datos de origen, se optó por utilizar una
    # implementación simple para la la funcion 'run_location_queries'.
    # Cuando los datos de departamentos cubran todo el departamento nacional,
    # se podría modificar la función para que funcione de la siguiente forma:
    #
    # (Recordar que las provincias y departamentos cubren todo el territorio
    # nacional, pero no los municipios.)
    #
    # Por cada consulta, implementar un patrón similar al de address.py (con
    # iteradores de consultas), donde cada iterador ('búsqueda') realiza los
    # siguientes pasos:
    #
    # 1) Buscar la posición en el índice de departamentos.
    # 2) Si se obtuvo un departamento, buscar la posición nuevamente pero en el
    #    índice de municipios. Si no se obtuvo nada, cancelar la búsqueda.
    # 3) Componer el departamento, la provincia del departamento y el municipio
    #    en un QueryResult para completar la búsqueda.

    all_searches = []

    state_searches = []
    muni_searches = []
    dept_searches = []

    for query in queries:
        es_query = {
            'geo_shape_geoms': [Point.from_json_location(query).to_geojson()],
            'fields': [N.ID, N.NAME, N.SOURCE],
            'size': 1
        }

        # Buscar la posición en provincias, departamentos y municipios

        search = StatesSearch(es_query)
        all_searches.append(search)
        state_searches.append(search)

        search = DepartmentsSearch(es_query)
        all_searches.append(search)
        dept_searches.append(search)

        search = MunicipalitiesSearch(es_query)
        all_searches.append(search)
        muni_searches.append(search)

    # Ejecutar todas las búsquedas preparadas
    ElasticsearchSearch.run_searches(es, all_searches)

    locations = []
    iterator = zip(params_list, queries, state_searches, dept_searches,
                   muni_searches)

    for params, query, state_search, dept_search, muni_search in iterator:
        # Ya que la query de tipo location retorna una o cero entidades,
        # extraer la primera entidad de los resultados, o tomar None si
        # no hay resultados.
        state = state_search.result.hits[0] if state_search.result else None
        dept = dept_search.result.hits[0] if dept_search.result else None
        muni = muni_search.result.hits[0] if muni_search.result else None

        result = _build_location_result(params.received_values(), query, state,
                                        dept, muni)
        locations.append(result)

    return locations
