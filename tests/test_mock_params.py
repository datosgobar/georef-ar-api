from random import choice
from service import constants
from service.params import ParamErrorType as T
from service.formatter import value_to_xml
from . import GeorefMockTest

ENDPOINTS = [
    '/provincias',
    '/departamentos',
    '/municipios',
    '/localidades',
    '/calles'
]


class ParamParsingTest(GeorefMockTest):
    def setUp(self):
        self.url_base = '/api/v1.0'
        super().setUp()

    def test_404_response(self):
        """Se debería devolver un error 404 con contenido JSON en caso de
        intentar acceder a un recurso inexistente."""
        resp = self.app.get('/api/foobar')
        self.assertTrue(resp.status_code == 404 and 'errores' in resp.json)

    def test_bulk_no_json(self):
        """No se deberían aceptar operaciones bulk cuando el body HTTP
        no contiene JSON."""
        self.assert_errors_match('/provincias', [
            {(T.INVALID_BULK.value, 'provincias')}
        ], method='POST')

    def test_bulk_empty_json(self):
        """No se deberían aceptar operaciones bulk cuando el body HTTP
        contiene JSON vacío."""
        endpoint = choice(ENDPOINTS)

        self.assert_errors_match(endpoint, [
            {(T.INVALID_BULK.value, endpoint[1:])}
        ], method='POST', body={})

    def test_bulk_empty_json_locations(self):
        """No se deberían aceptar operaciones bulk cuando el body HTTP
        contiene JSON vacío."""
        self.assert_errors_match('/ubicacion', [
            {(T.INVALID_BULK.value, 'ubicaciones')}
        ], method='POST', body={})

    def test_bulk_empty(self):
        """No se deberían aceptar operaciones bulk vacías."""
        body = {
            'provincias': []
        }

        self.assert_errors_match('/municipios', [
            {(T.INVALID_BULK.value, 'municipios')}
        ], body=body)

    def test_bulk_invalid_type(self):
        """No se deberían aceptar operaciones bulk que no sean de
        tipo lista."""
        body = {
            'departamentos': 'foobar'
        }

        self.assert_errors_match('/departamentos', [
            {(T.INVALID_BULK.value, 'departamentos')}
        ], body=body)

    def test_bulk_invalid_root_element(self):
        """El elemento JSON de raíz debe ser un diccionario."""
        body = ['foobar']

        self.assert_errors_match('/departamentos', [
            {(T.INVALID_BULK.value, 'departamentos')}
        ], body=body)

    def test_bulk_invalid_item_type(self):
        """No se deberían aceptar operaciones bulk que contengan
        elementos que no sean objetos."""
        body = {
            'municipios': [{}, 1]
        }

        self.assert_errors_match('/municipios', [
            set(),
            {(T.INVALID_BULK_ENTRY.value, 'municipios')}
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

    def test_invalid_param_location(self):
        """El parámetro 'formato' solo se puede especificar vía querystring."""
        body = {
            'municipios': [
                {
                    'formato': 'csv'
                }
            ]
        }

        self.assert_errors_match('/municipios', [
            {(T.UNKNOWN_PARAM.value, 'formato')}
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

    def test_field_set_and_specific(self):
        """No se debería aceptar un conjunto de campos (por ejemplo, estandar)
        y campos específicos en una misma consulta."""
        self.assert_errors_match('/provincias?campos=estandar,id', {
            (T.INVALID_CHOICE.value, 'campos')
        })

    def test_field_invalid_prefix(self):
        """No se debería aceptar un prefijo arbitrario de un campo. Si se
        separa el nombre del campo por puntos, el prefijo debe ser igual
        a una o más de las partes concatenadas."""
        self.assert_errors_match('/calles?campos=altura.inic', {
            (T.INVALID_CHOICE.value, 'campos')
        })

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

    def test_string_list_repeated(self):
        """Los parámtros de tipo string list no deberían aceptar valores
        repetidos."""
        self.assert_errors_match('/localidades?campos=id,id', {
            (T.VALUE_ERROR.value, 'campos')
        })

    def test_id_param_length(self):
        """Los parámtros de tipo ID no deberían aceptar valores de longitud
        mayores a las especificadas."""
        self.assert_errors_match('/municipios?id=1111111', {
            (T.VALUE_ERROR.value, 'id')
        })

    def test_id_param_length_short(self):
        """Los parámtros de tipo ID no deberían aceptar valores de longitud
        menores a las de cierto rango de tolerancia."""
        self.assert_errors_match('/municipios?id=1111', {
            (T.VALUE_ERROR.value, 'id')
        })

    def test_id_param_digit(self):
        """Los parámtros de tipo ID no deberían aceptar valores no
        numéricos."""
        self.assert_errors_match('/calles?id=foobar', {
            (T.VALUE_ERROR.value, 'id')
        })

    def test_id_param_repeated(self):
        """Los parámtros de tipo ID no deberían aceptar listas con elementos
        repetidos."""
        self.assert_errors_match('/provincias?id=02,06,02', {
            (T.VALUE_ERROR.value, 'id')
        })

    def test_id_param_list_digit(self):
        """Los parámtros de tipo ID no deberían aceptar listas con elementos
        no-numéricos."""
        self.assert_errors_match('/provincias?id=54,14,foo,02', {
            (T.VALUE_ERROR.value, 'id')
        })

    def test_id_param_list_empty(self):
        """Los parámtros de tipo ID no deberían aceptar listas con elementos
        vacíos."""
        self.assert_errors_match('/provincias?id=54,14,,02', {
            (T.VALUE_ERROR.value, 'id')
        })

    def test_max_offset_sum(self):
        """La suma de los parámetros max e inicio debería estar limitada."""
        self.assert_errors_match(
            choice(ENDPOINTS) + '?max=4000&inicio=10000', {
                (T.INVALID_SET.value, 'max'),
                (T.INVALID_SET.value, 'inicio')
            })

    def test_max_offset(self):
        """El parámetro inicio debería tener un valor máximo permitido."""
        self.assert_errors_match(choice(ENDPOINTS) + '?inicio=100000', {
            (T.VALUE_ERROR.value, 'inicio')
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

    def test_big_int_param(self):
        """Los parámtros de tipo int no deberían aceptar strings que
        representen números por encima de los límites establecidos."""
        self.assert_errors_match(choice(ENDPOINTS) + '?max=5001', {
            (T.VALUE_ERROR.value, 'max')
        })

    def test_bulk_int_compound_param(self):
        """En bulk, el parámetro 'max' debe realizar validaciones a nivel
        conjunto de valores."""
        body = {
            'municipios': [
                {
                    'max': 4000
                },
                {
                    'max': 1000
                },
                {
                    'max': 1
                }
            ]
        }

        self.assert_errors_match('/municipios', [
            {(T.INVALID_SET.value, 'max')},
            {(T.INVALID_SET.value, 'max')},
            {(T.INVALID_SET.value, 'max')}
        ], body=body)

    def test_bulk_int_compound_param_individual_error(self):
        """En bulk, el parámetro 'max' debe realizar validaciones a nivel
        conjunto de valores, sólo si no existen errores a nivel consulta
        individuales."""
        body = {
            'municipios': [
                {
                    'max': 6000
                },
                {
                    'max': 1000
                },
                {
                    'max': "foobar"
                }
            ]
        }

        self.assert_errors_match('/municipios', [
            {(T.VALUE_ERROR.value, 'max')},
            set(),
            {(T.VALUE_ERROR.value, 'max')}
        ], body=body)

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
        """Un parámetro de dirección vacío no debería ser válido."""
        self.assert_errors_match('/direcciones?direccion=', {
            (T.VALUE_ERROR.value, 'direccion')
        })

    def test_max_bulk_len(self):
        """Debería haber un máximo de operaciones bulk posibles."""
        body = {
            'calles': [{}] * (constants.MAX_BULK_LEN + 1)
        }

        self.assert_errors_match('/calles', [
            {
                (T.INVALID_BULK_LEN.value, 'calles')
            }
        ], body=body)

    def test_invalid_intersection_empty(self):
        """El parámetro 'interseccion' no debería aceptar valores vacíos."""
        self.assert_errors_match('/provincias?interseccion=', {
            (T.VALUE_ERROR.value, 'interseccion')
        })

    def test_invalid_intersection_empty_list(self):
        """El parámetro 'interseccion' no debería aceptar listas de IDs
        vacías."""
        self.assert_errors_match('/provincias?interseccion=municipio:', {
            (T.VALUE_ERROR.value, 'interseccion')
        })

    def test_invalid_intersection_entity(self):
        """El parámetro 'interseccion' no debería aceptar tipos de entidades
        desconocidas."""
        self.assert_errors_match('/provincias?interseccion=foobar:1', {
            (T.VALUE_ERROR.value, 'interseccion')
        })

    def test_invalid_intersection_state(self):
        """El parámetro 'interseccion' no debería aceptar buscar entidades
        utilizando la misma entidad como argumento."""
        self.assert_errors_match('/provincias?interseccion=provincia:14', {
            (T.VALUE_ERROR.value, 'interseccion')
        })

    def test_invalid_intersection_department(self):
        """El parámetro 'interseccion' no debería aceptar buscar entidades
        utilizando la misma entidad como argumento."""
        self.assert_errors_match(
            '/departamentos?interseccion=departamento:90084', {
                (T.VALUE_ERROR.value, 'interseccion')
            }
        )

    def test_invalid_intersection_municipality(self):
        """El parámetro 'interseccion' no debería aceptar buscar entidades
        utilizando la misma entidad como argumento."""
        self.assert_errors_match(
            '/municipios?interseccion=municipio:900105', {
                (T.VALUE_ERROR.value, 'interseccion')
            }
        )

    def test_invalid_intersection_id_len(self):
        """El parámetro 'interseccion' debería comprobar la longitud de los
        IDs recibidos."""
        self.assert_errors_match('/provincias?interseccion=municipio:99', {
            (T.VALUE_ERROR.value, 'interseccion')
        })

    def test_invalid_intersection_id_empty(self):
        """El parámetro 'interseccion' no debería aceptar IDs vacíos."""
        self.assert_errors_match('/departamentos?interseccion=municipio:::', {
            (T.VALUE_ERROR.value, 'interseccion')
        })

    def test_invalid_intersection_id_repeated(self):
        """El parámetro 'interseccion' no debería aceptar IDs repetidos."""
        self.assert_errors_match(
            '/municipios?interseccion=departamento:90084:90084', {
                (T.VALUE_ERROR.value, 'interseccion')
            }
        )

    def test_invalid_intersection_empty_set(self):
        """El parámetro 'interseccion' no debería aceptar conjuntos
        entidad-IDs vacíos."""
        self.assert_errors_match('/municipios?interseccion=provincia:02,,,', {
            (T.VALUE_ERROR.value, 'interseccion')
        })

    def test_xml_error_unknown_param(self):
        """Se deberían generar errores al especificar parámetros no existentes
        (con formato=xml)."""
        self.assert_xml_errors_valid(choice(ENDPOINTS), {'foo': 'bar'})

    def test_xml_error_missing_param(self):
        """Se deberían generar errores al no especificar parámetros requeridos
        (con formato=xml)."""
        self.assert_xml_errors_valid('/direcciones', {})

    def test_xml_error_invalid_value(self):
        """Se deberían generar errores al especificar valores inválidos para
        parámetros (con formato=xml)."""
        self.assert_xml_errors_valid(choice(ENDPOINTS), {'id': 'foobar'})

    def assert_xml_errors_valid(self, endpoint, params):
        """Si se especifica formato=xml y se produce un error, los errores
        deben ser devueltos en formato XML y deben contener la misma
        información que cuando se utiliza JSON."""
        endpoint = self.url_base + endpoint

        json_resp = self.get_response(params=params, endpoint=endpoint,
                                      return_value='full', expect_status=[400])

        params['formato'] = 'xml'
        xml_resp = self.get_response(params=params, endpoint=endpoint,
                                     expect_status=[400])

        json_as_xml = value_to_xml('errores', json_resp['errores'],
                                   list_item_names={'ayuda': 'item'})

        self.assert_xml_equal(xml_resp.find('errores'), json_as_xml)

    def assert_errors_match(self, url, errors_set, body=None, method=None):
        url = self.url_base + url
        if not method:
            method = 'POST' if body else 'GET'

        resp = self.get_response(method=method, body=body, return_value='full',
                                 url=url, expect_status=[400, 404])

        if method == 'POST':
            resp_errors = []
            for errors in resp['errores']:
                query_errors = {
                    (e['codigo_interno'], e['nombre_parametro'])
                    for e in errors
                }
                resp_errors.append(query_errors)
        else:
            resp_errors = {
                (e['codigo_interno'], e['nombre_parametro'])
                for e in resp['errores']
            }

        self.assertEqual(errors_set, resp_errors)
