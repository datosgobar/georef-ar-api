from service import geometry
from .test_search_addresses_simple import SearchAddressesBaseTest

COMMON_ISCT = 'salta y santa fe'


class SearchAddressesIsctTest(SearchAddressesBaseTest):
    """Pruebas de búsqueda por dirección de tipo 'intersection'."""

    def setUp(self):
        self.endpoint = '/api/direcciones'
        self.entity = 'direcciones'
        super().setUp()

    def test_default_results_fields(self):
        """Las entidades devueltas deben tener los campos default."""
        self.assert_default_results_fields(COMMON_ISCT)

    def test_basic_fields_set(self):
        """Se debería poder especificar un conjunto de parámetros
        preseleccionados llamado 'basico'."""
        self.assert_basic_fields_set(COMMON_ISCT)

    def test_standard_fields_set(self):
        """Se debería poder especificar un conjunto de parámetros
        preseleccionados llamado 'estandar'."""
        self.assert_standard_fields_set(COMMON_ISCT)

    def test_complete_fields_set(self):
        """Se debería poder especificar un conjunto de parámetros
        preseleccionados llamado 'completo'."""
        self.assert_complete_fields_set(COMMON_ISCT)

    def test_basic_intersection_search(self):
        """La búsqueda de direcciones de tipo intersección debería devolver
        resultados con dos IDs cada uno, uno para cada calle, en el orden
        apropiado."""
        self.assert_intersection_search_ids_matches(
            'Av. San Juan y Piedras',
            [
                ('0200701001725', '0200701009350')
            ])

    def test_basic_intersection_search_reversed(self):
        """La búsqueda de direcciones de tipo intersección debería devolver
        resultados con dos IDs cada uno, uno para cada calle, en el orden
        apropiado."""
        self.assert_intersection_search_ids_matches(
            'Piedras y Av. San Juan',
            [
                ('0200701009350', '0200701001725')
            ])

    def test_intersection_search_keywords(self):
        """La búsqueda de direcciones de tipo intersección debería reconocer
        palabras clave como 'esquina', 'esq.', 'y', 'e', etc."""
        self.assert_intersection_search_ids_matches(
            'Larrea esquina Sarmiento',  # al 3500?
            [
                ('0202101007345', '0202101010480')
            ],
            params={
                'provincia': '02'
            }
        )

    def test_intersection_location_with_door_num(self):
        """Si se especifica una intersección con altura, se debería utilizar
        la posición de la altura sobre la primera calle como posición final."""
        resp_simple = self.get_response({'direccion': 'Cerro Beldevere 500'})
        loc_simple = resp_simple[0]['ubicacion']

        resp_isct = self.get_response({
            'direccion': 'Cerro Beldevere 500 y El Calafate'
        })
        loc_isct = resp_isct[0]['ubicacion']

        self.assertAlmostEqual(loc_simple['lat'], loc_isct['lat'])
        self.assertAlmostEqual(loc_simple['lon'], loc_isct['lon'])

    def test_intersection_location_no_door_num(self):
        """Si no se especifica una altura en una intersección, se debería
        utilizar la posición de la intersección como campo 'ubicacion'."""
        resp = self.get_response({
            'direccion': 'Maipú esquina Mendoza',
            'departamento': 'Rosario'
        })
        loc = resp[0]['ubicacion']

        self.assertAlmostEqual(loc['lat'], -32.9519930139424)
        self.assertAlmostEqual(loc['lon'], -60.636562374115)

    def test_intersection_nonexistent_door_num(self):
        """Si se especifica una intersección con altura, la posición de la
        altura sobre la primera calle debería estar a menos de
        ISCT_DOOR_NUM_TOLERANCE_M metros de la posición de la intersección.
        Solo se retornan casos donde se cumpla esa condidición."""
        resp_simple = self.get_response({
            'direccion': 'Cabrera 1000',
            'departamento': 'Rio Cuarto'
        })

        resp_isct = self.get_response({
            'direccion': 'Cabrera 1000 y Deán Funes',
            'departamento': 'Rio Cuarto'
        })

        self.assertTrue(resp_simple and not resp_isct)

    def test_intersection_position(self):
        """La posición de una intersección debería estar cerca a la posición de
        una altura sobre la primera calle cerca de la esquina."""
        resp_simple = self.get_response({
            'direccion': 'Dr. Adolfo Guemes al 550',
            'departamento': '66028'
        })

        resp_isct = self.get_response({
            'direccion': 'Dr. Adolfo esq. Rivadavia',
            'departamento': '66028'
        })

        loc_simple = resp_simple[0]['ubicacion']
        loc_isct = resp_isct[0]['ubicacion']

        self.assertLess(
            geometry.approximate_distance_meters(loc_simple, loc_isct),
            30  # metros
        )

    def test_invalid_intersection_a(self):
        """Una búsqueda de intersecciones con la primera calle inexistente
        debería traer 0 resultados."""
        self.assert_intersection_search_ids_matches('FoobarFoobar y Tucumán',
                                                    [])

    def test_invalid_intersection_b(self):
        """Una búsqueda de intersecciones con la segunda calle inexistente
        debería traer 0 resultados."""
        self.assert_intersection_search_ids_matches('Tucumán y FoobarFoobar',
                                                    [])

    def test_invalid_intersection_both(self):
        """Una búsqueda de intersecciones con ambas calles inexistentes debería
        traer 0 resultados."""
        self.assert_intersection_search_ids_matches('QuuzQuux y FoobarFoobar',
                                                    [])

    def assert_intersection_search_ids_matches(self, address, ids,
                                               params=None):
        if not params:
            params = {}

        params['direccion'] = address
        resp = self.get_response(params)
        resp_ids = []

        for address_hit in resp:
            resp_ids.append((address_hit['calle']['id'],
                             address_hit['calle_cruce_1']['id']))

        self.assertListEqual(sorted(ids), sorted(resp_ids))
