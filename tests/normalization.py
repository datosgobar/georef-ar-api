# -*- coding: utf-8 -*-
from unittest import TestCase
import service


class HouseNumberTest(TestCase):
    """Pruebas relacionadas con la altura de una calle."""
    def test_normalize_when_number_in_range(self):
        """La altura está en el rango de la calle en la base de datos."""
        pass

    def test_normalize_when_number_out_of_range(self):
        """La altura no está en el rango de la calle en la base de datos."""
        pass

    def test_normalize_when_number_not_present(self):
        """La calle no tiene numeración en la base de datos."""
        pass


class MatchResultsTest(TestCase):
    """Pruebas para casos de normalización con uno o más resultados."""
    def setUp(self):
        self.app = service.app.test_client()

    def test_input_matches_single_address(self):
        """La dirección recibida coincide con una única dirección."""
        result = self.app.get('/api/v1.0/normalizador')
        assert b'estado' in result.data

    def test_input_matches_many_addresses(self):
        """La dirección recibida puede ser una de varias al normalizar."""
        pass


class RequestStatusTest(TestCase):
    """Pruebas de los distintos estados de respuesta para un request."""
    def test_valid_request_with_results(self):
        """Request válido con resultados. Retorna OK."""
        pass

    def test_valid_request_with_no_results(self):
        """Request válido sin resultados. Retorna SIN_RESULTADOS."""
        pass

    def test_invalid_request(self):
        """Request inválido. Retorna INVALIDO."""
        pass
