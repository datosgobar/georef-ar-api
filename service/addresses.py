"""Módulo 'addresses' de georef-ar-api.

Contiene funciones y clases utilizadas para normalizar direcciones (recurso
/direcciones). Este módulo puede ser considerado una extensión del módulo
'normalizer', con funciones específicas para el procesamiento de direcciones.
"""

from collections import defaultdict
from service import names as N
from service import data, constants, geometry
from service.query_result import QueryResult


class AddressQueryPlanner:
    def __init__(self, query, fmt):
        self._query = query.copy()
        self._format = fmt
        self._address_data = self._query.pop(N.ADDRESS)

        if self._address_data:
            self._numerical_door_number = \
                self._address_data.normalized_door_number_value()

    def planner_steps(self):
        raise NotImplementedError()

    def get_query_result(self):
        raise NotImplementedError()

    def _address_full_name(self, *streets):
        door_number = ''
        if self._numerical_door_number:
            door_number = ' {}'.format(self._numerical_door_number)

        # Usar siempre datos de provincia/departamento de la primera calle
        # En la mayoría de los casos, las tres calles van a ser del mismo
        # lugar.
        fmt = {
            'state': streets[0][N.STATE][N.NAME],
            'dept': streets[0][N.DEPT][N.NAME],
            'door_number': door_number
        }

        for i, street in enumerate(streets):
            fmt['street_{}'.format(i + 1)] = street[N.NAME]

        if self._address_data.type == 'simple':
            template = '{street_1}{door_number}'
        elif self._address_data.type == 'intersection':
            template = '{street_1}{door_number} y {street_2}'
        elif self._address_data.type == 'between':
            template = '{street_1}{door_number} entre {street_2} y {street_3}'
        else:
            raise ValueError('Unknown address type')

        template += ', {dept}, {state}'
        return template.format(**fmt)

    def _build_base_address_hit(self, state=None, dept=None):
        address_hit = {}
        if state:
            address_hit[N.STATE] = state

        if dept:
            address_hit[N.DEPT] = dept

        address_hit[N.SOURCE] = constants.INDEX_SOURCES[N.STREETS]
        address_hit[N.DOOR_NUM] = {
            N.VALUE: self._address_data.door_number_value,
            N.UNIT: self._address_data.door_number_unit
        }
        address_hit[N.FLOOR] = self._address_data.floor
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

    def planner_steps(self):
        return iter(())

    def get_query_result(self):
        return QueryResult.empty()


