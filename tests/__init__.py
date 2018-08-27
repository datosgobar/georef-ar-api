from unittest import TestCase
from service import app, formatter
import json
import urllib
import csv
import geojson


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


class SearchEntitiesTest(TestCase):
    def setUp(self):
        app.testing = True
        self.app = app.test_client()

    def get_response(self, params=None, method='GET', body=None,
                     status_only=False, fmt='json', endpoint=None,
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

        if status_only:
            return response.status_code
        elif response.status_code != 200:
            raise Exception(
                'La petición no devolvió código 200: {}'.format(response.data))

        if fmt == 'json':
            key = entity if method == 'GET' else 'resultados'
            return json.loads(response.data)[key]
        elif fmt == 'csv':
            return csv.reader(response.data.decode().splitlines(),
                              delimiter=formatter.CSV_SEP,
                              quotechar=formatter.CSV_ESCAPE,
                              lineterminator=formatter.CSV_NEWLINE)
        else:
            raise ValueError('Formato desconocido.')

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

    def assert_valid_geojson(self, params=None):
        if not params:
            params = {}

        params['formato'] = 'geojson'

        query = self.endpoint + '?' + urllib.parse.urlencode(params)
        response = self.app.get(query)
        geodata = geojson.loads(response.data.decode())

        self.assertTrue(len(geodata['features']) > 0)

    def assert_flat_results(self):
        resp = self.get_response({'aplanar': 1, 'max': 1})
        self.assertTrue(all([
            not isinstance(v, dict) for v in resp[0].values()
        ]) and resp)

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
