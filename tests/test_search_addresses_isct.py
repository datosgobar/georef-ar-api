from . import GeorefLiveTest

COMMON_ISCT = 'salta y santa fe'


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
            'Larrea esquina Sarmiento',
            [
                ('0202101007345', '0202101010480')
            ],
            params={
                'provincia': '02'
            }
        )

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