class AddressSimpleQueryPlanner(AddressQueryPlanner):
    required_iterations = 1

    def __init__(self, query, fmt):
        self._elasticsearch_result = None
        super().__init__(query, fmt)

    def planner_steps(self):
        query = self._query.copy()
        query['name'] = self._address_data.street_names[0]

        if self._numerical_door_number:
            query['number'] = self._numerical_door_number

        self._elasticsearch_result = yield (data.search_streets, query)

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
                address_hit[N.FULL_NAME] = self._address_full_name(street)

            if (N.LOCATION_LAT in fields or N.LOCATION_LON in fields) and \
               self._numerical_door_number:
                loc = geometry.street_number_location(
                    street, self._numerical_door_number)

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
        self._intersection_hits = None

        super().__init__(query, fmt)

    def _build_intersections_query(self, street_1_ids, street_2_ids,
                                   locations, tolerance_m, ignore_max=False):
        query = self._query.copy()

        # El orden por id/nombre se hace localmente (para direcciones de tipo
        # intersection y between)
        query.pop('order', None)
        query['ids'] = (list(street_1_ids), list(street_2_ids))

        if ignore_max:
            query['max'] = constants.MAX_RESULT_LEN
            query['offset'] = 0

        if locations:
            geoms = []

            for loc in locations:
                geoms.append(geometry.build_circle_geometry(loc, tolerance_m))

            query['geo_shape_geoms'] = geoms

        return data.search_intersections, query

    def _build_street_query(self, street, add_number=False):
        query = self._query.copy()

        query['name'] = street
        if add_number and self._numerical_door_number:
            query['number'] = self._numerical_door_number
        query['max'] = constants.MAX_RESULT_LEN
        query['offset'] = 0

        return data.search_streets, query

    def _read_street_1_results(self, result):
        # Recolectar resultados de la primera calle
        street_1_ids = set()
        street_1_locations = {}

        # Si tenemos altura, comprobar que podemos calcular la ubicación
        # geográfica de cada altura por cada resultado de la calle 1.
        # Ignorar los resultados donde la ubicación no se puede calcular.
        if self._numerical_door_number:
            for street in result.hits:
                loc = geometry.street_number_location(
                    street, self._numerical_door_number)

                if loc[N.LAT] and loc[N.LON]:
                    street_1_ids.add(street[N.ID])
                    street_1_locations[street[N.ID]] = loc
        else:
            # No tenemos altura: la dirección es "Calle 1 y Calle 2".
            # No necesitamos calcular ninguna posición sobre la calle 1,
            # porque se usa la posición de la intersección de las dos
            # calles, que ya está pre-calculada.
            street_1_ids = {hit[N.ID] for hit in result.hits}

        return street_1_ids, street_1_locations

    def planner_steps(self):
        # Buscar la primera calle, incluyendo la altura si está presente
        result = yield self._build_street_query(
            self._address_data.street_names[0], True)

        if result:
            street_1_ids, street_1_locations = self._read_street_1_results(
                result)

            if not street_1_ids:
                # Ninguno de los resultados pudo ser utilizado para
                # calcular la ubicación, o no se encontraron resultados.
                # Devolver 0 resultados de intersección.
                return
        else:
            return

        result = yield self._build_street_query(
            self._address_data.street_names[1])

        if result:
            # Resultados de la segunda calle
            street_2_ids = {hit[N.ID] for hit in result.hits}
        else:
            return

        # Buscar intersecciones que tengan nuestras dos calles en cualquier
        # orden ("Calle 1 y Calle 2" o "Calle 2 y Calle 1"). Si tenemos altura,
        # comprobar que las intersecciones no estén a mas de X metros de cada
        # ubicación sobre la calle 1 que calculamos anteriormente.
        result = yield self._build_intersections_query(
            street_1_ids,
            street_2_ids,
            street_1_locations.values(),
            constants.ISCT_DOOR_NUM_TOLERANCE_M
        )

        self._intersections_result = result

        # Iterar sobre los resultados, fijándose si cada intersección tiene la
        # calle 1 del lado A o B. Si la calle 1 está del lado B, invertir la
        # intersección. Se requiere que los datos devueltos al usuario tengan
        # el mismo orden en el que fueron recibidos.
        intersections = []
        for intersection in self._intersections_result.hits:
            id_a = intersection[N.STREET_A][N.ID]
            id_b = intersection[N.STREET_B][N.ID]

            if id_a in street_1_ids and id_b in street_2_ids:
                street_1 = intersection[N.STREET_A]
                street_2 = intersection[N.STREET_B]
            elif id_a in street_2_ids and id_b in street_1_ids:
                street_1 = intersection[N.STREET_B]
                street_2 = intersection[N.STREET_A]
            else:
                raise RuntimeError(
                    'Unknown street IDs for intersection {} - {}'.format(id_a,
                                                                         id_b))

            if street_1[N.ID] in street_1_locations:
                # Como tenemos altura, usamos la posición sobre la calle 1 en
                # lugar de la posición de la intersección.
                geom = street_1_locations[street_1[N.ID]]
            else:
                geom = geometry.geojson_point_to_location(intersection[N.GEOM])

            intersections.append((street_1, street_2, geom))

        self._intersection_hits = self._build_intersection_hits(intersections)

    def _apply_sort(self, hits):
        order = self._query.get('order')
        if not order:
            return

        # Ordenar resultados utilizando la primera calle
        if order == N.ID:
            hits.sort(key=lambda hit: hit[N.STREET][N.ID])
        elif order == N.NAME:
            hits.sort(key=lambda hit: hit[N.STREET][N.NAME])
        else:
            raise ValueError('Invalid sort field')

    def _build_intersection_hits(self, intersections):
        intersection_hits = []
        fields = self._format[N.FIELDS]

        for street_1, street_2, loc in intersections:
            address_hit = self._build_base_address_hit(street_1.get(N.STATE),
                                                       street_1.get(N.DEPT))

            address_hit[N.STREET] = self._build_street_entity(street_1)
            address_hit[N.STREET_X1] = self._build_street_entity(street_2)
            address_hit[N.STREET_X2] = self._build_street_entity()
            address_hit[N.LOCATION] = loc

            if N.FULL_NAME in fields:
                address_hit[N.FULL_NAME] = self._address_full_name(street_1,
                                                                   street_2)

            intersection_hits.append(address_hit)

        self._apply_sort(intersection_hits)
        return intersection_hits

    def get_query_result(self):
        if not self._intersection_hits:
            return QueryResult.empty()

        return QueryResult.from_entity_list(self._intersection_hits,
                                            self._intersections_result.total,
                                            self._intersections_result.offset)


