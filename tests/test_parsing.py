# -*- coding: utf-8 -*-
from service import app, normalizer, parser
from unittest import TestCase
from unittest.mock import Mock
import flask
import json


class InputParsingTest(TestCase):
    """Pruebas de procesamiento de parámetros de entrada de la API."""
    def test_query_with_locality_provided(self):
        """El parámetro 'localidad' está presente en el request."""
        with app.test_request_context('?direccion&localidad=Buenos+Aires'):
            search = parser.build_search_from(flask.request.args)
            assert search['locality'] == 'Buenos Aires'

    def test_query_with_locality_not_provided(self):
        """El parámetro 'localidad' no está en el request."""
        with app.test_request_context('?direccion'):
            search = parser.build_search_from(flask.request.args)
            assert search['locality'] is None

    def test_query_with_state_provided(self):
        """El parámetro 'provincia' está presente en el request."""
        with app.test_request_context('?direccion&provincia=Buenos+Aires'):
            search = parser.build_search_from(flask.request.args)
            assert search['state'] == 'Buenos Aires'

    def test_query_with_state_not_provided(self):
        """El parámetro 'provincia' no está en el request."""
        with app.test_request_context('?direccion'):
            search = parser.build_search_from(flask.request.args)
            assert search['state'] is None

    def test_query_with_max_provided(self):
        """El parámetro 'max' está presente en el request."""
        with app.test_request_context('?direccion&max=50'):
            search = parser.build_search_from(flask.request.args)
            assert search['max'] == '50'

    def test_query_with_max_not_provided(self):
        """El parámetro 'max' no está en el request."""
        with app.test_request_context('?direccion'):
            search = parser.build_search_from(flask.request.args)
            assert search['max'] is None

    def test_query_with_fields_provided(self):
        """El parámetro 'campos' está en el request."""
        with app.test_request_context('?direccion&campos=param1,param2'):
            search = parser.build_search_from(flask.request.args)
            assert 'param1' in search['fields'] and 'param2' in search['fields']

    def test_query_with_fields_not_provided(self):
        """El parámetro 'campos' no está en el request."""
        with app.test_request_context('?direccion'):
            search = parser.build_search_from(flask.request.args)
            assert search['fields'] == []

    def test_number_is_parsed(self):
        """La altura está presente en el parámetro dirección."""
        with app.test_request_context('?direccion=av principal 100'):
            search = parser.build_search_from(flask.request.args)
            assert search['number'] == 100

    def test_number_is_not_parsed(self):
        """La altura no está presente en el parámetro dirección."""
        with app.test_request_context('?direccion=av principal'):
            search = parser.build_search_from(flask.request.args)
            assert search['number'] is None

    def test_road_type_is_not_parsed(self):
        """El tipo de camino está presente y se devuelve su abreviación."""
        with app.test_request_context('?direccion=av'):
            search = parser.build_search_from(flask.request.args)
            assert search['road_type'] is None


class ResultsParsingTest(TestCase):
    """Pruebas de filtrado de resultados según parámetos de entrada."""
    test_response = """{
        "estado": "OK",
        "direcciones": [
        {
            "localidad": "CIUDAD AUTONOMA BUENOS AIRES",
            "nombre": "AUSTRIA",
            "nomenclatura": "CALLE AUSTRIA, CIUDAD AUTONOMA BUENOS AIRES...",
            "observaciones": {
                "fuente": "INDEC"
            },
            "provincia": "CAPITAL FEDERAL",
            "tipo": "CALLE"
        },
        {
            "localidad": "CIUDAD AUTONOMA BUENOS AIRES",
            "nombre": "AUSTRALIA",
            "nomenclatura": "CALLE AUSTRALIA, CIUDAD AUTONOMA BUENOS AIRES...",
            "observaciones": {
                "fuente": "INDEC"
            },
            "provincia": "CAPITAL FEDERAL",
            "tipo": "CALLE"
        }]
    }"""

    def setUp(self):
        app.testing = True
        self.app = app.test_client()
        normalizer.process_address = Mock(return_value=self.test_response)

    def test_result_filtered_by_locality_only(self):
        """Devuelve todas las direcciones para una localidad dada."""
        pass

    def test_result_filtered_by_locality_with_address(self):
        """Busca y normaliza una dirección para una localidad dada."""
        endpoint = '/api/v1.0/direcciones?direccion=Austria&localidad=Buenos'
        response = self.app.get(endpoint)
        results = json.loads(response.data)
        assert len(results['direcciones']) > 1

    def test_result_filtered_by_state_only(self):
        """Devuelve todas las direcciones para una provincia dada."""
        pass

    def test_result_filtered_by_state_with_address(self):
        """Busca y normaliza una dirección para una provincia dada."""
        endpoint = '/api/v1.0/direcciones?direccion=Austria&provincia=Capital'
        response = self.app.get(endpoint)
        results = json.loads(response.data)
        assert len(results['direcciones']) > 1

    def test_result_has_fields_requested(self):
        """Devuelve resultado con los 'campos' especificados en el request."""
        pass

    def test_result_has_max_requested_or_less(self):
        """Devuelve resultados hasta la cantidad especificada en 'max'."""
        pass


if __name__ == '__main__':
    unittest.main()
