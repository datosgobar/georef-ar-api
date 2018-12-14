import csv
import copy
from xml.etree import ElementTree
from unittest import mock, TestCase
import json
import urllib
from flask import current_app
import geojson
from service import app, formatter


def asciifold(text):
    conv = {
        'Á': 'A',
        'É': 'E',
        'Í': 'I',
        'Ó': 'O',
        'Ú': 'U',
        'Ñ': 'N'
    }

    return text.upper().translate(text.maketrans(conv))


class GeorefLiveTest(TestCase):
    def __init__(self, *args, **kwargs):
        self.endpoint = None
        self.entity = None
        super().__init__(*args, **kwargs)

    def setUp(self):
        app.testing = True
        self.app = app.test_client()

    def get_response(self, params=None, method='GET', body=None,
                     return_value='data', fmt='json', endpoint=None,
                     entity=None):
        """Método de uso general para obtener resultados de la API, utilizando
        internamente los métodos .get() y .post() del app Flask."""

        if not params:
            params = {}

        endpoint = endpoint or self.endpoint
        entity = entity or self.entity

        query = endpoint + '?' + urllib.parse.urlencode(params)

        if method == 'GET':
            response = self.app.get(query)
        elif method == 'POST':
            response = self.app.post(query, json=body)
        else:
            raise ValueError('Método desconocido.')

        if return_value == 'status':
            return response.status_code

        if return_value in ['data', 'full', 'raw']:
            if response.status_code != 200:
                raise Exception(
                    'La petición no devolvió código 200: {}'.format(
                        response.data))

            if return_value == 'data':
                if fmt == 'json':
                    key = entity if method == 'GET' else 'resultados'
                    return json.loads(response.data)[key]

                if fmt == 'csv':
                    return csv.reader(response.data.decode().splitlines(),
                                      delimiter=formatter.CSV_SEP,
                                      quotechar=formatter.CSV_QUOTE,
                                      lineterminator=formatter.CSV_NEWLINE)

                if fmt == 'xml':
                    return ElementTree.fromstring(response.data.decode())

                raise ValueError('Formato desconocido.')

            if return_value == 'full':
                return json.loads(response.data)

            if return_value == 'raw':
                return response.data

        raise ValueError('Tipo de retorno desconocido.')

    def assert_unknown_param_returns_400(self):
        response = self.app.get(self.endpoint + '?foo=bar')
        self.assertEqual(response.status_code, 400)

    def assert_valid_csv(self, params=None):
        if not params:
            params = {}

        params['formato'] = 'csv'

        query = self.endpoint + '?' + urllib.parse.urlencode(params)
        response = self.app.get(query)
        text = response.data.decode()

        dialect = csv.Sniffer().sniff(text)
        has_header = csv.Sniffer().has_header(text)
        row_count = len(text.splitlines())

        self.assertTrue(all([dialect.delimiter == formatter.CSV_SEP,
                             has_header,
                             row_count > 0]))

    def get_geojson(self, params=None):
        if not params:
            params = {}
        params['formato'] = 'geojson'

        resp = self.get_response(params=params, return_value='raw')
        return geojson.loads(resp.decode())

    def assert_valid_geojson(self, params=None):
        geodata = self.get_geojson(params)
        self.assertTrue(len(geodata['features']) > 0)

    def assert_valid_xml(self, params=None):
        if not params:
            params = {}

        entity_plural = self.endpoint.split('/')[-1]

        json_resp = self.get_response(params=params, return_value='full')
        json_as_xml = formatter.value_to_xml(
            entity_plural, json_resp[entity_plural],
            list_item_names=formatter.XML_LIST_ITEM_NAMES)

        params['formato'] = 'xml'
        xml_resp = self.get_response(params=params, fmt='xml')
        xml_entities = xml_resp.find('resultado').find(entity_plural)

        self.assertEqual(ElementTree.tostring(xml_entities,
                                              encoding='unicode'),
                         ElementTree.tostring(json_as_xml, encoding='unicode'))

    def assert_flat_results(self):
        resp = self.get_response({'aplanar': 1, 'max': 1})
        self.assertTrue(all([
            not isinstance(v, dict) for v in resp[0].values()
        ]) and resp)

    def assert_fields_set_equals(self, set_name, fields, params=None,
                                 iterable=True):
        if not params:
            params = {}

        params['campos'] = set_name
        resp = self.get_response(params)
        entity_a = resp[0] if iterable else resp
        formatter.flatten_dict(entity_a, sep='.')

        params['campos'] = ', '.join(fields)
        resp = self.get_response(params)
        entity_b = resp[0] if iterable else resp
        formatter.flatten_dict(entity_b, sep='.')

        self.assertListEqual(sorted(entity_a.keys()), sorted(entity_b.keys()))

    def assert_name_search_id_matches(self, term_matches, exact=False):
        results = []
        for _, query in term_matches:
            params = {'nombre': query}
            if exact:
                params['exacto'] = 1
            res = self.get_response(params)
            results.append(sorted([p['id'] for p in res]))

        self.assertListEqual([sorted(ids) for ids, _ in term_matches], results)

    def assert_empty_params_return_400(self, params):
        statuses = []
        for param in params:
            response = self.app.get(self.endpoint + '?' + param + '=')
            statuses.append(response.status_code)

        self.assertListEqual([400] * len(params), statuses)


class GeorefMockTest(GeorefLiveTest):
    def setUp(self):
        self.patcher = mock.patch('elasticsearch.Elasticsearch', autospec=True)
        self.es = self.patcher.start()
        super().setUp()

    def tearDown(self):
        with app.app_context():
            if hasattr(current_app, 'elasticsearch'):
                delattr(current_app, 'elasticsearch')

        self.es = None
        self.patcher.stop()
        self.patcher = None
        super().tearDown()

    def set_msearch_results(self, results):
        """Establece los valores que debería retornar el método msearch() de
        Elasticsearch. Notar que se establecen los resultados para una sola
        query: si se llega a utilizar uno de los recursos POST con más de una
        query, ocurriría un error interno en la API.

        Args:
            results (list): Lista de 'hits' (documentos) para una única query.

        """
        hits = [{'_source': copy.deepcopy(result)} for result in results]

        self.es.return_value.msearch.return_value = {
            'responses': [
                {
                    'hits': {
                        'hits': hits,
                        'total': len(hits)
                    }
                }
            ]
        }
