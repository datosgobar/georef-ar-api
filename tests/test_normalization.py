# -*- coding: utf-8 -*-
from service import app, data
from service.names import *
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
        self.endpoint = '/api/v1.0/direcciones'
        data.query_address = Mock(return_value=test_response)

    def test_normalize_when_number_in_range(self):
        """La altura está en el rango de la calle en la base de datos."""
        url = self.endpoint + '?direccion=Austria+123,Buenos+Aires'
        response = self.app.get(url)
        result = json.loads(response.data)
        assert 'AUSTRIA 123' in result[ADDRESSES][0][FULL_NAME]

    def test_normalize_when_number_out_of_range(self):
        """La altura no está en el rango de la calle en la base de datos."""
        url = self.endpoint + '?direccion=Austria+501,Buenos+Aires'
        response = self.app.get(url)
        result = json.loads(response.data)
        assert 'AUSTRIA 501' not in result[ADDRESSES][0][FULL_NAME]

    def test_normalize_when_number_not_present(self):
        """La calle no tiene numeración en la base de datos."""
        url = self.endpoint + '?direccion=Australia+123,Buenos+Aires'
        response = self.app.get(url)
        result = json.loads(response.data)
        assert 'AUSTRALIA 123' not in result[ADDRESSES][0][FULL_NAME]

    def test_number_missing_from_request(self):
        """Request inválido. Retorna estado 400 y mensaje de error."""
        url = self.endpoint + '?direccion=Austria'
        response = self.app.get(url)
        result = json.loads(response.data)
        assert (response.status_code == 400 and
                result[ERROR][MESSAGE] == NUMBER_REQUIRED)


class MatchResultsTest(TestCase):
    """Pruebas para casos de normalización con uno o más resultados."""
    def setUp(self):
        self.app = app.test_client()
        self.endpoint = '/api/v1.0/direcciones'
        data.query_address = Mock(return_value=test_response)

    def test_get_request_with_single_match(self):
        """La dirección recibida coincide con una única dirección."""
        url = self.endpoint + '?direccion=Austria 100,Buenos Aires'
        response = self.app.get(url)
        result = json.loads(response.data)
        assert len(result[ADDRESSES]) == 2

    def test_get_request_with_many_matches(self):
        """La dirección recibida puede ser una de varias al normalizar."""
        url = self.endpoint + '?direccion=Italia 100'
        response = self.app.get(url)
        result = json.loads(response.data)
        assert len(result[ADDRESSES]) > 1

    def test_get_request_with_no_results(self):
        """Request válido sin resultados. Retorna SIN_RESULTADOS."""
        data.query_address = Mock(return_value=[])
        url = self.endpoint + '?direccion=CalleQueNoExiste 100'
        response = self.app.get(url)
        result = json.loads(response.data)
        assert len(result[ADDRESSES]) == 0

    def test_post_request_with_matches(self):
        """La direcciones están en el cuerpo del Request, en formato JSON."""
        addresses = {
            'direcciones':[
                'AUSTRIA, BUENOS AIRES',
                'DIAGONAL NORTE, BUENOS AIRES'
            ]
        }
        response = self.app.post(self.endpoint,
                                 data=json.dumps(addresses),
                                 content_type='application/json')
        result = json.loads(response.data)
        assert len(result[ADDRESSES]) == 2


class RequestStatusTest(TestCase):
    """Pruebas de los distintos estados de respuesta para un request."""
    def setUp(self):
        self.app = app.test_client()
        self.endpoint = '/api/v1.0/direcciones'
        data.query_address = Mock(return_value=test_response)

    def test_valid_request_with_results(self):
        """Request válido con resultados. Retorna OK."""
        url = self.endpoint + '?direccion=Austria 100'
        response = self.app.get(url)
        result = json.loads(response.data)
        assert response.status_code == 200 and len(result[ADDRESSES]) > 0

    def test_invalid_request(self):
        """Request inválido. Retorna estado INVALIDO."""
        response = self.app.get(self.endpoint)
        result = json.loads(response.data)
        assert (response.status_code == 400 and
                result[ERROR][MESSAGE] == ADDRESS_REQUIRED)


if __name__ == '__main__':
    unittest.main()
