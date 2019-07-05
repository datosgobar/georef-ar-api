"""Módulo 'address' de georef-ar-api.

Contiene funciones y clases utilizadas para normalizar direcciones (recurso
/direcciones). Este módulo puede ser considerado una extensión del módulo
'normalizer', con funciones específicas para el procesamiento de direcciones.
"""

from abc import ABC, abstractmethod
from service import names as N
from service import data, constants, utils
from service.geometry import Point, street_block_number_location
from service.query_result import QueryResult


class AddressQueryPlanner(ABC):
    """Representa una búsqueda de una dirección de calle. Buscar una dirección
    involucra potencialmente más de una consulta a la capa de datos (data.py),
    utilizando distintos índices, dependiendo del tipo de dirección. Para poder
    ejecutar varias búsquedas de direcciones de distintos tipos a la vez, se
    utiliza la clase 'AddressQueryPlanner' y sus derivados para organizar el
    proceso de creación de búsquedas ElasticsearchSearch y la ejecución de las
    mismas.

    Attributes:
        _query (dict): Parámetros de la consulta.
        _format (dict): Formato de salida deseado de la consulta, incluyendo
            los campos que el usuario especificó. Se incluye este dato
            exclusivamente como una optimización: algunos campos son costosos
            de calcular y es conveniente saber si deben ser calculados o no. No
            se aplica nada relacionado a la presentación de los resultados de
            la búsqueda (ya que es responsabilidad del módulo formatter.py).
        _address_data (georef_ar_address.AddressData): Datos de la dirección
            recibida (componentes).

    """

    def __init__(self, query, fmt):
        """Inicializa un objeto de tipo 'AddressQueryPlanner'.

        Args:
            query (dict): Ver atributo '_query'.
            fmt (dict): Ver atributo '_format'.

        """
        self._query = query.copy()
        self._format = fmt
        self._address_data = self._query.pop(N.ADDRESS)
        self._locality = self._query.pop(N.LOCALITY, None)

        if self._address_data:
            self._numerical_door_number = \
                self._address_data.normalized_door_number_value()

    @abstractmethod
    def planner_steps(self):
        """Crea un iterador de ElasticsearchSearch, representando los pasos
        requeridos para completar la búsqueda de los datos la dirección.
        Distintas direcciones requieren distintas cantidades de pasos.

        Yields:
            ElasticsearchSearch: Búsqueda que debe ser ejecutada por el
                invocador de 'next()'.

        """
        raise NotImplementedError()

    @abstractmethod
    def get_query_result(self, params):
        """Retorna los resultados de la búsqueda de direcciones. Este método
        debe ser invocado luego de haber recorrido todo el iterador obtenido
        con 'planner_steps'.

        Args:
            params (dict): Parámetros recibidos que generaron la consulta.

        Returns:
            QueryResult: Resultados de la búsqueda de direcciones.

        """
        raise NotImplementedError()

    def _build_street_blocks_search(self, street, add_number=False,
                                    force_all=False):
        """Método de utilidad para crear búsquedas de tipo StreetBlocksSearch.
        Para buscar una calle, se consulta el índice de cuadras, en lugar del
        de calles. Esto se debe a que ambos índices representan los mismos
        datos (las calles de Argentina), pero el de cuadras contiene datos con
        mucha mayor granularidad: por cada cuadra de la calle, se tiene la
        altura inicial y final. Como cada cuadra es una recta (en lugar de
        varias) en la mayoría de los casos es trivial calcular la posición
        geográfica de una dirección sobre ellas.

        Args:
            street (str): Nombre de la calle a buscar.
            add_number (bool): Si es verdadero, agrega a la búsqueda un
                filtrado por altura, utilizando el atributo
                '_numerical_door_number'.
            force_all (bool): Si es verdadero, se ignoran los parámetros
                'size' y 'offset' de la consulta original, y se buscan todas
                las cuadras posibles.

        Returns:
            StreetBlocksSearch: Búsqueda de cuadras para ejecutar.

        """
        query = self._query.copy()

        query['name'] = street
        if add_number and self._numerical_door_number is not None:
            query['number'] = self._numerical_door_number

        if force_all:
            query['size'] = constants.MAX_RESULT_LEN
            query['offset'] = 0

        return data.StreetBlocksSearch(query)

    def _address_full_name(self, *streets):
        """Obtiene una representación canónica de una dirección, utilizando los
        nombres ya normalizados de las calles que la componen (y su altura).

        Por ejemplo, 'Sarmiento al 1443' se convierte a 'SARMIENTO 1443'.
        'Santa fe esq. Pampa' se convierte a 'SANTA FE (ESQUINA LA PAMPA)'.

        Args:
            streets (list): Lista de calles (documentos) representando cada
                calle de la dirección.

        Returns:
            str: Nombre completo canónico de la dirección.

        """
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
            template = '{street_1}{door_number} (ESQUINA {street_2})'
        elif self._address_data.type == 'between':
            template = \
                '{street_1}{door_number} (ENTRE {street_2} Y {street_3})'
        else:
            raise ValueError('Unknown address type')

        template += ', {dept}, {state}'
        return template.format(**fmt)

    def _build_base_address_hit(self, state=None, dept=None,
                                census_locality=None):
        """Construye la base de un resultado de búsqueda de direcciones.

        Args:
            state (dict): Valor a utilizar como provincia (id y nombre).
            dept (dict): Valor a utilizar como departamento (id y nomnbre).
            census_locality (dict): Valor a utilizar como localidad censal
                (id y nombre).

        Returns:
            dict: Resultado a ser completado con datos de calles, ubicación,
                etc.

        """
        address_hit = {}
        if state:
            address_hit[N.STATE] = state

        if dept:
            address_hit[N.DEPT] = dept

        if census_locality:
            address_hit[N.CENSUS_LOCALITY] = census_locality

        address_hit[N.DOOR_NUM] = {
            # Utilizar el valor numérico (int/float) como valor de altura
            N.VALUE: self._numerical_door_number,
            N.UNIT: self._address_data.door_number_unit
        }
        address_hit[N.FLOOR] = self._address_data.floor
        address_hit[N.LOCATION] = {
            N.LAT: None,
            N.LON: None
        }

        return address_hit

    def _build_street_entity(self, elasticsearch_street_hit=None):
        """Construye una sub-entidad calle para un resultado de dirección, a
        partir de un resultado de búsqueda de calles. Los resultados de
        direcciones poseen tres sub-entidades calles: 'calle', 'calle_cruce_1'
        y 'calle_cruce_2'.

        Args:
            elasticsearch_street_hit (dict): Resultado de una búsqueda de
                calles (documento).

        Returns:
            dict: Sub-entidad calle para resultados de direcciones.

        """
        if not elasticsearch_street_hit:
            elasticsearch_street_hit = {}

        street_entity = {
            key: elasticsearch_street_hit.get(key)
            for key in [N.ID, N.NAME, N.CATEGORY]
        }

        return street_entity

    def _expand_locality_search(self):
        """Prepara los datos necesarios para poder buscar direcciones por
        localidad. Recordar que:
        - localidad != localidad censal
        - Las localidades censales contienen varias localidades.
        - Las cuadras e intersecciones solo tienen asociados datos de
          localidades censales.
        - Las direcciones se contruyen buscando cuadras e interseciones.

        Es decir:

                  +------------------+
                  | localidad_censal |
                  +------------------+
                    ^              ^
                   /                \
                  /                  \
                 /                    \
                /                      \
               /                        \
         +-----------+         +---------------------+
         | localidad |         | cuadra/interseccion |
         +-----------+         +---------------------+

        El método realiza una búsqueda de localidades, luego toma el ID de la
        localidad censal de cada resultado, y los agrega al atributo
        _query['census_locality'], de forma tal que todas las búsquedas de
        cuadras o intersecciones se ejecuten filtrando por esas localidades
        censales. Esto nos permite 'filtrar' cuadras por localidad, aunque las
        mismas no tengan ese atributo.

        Yields:
            data.LocalitiesSearch: Búsqueda de localidades.

        Returns:
            bool: Verdadero si se encontraron localidades.

        """
        localities_query = {
            'size': constants.MAX_RESULT_LEN,
            'fields': [N.CENSUS_LOCALITY_ID],
            'exact': self._query.get('exact'),
            'state': self._query.get('state'),
            'department': self._query.get('department'),
            'census_locality': self._query.get('census_locality')
        }

        if isinstance(self._locality, list):
            localities_query['ids'] = self._locality
        else:
            localities_query['name'] = self._locality

        result = yield data.LocalitiesSearch(localities_query)

        if not result:
            return False

        ids = set()
        for hit in result.hits:
            ids.add(hit[N.CENSUS_LOCALITY][N.ID])

        # Combinar las localidades censales encontradas con el valor previo de
        # 'census_locality' en _query (si lo hay)
        prev_census_locality = self._query['census_locality'] or []
        if isinstance(prev_census_locality, list):
            # Buscar con lista de IDs
            self._query['census_locality'] = prev_census_locality + list(ids)
        else:
            # Buscar con tupla de (lista de IDs, nombre)
            self._query['census_locality'] = (list(ids), prev_census_locality)

        return True


