import unittest
from service import formatter
import random
from . import SearchEntitiesTest


class SearchStreetsTest(SearchEntitiesTest):
    """
    Pruebas de búsqueda de calles.

    Ir al archivo test_addresses.py para ver los tests de búsqueda de calles
    por dirección (nombre + altura).
    """

    def setUp(self):
        self.endpoint = '/api/v1.0/calles'
        self.entity = 'calles'
        super().setUp()

    def test_max_results_returned(self):
        """La cantidad máxima de resultados debe ser configurable."""
        lengths = [1, 4, 9, 10, 20]
        results_lengths = [
            len(self.get_response({'max': length}))
            for length in lengths
        ]

        self.assertListEqual(lengths, results_lengths)

    def test_id_length(self):
        """El ID de la entidad debe tener la longitud correcta."""
        data = self.get_response({'max': 1})[0]
        self.assertTrue(len(data['id']) == 13)

    def test_default_results_fields(self):
        """Las entidades devueltas deben tener los campos default."""
        data = self.get_response({'max': 1})[0]
        fields = sorted([
            'departamento',
            'fuente',
            'id',
            'altura_fin_derecha',
            'altura_fin_izquierda',
            'altura_inicio_derecha',
            'altura_inicio_izquierda',
            'nombre',
            'nomenclatura',
            'provincia',
            'tipo'
        ])
        self.assertListEqual(fields, sorted(data.keys()))

    def test_filter_results_fields(self):
        """Los campos de las direcciones devueltas deben ser filtrables."""
        fields_lists = [
            ['fuente', 'id', 'nombre'],
            ['fuente', 'id', 'nombre', 'nomenclatura'],
            ['departamento.nombre', 'fuente', 'id', 'nombre'],
            ['fuente', 'id', 'altura_inicio_derecha', 'nombre'],
        ]
        fields_lists = [sorted(l) for l in fields_lists]
        fields_results = []

        for fields in fields_lists:
            data = self.get_response({
                'campos': ','.join(fields),
                'max': 1
            })
            formatter.flatten_dict(data[0], sep='.')
            fields_results.append(sorted(data[0].keys()))

        self.assertListEqual(fields_lists, fields_results)

    def assert_street_search_id_matches(self, term_matches, exact=False):
        results = []
        for code, query in term_matches:
            params = {'nombre': query, 'provincia': code[0][:2]}
            if exact:
                params['exacto'] = 1
            res = self.get_response(params)
            results.append(sorted([p['id'] for p in res]))

        self.assertListEqual([sorted(ids) for ids, _ in term_matches], results)

    def test_name_exact_gibberish_search(self):
        """La búsqueda exacta debe devolver 0 resultados cuando se utiliza un
        nombre no existente."""
        data = self.get_response({'nombre': 'FoobarFoobar', 'exacto': 1})
        self.assertTrue(len(data) == 0)

    def test_search_road_type(self):
        """Se debe poder especificar el tipo de calle en la búsqueda."""
        validations = []
        road_types = [
            ('AV', 'avenida'),
            ('RUTA', 'ruta'),
            ('AUT', 'autopista'),
            ('CALLE', 'calle'),
            ('PJE', 'pasaje')
        ]

        for road_type, road_type_long in road_types:
            res = self.get_response({
                'tipo': road_type_long,
                'max': 100
            })

            validations.append(len(res) > 0)
            validations.append(all(
                road['tipo'] == road_type for road in res
            ))

        assert(validations and all(validations))

    def test_id_search(self):
        """Se debería poder buscar calles por ID."""
        identifier = '8208416001280'
        data = self.get_response({'id': identifier})[0]

        self.assertEqual(identifier, data['id'])

    def test_flatten_results(self):
        """Los resultados se deberían poder obtener en formato aplanado."""
        data = self.get_response({'max': 1, 'aplanar': True})[0]

        self.assertTrue(all([
            not isinstance(v, dict) for v in data.values()
        ]) and data)

    def test_empty_params(self):
        """Los parámetros que esperan valores no pueden tener valores
        vacíos."""
        params = ['nombre', 'tipo', 'departamento', 'provincia', 'max',
                  'campos']
        self.assert_empty_params_return_400(params)

    def test_unknown_param_returns_400(self):
        """El endpoint no debe aceptar parámetros desconocidos."""
        self.assert_unknown_param_returns_400()

    def test_bulk_empty_400(self):
        """La búsqueda bulk vacía debería retornar un error 400."""
        status = self.get_response(method='POST', body={}, status_only=True)
        self.assertEqual(status, 400)

    def test_bulk_response_len(self):
        """La longitud de la respuesta bulk debería ser igual a la cantidad
        de queries envíadas."""
        req_len = random.randint(10, 20)
        query = {
            'nombre': 'SANTA FE'
        }

        body = {
            'calles': [query] * req_len
        }

        results = self.get_response(method='POST', body=body)
        self.assertEqual(len(results), req_len)

    def test_bulk_basic(self):
        """La búsqueda de una query sin parámetros debería funcionar
        correctamente."""
        results = self.get_response(method='POST', body={
            'calles': [{}]
        })

        first = results[0]
        self.assertTrue(len(results) == 1 and len(first['calles']) == 10)

    def test_bulk_equivalent(self):
        """Los resultados de una query envíada vía bulk deberían ser idénticos a
        los resultados de una query individual (GET)."""
        queries = [
            {
                'nombre': 'CORRIENTES'
            },
            {
                'tipo': 'avenida'
            },
            {
                'max': 3
            },
            {
                'id': '8208416001280'
            },
            {
                'campos': 'nombre,tipo'
            },
            {
                'provincia': '02'
            },
            {
                'departamento': '06805'
            },
            {
                'exacto': True,
                'nombre': 'LISANDRO DE LA TORRE'
            }
        ]

        individual_results = []
        for query in queries:
            individual_results.append({
                'calles': self.get_response(params=query)
            })

        bulk_results = self.get_response(method='POST', body={
            'calles': queries
        })

        self.assertEqual(individual_results, bulk_results)

    def test_json_format(self):
        """Por default, los resultados de una query deberían estar en
        formato JSON."""
        default_response = self.get_response()
        json_response = self.get_response({'formato': 'json'})
        self.assertEqual(default_response, json_response)

    def test_csv_format(self):
        """Se debería poder obtener resultados en formato
        CSV (sin parámetros)."""
        self.assert_valid_csv()

    def test_csv_format_query(self):
        """Se debería poder obtener resultados en formato
        CSV (con parámetros)."""
        self.assert_valid_csv({
            'nombre': 'SANTA FE',
            'campos': 'nombre,id,tipo'
        })

    def test_csv_fields(self):
        """Una consulta CSV debería tener ciertos campos, ordenados de una
        forma específica."""
        resp = self.get_response({'formato': 'csv'}, fmt='csv')
        headers = next(resp)
        self.assertListEqual(headers, ['calle_id',
                                       'calle_nombre',
                                       'calle_altura_inicio_derecha',
                                       'calle_altura_inicio_izquierda',
                                       'calle_altura_fin_derecha',
                                       'calle_altura_fin_izquierda',
                                       'calle_nomenclatura',
                                       'calle_tipo',
                                       'provincia_id',
                                       'provincia_nombre',
                                       'departamento_id',
                                       'departamento_nombre',
                                       'calle_fuente'])


if __name__ == '__main__':
    unittest.main()
