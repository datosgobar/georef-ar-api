import unittest
import random
from . import SearchEntitiesTest, asciifold

MUNICIPALITIES = [
    (['060098'], 'BERISSO'),
    (['060756', '180143'], 'SAN ISIDRO'),
    (['100056'], 'ANTOFAGASTA DE LA SIERRA'),
    (['060154'], 'CARLOS TEJEDOR'),
    (['100063'], 'BELÉN'),
    (['060134'], 'CAÑUELAS'),
    (['060168'], 'CASTELLI'),
    (['060175'], 'COLÓN'),
    (['060182'], 'CORONEL DE MARINA LEONARDO ROSALES'),
    (['060203'], 'CORONEL SUÁREZ'),
    (['060274'], 'FLORENCIO VARELA'),
    (['060277'], 'FLORENTINO AMEGHINO'),
    (['060351'], 'GENERAL PINTO'),
    (['340126'], 'IBARRETA'),
    (['060294'], 'GENERAL ARENALES'),
    (['140658'], 'VILLA ROSSI'),
    (['140665'], 'BIALET MASSÉ'),
    (['060322'], 'GENERAL LA MADRID'),
    (['060408'], 'HURLINGHAM'),
    (['060476'], 'LOBERÍA'),
    (['060515', '140133'], 'MALVINAS ARGENTINAS'),
    (['060602'], 'PATAGONES'),
    (['060547'], 'MONTE'),
    (['060581'], 'NECOCHEA'),
    (['060644'], 'PINAMAR'),
    (['060648'], 'PRESIDENTE PERÓN'),
    (['060679', '500084', '700084', '823183'], 'RIVADAVIA'),
    (['060700'], 'SAAVEDRA'),
    (['060714'], 'SALTO'),
    (['060770', '141106', '540504'], 'SAN PEDRO'),
    (['060778', '142875', '540203', '822350'], 'SAN VICENTE'),
    (['060840'], 'TRES DE FEBRERO'),
    (['060798'], 'TAPALQUÉ'),
    (['060819'], 'TORNQUIST'),
    (['060847'], 'TRES LOMAS'),
    (['060861'], 'VICENTE LÓPEZ')
]

