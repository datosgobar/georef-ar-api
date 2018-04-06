import unittest
from service import app
from . import SearchEntitiesTest, asciifold

VALID_ADDRESS = 'Corrientes 1000'

class SearchAddressesTest(SearchEntitiesTest):
    """Pruebas de búsqueda por dirección."""

    def setUp(self):
        self.endpoint = '/api/v1.0/direcciones'
        self.entity = 'direcciones'
        super().setUp()

    @unittest.skip('Parámetro max de direcciones no funciona correctamente')
    def test_max_results_returned(self):
        """La cantidad máxima de resultados debe ser configurable."""
        lengths = [1, 2, 4]
        results_lengths = [
            len(self.get_response({
                'max': length,
                'direccion': VALID_ADDRESS
            }))
            for length in lengths
        ]

        self.assertListEqual(lengths, results_lengths)

    def test_id_length(self):
        """El ID de la entidad debe tener la longitud correcta."""
        data = self.get_response({'direccion': VALID_ADDRESS})[0]
        self.assertTrue(len(data['id']) == 13)

    def test_default_results_fields(self):
        """Las entidades devueltas deben tener los campos default."""
        data = self.get_response({'direccion': VALID_ADDRESS})[0]
        fields = sorted([
            'altura',
            'departamento',
            'id',
            'localidad',
            'nombre',
            'nomenclatura',
            'observaciones',
            'provincia',
            'tipo'
        ])
        self.assertListEqual(fields, sorted(data.keys()))

    @unittest.skip('Parámetro campos de direcciones no funciona correctamente')
    def test_filter_results_fields(self):
        """Los campos de las direcciones devueltas deben ser filtrables."""
        fields_lists = [
            ['altura', 'nombre'],
            ['nomenclatura', 'nombre'],
            ['id', 'observaciones'],
            ['tipo', 'provincia', 'localidad', 'id']
        ]
        fields_results = []

        for fields in fields_lists:
            fields = sorted(fields)
            data = self.get_response({
                'campos': ','.join(fields),
                'direccion': VALID_ADDRESS
            })
            fields_results.append(sorted(data[0].keys()))

        self.assertListEqual(fields_lists, fields_results)

    def test_empty_params(self):
        """Los parámetros que esperan valores no pueden tener valores
        vacíos."""
        params = ['direccion', 'tipo', 'localidad', 'departamento', 'provincia', 
            'max', 'fuente', 'campos']
        self.assert_empty_params_return_400(params)

    def test_unknown_param_returns_400(self):
        """El endpoint no debe aceptar parámetros desconocidos."""
        self.assert_unknown_param_returns_400()


if __name__ == '__main__':
    unittest.main()
