import random
import unittest
from service import formatter
from . import SearchEntitiesTest, asciifold


class SearchCountriesTest(SearchEntitiesTest):
    """Pruebas de búsqueda de países."""

    def setUp(self):
        self.endpoint = '/api/v1.0/paises'
        self.entity = 'paises'
        super().setUp()

    def test_argentina_present(self):
        """Debe existir la República Argentina."""
        data = self.get_response({'nombre': 'Argentina'})
        self.assertEqual(data[0]['nombre'], 'República Argentina')

    def test_max_results_returned(self):
        """La cantidad máxima de resultados debe ser configurable."""
        lengths = [1, 5, 20, 24]
        results_lengths = [
            len(self.get_response({'max': length}))
            for length in lengths
        ]

        self.assertListEqual(lengths, results_lengths)

    def test_flat_results(self):
        """El parametro aplanar deberia aplanar los resultados devueltos."""
        self.assert_flat_results()

    def test_pagination(self):
        """Los resultados deberían poder ser paginados."""
        page_size = 8
        pages = 3
        results = set()

        for i in range(pages):
            resp = self.get_response({
                'inicio': i * page_size,
                'max': page_size
            })

            for result in resp:
                results.add(result['nombre'])

        # Si el paginado funciona correctamente, no deberían haberse repetido
        # nomnres de países entre resultados.
        self.assertEqual(len(results), page_size * pages)

    def test_total_results(self):
        """Dada una query sin parámetros, se deben retornar los metadatos de
        resultados apropiados."""
        resp = self.get_response(return_value='full')
        self.assertEqual(resp['cantidad'], 10)

    def test_default_results_fields(self):
        """Los países devueltos deben tener los campos default."""
        data = self.get_response({'max': 1})[0]
        fields = sorted(['centroide', 'nombre'])
        self.assertListEqual(fields, sorted(data.keys()))

    def test_filter_results_fields(self):
        """Los campos de las provincias devueltas deben ser filtrables."""
        fields_lists = [
            ['fuente', 'nombre'],
            ['fuente', 'centroide.lat', 'centroide.lon', 'nombre'],
            ['centroide.lat', 'nombre']
        ]
        fields_lists = [sorted(l) for l in fields_lists]
        fields_results = []

        for fields in fields_lists:
            data = self.get_response({'campos': ','.join(fields), 'max': 1})
            formatter.flatten_dict(data[0], sep='.')
            fields_results.append(sorted(data[0].keys()))
        self.assertListEqual(fields_lists, fields_results)

    def test_basic_fields_set(self):
        """Se debería poder especificar un conjunto de parámetros
        preseleccionados llamado 'basico'."""
        self.assert_fields_set_equals('basico', ['nombre'])

    def test_standard_fields_set(self):
        """Se debería poder especificar un conjunto de parámetros
        preseleccionados llamado 'estandar'."""
        self.assert_fields_set_equals('estandar',
                                      ['nombre', 'centroide.lat',
                                       'centroide.lon'])

    def test_complete_fields_set(self):
        """Se debería poder especificar un conjunto de parámetros
        preseleccionados llamado 'completo'."""
        self.assert_fields_set_equals('completo',
                                      ['nombre', 'centroide.lat',
                                       'centroide.lon', 'fuente'])

    def test_name_ordering(self):
        """Los resultados deben poder ser ordenados por nombre."""
        data = [
            asciifold(dep['nombre'])
            for dep
            in self.get_response({'orden': 'nombre', 'max': 50})
        ]

        self.assertListEqual(sorted(data), data)

    def test_name_exact_search_ignores_case(self):
        """La búsqueda por nombre exacto debe ignorar mayúsculas y
        minúsculas."""
        expected = [
            (['República Argentina'], 'república argentina'),
            (['República Argentina'], 'República Argentina'),
            (['República Argentina'], 'REPÚBLICA ARGENTINA')
        ]

        self.assert_name_search_hit_matches(expected, exact=True)

    def test_name_exact_search_ignores_tildes(self):
        """La búsqueda por nombre exacto debe ignorar tildes."""
        expected = [
            (['República Argentina'], 'Republica Argentina')
        ]

        self.assert_name_search_hit_matches(expected, exact=True)

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
            (['República Argentina'], 'rgentina'),
            (['República Argentina'], 'argentin'),
            (['Reino de Swazilandia'], 'swaziland'),
            (['Reino de Swazilandia'], 'swazilandi')
        ]

        self.assert_name_search_hit_matches(expected)

    def test_name_search_autocompletes(self):
        """La búsqueda por nombre aproximado debe también actuar como
        autocompletar cuando la longitud de la query es >= 4."""
        expected = [
            (['República Argentina',
              'República Democrática Popular de Argelia'], 'arge'),
            (['República Argentina'], 'argen'),
            (['República Argentina'], 'argent'),
            (['República Argentina'], 'argenti'),
            (['República Argentina'], 'argentin')
        ]

        self.assert_name_search_hit_matches(expected)

    def test_name_search_stopwords(self):
        """La búsqueda por nombre aproximado debe ignorar stopwords."""
        expected = [
            (['República Federativa del Brasil'], 'Federativa del Brazil'),
            (['República Federativa del Brasil'], 'Federativa del del Brazil'),
            (['República Federativa del Brasil'], 'Federativa del el Brazil')
        ]

        self.assert_name_search_hit_matches(expected)

    def test_empty_params(self):
        """Los parámetros que esperan valores no pueden tener valores
        vacíos."""
        params = ['nombre', 'orden', 'campos', 'max', 'formato']
        self.assert_empty_params_return_400(params)

    def test_unknown_param_returns_400(self):
        """El endpoint no debe aceptar parámetros desconocidos."""
        self.assert_unknown_param_returns_400()

    def test_bulk_empty_400(self):
        """La búsqueda bulk vacía debería retornar un error 400."""
        status = self.get_response(method='POST', body={},
                                   return_value='status')
        self.assertEqual(status, 400)

    def test_bulk_response_len(self):
        """La longitud de la respuesta bulk debería ser igual a la cantidad
        de queries envíadas."""
        req_len = random.randint(10, 20)
        query = {
            'nombre': 'republica'
        }

        body = {
            'paises': [query] * req_len
        }

        results = self.get_response(method='POST', body=body)
        self.assertEqual(len(results), req_len)

    def test_bulk_basic(self):
        """La búsqueda de una query sin parámetros debería funcionar
        correctamente."""
        results = self.get_response(method='POST', body={
            'paises': [{}]
        })

        first = results[0]
        self.assertTrue(
            len(results) == 1 and len(first['paises']) == 10)

    def test_bulk_equivalent(self):
        """Los resultados de una query envíada vía bulk deberían ser idénticos a
        los resultados de una query individual (GET)."""
        queries = [
            {
                'nombre': 'Argentina'
            },
            {
                'max': 1
            },
            {
                'campos': 'centroide.lon,nombre'
            },
            {
                'orden': 'nombre'
            },
            {
                'exacto': True,
                'nombre': 'República del Paraguay'
            }
        ]

        individual_results = []
        for query in queries:
            individual_results.append(self.get_response(params=query,
                                                        return_value='full'))

        bulk_results = self.get_response(method='POST', body={
            'paises': queries
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
            'campos': 'id,centroide_lat'
        })

    def test_empty_csv_valid(self):
        """Una consulta CSV con respuesta vacía debería ser CSV válido."""
        self.assert_valid_csv({
            'nombre': 'foobarfoobar'
        })

    def test_csv_fields(self):
        """Una consulta CSV debería tener ciertos campos, ordenados de una
        forma específica."""
        resp = self.get_response({'formato': 'csv'}, fmt='csv')
        headers = next(resp)
        self.assertListEqual(headers, ['pais_nombre',
                                       'pais_centroide_lat',
                                       'pais_centroide_lon'])

    def test_geojson_format(self):
        """Se debería poder obtener resultados en formato
        GEOJSON (sin parámetros)."""
        self.assert_valid_geojson()

    def test_geojson_format_query(self):
        """Se debería poder obtener resultados en formato
        GEOJSON (con parámetros)."""
        self.assert_valid_geojson({
            'nombre': 'republica',
            'max': 10
        })


if __name__ == '__main__':
    unittest.main()
