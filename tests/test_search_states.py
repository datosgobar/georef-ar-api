from . import SearchEntitiesTest, asciifold
import random
import unittest


STATES = [
    (['54'], 'MISIONES'),
    (['74'], 'SAN LUIS'),
    (['86'], 'SANTIAGO DEL ESTERO'),
    (['94'], 'TIERRA DEL FUEGO, ANTÁRTIDA E ISLAS DEL ATLÁNTICO SUR'),
    (['18'], 'CORRIENTES'),
    (['30'], 'ENTRE RÍOS'),
    (['34'], 'FORMOSA'),
    (['38'], 'JUJUY'),
    (['46'], 'LA RIOJA'),
    (['82'], 'SANTA FE'),
    (['06'], 'BUENOS AIRES'),
    (['14'], 'CÓRDOBA'),
    (['22'], 'CHACO'),
    (['58'], 'NEUQUÉN'),
    (['78'], 'SANTA CRUZ'),
    (['02'], 'CIUDAD AUTÓNOMA DE BUENOS AIRES'),
    (['26'], 'CHUBUT'),
    (['50'], 'MENDOZA'),
    (['62'], 'RÍO NEGRO'),
    (['70'], 'SAN JUAN'),
    (['10'], 'CATAMARCA'),
    (['42'], 'LA PAMPA'),
    (['66'], 'SALTA'),
    (['90'], 'TUCUMÁN')
]


