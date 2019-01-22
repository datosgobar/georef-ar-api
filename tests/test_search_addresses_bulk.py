import random
from . import GeorefLiveTest

STREET_NAMES = [
    'salta', 'santa fe', 'corrientes', 'cordoba', 'mitre', 'calle', 'avenida',
    'sarmiento', '9 de julio', '25 de mayo', 'belgrano', 'buenos aires',
    'san martin', 'general paz'
]


def random_address():
    """Genera una dirección al azar, de cualquier tipo."""
    street_count = random.randint(1, 3)

    if random.getrandbits(1):
        door_num = ' {}'.format(random.randint(100, 3000))
    else:
        door_num = ''

    if street_count == 1:
        return '{}{}'.format(random.choice(STREET_NAMES), door_num)

    if street_count == 2:
        return '{}{} esquina {}'.format(random.choice(STREET_NAMES),
                                        door_num,
                                        random.choice(STREET_NAMES))

    return '{}{} e/ {} y {}'.format(random.choice(STREET_NAMES),
                                    door_num,
                                    random.choice(STREET_NAMES),
                                    random.choice(STREET_NAMES))


class SearchAddressesBulkTest(GeorefLiveTest):
    """Pruebas de búsqueda de direcciones por lote, para cualquier tipo."""

    def setUp(self):
        self.endpoint = '/api/direcciones'
        self.entity = 'direcciones'
        super().setUp()

    def test_short_bulk_1(self):
        """Una búsqueda de N direcciones utilizando POST debería ser
        equivalente a buscar las N direcciones por separado."""
        self.assert_bulk_results(1)

    def test_short_bulk_50(self):
        """Una búsqueda de N direcciones utilizando POST debería ser
        equivalente a buscar las N direcciones por separado."""
        self.assert_bulk_results(25)

    def assert_bulk_results(self, size):
        queries = []
        for _ in range(size):
            queries.append({
                'direccion': random_address(),
                'max': 1,
                'campos': random.choice(['basico', 'estandar', 'completo'])
            })

        individual_results = []
        for query in queries:
            individual_results.append(self.get_response(params=query,
                                                        return_value='full'))

        bulk_results = self.get_response(method='POST', body={
            'direcciones': queries
        })

        self.assertEqual(individual_results, bulk_results)
