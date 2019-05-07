from service.geometry import Point
from . import asciifold
from .test_search_addresses_simple import SearchAddressesBaseTest

COMMON_ISCT = 'salta y santa fe'


class SearchAddressesIsctTest(SearchAddressesBaseTest):
    """Pruebas de búsqueda por dirección de tipo 'intersection'."""

    def setUp(self):
        self.endpoint = '/api/direcciones'
        self.entity = 'direcciones'
        super().setUp()

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
        resp_simple = self.get_response({'direccion': 'Cerro Beldevere 501'})
        loc_simple = resp_simple[0]['ubicacion']

        resp_isct = self.get_response({
            'direccion': 'Cerro Beldevere 501 y El Calafate'
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

        point_isct = Point.from_json_location(loc)
        point_target = Point(-60.636548, -32.952020)
        error_m = point_isct.approximate_distance_meters(point_target)
        self.assertTrue(error_m < 15, error_m)

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
            'direccion': 'Dr. Adolfo Guemes al 600',
            'departamento': '66028'
        })

        resp_isct = self.get_response({
            'direccion': 'Dr. Adolfo esq. Rivadavia',
            'departamento': '66028'
        })

        point_simple = Point.from_json_location(resp_simple[0]['ubicacion'])
        point_isct = Point.from_json_location(resp_isct[0]['ubicacion'])

        self.assertLess(
            point_simple.approximate_distance_meters(point_isct),
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

    def test_name_ordering(self):
        """Los resultados deben poder ser ordenados por nombre."""
        resp = self.get_response({
            'direccion': 'santa fe y salta',
            'orden': 'nombre',
            'max': 1000
        })

        ordered = [r['calle']['nombre'] for r in resp]
        expected = sorted(ordered, key=asciifold)
        self.assertListEqual(ordered, expected)

    def test_id_ordering(self):
        """Los resultados deben poder ser ordenados por ID."""
        resp = self.get_response({
            'direccion': 'santa fe y salta',
            'orden': 'id',
            'max': 1000
        })

        ordered = [r['calle']['id'] for r in resp]
        expected = sorted(ordered)
        self.assertListEqual(ordered, expected)

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
