import random
from . import GeorefMockTest


class DataMockTest(GeorefMockTest):
    def test_offset_value(self):
        """El valor de 'inicio' de las respuestas debería ser idéntico al que
        se especifica vía el parámetro 'inicio'.
        """
        self.set_msearch_results([
            {
                'id': '06091010009',
                'nombre': 'RANELAGH'
            }
        ])
        offset = random.randint(10, 100)

        resp = self.get_response(
            return_value='full',
            url='/api/localidades?inicio={}&campos=id'.format(offset)
        )

        self.assertEqual(resp['inicio'], offset)
