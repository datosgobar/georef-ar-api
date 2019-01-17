"""Módulo 'addresses' de georef-ar-api.

Contiene funciones y clases utilizadas para normalizar direcciones (recurso
/direcciones). Este módulo puede ser considerado una extensión del módulo
'normalizer', con funciones específicas para el procesamiento de direcciones.
"""

import re
from collections import defaultdict
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
        self._query = query.copy()
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

    def _build_base_address_hit(self, state=None, dept=None):
        address_hit = {}
        if state:
            address_hit[N.STATE] = state

        if dept:
            address_hit[N.DEPT] = dept

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

        keys = [N.ID, N.NAME, N.TYPE]

        street_entity = {
            key: elasticsearch_street_hit.get(key)
            for key in keys
        }

        # TODO: Borar y usar 'categoria' directamente
        if not street_entity[N.TYPE]:
            street_entity[N.TYPE] = elasticsearch_street_hit.get(N.CATEGORY)

        return street_entity


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

        return data.search_streets, query

    def set_elasticsearch_result(self, result, _iteration):
        # Para direcciones de tipo 'simple', el resultado final es simplemente
        # la primera consulta hecha a Elasticsearch.
        self._elasticsearch_result = result

    def _build_address_hits(self):
        address_hits = []
        fields = self._format[N.FIELDS]

        for street in self._elasticsearch_result.hits:
            address_hit = self._build_base_address_hit(street.get(N.STATE),
                                                       street.get(N.DEPT))

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
    required_iterations = 3

    def __init__(self, query, fmt):
        self._intersections_result = None
        self._street_1_result = None
        self._street_2_result = None
        self._street_1_ids = None
        self._street_2_ids = None
        self._intersection_hits = None

        super().__init__(query, fmt)

        # TODO: Definir si estos parámetros de búsqueda van a seguir
        # disponibles en /direcciones. Notar también los cambios en
        # data.py - build_address_query_format().
        self._query.pop('order', None)
        self._query.pop('street_type', None)

    def _build_intersections_query(self, street_1_ids, street_2_ids):
        query = self._query.copy()
        query['ids'] = (list(street_1_ids), list(street_2_ids))

        return data.search_intersections, query

    def _build_street_query(self, street, add_number):
        query = self._query.copy()

        query['name'] = street
        if add_number and self._door_number:
            query['number'] = self._door_number
        query['max'] = constants.MAX_RESULT_LEN
        query['offset'] = 0

        return data.search_streets, query

    def get_next_query(self, iteration):
        if iteration == 1:
            return self._build_street_query(self._street_names[0], True)
        if iteration == 2:
            return self._build_street_query(self._street_names[1], False)

        # iteration == 3
        return self._build_intersections_query(self._street_1_ids,
                                               self._street_2_ids)

    def _build_intersection_hits(self, intersections):
        intersection_hits = []
        fields = self._format[N.FIELDS]

        for street_1, street_2, geom in intersections:
            address_hit = self._build_base_address_hit(street_1.get(N.STATE),
                                                       street_1.get(N.DEPT))

            # TODO: Usar prov/dept de cual calle?
            address_hit[N.STREET] = self._build_street_entity(street_1)
            address_hit[N.STREET_X1] = self._build_street_entity(street_2)
            address_hit[N.STREET_X2] = self._build_street_entity()

            if N.FULL_NAME in fields:
                door_number = ''
                if self._door_number:
                    door_number = ' {}'.format(self._door_number)

                full_name = '{}{} y {}, {}, {}'.format(
                    street_1[N.NAME],
                    door_number,
                    street_2[N.NAME],
                    address_hit[N.DEPT][N.NAME],
                    address_hit[N.STATE][N.NAME]
                )

                address_hit[N.FULL_NAME] = full_name

            address_hit[N.LOCATION] = {
                N.LON: geom['coordinates'][0],
                N.LAT: geom['coordinates'][1]
            }

            intersection_hits.append(address_hit)

        return intersection_hits

    def set_elasticsearch_result(self, result, iteration):
        if iteration == 1:
            self._street_1_result = result
            if not self._street_1_result:
                self.required_iterations = 0
                return

            self._street_1_ids = {
                hit[N.ID]
                for hit in self._street_1_result.hits
            }
            return
        if iteration == 2:
            self._street_2_result = result
            if not self._street_2_result:
                self.required_iterations = 0
                return

            self._street_2_ids = {
                hit[N.ID]
                for hit in self._street_2_result.hits
            }
            return

        # iteration == 3
        self._intersections_result = result

        intersections = []
        for intersection in self._intersections_result.hits:
            id_1, id_2 = intersection[N.ID].split('-')

            if id_1 in self._street_1_ids and id_2 in self._street_2_ids:
                intersections.append((intersection[N.STREET_A],
                                      intersection[N.STREET_B],
                                      intersection[N.GEOM]))
            elif id_1 in self._street_2_ids and id_2 in self._street_1_ids:
                intersections.append((intersection[N.STREET_B],
                                      intersection[N.STREET_A],
                                      intersection[N.GEOM]))
            else:
                raise RuntimeError(
                    'Unknown street IDs for intersection {} - {}'.format(id_1,
                                                                         id_2))

        self._intersection_hits = self._build_intersection_hits(intersections)

    def get_query_result(self):
        if self._intersection_hits:
            return QueryResult.from_entity_list(
                self._intersection_hits, self._intersections_result.total,
                self._intersections_result.offset)
        else:
            return QueryResult.empty()


class AddressBtwnQueryPlanner(AddressQueryPlanner):
    # TODO: Completar clase

    def get_query_result(self):
        raise NotImplementedError()


def step_query_planners(es, query_planners, iteration):
    search_fn_queries = defaultdict(list)

    for planner in query_planners:
        if planner.required_iterations >= iteration:
            search_fn, query = planner.get_next_query(iteration)
            search_fn_queries[search_fn].append((query, planner))

    for search_fn, planner_queries in search_fn_queries.items():
        results = search_fn(es, [
            planner_query[0]
            for planner_query in planner_queries
        ])

        for result, planner_query in zip(results, planner_queries):
            planner = planner_query[1]
            planner.set_elasticsearch_result(result, iteration)


def run_address_queries(es, queries, formats):
    query_planners = []
    min_iterations = 0

    for query, fmt in zip(queries, formats):
        address_type = query[N.ADDRESS]['type']

        if not address_type:
            query_planner = AddressNoneQueryPlanner(query, fmt)
        elif address_type == 'simple':
            query_planner = AddressSimpleQueryPlanner(query, fmt)
        elif address_type == 'intersection':
            query_planner = AddressIsctQueryPlanner(query, fmt)
        elif address_type == 'between':
            # TODO: Complentar AddressBtwnQueryPlanner
            # query_planners.append(AddressBtwnQueryPlanner(query, fmt))
            query_planner = AddressNoneQueryPlanner(query, fmt)
        else:
            raise TypeError('Unknown address type')

        min_iterations = max(query_planner.required_iterations, min_iterations)
        query_planners.append(query_planner)

    for i in range(min_iterations):
        step_query_planners(es, query_planners, iteration=i + 1)

    return [
        query_planner.get_query_result()
        for query_planner in query_planners
    ]