class AddressNoneQueryPlanner(AddressQueryPlanner):
    """AddressQueryPlanner simbólico para direcciones inválidas. Se implementa
    esta clase para facilitar la implementación de la función
    'run_address_queries', con el objetivo de no tener que crear casos
    especiales para direcciones que no pudieron ser interpretadas.

    Ver documentación de la clase AddressQueryPlanner para más información.

    """

    def planner_steps(self):
        """Pasos requeridos (búsquedas) para direcciones inválidas. En el caso
        de 'AddressNoneQueryPlanner', la cantidad de pasos requeridos es cero.

        Yields:
            ElasticsearchSearch: Búsqueda a realizar.

        """
        return iter(())  # Iterador vacío

    def get_query_result(self, params):
        """Retorna los resultados de la búsqueda de direcciones. En el caso de
        'AddressNoneQueryPlanner', siempre se retornan resultados vacíos.

        Args:
            params (dict): Parámetros recibidos que generaron la consulta.

        Returns:
            QueryResult: Resultados de la búsqueda de direcciones.

        """
        return QueryResult.empty(params)


class AddressSimpleQueryPlanner(AddressQueryPlanner):
    """AddressQueryPlanner para direcciones de tipo 'simple'. Una dirección
    'simple' es del tipo '<calle 1> <altura>'.

    Ver documentación de la clase AddressQueryPlanner para más información.

    """

    def __init__(self, query, fmt):
        """Inicializa un objeto de tipo 'AddressSimpleQueryPlanner'.

        Args:
            query (dict): Ver atributo '_query'.
            fmt (dict): Ver atributo '_format'.

        """
        self._elasticsearch_result = None
        super().__init__(query, fmt)

    def planner_steps(self):
        """Crea un iterador de ElasticsearchSearch, representando los pasos
        requeridos para completar la búsqueda de los datos la dirección.

        Pasos requeridos:
            1) Expandir búsqueda de localidad, si la hay.
            2) Búsqueda de la calle principal.

        Yields:
            ElasticsearchSearch: Búsqueda que debe ser ejecutada por el
                invocador de 'next()'.

        """
        if self._locality:
            found = yield from self._expand_locality_search()
            if not found:
                return

        name = self._address_data.street_names[0]
        self._elasticsearch_result = yield self._build_street_blocks_search(
            name, add_number=True)

    def _build_address_hits(self):
        """Construye los resultados de la búsqueda de direcciones a partir
        del atributo '_elasticsearch_result' (lista de cuadras).

        Returns:
            list: Lista de resultados.

        """
        address_hits = []
        fields = self._format[N.FIELDS]

        for street_block in self._elasticsearch_result.hits:
            street = street_block[N.STREET]
            address_hit = self._build_base_address_hit(
                street.get(N.STATE), street.get(N.DEPT),
                street.get(N.CENSUS_LOCALITY))

            address_hit[N.STREET] = self._build_street_entity(street)
            address_hit[N.STREET_X1] = self._build_street_entity()
            address_hit[N.STREET_X2] = self._build_street_entity()
            address_hit[N.SOURCE] = street[N.SOURCE]

            if N.FULL_NAME in fields:
                address_hit[N.FULL_NAME] = self._address_full_name(street)

            if N.LOCATION_LAT in fields or N.LOCATION_LON in fields:
                point = street_block_number_location(
                    street_block[N.GEOM],
                    street_block[N.DOOR_NUM],
                    self._numerical_door_number,
                    approximate=True
                )

                address_hit[N.LOCATION] = point.to_json_location()

            address_hits.append(address_hit)

        return address_hits

    def get_query_result(self, params):
        """Retorna los resultados de la búsqueda de direcciones. Este método
        debe ser invocado luego de haber recorrido todo el iterador obtenido
        con 'planner_steps'.

        Args:
            params (dict): Parámetros recibidos que generaron la consulta.

        Returns:
            QueryResult: Resultados de la búsqueda de direcciones.

        """
        if not self._elasticsearch_result:
            return QueryResult.empty(params)

        address_hits = self._build_address_hits()
        return QueryResult.from_entity_list(address_hits,
                                            params,
                                            self._elasticsearch_result.total,
                                            self._elasticsearch_result.offset)


