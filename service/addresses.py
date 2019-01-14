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
    required_iterations = 3

    def __init__(self, query, fmt):
        self._elasticsearch_result_1 = None
        self._elasticsearch_result_2 = None
        self._elasticsearch_result_3 = None
        self._intersection_hits = []
        super().__init__(query, fmt)

    def get_next_query(self, iteration):
        if iteration == 0:
            # Buscar la calle principal
            query = self._query.copy()
            query['name'] = self._street_names[0]
            query['max'] = constants.MAX_RESULT_LEN
            query['offset'] = 0

            if self._door_number:
                query['number'] = self._door_number

            return query
        elif iteration == 1:
            # Segunda calle
            query = self._query.copy()
            query['name'] = self._street_names[1]
            query['max'] = constants.MAX_RESULT_LEN
            query['offset'] = 0

            return query

        # iteration == 2

        result_1_len = len(self._elasticsearch_result_1.hits)
        result_2_len = len(self._elasticsearch_result_2.hits)

        if result_1_len > result_2_len:
            geoms = [hit[N.GEOM] for hit in self._elasticsearch_result_2.hits]
            ids = [hit[N.ID] for hit in self._elasticsearch_result_1.hits]
        else:
            geoms = [hit[N.GEOM] for hit in self._elasticsearch_result_1.hits]
            ids = [hit[N.ID] for hit in self._elasticsearch_result_2.hits]

        query = self._query.copy()
        query['street_ids'] = ids
        query['intersection_geoms'] = geoms

        return query

    def _find_intersections(self, streets_1, streets_2):
        intersections = []
        streets_2_found = set()

        for street_1 in streets_1:
            for street_2 in streets_2:
                if street_2[N.ID] in streets_2_found:
                    continue

                geom_1 = street_1[N.GEOM]
                geom_2 = street_2[N.GEOM]
                loc = geometry.streets_intersection_location(geom_1, geom_2)

                if loc[N.LAT] and loc[N.LON]:
                    intersections.append((street_1, street_2, loc))
                    streets_2_found.add(street_2[N.ID])
                    break

        return intersections

    def _build_intersection_hits(self, intersections):
        intersection_hits = []
        fields = self._format[N.FIELDS]

        for street_1, street_2, loc in intersections:
            intersection_hit = self._build_base_address_hit(street_1)
            intersection_hit[N.STREET] = self._build_street_entity(street_1)
            intersection_hit[N.STREET_X1] = self._build_street_entity(street_2)
            intersection_hit[N.STREET_X2] = self._build_street_entity()
            intersection_hit[N.LOCATION] = loc

            if N.FULL_NAME in fields:
                door_number = ''
                if self._door_number:
                    door_number = ' {}'.format(self._door_number)

                full_name = '{}{} y {}, {}, {}'.format(
                    street_1[N.NAME],
                    door_number,
                    street_2[N.NAME],
                    intersection_hit[N.DEPT][N.NAME],
                    intersection_hit[N.STATE][N.NAME]
                )

                intersection_hit[N.FULL_NAME] = full_name

            intersection_hits.append(intersection_hit)

        return intersection_hits

    def set_elasticsearch_result(self, result, iteration):
        if iteration == 0:
            self._elasticsearch_result_1 = result

            if len(self._elasticsearch_result_1) == 0:
                self.required_iterations = 0

            return
        elif iteration == 1:
            self._elasticsearch_result_2 = result

            if len(self._elasticsearch_result_2) == 0:
                self.required_iterations = 0

            return

        # iteration == 2

        self._elasticsearch_result_3 = result
        result_1_len = len(self._elasticsearch_result_1.hits)
        result_2_len = len(self._elasticsearch_result_2.hits)

        if result_1_len > result_2_len:
            streets_1 = self._elasticsearch_result_3.hits
            streets_2 = self._elasticsearch_result_2.hits
        else:
            streets_1 = self._elasticsearch_result_1.hits
            streets_2 = self._elasticsearch_result_3.hits

        # Separar las calles por departamentos para minimizar la cantidad de
        # cruces que hay que comprobar (dos calles de distintos departamentos
        # no pueden cruzarse entre sí)
        department_groups = {
            hit[N.DEPT][N.ID]: ([], [])
            for hit in self._elasticsearch_result_3.hits
        }

        for street_1 in streets_1:
            dept_id = street_1['departamento']['id']

            if dept_id in department_groups:
                department_groups[dept_id][0].append(street_1)

        for street_2 in streets_2:
            dept_id = street_2['departamento']['id']

            if dept_id in department_groups:
                department_groups[dept_id][1].append(street_2)

        intersections = []
        for dept in department_groups.values():
            intersections.extend(self._find_intersections(*dept))

        self._intersection_hits = self._build_intersection_hits(intersections)

    def get_query_result(self):
        if self._elasticsearch_result_3:
            return QueryResult.from_entity_list(
                self._intersection_hits, self._elasticsearch_result_3.total,
                self._elasticsearch_result_3.offset)
        else:
            return QueryResult.empty()


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
            query_planners.append(AddressIsctQueryPlanner(query, fmt))
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
