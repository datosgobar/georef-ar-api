from unittest import TestCase
from service import app
from service.params import ParamErrorType as T
from random import choice

ENDPOINTS = [
    '/provincias',
    '/departamentos',
    '/municipios',
    '/localidades',
    '/calles'
]


class ParamParsingTest(TestCase):
    def setUp(self):
        app.testing = True

        self.app = app.test_client()
        self.url_base = '/api/v1.0'

    def test_bulk_no_json(self):
        """No se deberían aceptar operaciones bulk cuando el body HTTP
        no contiene JSON."""
        self.assert_errors_match('/provincias', [
            {(T.INVALID_BULK.value, 'body')}
        ], method='POST')

    def test_bulk_empty_json(self):
        """No se deberían aceptar operaciones bulk cuando el body HTTP
        contiene JSON vacío."""
        self.assert_errors_match('/calles', [
            {(T.INVALID_BULK.value, 'body')}
        ], method='POST', body={})

    def test_bulk_empty(self):
        """No se deberían aceptar operaciones bulk vacías."""
        body = {
            'provincias': []
        }

        self.assert_errors_match('/municipios', [
            {(T.INVALID_BULK.value, 'body')}
        ], body=body)

    def test_bulk_invalid_type(self):
        """No se deberían aceptar operaciones bulk que no sean de
        tipo lista."""
        body = {
            'departamentos': "prueba"
        }

        self.assert_errors_match('/departamentos', [
            {(T.INVALID_BULK.value, 'body')}
        ], body=body)

    def test_bulk_invalid_item_type(self):
        """No se deberían aceptar operaciones bulk que contengan
        elementos que no sean objetos."""
        body = {
            'municipios': [{}, 1]
        }

        self.assert_errors_match('/municipios', [
            set(),
            {(T.INVALID_BULK_ENTRY.value, 'body')}
        ], body=body)

    def test_unknown_param(self):
        """No se deberían aceptar parámetros desconocidos."""
        self.assert_errors_match('/localidades?hola=hola', {
            (T.UNKNOWN_PARAM.value, 'hola')
        })

    def test_unknown_param_bulk(self):
        """No se deberían aceptar parámetros desconocidos vía JSON."""
        body = {
            'provincias': [
                {
                    'hola': 'hola'
                }
            ]
        }

        self.assert_errors_match('/provincias', [
            {(T.UNKNOWN_PARAM.value, 'hola')}
        ], body=body)

    def test_missing_param(self):
        """Los parámetros requeridos faltantes deberían generar errores."""
        self.assert_errors_match('/direcciones', {
            (T.PARAM_REQUIRED.value, 'direccion')
        })

    def test_missing_param_bulk(self):
        """Los parámetros requeridos faltantes deberían generar errores
        vía JSON."""
        body = {
            'direcciones': [
                {}
            ]
        }

        self.assert_errors_match('/direcciones', [
            {(T.PARAM_REQUIRED.value, 'direccion')}
        ], body=body)

    def test_invalid_value_param(self):
        """Los parámetros con valores inválidos deberían generar errores."""
        self.assert_errors_match('/localidades?max=foobar', {
            (T.VALUE_ERROR.value, 'max')
        })

    def test_invalid_value_param_bulk(self):
        """Los parámetros con valores inválidos deberían generar errores
        vía JSON."""
        body = {
            'localidades': [
                {
                    'max': 'foobar'
                }
            ]
        }

        self.assert_errors_match('/localidades', [
            {(T.VALUE_ERROR.value, 'max')}
        ], body=body)

    def test_repeated_param(self):
        """Los parámetros repetidos deberían generar errores."""
        self.assert_errors_match('/calles?nombre=foo&nombre=bar', {
            (T.REPEATED.value, 'nombre')
        })

    def test_invalid_location(self):
        """El parámetro 'formato' solo se puede especificar vía querystring."""
        """Los parámetros con valores inválidos deberían generar errores
        vía JSON."""
        body = {
            'municipios': [
                {
                    'formato': 'csv'
                }
            ]
        }

        self.assert_errors_match('/municipios', [
            {(T.INVALID_LOCATION.value, 'formato')}
        ], body=body)

    def test_invalid_choice_param(self):
        """Los parámetros con valores no en rango deberían generar errores."""
        self.assert_errors_match('/localidades?orden=foobar', {
            (T.INVALID_CHOICE.value, 'orden')
        })

    def test_invalid_choice_param_bulk(self):
        """Los parámetros con valores no en rango deberían generar errores
        vía JSON."""
        body = {
            'localidades': [
                {
                    'campos': 'foobar,id'
                }
            ]
        }

        self.assert_errors_match('/localidades', [
            {(T.INVALID_CHOICE.value, 'campos')}
        ], body=body)

    def test_empty_string_param(self):
        """Los parámtros de tipo string no deberían aceptar strings
        vacíos."""
        self.assert_errors_match('/departamentos?nombre=', {
            (T.VALUE_ERROR.value, 'nombre')
        })

    def test_empty_string_list_param(self):
        """Los parámtros de tipo string list no deberían aceptar strings
        vacíos."""
        self.assert_errors_match('/departamentos?campos=', {
            (T.VALUE_ERROR.value, 'campos')
        })

    def test_empty_int_param(self):
        """Los parámtros de tipo int no deberían aceptar strings
        vacíos."""
        self.assert_errors_match('/localidades?max=', {
            (T.VALUE_ERROR.value, 'max')
        })

    def test_invalid_int_param(self):
        """Los parámtros de tipo int no deberían aceptar strings que no
        representen números."""
        self.assert_errors_match(choice(ENDPOINTS) + '?max=foobar', {
            (T.VALUE_ERROR.value, 'max')
        })

    def test_small_int_param(self):
        """Los parámtros de tipo int no deberían aceptar strings que
        representen números debajo de los límites establecidos."""
        self.assert_errors_match(choice(ENDPOINTS) + '?max=-10', {
            (T.VALUE_ERROR.value, 'max')
        })

    def test_empty_float_param(self):
        """Los parámtros de tipo float no deberían aceptar strings
        vacíos."""
        self.assert_errors_match('/ubicacion?lat=0&lon=', {
            (T.VALUE_ERROR.value, 'lon')
        })

    def test_multiple_errors(self):
        """Si varios parámetros tienen errores, se deberían informar todos
        los errores generados."""
        url = '/direcciones?foo=bar&max=bar&provincia=02&provincia=02&campos=a'
        self.assert_errors_match(url, {
            (T.UNKNOWN_PARAM.value, 'foo'),
            (T.PARAM_REQUIRED.value, 'direccion'),
            (T.VALUE_ERROR.value, 'max'),
            (T.REPEATED.value, 'provincia'),
            (T.INVALID_CHOICE.value, 'campos')
        })

    def test_multiple_errors_bulk(self):
        """En bulk, si varios parámetros tienen errores, se deberían informar todos
        los errores generados por query. Las queries sin errores deberían
        figurar como listas de errores vacías."""

        body = {
            'direcciones': [
                {
                    'direccion': 'Corrientes 1000'
                },
                {
                    'max': 'foobar',
                    'foobar': 'foobar'
                },
                {
                    'direccion': 'Corrientes 1000',
                    'campos': 'id,foobar,provincia',
                    'departamento': ''
                }
            ]
        }

        self.assert_errors_match('/direcciones', [
            set(),
            {
                (T.PARAM_REQUIRED.value, 'direccion'),
                (T.VALUE_ERROR.value, 'max'),
                (T.UNKNOWN_PARAM.value, 'foobar')
            },
            {
                (T.INVALID_CHOICE.value, 'campos'),
                (T.VALUE_ERROR.value, 'departamento')
            }
        ], body=body)

    def test_bulk_querystring_error(self):
        """En bulk, no se deberían aceptar parámetros vía querystring."""
        self.assert_errors_match('/calles?foo=bar', [
            {
                (T.INVALID_LOCATION.value, 'querystring')
            }
        ], body={
            'calles': []
        })

    def test_address_param(self):
        """Un parámetro de dirección sin altura no debería ser válido."""
        self.assert_errors_match('/direcciones?direccion=SANTA FE', {
            (T.VALUE_ERROR.value, 'direccion')
        })

    def test_max_bulk_len(self):
        """Debería haber un máximo de operaciones bulk posibles."""
        body = {
            'calles': [{}] * 101
        }

        self.assert_errors_match('/calles', [
            {
                (T.INVALID_BULK_LEN.value, 'body')
            }
        ], body=body)

    def assert_errors_match(self, url, errors_set, body=None, method=None):
        url = self.url_base + url
        if not method:
            method = 'POST' if body else 'GET'
        
        if method == 'POST':
            resp = self.app.post(url, json=body)
        elif method == 'GET':
            resp = self.app.get(url)
        else:
            raise ValueError('Método HTTP desconocido.')

        if resp.status_code == 200:
            raise Exception('La petición no devolvió errores.')

        if method == 'POST':
            resp_errors = []
            for errors in resp.json['errores']:
                query_errors = {
                    (e['codigo_interno'], e['nombre_parametro'])
                    for e in errors
                }
                resp_errors.append(query_errors)
        else:
            resp_errors = {
                (e['codigo_interno'], e['nombre_parametro'])
                for e in resp.json['errores']
            }

        self.assertEqual(errors_set, resp_errors)
