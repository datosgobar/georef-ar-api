import random
import unittest
from . import SearchEntitiesTest, asciifold
from service import formatter
from .test_search_states import STATES


DEPARTMENTS = [
    (['54063'], 'IGUAZÚ'),
    (['74042'], 'GOBERNADOR DUPUY'),
    (['86021'], 'ATAMISQUI'),
    (['94014'], 'USHUAIA'),
    (['18161'], 'SAN ROQUE'),
    (['30063'], 'ISLAS DEL IBICUY'),
    (['34042'], 'PILAGÁS'),
    (['38042'], 'PALPALÁ'),
    (['46119'], 'SAN BLAS DE LOS SAUCES'),
    (['82028'], 'VILLA CONSTITUCIÓN'),
    (['06266'], 'EXALTACIÓN DE LA CRUZ'),
    (['14154'], 'SOBREMONTE'),
    (['22161'], 'TAPENAGÁ'),
    (['58091'], 'PEHUENCHES'),
    (['78042'], 'MAGALLANES'),
    (['02084'], 'COMUNA 12'),
    (['26014'], 'CUSHAMEN'),
    (['50119'], 'TUNUYÁN'),
    (['62056'], 'ÑORQUINCO'),
    (['70021'], 'CALINGASTA'),
    (['10063'], 'FRAY MAMERTO ESQUIÚ'),
    (['42056'], 'CHAPALEUFÚ'),
    (['66021'], 'CAFAYATE'),
    (['90021'], 'CHICLIGASTA'),
    (['50035', '74049', '06413'], 'JUNÍN')
]


