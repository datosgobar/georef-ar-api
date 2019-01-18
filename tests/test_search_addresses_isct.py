import math
from service import names as N
from . import GeorefLiveTest

MEAN_EARTH_RADIUS_KM = 6371
COMMON_ISCT = 'salta y santa fe'


def approximate_distance_meters(loc_a, loc_b):
    # https://en.wikipedia.org/wiki/Haversine_formula
    lat_a = math.radians(loc_a[N.LAT])
    lat_b = math.radians(loc_b[N.LAT])
    diff_lat = math.radians(loc_b[N.LAT] - loc_a[N.LAT])
    diff_lon = math.radians(loc_b[N.LON] - loc_a[N.LON])

    a = math.sin(diff_lat / 2) ** 2
    b = math.cos(lat_a) * math.cos(lat_b) * (math.sin(diff_lon / 2) ** 2)

    kms = 2 * MEAN_EARTH_RADIUS_KM * math.asin(math.sqrt(a + b))
    return kms * 1000


class SearchAddressesIsctTest(GeorefLiveTest):
    """Pruebas de búsqueda por dirección de tipo 'intersection'."""

    def setUp(self):
        self.endpoint = '/api/direcciones'
        self.entity = 'direcciones'
        super().setUp()

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

    def test_intersection_nonexistent_door_num(self):
        """Si se especifica una intersección con altura, la posición de la
        altura sobre la primera calle debería estar a menos de
        ISCT_DOOR_NUM_TOLERANCE_M metros de la posición del a intersección.
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
            approximate_distance_meters(loc_simple, loc_isct),
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
