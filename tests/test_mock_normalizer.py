import logging
import random
from unittest import TestCase
from unittest import mock
import elasticsearch
from flask import current_app
from service import app


ENDPOINTS = [
    '/calles',
    '/provincias',
    '/departamentos',
    '/municipios',
    '/localidades'
]

MOCK_STREET = {
    'nomenclatura': 'SANTA FE, SAAVEDRA, BUENOS AIRES',
    'altura': {
        'inicio': {
            'derecha': 0,
            'izquierda': 0
        },
        'fin': {
            'derecha': 1000,
            'izquierda': 1001
        }
    },
    'geometria': None
}

logging.getLogger('georef').setLevel(logging.CRITICAL)


class NormalizerTest(TestCase):
    def setUp(self):
        app.testing = True
        self.app = app.test_client()
        self.base_url = '/api/v1.0'

    def tearDown(self):
        with app.app_context():
            if hasattr(current_app, 'elasticsearch'):
                delattr(current_app, 'elasticsearch')

    @mock.patch("elasticsearch.Elasticsearch", autospec=True)
    def test_elasticsearch_connection_error(self, es):
        """Se debería devolver un error 500 cuando falla la conexión a
        Elasticsearch."""
        es.side_effect = elasticsearch.ElasticsearchException()
        self.assert_500_error(random.choice(ENDPOINTS))

    @mock.patch("elasticsearch.Elasticsearch", autospec=True)
    def test_elasticsearch_msearch_error(self, es):
        """Se debería devolver un error 500 cuando falla la query
        MultiSearch."""
        es.return_value.msearch.side_effect = \
            elasticsearch.ElasticsearchException()
        self.assert_500_error(random.choice(ENDPOINTS))

    @mock.patch("elasticsearch.Elasticsearch", autospec=True)
    def test_elasticsearch_msearch_results_error(self, es):
        """Se debería devolver un error 500 cuando falla la query
        MultiSearch (retorna errores)."""
        es.return_value.msearch.return_value = {
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

    def set_msearch_results(self, mock_es, results):
        # Resultados para una búsqueda de una query sola
        hits = [{'_source': result.copy()} for result in results]

        mock_es.return_value.msearch.return_value = {
            'responses': [
                {
                    'hits': {
                        'hits': hits,
                        'total': 1
                    }
                }
            ]
        }