class AddressIsctQueryPlanner(AddressQueryPlanner):
    """AddressQueryPlanner para direcciones de tipo 'intersection'. Una
    dirección 'intersection' es del tipo '<calle 1> y <calle 2>'.

    Ver documentación de la clase AddressQueryPlanner para más información.

    """

    def __init__(self, query, fmt):
        """Inicializa un objeto de tipo 'AddressIsctQueryPlanner'.

        Args:
            query (dict): Ver atributo '_query'.
            fmt (dict): Ver atributo '_format'.

        """
        self._intersections_result = None
        self._intersection_hits = None

        super().__init__(query, fmt)

    def _build_intersections_search(self, street_1_ids, street_2_ids,
                                    points, tolerance_m, force_all=False):
        """Método de utilidad para construir objetos IntersectionsSearch, para
        buscar intersecciones de calles.

        Args:
            street_1_ids (list): Lista de IDs a utilizar como un lado de la
                intersección.
            street_2_ids (list): Lista de IDs a utilizar como el otro lado de
                la intersección.
            points (list): Lista de 'Point' a utilizar para filtrar por radios
                circulares. Solo se retornan intersecciones que caigan dentro
                de cualquier círculo de la lista.
            tolerance_m (float): Distancia en metros a utilizar como radio de
                los círculos.
            force_all (bool): Si es verdadero, se ignoran los parámetros
                'size' y 'offset' de la consulta original, y se buscan todas
                las intersecciones posibles.

        """
        query = self._query.copy()

        # El orden por id/nombre se hace localmente (para direcciones de tipo
        # intersection y between). Esto se debe a que los resultados para estos
        # tipos de direcciones son construidos a partir de más de una búsqueda
        # a Elasticsearch, por lo que ordenar los resultados se deber hacer al
        # final, una vez que todos los resultados están listos.
        query.pop('order', None)
        query['ids'] = (list(street_1_ids), list(street_2_ids))

        if force_all:
            query['size'] = constants.MAX_RESULT_LEN
            query['offset'] = 0

        if points:
            query['geo_shape_geoms'] = [
                point.to_geojson_circle(tolerance_m)
                for point in points
            ]

        return data.IntersectionsSearch(query)

    def _read_street_blocks_1_results(self, result):
        """Lee los resultados de la búsqueda de cuadras de la primera calle.
        Los resultados de la primera calle se manejan separadamente ya que
        potencialmente se necesite calcular la posición de la altura
        especificada sobre la misma.

        Args:
            result (ElasticsearchResult): Resultados de la búsqueda realizada
                para la calle 1.

        Returns:
            tuple: Tupla de (set, dict). El conjunto contiene los IDs de las
                calles encontradas, y el diccionario las posiciones de la
                altura '_numerical_door_number' sobre las mismas (si la
                consulta incluye una altura).

        """
        # Recolectar resultados de la primera calle
        street_1_ids = set()
        street_1_points = {}

        # Si tenemos altura, comprobar que podemos calcular la ubicación
        # geográfica de cada altura por cada resultado de la calle 1.
        # Ignorar los resultados donde la ubicación no se puede calcular.
        if self._numerical_door_number:
            for street_block in result.hits:
                street = street_block[N.STREET]

                point = street_block_number_location(
                    street_block[N.GEOM],
                    street_block[N.DOOR_NUM],
                    self._numerical_door_number
                )

                if point:
                    street_1_ids.add(street[N.ID])
                    street_1_points[street[N.ID]] = point
        else:
            # No tenemos altura: la dirección es "Calle 1 y Calle 2" o
            # "Calle 1 entre Calle 2 y Calle 3". No necesitamos calcular
            # ninguna posición sobre la calle 1, porque se usa la posición de
            # la/s intersección/es de las calles, que ya está/n
            # pre-calculada/s.
            street_1_ids = {hit[N.STREET][N.ID] for hit in result.hits}

        return street_1_ids, street_1_points

    def planner_steps(self):
        """Crea un iterador de ElasticsearchSearch, representando los pasos
        requeridos para completar la búsqueda de los datos la dirección.

        Pasos requeridos:
            1) Expandir búsqueda de localidad, si la hay.
            2) Búsqueda de la calle principal (calle 1).
            3) Búsqueda de la calle 2.
            4) Búsqueda de intersecciones entre las calles 1 y 2.

        Explicación: Primero, se buscan las calles 1 y 2, obteniendo todos los
        IDs de las mismas. Luego, se buscan intersecciones de calles que
        hagan referencia a los IDs obtenidos. Aunque es posible buscar
        intersecciones directamente por nombre, no se hace esto ya que sería
        difícil luego interpretar si la calle A de la intersección corresponde
        a la calle 1 y la B a la 2, o vice versa.

        Yields:
            ElasticsearchSearch: Búsqueda que debe ser ejecutada por el
                invocador de 'next()'.

        """
        if self._locality:
            found = yield from self._expand_locality_search()
            if not found:
                return

        # Buscar la primera calle, incluyendo la altura si está presente
        result = yield self._build_street_blocks_search(
            self._address_data.street_names[0],
            add_number=True,
            force_all=True
        )

        street_1_ids, street_1_points = self._read_street_blocks_1_results(
            result)

        if not street_1_ids:
            # Ninguno de los resultados pudo ser utilizado para
            # calcular la ubicación, o no se encontraron resultados.
            # Devolver 0 resultados de intersección.
            return

        result = yield self._build_street_blocks_search(
            self._address_data.street_names[1],
            force_all=True
        )

        # Resultados de la segunda calle
        street_2_ids = {hit[N.STREET][N.ID] for hit in result.hits}
        if not street_2_ids:
            return

        # Buscar intersecciones que tengan nuestras dos calles en cualquier
        # orden ("Calle 1 y Calle 2" o "Calle 2 y Calle 1"). Si tenemos altura,
        # comprobar que las intersecciones no estén a mas de X metros de cada
        # ubicación sobre la calle 1 que calculamos anteriormente.
        self._intersections_result = yield self._build_intersections_search(
            street_1_ids,
            street_2_ids,
            street_1_points.values(),
            constants.ISCT_DOOR_NUM_TOLERANCE_M
        )

        # Iterar sobre los resultados, fijándose si cada intersección tiene la
        # calle 1 del lado A o B. Si la calle 1 está del lado B, invertir la
        # intersección. Se requiere que los datos devueltos al usuario tengan
        # el mismo orden en el que fueron recibidos ("calle X y calle Y" no es
        # lo mismo que "calle Y y calle X").
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

            if street_1[N.ID] in street_1_points:
                # Como tenemos altura, usamos la posición sobre la calle 1 en
                # lugar de la posición de la intersección.
                point = street_1_points[street_1[N.ID]]
            else:
                point = Point.from_geojson_point(intersection[N.GEOM])

            intersections.append((street_1, street_2, point))

        self._intersection_hits = self._build_intersection_hits(intersections)

    def _apply_sort(self, hits):
        """Ordena los resultados de direcciones. El ordenamiento se hace
        localmente ya que en 'planner_steps' se modifican los lados de las
        intersecciones. El ordenamiento se realiza exclusivamente sobre la
        calle 1.

        Args:
            hits (list): Lista de resultados de búsqueda de direcciones.

        """
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
        """Construye los resultados de la búsqueda de direcciones a partir de
        los datos generados en 'planner_steps'.

        Args:
            intersections (list): Lista de tuplas, cada una conteniendo la
                calle 1, calle 2 y el 'Point' de intersección entre las dos.

        Returns:
            list: Lista de resultados de la búsqueda de direcciones.

        """
        intersection_hits = []
        fields = self._format[N.FIELDS]

        for street_1, street_2, point in intersections:
            address_hit = self._build_base_address_hit(
                street_1.get(N.STATE), street_1.get(N.DEPT),
                street_1.get(N.CENSUS_LOCALITY))

            address_hit[N.STREET] = self._build_street_entity(street_1)
            address_hit[N.STREET_X1] = self._build_street_entity(street_2)
            address_hit[N.STREET_X2] = self._build_street_entity()
            address_hit[N.LOCATION] = point.to_json_location()
            address_hit[N.SOURCE] = street_1[N.SOURCE]

            if N.FULL_NAME in fields:
                address_hit[N.FULL_NAME] = self._address_full_name(street_1,
                                                                   street_2)

            intersection_hits.append(address_hit)

        self._apply_sort(intersection_hits)
        return intersection_hits

    def get_query_result(self, params):
        """Retorna los resultados de la búsqueda de direcciones. Este método
        debe ser invocado luego de haber recorrido todo el iterador obtenido
        con 'planner_steps'.

        Se utiliza el 'total' y 'offset' de la búsqueda #3 (intersecciones)
        como metadatos de los resultados.

        Args:
            params (dict): Parámetros recibidos que generaron la consulta.

        Returns:
            QueryResult: Resultados de la búsqueda de direcciones.

        """
        if not self._intersection_hits:
            return QueryResult.empty(params)

        return QueryResult.from_entity_list(self._intersection_hits,
                                            params,
                                            self._intersections_result.total,
                                            self._intersections_result.offset)