class AddressBtwnQueryPlanner(AddressIsctQueryPlanner):
    required_iterations = 4

    class BetweenEntry:
        def __init__(self, street_1):
            self.street_1 = street_1
            self.street_2 = None
            self.intersection_2 = None
            self.street_3 = None
            self.intersection_3 = None
            self.loc = None

        def valid(self):
            if not all((self.street_1, self.street_2, self.street_3)):
                return False

            location_a = geometry.geojson_point_to_location(
                self.intersection_2[N.GEOM])

            location_b = geometry.geojson_point_to_location(
                self.intersection_3[N.GEOM])

            distance = geometry.approximate_distance_meters(location_a,
                                                            location_b)

            return distance < constants.BTWN_DISTANCE_TOLERANCE_M

        def location(self):
            if self.loc:
                return self.loc

            return geometry.geojson_points_centroid(
                self.intersection_2[N.GEOM],
                self.intersection_3[N.GEOM]
            )

    def __init__(self, query, fmt):
        self._between_hits = None
        super().__init__(query, fmt)

    def _process_intersections(self, intersections, street_1_ids, street_2_ids,
                               street_3_ids, street_1_locations):
        between_entries = {}
        street_2_3_ids = street_2_ids | street_3_ids

        for intersection in intersections:
            id_a = intersection[N.STREET_A][N.ID]
            id_b = intersection[N.STREET_B][N.ID]

            if id_a in street_1_ids and id_b in street_2_3_ids:
                street_1 = intersection[N.STREET_A]
                street_other = intersection[N.STREET_B]
            elif id_a in street_2_3_ids and id_b in street_1_ids:
                street_1 = intersection[N.STREET_B]
                street_other = intersection[N.STREET_A]
            else:
                raise RuntimeError(
                    'Unknown street IDs for intersection {} - {}'.format(id_a,
                                                                         id_b))

            if street_1[N.ID] in between_entries:
                entry = between_entries[street_1[N.ID]]
            else:
                entry = AddressBtwnQueryPlanner.BetweenEntry(street_1)
                if self._numerical_door_number:
                    entry.loc = street_1_locations[street_1[N.ID]]

                between_entries[street_1[N.ID]] = entry

            if street_other[N.ID] in street_2_ids:
                entry.street_2 = street_other
                entry.intersection_2 = intersection
            elif street_other[N.ID] in street_3_ids:
                entry.street_3 = street_other
                entry.intersection_3 = intersection
            else:
                raise RuntimeError('Unknown street ID: {}'.format(
                    street_other[N.ID]))

        return between_entries

    def planner_steps(self):
        # Buscar la primera calle, incluyendo la altura si está presente
        result = yield self._build_street_query(
            self._address_data.street_names[0], True)

        if result:
            street_1_ids, street_1_locations = self._read_street_1_results(
                result)

            if not street_1_ids:
                # Ninguno de los resultados pudo ser utilizado para
                # calcular la ubicación, o no se encontraron resultados.
                # Devolver 0 resultados de intersección.
                return
        else:
            return

        result = yield self._build_street_query(
            self._address_data.street_names[1])

        if result:
            # Resultados de la segunda calle
            street_2_ids = {hit[N.ID] for hit in result.hits}
        else:
            return

        result = yield self._build_street_query(
            self._address_data.street_names[2])

        if result:
            # Resultados de la tercera calle
            street_3_ids = {hit[N.ID] for hit in result.hits}
        else:
            return

        street_2_3_ids = street_2_ids | street_3_ids

        result = yield self._build_intersections_query(
            street_1_ids,
            street_2_3_ids,
            street_1_locations.values(),
            constants.BTWN_DOOR_NUM_TOLERANCE_M,
            ignore_max=True
        )

        entries = self._process_intersections(result.hits, street_1_ids,
                                              street_2_ids, street_3_ids,
                                              street_1_locations)

        # Las tres calles deben estar presentes, y las dos intersecciones
        # deben estar a menos de cierta distancia entre sí
        self._between_hits = self._build_between_hits(
            entry for entry in entries.values() if entry.valid()
        )

    def _build_between_hits(self, entries):
        between_hits = []
        fields = self._format[N.FIELDS]

        for entry in entries:
            address_hit = self._build_base_address_hit(
                entry.street_1.get(N.STATE), entry.street_1.get(N.DEPT))

            address_hit[N.STREET] = self._build_street_entity(entry.street_1)
            address_hit[N.STREET_X1] = self._build_street_entity(
                entry.street_2)
            address_hit[N.STREET_X2] = self._build_street_entity(
                entry.street_3)

            if N.LOCATION_LAT in fields or N.LOCATION_LON in fields:
                address_hit[N.LOCATION] = entry.location()

            if N.FULL_NAME in fields:
                address_hit[N.FULL_NAME] = self._address_full_name(
                    entry.street_1,
                    entry.street_2,
                    entry.street_3
                )

            between_hits.append(address_hit)

        self._apply_sort(between_hits)
        return between_hits

    def get_query_result(self):
        if not self._between_hits:
            return QueryResult.empty()

        # TODO: Revisar total y offset
        return QueryResult.from_entity_list(self._between_hits,
                                            len(self._between_hits),
                                            0)