class SearchDepartmentsTest(SearchEntitiesTest):
    """Pruebas de búsqueda de departamentos."""

    def setUp(self):
        self.endpoint = '/api/v1.0/departamentos'
        self.entity = 'departamentos'
        super().setUp()

    def test_max_results_returned(self):
        """La cantidad máxima de resultados debe ser configurable."""
        lengths = [1, 5, 25, 50]
        results_lengths = [
            len(self.get_response({'max': length}))
            for length in lengths
        ]

        self.assertListEqual(lengths, results_lengths)

    def test_id_length(self):
        """El ID de la entidad debe tener la longitud correcta."""
        data = self.get_response({'max': 1})[0]
        self.assertTrue(len(data['id']) == 5)

    def test_id_search(self):
        """La búsqueda por ID debe devolver el depto. correspondiente."""
        data = self.get_response({'id': '06077'})
        self.assertListEqual([p['nombre'] for p in data], ['ARRECIFES'])

    def test_id_invalid_search(self):
        """La búsqueda por ID debe devolver error 400 cuando se
        utiliza un ID no válido."""
        status = self.get_response(params={'id': 999999}, status_only=True)
        self.assertEqual(status, 400)

    def test_short_id_search(self):
        """La búsqueda por ID debe devolver la entidad correcta incluso si
        se omiten ceros iniciales."""
        data = self.get_response({'id': '2007'})
        self.assertTrue(data[0]['id'] == '02007')

    def test_default_results_fields(self):
        """Las entidades devueltas deben tener los campos default."""
        data = self.get_response({'max': 1})[0]
        fields = sorted(['fuente', 'id', 'lat', 'lon', 'nombre', 'provincia'])
        self.assertListEqual(fields, sorted(data.keys()))

    def test_filter_results_fields(self):
        """Los campos de los deptos. devueltos deben ser filtrables."""
        fields_lists = [
            ['fuente', 'id', 'nombre'],
            ['fuente', 'id', 'lat', 'lon', 'nombre'],
            ['fuente', 'id', 'lat', 'nombre'],
            ['fuente', 'id', 'lat', 'nombre', 'provincia.id',
             'provincia.nombre']
        ]
        fields_results = []

        for fields in fields_lists:
            data = self.get_response({'campos': ','.join(fields), 'max': 1})
            formatter.flatten_dict(data[0], sep='.')
            fields_results.append(sorted(data[0].keys()))

        self.assertListEqual(fields_lists, fields_results)

    def test_name_ordering(self):
        """Los resultados deben poder ser ordenados por nombre."""
        data = [
            asciifold(dep['nombre'])
            for dep
            in self.get_response({'orden': 'nombre', 'max': 25})
        ]

        self.assertListEqual(sorted(data), data)

    def test_id_ordering(self):
        """Los resultados deben poder ser ordenados por ID."""
        data = [
            dep['id']
            for dep
            in self.get_response({'orden': 'id', 'max': 25})
        ]

        self.assertListEqual(sorted(data), data)

    def test_name_exact_search(self):
        """La búsqueda por nombre exacto debe devolver los deptos.
         correspondientes."""
        self.assert_name_search_id_matches(DEPARTMENTS, exact=True)

    def test_name_exact_search_ignores_case(self):
        """La búsqueda por nombre exacto debe ignorar mayúsculas y
        minúsculas."""
        expected = [
            (['90091'], 'SIMOCA'),
            (['90091'], 'Simoca'),
            (['90091'], 'simoca'),
            (['90091'], 'SiMoCa')
        ]

        self.assert_name_search_id_matches(expected, exact=True)

    def test_name_exact_search_ignores_tildes(self):
        """La búsqueda por nombre exacto debe ignorar tildes."""
        expected = [
            (['90007'], 'BURRUYACÚ'),
            (['90007'], 'burruyacú'),
            (['90007'], 'BURRUYACU'),
            (['90007'], 'burruyacu')
        ]

        self.assert_name_search_id_matches(expected, exact=True)

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
            (['90021'], 'ICLIGASTA'),        # -2 caracteres (de 8+)
            (['90021'], 'HICLIGASTA'),       # -1 caracteres (de 8+)
            (['90021'], 'cCHICLIGASTA'),     # +1 caracteres (de 8+)
            (['90021'], 'ccCHICLIGASTA'),    # +2 caracteres (de 8+)
            (['78042'], 'GALLANES'),      # -2 caracteres (de 8+)
            (['78042'], 'AGALLANES'),     # -1 caracteres (de 8+)
            (['78042'], 'mMAGALLANES'),   # +1 caracteres (de 8+)
            (['78042'], 'mMAGALLANESs'),  # +2 caracteres (de 8+)
            (['54063'], 'GUAZÚ'),         # -1 caracteres (de 4-7)
            (['54063'], 'iIGUAZÚ')        # +1 caracteres (de 4-7)
        ]

        self.assert_name_search_id_matches(expected)

    def test_name_search_autocompletes(self):
        """La búsqueda por nombre aproximado debe también actuar como
        autocompletar cuando la longitud de la query es >= 4."""
        expected = [
            (['66063'], 'Guachipas'),
            (['66063'], 'Guachipa'),
            (['66063'], 'Guachip'),
            (['66063'], 'Guachi'),
            (['66063'], 'Guach'),
            (['66063'], 'Guac'),
            (['06277', '26028'], 'Florentino A'),
            (['06277', '26028'], 'Florentino Am'),
            (['06277', '26028'], 'Florentino Ame'),
            (['06277', '26028'], 'Florentino Ameg'),
            (['06277', '26028'], 'Florentino Amegh'),
            (['06277', '26028'], 'Florentino Ameghi')
        ]

        self.assert_name_search_id_matches(expected)

    def test_name_search_stopwords(self):
        """La búsqueda por nombre aproximado debe ignorar stopwords."""
        expected = [
            (['06266'], 'EXALTACIÓN DE LA CRUZ'),
            (['06266'], 'EXALTACIÓN CRUZ'),
            (['06266'], 'EXALTACIÓN DE CRUZ'),
            (['06266'], 'EXALTACIÓN LA CRUZ'),
            (['06266'], 'EXALTACIÓN DE DE LA LA CRUZ'),
        ]

        self.assert_name_search_id_matches(expected)

    def test_code_prefix(self):
        """Los IDs de los departamentos deben comenzar con el ID de sus
        provincias."""
        data = self.get_response({'max': 25})
        results = [
            dept['id'].startswith(dept['provincia']['id'])
            for dept in data
        ]

        self.assertTrue(all(results) and results)

    def test_search_by_state(self):
        """Se debe poder buscar departamentos por provincia."""
        state = random.choice(STATES)
        state_id, state_name = state[0][0], state[1]

        data = self.get_response({'provincia': state_id})
        data.extend(self.get_response({'provincia': state_name}))
        data.extend(self.get_response({'provincia': state_name, 'exacto': 1}))

        results = [dept['id'].startswith(state_id) for dept in data]
        self.assertTrue(all(results) and results)

    def test_empty_params(self):
        """Los parámetros que esperan valores no pueden tener valores
        vacíos."""
        params = ['id', 'nombre', 'orden', 'campos', 'max', 'formato',
                  'provincia']
        self.assert_empty_params_return_400(params)

    def test_unknown_param_returns_400(self):
        """El endpoint no debe aceptar parámetros desconocidos."""
        self.assert_unknown_param_returns_400()

    def test_flat_results(self):
        """El parametro aplanar deberia aplanar los resultados devueltos."""
        self.assert_flat_results()

    def test_bulk_empty_400(self):
        """La búsqueda bulk vacía debería retornar un error 400."""
        status = self.get_response(method='POST', body={}, status_only=True)
        self.assertEqual(status, 400)

    def test_bulk_response_len(self):
        """La longitud de la respuesta bulk debería ser igual a la cantidad
        de queries envíadas."""
        req_len = random.randint(10, 20)
        query = {
            'nombre': 'MARTIN'
        }

        body = {
            'departamentos': [query] * req_len
        }

        results = self.get_response(method='POST', body=body)
        self.assertEqual(len(results), req_len)

    def test_bulk_basic(self):
        """La búsqueda de una query sin parámetros debería funcionar
        correctamente."""
        results = self.get_response(method='POST', body={
            'departamentos': [{}]
        })

        first = results[0]
        self.assertTrue(
            len(results) == 1 and len(first['departamentos']) == 10)

    def test_bulk_equivalent(self):
        """Los resultados de una query envíada vía bulk deberían ser idénticos a
        los resultados de una query individual (GET)."""
        queries = [
            {
                'nombre': 'MARTIN'
            },
            {
                'id': '46119'
            },
            {
                'max': 1
            },
            {
                'campos': 'id,nombre'
            },
            {
                'provincia': '14'
            },
            {
                'orden': 'nombre'
            },
            {
                'exacto': True,
                'nombre': 'SAN BLAS DE LOS SAUCES'
            }
        ]

        individual_results = []
        for query in queries:
            individual_results.append({
                'departamentos': self.get_response(params=query)
            })

        bulk_results = self.get_response(method='POST', body={
            'departamentos': queries
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
            'nombre': 'TRES',
            'campos': 'nombre,provincia.id'
        })

    def test_geojson_format(self):
        """Se debería poder obtener resultados en formato
        GEOJSON (sin parámetros)."""
        self.assert_valid_geojson()

    def test_geojson_format_query(self):
        """Se debería poder obtener resultados en formato
        GEOJSON (con parámetros)."""
        self.assert_valid_geojson({
            'nombre': 'BELGRANO',
            'max': 10
        })

    def test_csv_fields(self):
        """Una consulta CSV debería tener ciertos campos, ordenados de una
        forma específica."""
        resp = self.get_response({'formato': 'csv'}, fmt='csv')
        headers = next(resp)
        self.assertListEqual(headers, ['departamento_id',
                                       'departamento_nombre',
                                       'departamento_lat',
                                       'departamento_lon',
                                       'provincia_id',
                                       'provincia_nombre',
                                       'departamento_fuente'])


if __name__ == '__main__':
    unittest.main()