class AddressBtwnQueryPlanner(AddressIsctQueryPlanner):
    """AddressQueryPlanner para direcciones de tipo 'between'. Una dirección
    'between' es del tipo '<calle 1> entre <calle 2> y <calle 3>'.

    Ver documentación de la clase AddressQueryPlanner para más información.

    """

    class BetweenEntry:
        """Reprsenta una dirección 'between' potencial durante la búsqueda de
        direcciones.

        Attributes:
            street_1 (dict): Calle 1 (documento).
            street_1_point (Point): Punto sobre la calle 1 (calculado
                utilizando la altura '_numerical_door_number').
            street_2 (dict): Calle 2 (documento).
            street_2_point (Point): Punto de intersección entre la calle 1 y la
                calle 2.
            street_3 (dict): Calle 3 (documento).
            street_3_point (Point): Punto de intersección entre la calle 1 y la
                calle 3.

        """

        def __init__(self, street_1):
            """Inicializa un objeto de tipo 'BetweenEntry'.

            Args:
                street_1 (dict): Ver atributo 'street_1'.

            """
            self.street_1 = street_1
            self.street_1_point = None

            self.street_2 = None
            self.street_2_point = None

            self.street_3 = None
            self.street_3_point = None

        def valid(self):
            """Comprueba que el resultado potencial 'between' sea válido.

            Returns:
                bool: Verdadero si las tres calles están presentes y las
                    calles 2 y 3 no están a mas de cierta distancia entre sí.

            """
            if not all((self.street_1, self.street_2, self.street_3)):
                return False

            distance = self.street_2_point.approximate_distance_meters(
                self.street_3_point)

            return distance < constants.BTWN_DISTANCE_TOLERANCE_M

        def point(self):
            """Devuelve el punto 'Point' que representa la dirección
            encontrada.

            Returns:
                Point: Punto representativo de la dirección. Si calculó la
                    posición de la altura sobre la calle 1, se utiliza ese
                    dato. Si no, se utiliza el promedio de los puntos de las
                    dos intersecciones encontradas (calle 1-2, calle 1-3).

            """
            if self.street_1_point:
                return self.street_1_point

            return self.street_2_point.midpoint(self.street_3_point)

    def __init__(self, query, fmt):
        """Inicializa un objeto de tipo 'AddressBtwnQueryPlanner'.

        Args:
            query (dict): Ver atributo '_query'.
            fmt (dict): Ver atributo '_format'.

        """
        self._between_hits = None
        super().__init__(query, fmt)

    def _process_intersections(self, intersections, street_1_ids, street_2_ids,
                               street_3_ids, street_1_points):
        """Procesa los resultados de las tres búsquedas realizadas en
        'planner_steps', para generar los 'BetweenEntry' que representan
        resultados potenciales a la búsqueda de direcciones.

        Args:
            intersections (list): Lista de intersecciones encontradas
                (documentos).
            street_1_ids (set): Conjunto de IDs de resultados para la calle 1.
            street_2_ids (set): Conjunto de IDs de resultados para la calle 2.
            street_3_ids (set): Conjunto de IDs de resultados para la calle 3.
            street_1_points (dict): Posición calculada utilizando la altura
                sobre cada resultado de la calle 1.

        Returns:
            list: Lista de 'BetweenEntry', cada una representando un resultado
                potencial.

        """
        between_entries = {}
        street_2_3_ids = street_2_ids | street_3_ids

        # Recorrer cada intersección. Las intersecciones pueden ser entre las
        # calles 1 y 2, o 1 y 3. Es necesario distinguir entre las dos
        # opciones.
        for intersection in intersections:
            id_a = intersection[N.STREET_A][N.ID]
            id_b = intersection[N.STREET_B][N.ID]

            # Comprobar que la intersección es entre las calles 1 y 2, o 1 y 3
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

            # Si la calle 1 no está en between_entries, construir un nuevo
            # BetweenEntry.
            if street_1[N.ID] in between_entries:
                entry = between_entries[street_1[N.ID]]
            else:
                entry = AddressBtwnQueryPlanner.BetweenEntry(street_1)
                if self._numerical_door_number:
                    entry.street_1_point = street_1_points[street_1[N.ID]]

                between_entries[street_1[N.ID]] = entry

            point = Point.from_geojson_point(intersection[N.GEOM])

            # Tomar nuestro BetweenEntry asociado a la calle 1, y asignarle su
            # calle 2 o 3. Un BetweenEntry está completo cuando tiene las tres
            # calles asignadas (1, 2 y 3).
            if street_other[N.ID] in street_2_ids:
                entry.street_2 = street_other
                entry.street_2_point = point
            elif street_other[N.ID] in street_3_ids:
                entry.street_3 = street_other
                entry.street_3_point = point
            else:
                raise RuntimeError('Unknown street ID: {}'.format(
                    street_other[N.ID]))

        # Luego de iterar, algunos 'BetweenEntry' van a contener las tres
        # calles necesarias, y otros no.
        return between_entries.values()

    def planner_steps(self):
        """Crea un iterador de ElasticsearchSearch, representando los pasos
        requeridos para completar la búsqueda de los datos la dirección.

        Pasos requeridos:
            1) Expandir búsqueda de localidad, si la hay.
            2) Búsqueda de la calle principal (calle 1).
            3) Búsqueda de la calle 2.
            4) Búsqueda de la calle 3.
            5) Búsqueda de intersecciones entre las calles 1 y 2, y las calles
               1 y 3 (en simultáneo).

        Explicación: Primero, se buscan las calles 1, 2 y 3, obteniendo todos
        los IDs de las mismas. Luego, se buscan intersecciones de calles que
        hagan referencia a los IDs obtenidos: intersecciones entre las calles
        1 y 2, y entre las 1 y 3. Finalmente, se itera sobre cada intersección
        comprobando qué calles contiene, y se construyen los resultados
        finales.

        Yields:
            ElasticsearchSearch: Búsqueda que debe ser ejecutada por el
                invocador de 'next()'.

        """
        if self._locality:
            found = yield from self._expand_locality_search()
            if not found:
                return

        # Buscar la primera calle, incluyendo la altura si está presente
        result = yield self._build_street_blocks_search(
            self._address_data.street_names[0],
            add_number=True,
            force_all=True
        )

        street_1_ids, street_1_points = self._read_street_blocks_1_results(
            result)

        if not street_1_ids:
            # Ninguno de los resultados pudo ser utilizado para
            # calcular la ubicación, o no se encontraron resultados.
            # Devolver 0 resultados de intersección.
            return

        result = yield self._build_street_blocks_search(
            self._address_data.street_names[1],
            force_all=True
        )

        # Resultados de la segunda calle
        street_2_ids = {hit[N.STREET][N.ID] for hit in result.hits}
        if not street_2_ids:
            return

        result = yield self._build_street_blocks_search(
            self._address_data.street_names[2],
            force_all=True
        )

        # Resultados de la tercera calle
        street_3_ids = {hit[N.STREET][N.ID] for hit in result.hits}
        if not street_3_ids:
            return

        street_2_3_ids = street_2_ids | street_3_ids

        result = yield self._build_intersections_search(
            street_1_ids,
            street_2_3_ids,
            street_1_points.values(),
            constants.BTWN_DOOR_NUM_TOLERANCE_M,
            force_all=True
        )

        entries = self._process_intersections(result.hits, street_1_ids,
                                              street_2_ids, street_3_ids,
                                              street_1_points)

        # Las tres calles deben estar presentes, y las dos intersecciones
        # deben estar a menos de cierta distancia entre sí
        self._between_hits = self._build_between_hits(
            entry for entry in entries if entry.valid()
        )

    def _build_between_hits(self, entries):
        """Construye los resultados de la búsqueda de direcciones, dada una
        lista de 'BetweenEntry' válidas.

        Args:
            entries (list): Lista de 'BetweenEntry'.

        Returns:
            list: Resultados de la búsqueda de direcciones.

        """
        between_hits = []
        fields = self._format[N.FIELDS]

        for entry in entries:
            address_hit = self._build_base_address_hit(
                entry.street_1.get(N.STATE), entry.street_1.get(N.DEPT),
                entry.street_1.get(N.CENSUS_LOCALITY))

            address_hit[N.STREET] = self._build_street_entity(entry.street_1)
            address_hit[N.STREET_X1] = self._build_street_entity(
                entry.street_2)
            address_hit[N.STREET_X2] = self._build_street_entity(
                entry.street_3)
            address_hit[N.SOURCE] = entry.street_1[N.SOURCE]

            if N.LOCATION_LAT in fields or N.LOCATION_LON in fields:
                point = entry.point()
                address_hit[N.LOCATION] = point.to_json_location()

            if N.FULL_NAME in fields:
                address_hit[N.FULL_NAME] = self._address_full_name(
                    entry.street_1,
                    entry.street_2,
                    entry.street_3
                )

            between_hits.append(address_hit)

        self._apply_sort(between_hits)
        return between_hits

    def get_query_result(self, params):
        """Retorna los resultados de la búsqueda de direcciones. Este método
        debe ser invocado luego de haber recorrido todo el iterador obtenido
        con 'planner_steps'.

        Se utiliza la longitud de los resultados encontrados como 'total', y
        0 como 'offset'. Esto se debe a que ninguna de las búsquedas ejecutadas
        representa correctamente el total de resultados posibles que existen (
        ya que gran parte del procesamiento se hace localmente, combinando
        resultados de las mismas).

        Args:
            params (dict): Parámetros recibidos que generaron la consulta.

        Returns:
            QueryResult: Resultados de la búsqueda de direcciones.

        """
        if not self._between_hits:
            return QueryResult.empty(params)

        # TODO: Revisar total y offset
        return QueryResult.from_entity_list(self._between_hits,
                                            params,
                                            len(self._between_hits),
                                            0)


