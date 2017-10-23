# -*- coding: utf-8 -*-
from service import app, data
from unittest import TestCase
from unittest.mock import Mock
import json


test_response = [
    {
        "altura": 123,
        "localidad": "CIUDAD AUTONOMA BUENOS AIRES",
        "nombre": "AUSTRIA",
        "nomenclatura": "CALLE AUSTRIA 123, CIUDAD AUTONOMA BUENOS AIRES...",
        "observaciones": {
            "fuente": "INDEC"
        },
        "provincia": "CAPITAL FEDERAL",
        "tipo": "CALLE"
    },
    {
        "altura": None,
        "localidad": "CIUDAD AUTONOMA BUENOS AIRES",
        "nombre": "AUSTRALIA",
        "nomenclatura": "CALLE AUSTRALIA, CIUDAD AUTONOMA BUENOS AIRES...",
        "observaciones": {
            "fuente": "INDEC"
        },
        "provincia": "CAPITAL FEDERAL",
        "tipo": "CALLE"
    }
]


class HouseNumberTest(TestCase):
    """Pruebas relacionadas con la altura de una calle."""
    def setUp(self):
        self.app = app.test_client()
        data.query_address = Mock(return_value=test_response)

    def test_normalize_when_number_in_range(self):
        """La altura está en el rango de la calle en la base de datos."""
        endpoint = '/api/v1.0/direcciones?direccion=Austria+123,Buenos+Aires'
        response = self.app.get(endpoint)
        results = json.loads(response.data)
        assert 'AUSTRIA 123' in results['direcciones'][0]['nomenclatura']

    def test_normalize_when_number_out_of_range(self):
        """La altura no está en el rango de la calle en la base de datos."""
        endpoint = '/api/v1.0/direcciones?direccion=Austria+501,Buenos+Aires'
        response = self.app.get(endpoint)
        results = json.loads(response.data)
        assert 'AUSTRIA 501' not in results['direcciones'][0]['nomenclatura']

    def test_normalize_when_number_not_present(self):
        """La calle no tiene numeración en la base de datos."""
        endpoint = '/api/v1.0/direcciones?direccion=Australia+123,Buenos+Aires'
        response = self.app.get(endpoint)
        results = json.loads(response.data)
        assert 'AUSTRALIA 123' not in results['direcciones'][0]['nomenclatura']


class MatchResultsTest(TestCase):
    """Pruebas para casos de normalización con uno o más resultados."""
    def setUp(self):
        self.app = app.test_client()
        data.query_address = Mock(return_value=test_response)

    def test_get_request_with_single_match(self):
        """La dirección recibida coincide con una única dirección."""
        endpoint = '/api/v1.0/direcciones?direccion=Austria 100,Buenos Aires'
        response = self.app.get(endpoint)
        results = json.loads(response.data)
        assert len(results['direcciones']) == 2

    def test_get_request_with_many_matches(self):
        """La dirección recibida puede ser una de varias al normalizar."""
        endpoint = '/api/v1.0/direcciones?direccion=Italia 100'
        response = self.app.get(endpoint)
        results = json.loads(response.data)
        assert len(results['direcciones']) > 1
    
    def test_post_request_with_matches(self):
        """La direcciones están en el cuerpo del Request, en formato JSON."""
        addresses = {'direcciones':[
            'AUSTRIA, BUENOS AIRES',
            'DIAGONAL NORTE, BUENOS AIRES']}
        response = self.app.post(
            '/api/v1.0/direcciones',
            data=json.dumps(addresses),
            content_type='application/json')
        results = json.loads(response.data)
        assert len(results['direcciones']) == 2


class RequestStatusTest(TestCase):
    """Pruebas de los distintos estados de respuesta para un request."""
    def setUp(self):
        self.app = app.test_client()
        data.query_address = Mock(return_value=test_response)

    def test_valid_request_with_results(self):
        """Request válido con resultados. Retorna OK."""
        endpoint = '/api/v1.0/direcciones?direccion=Austria 100'
        response = self.app.get(endpoint)
        results = json.loads(response.data)
        assert results['estado'] == 'OK' \
        and len(results['direcciones']) > 0

    def test_valid_request_with_no_results(self):
        """Request válido sin resultados. Retorna SIN_RESULTADOS."""
        data.query_address = Mock(return_value=[])
        endpoint = '/api/v1.0/direcciones?direccion=CalleQueNoExiste 100'
        response = self.app.get(endpoint)
        results = json.loads(response.data)
        assert results['estado'] == 'SIN_RESULTADOS' \
        and len(results['direcciones']) == 0

    def test_invalid_request(self):
        """Request inválido. Retorna estado INVALIDO."""
        # This is invalid for missing a required parameter.
        response = self.app.get('/api/v1.0/direcciones')
        results = json.loads(response.data)
        assert results['estado'] == 'INVALIDO' and response.status_code == 400


if __name__ == '__main__':
    unittest.main()
