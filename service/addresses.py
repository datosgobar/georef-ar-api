"""Módulo 'addresses' de georef-ar-api.

Contiene funciones y clases utilizadas para normalizar direcciones (recurso
/direcciones). Este módulo puede ser considerado una extensión del módulo
'normalizer', con funciones específicas para el procesamiento de direcciones.
"""

import re
from service import names as N
from service import data, constants, geometry
from service.query_result import QueryResult


def street_extents(door_nums, number):
    """Dados los datos de alturas de una calle, y una altura recibida en una
    consulta, retorna los extremos de la calle que contienen la altura.
    Idealmente, se utilizaría siempre start_r y end_l, pero al contar a veces
    con datos incompletos, se flexibiliza la elección de extremos para poder
    geolocalizar más direcciones.

    Args:
        door_nums (dict): Datos de alturas de la calle.
        number (int): Altura recibida en una consulta.

    Returns:
        tuple (int, int): Altura inicial y final de la calle que contienen la
            altura especificada.

    Raises:
        ValueError: Si la altura no está contenida dentro de ninguna
            combinación de extremos.

    """
    start_r = door_nums[N.START][N.RIGHT]
    start_l = door_nums[N.START][N.LEFT]
    end_r = door_nums[N.END][N.RIGHT]
    end_l = door_nums[N.END][N.LEFT]

    combinations = [(start_r, end_l), (start_l, end_r), (start_r, end_r),
                    (start_l, end_l)]

    for start, end in combinations:
        if start <= number <= end:
            return start, end

    raise ValueError('Street number out of range')


class AddressQueryPlanner:
    def __init__(self, query, fmt):
        self._query = query
        self._format = fmt
        self._interpret_address_data(self._query.pop(N.ADDRESS))

    def _interpret_address_data(self, address_data):
        self._street_names = address_data['street_names']
        self._door_number = None
        self._door_number_unit = address_data['door_number']['unit']
        self._floor = address_data['floor']

        door_number_value = address_data['door_number']['value']
        if door_number_value:
            match = re.search(r'\d+', door_number_value)

            if match:
                num_int = int(match.group(0))
                if num_int != 0:
                    self._door_number = num_int

    def get_next_query(self, _iteration):
        return None

    def set_elasticsearch_result(self, result, _iteration):
        pass

    def get_query_result(self):
        raise NotImplementedError()

    def _build_base_address_hit(self, elasticsearch_street_hit):
        base_keys = [N.STATE, N.DEPT]

        address_hit = {
            key: elasticsearch_street_hit[key]
            for key in base_keys
            if key in elasticsearch_street_hit
        }

        address_hit[N.SOURCE] = constants.INDEX_SOURCES[N.STREETS]
        address_hit[N.DOOR_NUM] = {
            N.VALUE: self._door_number,
            N.UNIT: self._door_number_unit
        }
        address_hit[N.FLOOR] = self._floor
        address_hit[N.LOCATION] = {
            N.LAT: None,
            N.LON: None
        }

        return address_hit

    def _build_street_entity(self, elasticsearch_street_hit=None):
        if not elasticsearch_street_hit:
            elasticsearch_street_hit = {}

        keys = [N.ID, N.NAME, N.ROAD_TYPE]

        return {
            key: elasticsearch_street_hit.get(key)
            for key in keys
        }


class AddressNoneQueryPlanner(AddressQueryPlanner):
    required_iterations = 0

    def get_query_result(self):
        return QueryResult.empty()


class AddressSimpleQueryPlanner(AddressQueryPlanner):
    required_iterations = 1

    def __init__(self, query, fmt):
        self._elasticsearch_result = None
        super().__init__(query, fmt)

    def get_next_query(self, _iteration):
        query = self._query.copy()
        query['name'] = self._street_names[0]

        if self._door_number:
            query['number'] = self._door_number

        return query

    def set_elasticsearch_result(self, result, _iteration):
        # Para direcciones de tipo 'simple', el resultado final es simplemente
        # la primera consulta hecha a Elasticsearch.
        self._elasticsearch_result = result

    def _build_address_hits(self):
        address_hits = []
        fields = self._format[N.FIELDS]

        for street in self._elasticsearch_result.hits:
            address_hit = self._build_base_address_hit(street)
            address_hit[N.STREET] = self._build_street_entity(street)
            address_hit[N.STREET_X1] = self._build_street_entity()
            address_hit[N.STREET_X2] = self._build_street_entity()

            if N.FULL_NAME in fields:
                if self._door_number:
                    parts = street[N.FULL_NAME].split(',')
                    parts[0] += ' {}'.format(self._door_number)
                    address_hit[N.FULL_NAME] = ','.join(parts)
                else:
                    address_hit[N.FULL_NAME] = street[N.FULL_NAME]

            door_nums = street.pop(N.DOOR_NUM)
            geom = street.pop(N.GEOM)

            if (N.LOCATION_LAT in fields or N.LOCATION_LON in fields) and \
               self._door_number:
                # El llamado a street_extents() no puede lanzar una
                # excepción porque los resultados de Elasticsearch aseguran
                # que 'number' está dentro de alguna combinación de
                # extremos de la calle.
                start, end = street_extents(door_nums, self._door_number)
                loc = geometry.street_number_location(geom,
                                                      self._door_number,
                                                      start, end)

                address_hit[N.LOCATION] = loc

            address_hits.append(address_hit)

        return address_hits

    def get_query_result(self):
        address_hits = self._build_address_hits()

        return QueryResult.from_entity_list(address_hits,
                                            self._elasticsearch_result.total,
                                            self._elasticsearch_result.offset)


class AddressIsctQueryPlanner(AddressQueryPlanner):
    # TODO: Completar clase

    def get_query_result(self):
        raise NotImplementedError()


class AddressBtwnQueryPlanner(AddressQueryPlanner):
    # TODO: Completar clase

    def get_query_result(self):
        raise NotImplementedError()


def step_query_planners(es, query_planners, iteration=0):
    planner_queries = []
    for planner in query_planners:
        if planner.required_iterations > iteration:
            query = planner.get_next_query(iteration)
            planner_queries.append((planner, query))

    results = data.search_streets(es, [
        planner_query[1]
        for planner_query in planner_queries
        if planner_query[1]
    ])

    for result, planner_query in zip(results, planner_queries):
        planner = planner_query[0]
        planner.set_elasticsearch_result(result, iteration)


def run_address_queries(es, queries, formats):
    query_planners = []
    for query, fmt in zip(queries, formats):
        address_type = query[N.ADDRESS]['type']

        if not address_type:
            query_planners.append(AddressNoneQueryPlanner(query, fmt))
        elif address_type == 'simple':
            query_planners.append(AddressSimpleQueryPlanner(query, fmt))
        elif address_type == 'isct':
            # TODO: Complentar AddressIsctQueryPlanner
            # query_planners.append(AddressIsctQueryPlanner(query, fmt))
            query_planners.append(AddressNoneQueryPlanner(query, fmt))
        elif address_type == 'btwn':
            # TODO: Complentar AddressBtwnQueryPlanner
            # query_planners.append(AddressBtwnQueryPlanner(query, fmt))
            query_planners.append(AddressNoneQueryPlanner(query, fmt))
        else:
            raise TypeError('Unknown address type')

    for i in range(3):
        # TODO: Reducir cantidad de iteraciones (fijarse qué tipos de
        # direcciones hay en la lista)
        step_query_planners(es, query_planners, iteration=i)

    return [
        query_planner.get_query_result()
        for query_planner in query_planners
    ]