def _run_query_planners(es, query_planners):
    """Ejecuta las búsquedas requeridas por un conjunto de
    'AddressQueryPlanner'.

    Para lograr esto, se utiliza el método 'planner_steps' de cada
    'AddressQueryPlanner' para obtener un iterador de 'ElasticsearchSearch'. A
    cada iterador se le pide la primera búsqueda a ejecutar utilizando
    'next()'. Luego, se ejecutan todas las búsquedas a la vez utilizando
    'run_searches', y se entregan los resultados a los iteradores. El proceso
    se repite hasta que todos los iteradores no tengan más busquedas a
    realizar. De esta forma, se logra ejecutar varias búsquedas de direcciones
    de distintos tipos, minimizando la cantidad de consultas hechas a
    Elasticsearch.

    Args:
        es (Elasticsearch): Conexión a Elasticsearch.
        query_planners (list): Lista de 'AddressQueryPlanner' o derivados.

    """
    iterators = [planner.planner_steps() for planner in query_planners]
    iteration_data = []

    for iterator in iterators:
        # Generar datos de primera iteración
        search = utils.step_iterator(iterator)
        if search:
            iteration_data.append((iterator, search))

    while iteration_data:
        # Tomar las búsquedas anteriores, ejecutarlas, tomar los resultados y
        # entregárselos a los QueryPlanners para que generen nuevas búsquedas
        # (si las necesitan). Repetir cuantas veces sea necesario.

        searches = [search for _, search in iteration_data]
        data.ElasticsearchSearch.run_searches(es, searches)

        iterators = (iterator for iterator, _ in iteration_data)
        iteration_data = []

        for iterator, prev_search in zip(iterators, searches):
            search = utils.step_iterator(iterator, prev_search.result)
            if search:
                iteration_data.append((iterator, search))


def run_address_queries(es, params_list, queries, formats):
    """Punto de entrada del módulo 'address.py'. Toma una lista de consultas de
    direcciones y las ejecuta, devolviendo los resultados QueryResult.

    Args:
        es (Elasticsearch): Conexión a Elasticsearch.
        params_list (list): Lista de ParametersParseResult, cada uno
            conteniendo los parámetros de una consulta al recurso de
            direcciones de la API.
        queries (list): Lista de parámetros de búsqueda en forma de
            diccionarios de parámetros (extraídos de params_list).
        formats (list): Lista de parámetros de formato de cada consulta, en
            forma de diccionario (extraídos de params_list).

    Returns:
        list: Lista de QueryResult, una por cada búsqueda.

    """
    query_planners = []

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

        query_planners.append(query_planner)

    _run_query_planners(es, query_planners)

    return [
        query_planner.get_query_result(params.received_values())
        for query_planner, params in zip(query_planners, params_list)
    ]
