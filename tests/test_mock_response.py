from service import formatter
from . import GeorefMockTest


class ResponsesTest(GeorefMockTest):
    def setUp(self):
        super().setUp()
        self.set_msearch_results([])

    def test_params_present(self):
        """Los parámetros enviados a la API deberían estar presentes bajo el
        valor 'parametros'."""
        resp = self.get_response(
            return_value='full',
            endpoint='/api/provincias',
            params={
                'id': '02',
                'max': 1,
                'aplanar': True,
                'orden': 'id',
                'interseccion': 'departamento:02000',
                'campos': 'nombre, id'
            }
        )

        resp['parametros']['campos'].sort()
        self.assertDictEqual(resp['parametros'], {
            'id': ['02'],
            'max': 1,
            'aplanar': True,
            'orden': 'id',
            'interseccion': {
                'departamentos': ['02000']
            },
            'campos': ['id', 'nombre']
        })

    def test_params_present_address(self):
        """Los parámetros enviados a la API deberían estar presentes bajo el
        valor 'parametros' (/direcciones)."""
        resp = self.get_response(
            return_value='full',
            endpoint='/api/direcciones',
            params={
                'direccion': 'Mitre N° 33 2B e/ Calle 11 y Sarmiento',
                'max': 1,
                'provincia': '6',
                'formato': 'json'
            }
        )

        self.assertDictEqual(resp['parametros'], {
            'direccion': {
                'altura': {
                    'unidad': 'N°',
                    'valor': '33'
                },
                'piso': '2B',
                'calles': ['Mitre', 'Calle 11', 'Sarmiento'],
                'tipo': 'entre_calles'
            },
            'max': 1,
            'provincia': ['06'],
            'formato': 'json'
        })

    def test_params_present_xml(self):
        """Los parámetros enviados a la API deberían estar presentes bajo el
        valor 'parametros' (formato XML)."""
        params = {
            'id': '1401401027080',
            'max': 1,
            'aplanar': True,
            'orden': 'id',
            'interseccion': 'departamento:02000'
        }

        json_resp = self.get_response(endpoint='/api/calles', params=params,
                                      return_value='full')
        json_resp['parametros']['formato'] = 'xml'
        json_as_xml = formatter.value_to_xml('parametros',
                                             json_resp['parametros'],
                                             list_item_default='item')

        params['formato'] = 'xml'
        xml_resp = self.get_response(endpoint='/api/calles', params=params)
        xml_params = xml_resp.find('resultado').find('parametros')

        self.assert_xml_equal(json_as_xml, xml_params)
