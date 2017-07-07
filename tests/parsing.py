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
            assert search['state']  == 'Buenos Aires'

    def test_query_with_state_not_provided(self):
        """El parámetro 'provincia' no está en el request."""
        with app.test_request_context('?direccion'):
            search = parser.build_search_from(flask.request.args)
            assert search['state'] is None

    def test_query_with_max_provided(self):
        """El parámetro 'max' está presente en el request."""
        with app.test_request_context('?direccion&max=50'):
            search = parser.build_search_from(flask.request.args)
            assert search['max']  == '50'

    def test_query_with_max_not_provided(self):
        """El parámetro 'max' no está en el request."""
        with app.test_request_context('?direccion'):
            search = parser.build_search_from(flask.request.args)
            assert search['max'] is None

    def test_query_with_fields_provided(self):
        """El parámetro 'campos' está en el request."""
        pass

    def test_query_with_fields_not_provided(self):
        """El parámetro 'campos' no está en el request."""
        pass


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
