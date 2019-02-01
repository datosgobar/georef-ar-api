"""Módulo 'location.py' de georef-ar-api.

Contiene las clases y funciones necesarias para la implementación del recurso
/ubicacion de la API.
"""

from service import data
from service import names as N
from service.geometry import Point
from service.query_result import QueryResult


def build_location_result(query, state, dept, muni):
    """Construye un resultado para una consulta al endpoint de ubicación.

    Args:
        query (dict): Query utilizada para obtener los resultados.
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
    })


def run_location_queries(es, queries):
    """Dada una lista de queries de ubicación, construye las queries apropiadas
    a índices de departamentos y municipios, y las ejecuta utilizando
    Elasticsearch.

    Args:
        es (Elasticsearch): Conexión a Elasticsearch.
        queries (list): Lista de queries de ubicación

    Returns:
        list: Resultados de ubicaciones (QueryResult).

    """

    # TODO:
    # Por problemas con los datos de origen, se optó por utilizar una
    # implementación simple para la la funcion 'process_location_queries'.
    # Cuando los datos de departamentos cubran todo el departamento nacional,
    # se podría modificar la función para que funcione de la siguiente forma:
    #
    # (Recordar que las provincias y departamentos cubren todo el territorio
    # nacional, pero no los municipios.)
    #
    # 1) Tomar las N consultas recibidas y enviar todas al índice de
    #    departamentos.
    # 2) Tomar las consultas *que retornaron una entidad*, y re-enviarlas pero
    #    esta vez al índice de municipios. Las consultas que *no* retornaron
    #    una entidad (es decir, no cayeron dentro de un depto.) quedan marcadas
    #    como nulas.
    # 3) Combinar los resultados de los pasos 1 y 2: Si la consulta no tiene
    #    depto. asociado, su resultado es nulo. Si tiene depto., entonces
    #    también tiene provincia. Si la consulta tiene municipio, entonces
    #    tiene provincia, departamento y municipio.

    all_searches = []

    state_searches = []
    muni_searches = []
    dept_searches = []

    for query in queries:
        search = data.StatesSearch({
            'geo_shape_geoms': [Point.from_json_location(query).to_geojson()],
            'fields': [N.ID, N.NAME, N.SOURCE],
            'size': 1
        })

        all_searches.append(search)
        state_searches.append(search)

        search = data.DepartmentsSearch({
            'geo_shape_geoms': [Point.from_json_location(query).to_geojson()],
            'fields': [N.ID, N.NAME, N.SOURCE],
            'size': 1
        })

        all_searches.append(search)
        dept_searches.append(search)

        search = data.MunicipalitiesSearch({
            'geo_shape_geoms': [Point.from_json_location(query).to_geojson()],
            'fields': [N.ID, N.NAME, N.SOURCE],
            'size': 1
        })

        all_searches.append(search)
        muni_searches.append(search)

    data.ElasticsearchSearch.run_searches(es, all_searches)

    locations = []
    for query, state_search, dept_search, muni_search in zip(queries,
                                                             state_searches,
                                                             dept_searches,
                                                             muni_searches):
        # Ya que la query de tipo location retorna una o cero entidades,
        # extraer la primera entidad de los resultados, o tomar None si
        # no hay resultados.
        state = state_search.result.hits[0] if state_search.result else None
        dept = dept_search.result.hits[0] if dept_search.result else None
        muni = muni_search.result.hits[0] if muni_search.result else None
        locations.append(build_location_result(query, state, dept, muni))

    return locations
