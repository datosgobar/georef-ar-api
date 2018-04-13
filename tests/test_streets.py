import unittest
from service import app
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
            'id',
            'fin_derecha',
            'fin_izquierda',
            'inicio_derecha',
            'inicio_izquierda',
            'nombre',
            'nomenclatura',
            'observaciones',
            'provincia',
            'tipo'
        ])
        self.assertListEqual(fields, sorted(data.keys()))

    def test_filter_results_fields(self):
        """Los campos de las direcciones devueltas deben ser filtrables."""
        fields_lists = [
            ['id', 'nombre', 'observaciones'],
            ['id', 'nombre', 'nomenclatura', 'observaciones'],
            ['departamento', 'id', 'nombre', 'observaciones'],
            ['id', 'inicio_derecha', 'nombre', 'observaciones'],
        ]
        fields_results = []

        for fields in fields_lists:
            data = self.get_response({
                'campos': ','.join(fields),
                'max': 1
            })
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

    def test_empty_params(self):
        """Los parámetros que esperan valores no pueden tener valores
        vacíos."""
        params = ['nombre', 'tipo', 'departamento', 'provincia', 'max',
            'campos']
        self.assert_empty_params_return_400(params)

    def test_unknown_param_returns_400(self):
        """El endpoint no debe aceptar parámetros desconocidos."""
        self.assert_unknown_param_returns_400()


if __name__ == '__main__':
    unittest.main()
