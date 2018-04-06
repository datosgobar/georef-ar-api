from unittest import TestCase
from service import app
import json
import urllib

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

    def get_response(self, params=None):
        if not params:
            params = {}

        query = self.endpoint + '?' + urllib.parse.urlencode(params)
        response = self.app.get(query)
        return json.loads(response.data)[self.entity]

    def assert_unknown_param_returns_400(self):
        response = self.app.get(self.endpoint + '?foo=bar')
        self.assertEqual(response.status_code, 400)

    def assert_formats_ok(self):
        for fmt in ['.json', '.csv', '.geojson']:
            response = self.app.get(self.endpoint + fmt)
            self.assertEqual(response.status_code, 200)

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
            