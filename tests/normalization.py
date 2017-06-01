# -*- coding: utf-8 -*-
from unittest import TestCase
import json
import service


class HouseNumberTest(TestCase):
    """Pruebas relacionadas con la altura de una calle."""
    def setUp(self):
        self.app = service.app.test_client()

    def test_normalize_when_number_in_range(self):
        """La altura está en el rango de la calle en la base de datos."""
        endpoint = '/api/v1.0/normalizador?direccion=Austria+123,Buenos+Aires'
        response = self.app.get(endpoint)
        results = json.loads(response.data)
        assert 'AUSTRIA 123' in results['direcciones'][0]['nomenclatura']

    def test_normalize_when_number_out_of_range(self):
        """La altura no está en el rango de la calle en la base de datos."""
        endpoint = '/api/v1.0/normalizador?direccion=Austria+501,Buenos+Aires'
        response = self.app.get(endpoint)
        results = json.loads(response.data)
        assert 'AUSTRIA 501' not in results['direcciones'][0]['nomenclatura']

    def test_normalize_when_number_not_present(self):
        """La calle no tiene numeración en la base de datos."""
        endpoint = '/api/v1.0/normalizador?direccion=Cabral+123,Buenos+Aires'
        response = self.app.get(endpoint)
        results = json.loads(response.data)
        assert 'AUSTRIA 123' not in results['direcciones'][0]['nomenclatura']


class MatchResultsTest(TestCase):
    """Pruebas para casos de normalización con uno o más resultados."""
    def setUp(self):
        self.app = service.app.test_client()

    def test_get_request_with_single_match(self):
        """La dirección recibida coincide con una única dirección."""
        endpoint = '/api/v1.0/normalizador?direccion=Austria,Buenos%20Aires'
        response = self.app.get(endpoint)
        results = json.loads(response.data)
        assert len(results['direcciones']) == 1

    def test_get_request_with_many_matches(self):
        """La dirección recibida puede ser una de varias al normalizar."""
        endpoint = '/api/v1.0/normalizador?direccion=Italia'
        response = self.app.get(endpoint)
        results = json.loads(response.data)
        assert len(results['direcciones']) > 1
    
    def test_post_request_with_matches(self):
        """La direcciones están en el cuerpo del Request, en formato JSON."""
        addresses = {'direcciones':[
            'AUSTRIA, BUENOS AIRES',
            'DIAGONAL NORTE, BUENOS AIRES']}
        response = self.app.post(
            '/api/v1.0/normalizador',
            data=json.dumps(addresses),
            content_type='application/json')
        results = json.loads(response.data)
        assert len(results['direcciones']) == 2


class RequestStatusTest(TestCase):
    """Pruebas de los distintos estados de respuesta para un request."""
    def setUp(self):
        self.app = service.app.test_client()

    def test_valid_request_with_results(self):
        """Request válido con resultados. Retorna OK."""
        endpoint = '/api/v1.0/normalizador?direccion=Austria'
        response = self.app.get(endpoint)
        results = json.loads(response.data)
        assert results['estado'] == 'OK' \
        and len(results['direcciones']) > 0

    def test_valid_request_with_no_results(self):
        """Request válido sin resultados. Retorna SIN_RESULTADOS."""
        endpoint = '/api/v1.0/normalizador?direccion=CalleQueNoExiste'
        response = self.app.get(endpoint)
        results = json.loads(response.data)
        assert results['estado'] == 'SIN_RESULTADOS' \
        and len(results['direcciones']) == 0

    def test_invalid_request(self):
        """Request inválido. Retorna estado INVALIDO."""
        # This should be invalid for missing a required parameter.
        response = self.app.get('/api/v1.0/normalizador')
        results = json.loads(response.data)
        assert results['estado'] == 'INVALIDO' and response.status_code == 400
