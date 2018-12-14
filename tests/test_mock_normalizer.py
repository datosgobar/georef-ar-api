import random
import elasticsearch
from . import GeorefMockTest


ENDPOINTS = [
    '/calles',
    '/provincias',
    '/departamentos',
    '/municipios',
    '/localidades'
]


class NormalizerTest(GeorefMockTest):
    def setUp(self):
        self.base_url = '/api/v1.0'
        super().setUp()

    def test_elasticsearch_connection_error(self):
        """Se debería devolver un error 500 cuando falla la conexión a
        Elasticsearch."""
        self.es.side_effect = elasticsearch.ElasticsearchException()
        self.assert_500_error(random.choice(ENDPOINTS))

    def test_elasticsearch_msearch_error(self):
        """Se debería devolver un error 500 cuando falla la query
        MultiSearch."""
        self.es.return_value.msearch.side_effect = \
            elasticsearch.ElasticsearchException()
        self.assert_500_error(random.choice(ENDPOINTS))

    def test_elasticsearch_msearch_results_error(self):
        """Se debería devolver un error 500 cuando falla la query
        MultiSearch (retorna errores)."""
        self.es.return_value.msearch.return_value = {
            'responses': [
                {
                    'error': {
                        'type': 'mock',
                        'reason': 'mock'
                    }
                }
            ]
        }

        self.assert_500_error(random.choice(ENDPOINTS))

    def assert_500_error(self, url):
        resp = self.app.get(self.base_url + url)
        self.assertTrue(resp.status_code == 500 and 'errores' in resp.json)
