from service.geometry import Point
from .test_search_addresses_simple import SearchAddressesBaseTest

COMMON_BTWN = 'parana entre santa fe y alvear'


class SearchAddressesBtwnTest(SearchAddressesBaseTest):
    """Pruebas de búsqueda por dirección de tipo 'between'."""

    def setUp(self):
        self.endpoint = '/api/direcciones'
        self.entity = 'direcciones'
        super().setUp()

    def test_basic_between_search(self):
        """Buscar una dirección de tipo 'between' debería devolver
        tres calles con sus IDs respectivos, en el orden apropiado."""
        self.assert_between_search_ids_matches(
            'Espejo entre Lamadrid y French',
            [
                ('5002802004425', '5002802004460', '5002802003795')
            ]
        )

    def test_basic_between_search_reversed(self):
        """Buscar una dirección de tipo 'between' debería devolver
        tres calles con sus IDs respectivos, en el orden apropiado.
        Las calles 2 y 3 pueden ser intercambiadas"""
        self.assert_between_search_ids_matches(
            'Espejo entre French y Lamadrid',
            [
                ('5002802004425', '5002802003795', '5002802004460')
            ]
        )

    def test_between_location_with_door_num(self):
        """Si se especifica una dirección de tipo 'between' con altura, se
        debería utilizar la posición de la altura sobre la primera calle como
        posición final."""
        resp_simple = self.get_response({
            'direccion': 'Miller 3550',
            'departamento': 'capital',
            'provincia': 'Córdoba'
        })
        loc_simple = resp_simple[0]['ubicacion']

        resp_btwn = self.get_response({
            'direccion': 'Miller nro. 3550 e/Niceto Vega y Villegas',
            'departamento': 'capital',
            'provincia': 'Córdoba'
        })
        loc_btwn = resp_btwn[0]['ubicacion']

        self.assertAlmostEqual(loc_simple['lat'], loc_btwn['lat'])
        self.assertAlmostEqual(loc_simple['lon'], loc_btwn['lon'])

    def test_between_location_no_door_num(self):
        """Si no se especifica una altura en una una dirección de tipo
        'between', el resultado final debería tener una posición calculada
        a partir del promedio de la posición de las dos intersecciones."""
        resp_btwn = self.get_response({
            'direccion': 'Mar del Plata entre Diaz y 12 de Octubre',
            'departamento': 'Río Hondo'
        })
        point_btwn = Point.from_json_location(resp_btwn[0]['ubicacion'])

        resp_isct_1 = self.get_response({
            'direccion': 'Mar del Plata esquina Diaz',
            'departamento': 'Río Hondo'
        })
        point_isct_1 = Point.from_json_location(resp_isct_1[0]['ubicacion'])

        resp_isct_2 = self.get_response({
            'direccion': 'Mar del Plata esq. 12 de Octubre',
            'departamento': 'Río Hondo'
        })
        point_isct_2 = Point.from_json_location(resp_isct_2[0]['ubicacion'])

        midpoint = point_isct_1.midpoint(point_isct_2)

        distance = point_btwn.approximate_distance_meters(midpoint)
        self.assertAlmostEqual(distance, 0)

    def test_between_nonexistent_door_num(self):
        """Si se especifica una dirección de tipo 'between' con altura,
        la posición de la altura sobre la primera calle debería estar a menos
        de BTWN_DOOR_NUM_TOLERANCE_M metros de la posición del las dos
        intersecciones. Solo se retornan casos donde se cumpla esa
        condidición."""
        resp_simple = self.get_response({
            'direccion': 'Villegas 500',
            'departamento': 'Capital',
            'provincia': 'La Pampa'
        })

        resp_btwn = self.get_response({
            'direccion': 'Villegas 500 entre Don Bosco y Quintana',
            'departamento': 'Capital',
            'provincia': 'La Pampa'
        })

        self.assertTrue(resp_simple and not resp_btwn)

    def test_streets_distance(self):
        """Si se especifica una dirección de tipo 'between' con las calles
        2 y 3 a más de cierta distancia, no debe ser considerada una dirección
        válida."""

        # Belgrano y Pringles están a una cuadra de distancia
        resp_btwn_1 = self.get_response({
            'direccion': 'Falucho entre Belgrano y Pringles',
            'departamento': 'Juan Martín de Pueyrredón'
        })

        # Ayacucho y Pringles están a dos cuadras de distancia
        resp_btwn_2 = self.get_response({
            'direccion': 'Falucho entre Ayacucho y Pringles',
            'departamento': 'Juan Martín de Pueyrredón'
        })

        self.assertTrue(resp_btwn_1 and not resp_btwn_2)

    def test_basic_fields_set(self):
        """Se debería poder especificar un conjunto de parámetros
        preseleccionados llamado 'basico'."""
        self.assert_basic_fields_set(COMMON_BTWN)

    def test_standard_fields_set(self):
        """Se debería poder especificar un conjunto de parámetros
        preseleccionados llamado 'estandar'."""
        self.assert_standard_fields_set(COMMON_BTWN)

    def test_complete_fields_set(self):
        """Se debería poder especificar un conjunto de parámetros
        preseleccionados llamado 'completo'."""
        self.assert_complete_fields_set(COMMON_BTWN)

    def test_invalid_between_a(self):
        """Una búsqueda de direcciones 'between' con la primera calle
        inexistente debería traer 0 resultados."""
        self.assert_between_search_ids_matches(
            'FoobarFoobar entre Santa Fe y Alvear',
            []
        )

    def test_invalid_between_b(self):
        """Una búsqueda de direcciones 'between' con la segunda calle
        inexistente debería traer 0 resultados."""
        self.assert_between_search_ids_matches(
            'Paraná entre FoobarFoobar y Alvear',
            []
        )

    def test_invalid_between_c(self):
        """Una búsqueda de direcciones 'between' con la tercera calle
        inexistente debería traer 0 resultados."""
        self.assert_between_search_ids_matches(
            'Paraná entre Santa Fe y FoobarFoobar',
            []
        )

    def test_invalid_between_both(self):
        """Una búsqueda de direcciones 'between' con todas calles inexistentes
        debería traer 0 resultados."""
        self.assert_between_search_ids_matches(
            'Foo entre QuuzQuux y FoobarFoobar',
            []
        )

    def assert_between_search_ids_matches(self, address, ids, params=None):
        if not params:
            params = {}

        params['direccion'] = address
        resp = self.get_response(params)
        resp_ids = []

        for address_hit in resp:
            resp_ids.append((address_hit['calle']['id'],
                             address_hit['calle_cruce_1']['id'],
                             address_hit['calle_cruce_2']['id']))

        self.assertListEqual(sorted(ids), sorted(resp_ids))