class SearchMunicipalitiesTest(SearchEntitiesTest):
    """Pruebas de búsqueda de municipios."""

    def setUp(self):
        self.endpoint = '/api/v1.0/municipios'
        self.entity = 'municipios'
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
        self.assertTrue(len(data['id']) == 6)

    def test_id_search(self):
        """La búsqueda por ID debe devolver el municipio correspondiente."""
        data = self.get_response({'id': '060182'})
        self.assertListEqual([p['nombre'] for p in data], ['CORONEL DE MARINA LEONARDO ROSALES'])

    def test_default_results_fields(self):
        """Las entidades devueltas deben tener los campos default."""
        data = self.get_response({'max': 1})[0]
        fields = sorted(['fuente', 'id', 'lat', 'lon', 'nombre', 'provincia', 'departamento'])
        self.assertListEqual(fields, sorted(data.keys()))

    def test_filter_results_fields(self):
        """Los campos de los municipios devueltos deben ser filtrables."""
        fields_lists = [
            ['fuente', 'id', 'nombre'],
            ['fuente', 'id', 'lat', 'lon', 'nombre'],
            ['fuente', 'id', 'lat', 'nombre'],
            ['fuente', 'id', 'lat', 'nombre', 'provincia'],
            ['departamento', 'fuente', 'id', 'nombre']
        ]
        fields_results = []

        for fields in fields_lists:
            data = self.get_response({'campos': ','.join(fields), 'max': 1})
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
        """La búsqueda por nombre exacto debe devolver los municipios
         correspondientes."""
        self.assert_name_search_id_matches(MUNICIPALITIES, exact=True)

    def test_name_exact_search_ignores_case(self):
        """La búsqueda por nombre exacto debe ignorar mayúsculas y 
        minúsculas."""
        expected = [
            (['060408'], 'HURLINGHAM'),
            (['060408'], 'hurlingham'),
            (['060408'], 'Hurlingham'),
            (['060408'], 'HuRlInGhAm')
        ]

        self.assert_name_search_id_matches(expected, exact=True)

    def test_name_exact_search_ignores_tildes(self):
        """La búsqueda por nombre exacto debe ignorar tildes."""
        expected = [
            (['140665'], 'BIALET MASSÉ'),
            (['140665'], 'bialet massé'),
            (['140665'], 'BIALET MASSE'),
            (['140665'], 'bialet masse')
        ]

        self.assert_name_search_id_matches(expected, exact=True)

    def test_id_invalid_search(self):
        """La búsqueda por ID debe devolver 0 resultados cuando se
        utiliza un ID no existente."""
        data = self.get_response({'id': '99999'})
        self.assertTrue(len(data) == 0)

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
            (['060408'], 'RLINGHAM'),     # -2 caracteres (de 8+)
            (['060408'], 'URLINGHAM'),    # -1 caracteres (de 8+)
            (['060408'], 'hHURLINGHAM'),  # +1 caracteres (de 8+)
            (['060408'], 'hHURLINGHAMm'), # +2 caracteres (de 8+)
            (['142448'], 'GUIZAMÓN'),     # -2 caracteres (de 8+)
            (['142448'], 'EGUIZAMÓN'),    # -1 caracteres (de 8+)
            (['142448'], 'lLEGUIZAMÓN'),  # +1 caracteres (de 8+)
            (['142448'], 'lLEGUIZAMÓNn'), # +2 caracteres (de 8+)
            (['142238'], 'INCEN'),        # -1 caracteres (de 4-7)
            (['142238'], 'pPINCEN'),      # +1 caracteres (de 4-7)
        ]

        self.assert_name_search_id_matches(expected)

    def test_name_search_autocompletes(self):
        """La búsqueda por nombre aproximado debe también actuar como
        autocompletar cuando la longitud de la query es >= 4."""
        expected = [
            (['142623'], 'CAPILLA DE LOS REMEDIO'),
            (['142623'], 'CAPILLA DE LOS REMEDI'),
            (['142623'], 'CAPILLA DE LOS REMED'),
            (['142623'], 'CAPILLA DE LOS REME'),
            (['142623'], 'CAPILLA DE LOS REM'),
            (['142623'], 'CAPILLA DE LOS RE'),
            (['142623'], 'CAPILLA DE LOS R'),
            (['142091'], 'VILLA QUILLINZ'),
            (['142091'], 'VILLA QUILLIN'),
            (['142091'], 'VILLA QUILLI'),
            (['142091'], 'VILLA QUILL'),
            (['142091'], 'VILLA QUIL'),
            (['142091', '908455'], 'VILLA QUI'),
            (['142091', '908455'], 'VILLA QU'),
            (['142091', '908455'], 'VILLA Q')
        ]

        self.assert_name_search_id_matches(expected)

    def test_name_search_stopwords(self):
        """La búsqueda por nombre aproximado debe ignorar stopwords."""
        expected = [
            (['060840'], 'TRES DE FEBRERO'),
            (['060840'], 'TRES DEL FEBRERO'),
            (['060840'], 'TRES D FEBRERO'),
            (['060840'], 'TRES LA FEBRERO'),
        ]

        self.assert_name_search_id_matches(expected)

    def test_code_prefix(self):
        """Los IDs de los municipios deben comenzar con el ID de sus
        provincias."""
        data = self.get_response({'max': 25})
        results = [
            mun['id'].startswith(mun['provincia']['id'])
            for mun in data
        ]

        self.assertTrue(all(results) and results)

    def test_search_by_state(self):
        """Se debe poder buscar municipios por provincia."""

        # Algunas provincias no tienen municipios, por el momento buscar
        # utilizando una provincia que sabemos contiene uno o mas
        state_id, state_name = '82', 'SANTA FE'

        data = self.get_response({'provincia': state_id})
        data.extend(self.get_response({'provincia': state_name}))
        data.extend(self.get_response({'provincia': state_name, 'exacto': 1}))

        results = [mun['id'].startswith(state_id) for mun in data]
        self.assertTrue(all(results) and results)

    def test_search_by_department(self):
        """Se debe poder buscar municipios por departamento."""

        # Algunos departamentos no tienen municipios, por el momento buscar
        # utilizando un departamento que sabemos contiene uno o mas
        dept_id, dept_name = '82021', 'CASTELLANOS'

        data = self.get_response({'departamento': dept_id})
        data.extend(self.get_response({'departamento': dept_name}))
        data.extend(self.get_response({'departamento': dept_name, 'exacto': 1}))

        results = [mun['departamento']['id'] == dept_id for mun in data]
        self.assertTrue(all(results) and results)

    def test_empty_params(self):
        """Los parámetros que esperan valores no pueden tener valores
        vacíos."""
        params = ['id', 'nombre', 'orden', 'campos', 'max', 'formato',
                  'provincia', 'departamento']
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
            'nombre': 'CORONEL'
        }

        body = {
            'municipios': [query] * req_len
        }

        results = self.get_response(method='POST', body=body)
        self.assertEqual(len(results), req_len)
        
    def test_bulk_basic(self):
        """La búsqueda de una query sin parámetros debería funcionar
        correctamente."""
        results = self.get_response(method='POST', body={
            'municipios': [{}]
        })

        first = results[0]
        self.assertTrue(len(results) == 1 and len(first['municipios']) == 10)

    def test_bulk_equivalent(self):
        """Los resultados de una query envíada vía bulk deberían ser idénticos a
        los resultados de una query individual (GET)."""
        queries = [
            {
                'nombre': 'CORONEL'
            },
            {
                'id': '060581'
            },
            {
                'max': 1
            },
            {
                'campos': 'id,nombre'
            },
            {
                'provincia': '54'
            },
            {
                'departamento': '82021'
            },
            {
                'orden': 'nombre'
            },
            {
                'exacto': True,
                'nombre': 'NECOCHEA'
            }
        ]

        individual_results = []
        for query in queries:
            individual_results.append({
                'municipios': self.get_response(params=query)
            })

        bulk_results = self.get_response(method='POST', body={
            'municipios': queries
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
            'nombre': 'VIAMONTE',
            'campos': 'nombre,departamento'
        })

    def test_geojson_format(self):
        """Se debería poder obtener resultados en formato
        GEOJSON (sin parámetros)."""
        self.assert_valid_geojson()

    def test_geojson_format_query(self):
        """Se debería poder obtener resultados en formato
        GEOJSON (con parámetros)."""
        self.assert_valid_geojson({
            'nombre': 'COLONIA',
            'provincia': '22'
        })


if __name__ == '__main__':
    unittest.main()
