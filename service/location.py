"""Módulo 'location.py' de georef-ar-api.

Contiene las clases y funciones necesarias para la implementación del recurso
/ubicacion de la API.
"""

from service.data import ElasticsearchSearch, StatesSearch, DepartmentsSearch
from service.data import LocalGovernmentsSearch
from service import names as N
from service.geometry import Point
from service.query_result import QueryResult


def _build_location_result(params, query, state, dept, lg):
    """Construye un resultado para una consulta al endpoint de ubicación.

    Args:
        params (dict): Parámetros recibidos.
        query (dict): Query utilizada para obtener los resultados (generada a
            partir de 'params').
        state (dict): Provincia encontrada en la ubicación especificada.
            Puede ser None.
        dept (dict): Departamento encontrado en la ubicación especificada.
            Puede ser None.
        lg (dict): Gobierno local encontrado en la ubicación especificada. Puede
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
        lg = empty_entity.copy()
    else:
        dept = dept or empty_entity.copy()
        lg = lg or empty_entity.copy()

    return QueryResult.from_single_entity({
        N.STATE: state,
        N.DEPT: dept,
        N.LG: lg,
        N.LAT: query['lat'],
        N.LON: query['lon']
    }, params)


def run_location_queries(es, params_list, queries):
    """Dada una lista de queries de ubicación, construye las queries apropiadas
    a índices de departamentos y gobiernos locales, y las ejecuta utilizando
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
    # nacional, pero no los gobiernos locales.)
    #
    # Por cada consulta, implementar un patrón similar al de address.py (con
    # iteradores de consultas), donde cada iterador ('búsqueda') realiza los
    # siguientes pasos:
    #
    # 1) Buscar la posición en el índice de departamentos.
    # 2) Si se obtuvo un departamento, buscar la posición nuevamente pero en el
    #    índice de gobiernos locales. Si no se obtuvo nada, cancelar la búsqueda.
    # 3) Componer el departamento, la provincia del departamento y el gobierno local
    #    en un QueryResult para completar la búsqueda.

    all_searches = []

    state_searches = []
    lg_searches = []
    dept_searches = []

    for query in queries:
        es_query = {
            'geo_shape_geoms': [Point.from_json_location(query).to_geojson()],
            'fields': [N.ID, N.NAME, N.SOURCE],
            'size': 1
        }

        # Buscar la posición en provincias, departamentos y gobiernos locales

        search = StatesSearch(es_query)
        all_searches.append(search)
        state_searches.append(search)

        search = DepartmentsSearch(es_query)
        all_searches.append(search)
        dept_searches.append(search)

        search = LocalGovernmentsSearch(es_query)
        all_searches.append(search)
        lg_searches.append(search)

    # Ejecutar todas las búsquedas preparadas
    ElasticsearchSearch.run_searches(es, all_searches)

    locations = []
    iterator = zip(params_list, queries, state_searches, dept_searches,
                   lg_searches)

    for params, query, state_search, dept_search, lg_search in iterator:
        # Ya que la query de tipo location retorna una o cero entidades,
        # extraer la primera entidad de los resultados, o tomar None si
        # no hay resultados.
        state = state_search.result.hits[0] if state_search.result else None
        dept = dept_search.result.hits[0] if dept_search.result else None
        lg = lg_search.result.hits[0] if lg_search.result else None

        result = _build_location_result(params.received_values(), query, state,
                                        dept, lg)
        locations.append(result)

    return locations
