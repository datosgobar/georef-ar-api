# -*- coding: utf-8 -*-
from unittest import TestCase


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