def step_plan_iterator(iterator, previous_result):
    try:
        if previous_result is None:
            return next(iterator)

        return iterator.send(previous_result)
    except StopIteration:
        return None, None


def step_plans(es, previous_iteration):
    search_fn_queries = defaultdict(list)
    next_iteration = []

    # Cada QueryPlanner puede generar queries a ser ejecutadas con distintas
    # funciones de data.py. Agruparlas y ejecutarlas.
    for iterator, search_fn, query in previous_iteration:
        search_fn_queries[search_fn].append((query, iterator))

    for search_fn, planner_queries in search_fn_queries.items():
        results = search_fn(es, [
            planner_query[0]
            for planner_query in planner_queries
        ])

        for result, planner_query in zip(results, planner_queries):
            iterator = planner_query[1]

            # Cada query genera un resultado. Entregar el resultado al
            # QueryPlanner correspondiente, y si genera una nueva query,
            # insertarla en generated_queries y continuar iterando.
            search_fn, query = step_plan_iterator(iterator,
                                                  previous_result=result)
            if search_fn and query:
                next_iteration.append((iterator, search_fn, query))

    return next_iteration


def run_query_planners(es, query_planners, min_iterations):
    iterators = [planner.planner_steps() for planner in query_planners]
    iteration_data = []

    for iterator in iterators:
        # Generar datos de primera iteración
        search_fn, query = step_plan_iterator(iterator, previous_result=None)
        if search_fn and query:
            iteration_data.append((iterator, search_fn, query))

    for _ in range(min_iterations):
        # Tomar las queries anteriores, ejecutarlas, tomar los resultados y
        # entregárselos a los QueryPlanners para que generen nuevas queries.
        # Repetir cuantas veces sea necesario.
        iteration_data = step_plans(es, iteration_data)


def run_address_queries(es, queries, formats):
    query_planners = []
    min_iterations = 0

    for query, fmt in zip(queries, formats):
        address_type = query[N.ADDRESS].type if query[N.ADDRESS] else None

        if not address_type:
            query_planner = AddressNoneQueryPlanner(query, fmt)
        elif address_type == 'simple':
            query_planner = AddressSimpleQueryPlanner(query, fmt)
        elif address_type == 'intersection':
            query_planner = AddressIsctQueryPlanner(query, fmt)
        elif address_type == 'between':
            query_planner = AddressBtwnQueryPlanner(query, fmt)
        else:
            raise TypeError('Unknown address type')

        min_iterations = max(query_planner.required_iterations, min_iterations)
        query_planners.append(query_planner)

    run_query_planners(es, query_planners, min_iterations)

    return [
        query_planner.get_query_result()
        for query_planner in query_planners
    ]
