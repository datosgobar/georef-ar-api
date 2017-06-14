# -*- coding: utf-8 -*-
from unittest import TestCase
import json
import service


class InputParsingTest(TestCase):
    """Pruebas de procesamiento de parámetros de entrada de la API."""
    def test_query_with_locality_provided(self):
        """El parámetro 'localidad' está presente en el request."""
        pass

    def test_query_with_locality_not_provided(self):
        """El parámetro 'localidad' no está en el request."""
        pass

    def test_query_with_state_provided(self):
        """El parámetro 'provincia' está presente en el request."""
        pass

    def test_query_with_state_not_provided(self):
        """El parámetro 'provincia' no está en el request."""
        pass

    def test_query_with_max_provided(self):
        """El parámetro 'max' está presente en el request."""
        pass

    def test_query_with_max_not_provided(self):
        """El parámetro 'max' no está en el request."""
        pass

    def test_query_with_fields_provided(self):
        """El parámetro 'campos' está en el request."""
        pass

    def test_query_with_fields_not_provided(self):
        """El parámetro 'campos' no está en el request."""
        pass


class ResultsParsingTest(TestCase):
    """Pruebas de filtrado de resultados según parámetos de entrada."""
    def setUp(self):
        self.app = service.app.test_client()

    def test_result_filtered_by_locality_only(self):
        """Devuelve todas las direcciones para una localidad dada."""
        pass

    def test_result_filtered_by_locality_with_address(self):
        """Busca y normaliza una dirección para una localidad dada."""
        endpoint = '/api/v1.0/direcciones?direccion=Austria&localidad=Buenos'
        response = self.app.get(endpoint)
        results = json.loads(response.data)
        assert len(results['direcciones']) == 1

    def test_result_filtered_by_state_only(self):
        """Devuelve todas las direcciones para una provincia dada."""
        pass

    def test_result_filtered_by_state_with_address(self):
        """Busca y normaliza una dirección para una provincia dada."""
        endpoint = '/api/v1.0/direcciones?direccion=Austria&provincia=Buenos'
        response = self.app.get(endpoint)
        results = json.loads(response.data)
        assert len(results['direcciones']) > 1

    def test_result_has_fields_requested(self):
        """Devuelve resultado con los 'campos' especificados en el request."""
        pass

    def test_result_has_max_requested_or_less(self):
        """Devuelve resultados hasta la cantidad especificada en 'max'."""
        pass
