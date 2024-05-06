"""Módulo 'location.py' de georef-ar-api.

Contiene las clases y funciones necesarias para la implementación del recurso
/ubicacion de la API.
"""
from service.constants import SB_DISTANCE_TOLERANCE, STREET_ID_LEN, SB_MAX_SEARCH
from service.data import ElasticsearchSearch, StatesSearch, DepartmentsSearch, StreetBlocksSearch
from service.data import LocalGovernmentsSearch
from service import names as N
from service.geometry import Point
from service.query_result import QueryResult


def _build_location_result(params, query, state, dept, lg, sb):
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
        sb (dict): Cuadra más cercana en un radio predefinido para la ubicación
            especificada. Puede ser None.

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
        sb = sb or empty_entity.copy()

    return QueryResult.from_single_entity({
        N.STATE: state,
        N.DEPT: dept,
        N.LG: lg,
        N.STREET: sb,
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
    sb_searches = []

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

        search = StreetBlocksSearch({
            'geo_shape_geoms': [Point.from_json_location(query).to_geojson_circle(SB_DISTANCE_TOLERANCE)],
            'fields': [N.ID, N.STREET_NAME, N.STREET_SOURCE, N.GEOM, N.DOOR_NUM],
            'size': SB_MAX_SEARCH
        })
        all_searches.append(search)
        sb_searches.append(search)

    # Ejecutar todas las búsquedas preparadas
    ElasticsearchSearch.run_searches(es, all_searches)

    locations = []
    iterator = zip(params_list, queries, state_searches, dept_searches,
                   lg_searches, sb_searches)

    for params, query, state_search, dept_search, lg_search, sb_search in iterator:
        # Ya que la query de tipo location retorna una o cero entidades,
        # extraer la primera entidad de los resultados, o tomar None si
        # no hay resultados.
        state = state_search.result.hits[0] if state_search.result else None
        dept = dept_search.result.hits[0] if dept_search.result else None
        lg = lg_search.result.hits[0] if lg_search.result else None
        sb = calc_nearest_street_block_params(params, sb_search)

        result = _build_location_result(params.received_values(), query, state,
                                        dept, lg, sb)
        locations.append(result)

    return locations


def calc_nearest_street_block_params(params, sb_search):
    """Analiza los resultados devueltos por la consulta y estima la numeración de la cuadra más cercana.

    Args:
        params: Los parámetros de la consulta.
        sb_search: Resultados de la consulta al índice de cuadras.

    Returns:
        dict: Parámetros de la calle y la altura

    """

    if sb_search.result is None:
        return None

    location = Point(params.values['lon'], params.values['lat'])

    nearest_street_block = None
    k = None
    min_dist_min = None
    point_a = None
    point_b = None

    for hit in sb_search.result.hits:
        coord = hit[N.GEOM]['coordinates']

        # Las cuadras deben estar constituidas por un único segmento
        if len(coord) != 1 or len(coord[0][0]) != 2:
            continue

        a = Point(*coord[0][0])
        b = Point(*coord[0][1])

        length_street_block = a.approximate_distance_meters(b)
        distance_a = location.approximate_distance_meters(a)
        distance_b = location.approximate_distance_meters(b)

        s = (distance_a + distance_b + length_street_block) / 2
        distance_a_b = 2 * (s * (s - distance_a) * (s - distance_b) * (s - length_street_block)) ** 0.5 / length_street_block

        k = max(0, min(1, ((distance_a ** 2 - distance_a_b ** 2) ** 0.5) / length_street_block))

        if k < 0:
            min_dist = distance_a
        elif k > 0:
            min_dist = distance_b
        else:
            min_dist = distance_a_b

        if not min_dist_min or min_dist < min_dist_min:
            min_dist_min = min_dist
            nearest_street_block = hit
            point_a = a
            point_b = b

    if not point_a or not point_b:
        return None

    a = [point_b.lon - point_a.lon, point_b.lat - point_a.lat]
    v = [location.lon - point_a.lon, location.lat - point_a.lat]

    parity = "even" if v[0] * a[1] - v[1] * a[0] < 0 else "odd"

    sr = nearest_street_block[N.DOOR_NUM][N.START][N.RIGHT]
    sl = nearest_street_block[N.DOOR_NUM][N.START][N.LEFT]
    er = nearest_street_block[N.DOOR_NUM][N.END][N.RIGHT]
    el = nearest_street_block[N.DOOR_NUM][N.END][N.LEFT]

    result = {
        'id': nearest_street_block['id'][:STREET_ID_LEN],
        'nombre': nearest_street_block['calle']['nombre'],
        'fuente': nearest_street_block['calle']['fuente'],
    }

    number = None
    if parity == "even" and el > 0 and sl < el:
        n = sl + k * (el - sl)
        number = min(el, max(sl, 2 * round(n / 2)))
    elif parity == "odd" and er > 0 and sr < er:
        n = sr + k * (er - sr)
        number = min(er, max(sr, 2 * round(n / 2) + 1))

    if number:
        result.update({
            'altura': number,
        })

    return result
