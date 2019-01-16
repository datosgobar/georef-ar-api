from service import formatter
from . import GeorefMockTest


class FormattingTest(GeorefMockTest):
    def test_fields_list_to_dict(self):
        """El resultado de fields_list_to_dict debería ser un diccionario
        equivalente a los valores de una lista, desaplanados."""
        fields = (
            'id',
            'nombre',
            'provincia.id',
            'provincia.nombre',
            'ubicacion.lat',
            'ubicacion.lon',
            'prueba.foo.bar',
            'prueba.foo.baz'
        )

        fields_dict = formatter.fields_list_to_dict(fields)
        self.assertEqual(fields_dict, {
            'id': True,
            'nombre': True,
            'provincia': {
                'id': True,
                'nombre': True
            },
            'ubicacion': {
                'lat': True,
                'lon': True
            },
            'prueba': {
                'foo': {
                    'bar': True,
                    'baz': True
                }
            }
        })

    def test_flatten_dict(self):
        """Se debería aplanar un diccionario correctamente."""
        original = {
            'provincia': {
                'id': '06',
                'nombre': 'BUENOS AIRES'
            },
            'foo': 'bar'
        }

        formatter.flatten_dict(original)
        self.assertEqual(original, {
            'provincia_id': '06',
            'provincia_nombre': 'BUENOS AIRES',
            'foo': 'bar'
        })

    def test_flatten_dict_max_depth(self):
        """El aplanado de diccionarios debería fallar con diccionarios
        demasiado profundos."""
        deep_dict = {
            'a': {
                'b': {
                    'c': {
                        'd': {}
                    }
                }
            }
        }

        with self.assertRaises(RuntimeError):
            formatter.flatten_dict(deep_dict)

    def test_flatten_dict_max_depth_circular(self):
        """La conversión a XML debería fallar con diccionarios o listas
        con referencias circulares."""
        c_dict = {}
        c_dict['a'] = c_dict

        with self.assertRaises(RuntimeError):
            formatter.flatten_dict(c_dict)

    def test_filter_result_fields(self):
        """Se debería poder filtrar los campos de un diccionario, utilizando
        otro diccionario para especificar cuáles campos deberían ser
        mantenidos."""
        result = {
            'simple': 'foo',
            'removed': 'foo',
            'nested': {
                'field1': 'foo',
                'field2': 'foo',
                'removed': 'foo',
                'nested2': {
                    'field1': 'foo',
                    'removed': 'foo'
                }
            }
        }

        fields = (
            'simple',
            'nested.field1',
            'nested.field2',
            'nested.nested2.field1'
        )

        formatter.filter_result_fields(result,
                                       formatter.fields_list_to_dict(fields))
        self.assertEqual(result, {
            'simple': 'foo',
            'nested': {
                'field1': 'foo',
                'field2': 'foo',
                'nested2': {
                    'field1': 'foo'
                }
            }
        })

    def test_xml_max_depth(self):
        """La conversión a XML debería fallar con diccionarios demasiado
        profundos."""
        deep_dict = {
            'a': {
                'b': {
                    'c': {
                        'd': {}
                    }
                }
            }
        }

        with self.assertRaises(RuntimeError):
            formatter.value_to_xml('test', deep_dict, max_depth=3)

    def test_xml_max_depth_circular(self):
        """La conversión a XML debería fallar con diccionarios o listas
        con referencias circulares."""
        c_dict = {}
        c_dict['a'] = c_dict

        with self.assertRaises(RuntimeError):
            formatter.value_to_xml('test', c_dict)

    def test_xml_structure(self):
        """El nodo raíz de todas las respuestas XML debería ser el tag
        'georef-ar-api'."""
        self.set_msearch_results([])
        resp = self.get_response(params={'formato': 'xml'},
                                 endpoint='/api/provincias',
                                 entity='provincias')

        self.assertEqual(resp.tag, 'georef-ar-api')