class SearchStatesTest(SearchEntitiesTest):
    """Pruebas de búsqueda de provincias."""

    def setUp(self):
        self.endpoint = '/api/v1.0/provincias'
        self.entity = 'provincias'
        super().setUp()

    def test_24_states_present(self):
        """Deben existir 24 provincias."""
        data = self.get_response()
        self.assertEqual(len(data), 24)

    def test_max_results_returned(self):
        """La cantidad máxima de resultados debe ser configurable."""
        lengths = [1, 5, 20, 24]
        results_lengths = [
            len(self.get_response({'max': length}))
            for length in lengths
        ]

        self.assertListEqual(lengths, results_lengths)

    def test_id_length(self):
        """El ID de la entidad debe tener la longitud correcta."""
        data = self.get_response({'max': 1})[0]
        self.assertTrue(len(data['id']) == 2)

    def test_id_search(self):
        """La búsqueda por ID debe devolver la provincia correspondiente."""
        data = self.get_response({'id': '06'})
        self.assertListEqual([p['nombre'] for p in data], ['BUENOS AIRES'])

    def test_default_results_fields(self):
        """Las entidades devueltas deben tener los campos default."""
        data = self.get_response({'max': 1})[0]
        fields = sorted(['id', 'lat', 'lon', 'nombre', 'fuente'])
        self.assertListEqual(fields, sorted(data.keys()))

    def test_filter_results_fields(self):
        """Los campos de las provincias devueltas deben ser filtrables."""
        fields_lists = [
            ['fuente', 'id', 'nombre'],
            ['fuente', 'id', 'lat', 'lon', 'nombre'],
            ['fuente', 'id', 'lat', 'nombre']
        ]
        fields_results = []

        for fields in fields_lists:
            data = self.get_response({'campos': ','.join(fields), 'max': 1})
            fields_results.append(sorted(data[0].keys()))

        self.assertListEqual(fields_lists, fields_results)

    def test_name_ordering(self):
        """Los resultados deben poder ser ordenados por nombre."""
        expected = [p[1] for p in STATES]

        expected.sort(key=asciifold)
        data = [p['nombre'] for p in self.get_response({'orden': 'nombre'})]

        self.assertListEqual(expected, data)

    def test_id_ordering(self):
        """Los resultados deben poder ser ordenados por ID."""
        expected = [p[0][0] for p in STATES]
        expected.sort()
        data = [p['id'] for p in self.get_response({'orden': 'id'})]

        self.assertListEqual(expected, data)

    def test_name_exact_search(self):
        """La búsqueda por nombre exacto debe devolver las provincias
         correspondientes."""
        self.assert_name_search_id_matches(STATES, exact=True)

    def test_name_exact_search_ignores_case(self):
        """La búsqueda por nombre exacto debe ignorar mayúsculas y
        minúsculas."""
        expected = [
            (['54'], 'MISIONES'),
            (['54'], 'misiones'),
            (['54'], 'Misiones'),
            (['54'], 'MiSiOnEs')
        ]

        self.assert_name_search_id_matches(expected, exact=True)

    def test_name_exact_search_ignores_tildes(self):
        """La búsqueda por nombre exacto debe ignorar tildes."""
        expected = [
            (['30'], 'entre rios'),
            (['30'], 'entre ríos'),
            (['30'], 'ENTRE RIOS'),
            (['30'], 'ENTRE RÍOS')
        ]

        self.assert_name_search_id_matches(expected, exact=True)

    def test_id_invalid_search(self):
        """La búsqueda por ID debe devolver error 400 cuando se
        utiliza un ID no válido."""
        status = self.get_response(params={'id': 99999}, status_only=True)
        self.assertEqual(status, 400)

    def test_short_id_search(self):
        """La búsqueda por ID debe devolver la entidad correcta incluso si
        se omiten ceros iniciales."""
        data = self.get_response({'id': '2'})
        self.assertTrue(data[0]['id'] == '02')

    def test_name_exact_gibberish_search(self):
        """La búsqueda por nombre exacto debe devolver 0 resultados cuando se
        utiliza un nombre no existente."""
        data = self.get_response({'nombre': 'FoobarFoobar', 'exacto': 1})
        self.assertTrue(len(data) == 0)

    def test_name_gibberish_search(self):
        """La búsqueda por nombre aproximado debe devolver 0 resultados cuando
        se utiliza un nombre no aproximable."""
        data = self.get_response({'nombre': 'FoobarFoobar'})
        self.assertTrue(len(data) == 0)

    def test_name_search_fuzziness(self):
        """La búsqueda por nombre aproximado debe tener una tolerancia
        de AUTO:4,8."""
        expected = [
            (['18'], 'rrientes'),      # -2 caracteres (de 8+)
            (['18'], 'orrientes'),     # -1 caracteres (de 8+)
            (['18'], 'cCorrientes'),   # +1 caracteres (de 8+)
            (['18'], 'cCorrientesS'),  # +2 caracteres (de 8+)
            (['38'], 'ujuy'),       # -1 caracteres (de 4-7)
            (['38'], 'jJujuy'),     # +1 caracteres (de 4-7)
            (['66'], 'alta'),       # -1 caracteres (de 4-7)
            (['66'], 'sSalta')      # +1 caracteres (de 4-7)
        ]

        self.assert_name_search_id_matches(expected)

    def test_name_search_autocompletes(self):
        """La búsqueda por nombre aproximado debe también actuar como
        autocompletar cuando la longitud de la query es >= 4."""
        expected = [
            (['54'], 'Misi'),
            (['54'], 'Misio'),
            (['54'], 'Mision'),
            (['54'], 'Misione'),
            (['86'], 'Santiag'),
            (['86'], 'Santiago'),
            (['86'], 'Santiago d'),
            (['86'], 'Santiago de'),
            (['86'], 'Santiago del'),
            (['86'], 'Santiago del E'),
            (['86'], 'Santiago del Es'),
            (['86'], 'Santiago del Est'),
            (['86'], 'Santiago del Este'),
            (['86'], 'Santiago del Ester'),
            (['02'], 'Ciud'),
            (['02'], 'Ciuda'),
            (['02'], 'Ciudad'),
            (['02'], 'Ciudad A'),
            (['02'], 'Ciudad Au'),
            (['02'], 'Ciudad Aut'),
            (['02'], 'Ciudad Auto'),
            (['02'], 'Ciudad Auton'),
            (['02'], 'Ciudad Autono'),
            (['90'], 'Tucu'),
            (['90'], 'Tucum'),
            (['90'], 'Tucuma')
        ]

        self.assert_name_search_id_matches(expected)

    def test_name_search_synonyms(self):
        """La búsqueda por nombre aproximado debe intercambiar términos
        equivalentes."""
        expected = [
            (['02'], 'CABA'),
            (['02'], 'Capital Federal'),
            (['02'], 'C.A.B.A.'),
            (['02'], 'Ciudad Autónoma de Buenos Aires'),
            (['06'], 'BsAs'),
            (['06'], 'Bs.As.'),
            (['94'], 'tdf'),
            (['86'], 'stgo del estero')
        ]

        self.assert_name_search_id_matches(expected)

    def test_name_search_stopwords(self):
        """La búsqueda por nombre aproximado debe ignorar stopwords."""
        expected = [
            (['46'], 'Rioja'),
            (['46'], 'La Rioja'),
            (['46'], 'La La Rioja'),
            (['46'], 'Los Rioja de'),
            (['02'], 'La Ciudad Autónoma de los la el Buenos Aires'),
            (['02'], 'Los Ciudad Autónoma de Buenos Aires los y e del')
        ]

        self.assert_name_search_id_matches(expected)

    def test_empty_params(self):
        """Los parámetros que esperan valores no pueden tener valores
        vacíos."""
        params = ['id', 'nombre', 'orden', 'campos', 'max', 'formato']
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
            'nombre': 'CATAMARCA'
        }

        body = {
            'provincias': [query] * req_len
        }

        results = self.get_response(method='POST', body=body)
        self.assertEqual(len(results), req_len)

    def test_bulk_basic(self):
        """La búsqueda de una query sin parámetros debería funcionar
        correctamente."""
        results = self.get_response(method='POST', body={
            'provincias': [{}]
        })

        first = results[0]
        self.assertTrue(
            len(results) == 1 and len(first['provincias']) == len(STATES))

    def test_bulk_equivalent(self):
        """Los resultados de una query envíada vía bulk deberían ser idénticos a
        los resultados de una query individual (GET)."""
        queries = [
            {
                'nombre': 'CATAMARCA'
            },
            {
                'id': '02'
            },
            {
                'max': 1
            },
            {
                'campos': 'id,nombre'
            },
            {
                'orden': 'nombre'
            },
            {
                'exacto': True,
                'nombre': 'BUENOS AIRES'
            }
        ]

        individual_results = []
        for query in queries:
            individual_results.append({
                'provincias': self.get_response(params=query)
            })

        bulk_results = self.get_response(method='POST', body={
            'provincias': queries
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
            'nombre': 'santa',
            'campos': 'id,lat'
        })

    def test_empty_csv_valid(self):
        """Una consulta CSV con respuesta vacía debería ser CSV válido."""
        self.assert_valid_csv({
            'nombre': 'foobarfoobar'
        })

    def test_geojson_format(self):
        """Se debería poder obtener resultados en formato
        GEOJSON (sin parámetros)."""
        self.assert_valid_geojson()

    def test_geojson_format_query(self):
        """Se debería poder obtener resultados en formato
        GEOJSON (con parámetros)."""
        self.assert_valid_geojson({
            'nombre': 'rio',
            'max': 10
        })


if __name__ == '__main__':
    unittest.main()
