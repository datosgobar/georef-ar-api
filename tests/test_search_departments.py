import random
from service import formatter, constants
from . import GeorefLiveTest, asciifold
from .test_search_states import STATES


DEPARTMENTS = [
    (['54063'], 'IGUAZÚ'),
    (['74042'], 'GOBERNADOR DUPUY'),
    (['86021'], 'ATAMISQUI'),
    (['94015'], 'USHUAIA'),
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


class SearchDepartmentsTest(GeorefLiveTest):
    """Pruebas de búsqueda de departamentos."""

    def setUp(self):
        self.endpoint = '/api/v1.0/departamentos'
        self.entity = 'departamentos'
        super().setUp()

    def test_529_departments_present(self):
        """Deben existir 529 departamentos."""
        data = self.get_response(return_value='full')
        self.assertEqual(data['total'], 529)

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
        self.assertListEqual([p['nombre'] for p in data], ['Arrecifes'])

    def test_id_invalid_search(self):
        """La búsqueda por ID debe devolver error 400 cuando se
        utiliza un ID no válido."""
        status = self.get_response(params={'id': 999999},
                                   return_value='status', expect_status=[400])
        self.assertEqual(status, 400)

    def test_short_id_search(self):
        """La búsqueda por ID debe devolver la entidad correcta incluso si
        se omiten ceros iniciales."""
        data = self.get_response({'id': '2007'})
        self.assertTrue(data[0]['id'] == '02007')

    def test_id_list_search(self):
        """La búsqueda por lista de IDs debe devolver los departamentos
        correspondientes."""
        data = self.get_response({
            'id': '22036,22147,22098,22007',
            'orden': 'nombre'
        })

        self.assertListEqual([p['nombre'] for p in data], [
            '12 de Octubre',
            'Almirante Brown',
            'Mayor Luis J. Fontana',
            'San Lorenzo',
        ])

    def test_default_results_fields(self):
        """Las entidades devueltas deben tener los campos default."""
        data = self.get_response({'max': 1})[0]
        fields = sorted(['id', 'centroide', 'nombre', 'provincia'])
        self.assertListEqual(fields, sorted(data.keys()))

    def test_filter_results_fields(self):
        """Los campos de los deptos. devueltos deben ser filtrables."""
        fields_lists = [
            ['fuente', 'id', 'nombre'],
            ['fuente', 'id', 'centroide.lat', 'centroide.lon', 'nombre'],
            ['fuente', 'id', 'centroide.lat', 'nombre'],
            ['fuente', 'id', 'centroide.lat', 'nombre', 'provincia.id',
             'provincia.nombre']
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
        self.assert_fields_set_equals('basico', ['id', 'nombre'])

    def test_standard_fields_set(self):
        """Se debería poder especificar un conjunto de parámetros
        preseleccionados llamado 'estandar'."""
        self.assert_fields_set_equals('estandar',
                                      ['id', 'nombre', 'centroide.lat',
                                       'centroide.lon', 'provincia.id',
                                       'provincia.nombre'])

    def test_complete_fields_set(self):
        """Se debería poder especificar un conjunto de parámetros
        preseleccionados llamado 'completo'."""
        self.assert_fields_set_equals('completo',
                                      ['id', 'fuente', 'nombre',
                                       'centroide.lat', 'centroide.lon',
                                       'provincia.id', 'provincia.nombre',
                                       'provincia.interseccion',
                                       'categoria', 'nombre_completo'])

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

    def test_search_by_state_single(self):
        """Se debe poder buscar departamentos por provincia."""
        state = random.choice(STATES)
        state_id, state_name = state[0][0], state[1]

        data = self.get_response({'provincia': state_id})
        data.extend(self.get_response({'provincia': state_name}))
        data.extend(self.get_response({'provincia': state_name, 'exacto': 1}))

        results = [dept['id'].startswith(state_id) for dept in data]
        self.assertTrue(all(results) and results)

    def test_search_by_state_id_list(self):
        """Se debe poder buscar departamentos por lista de IDs de
        provincias."""
        states = STATES[:]
        random.shuffle(states)
        id_count = random.randint(3, 6)
        ids = sorted(state[0][0] for state in states[:id_count])

        resp = self.get_response({'provincia': ','.join(ids), 'max': 500})
        id_prefixes = {dept['id'][:constants.STATE_ID_LEN] for dept in resp}

        self.assertListEqual(ids, sorted(id_prefixes))

    def test_flat_results(self):
        """El parametro aplanar deberia aplanar los resultados devueltos."""
        self.assert_flat_results()

    def test_pagination(self):
        """Los resultados deberían poder ser paginados."""
        page_size = 50
        pages = 5
        results = set()

        for i in range(pages):
            resp = self.get_response({
                'inicio': i * page_size,
                'max': page_size
            })

            for result in resp:
                results.add(result['id'])

        # Si el paginado funciona correctamente, no deberían haberse repetido
        # IDs de entidades entre resultados.
        self.assertEqual(len(results), page_size * pages)

    def test_total_results(self):
        """Dada una query sin parámetros, se deben retornar los metadatos de
        resultados apropiados."""
        resp = self.get_response(return_value='full')
        self.assertTrue(resp['cantidad'] == 10 and resp['inicio'] == 0)

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
            },
            {
                'interseccion': 'municipio:180315'
            },
            {
                'interseccion': 'provincia:14'
            }
        ]

        individual_results = []
        for query in queries:
            individual_results.append(self.get_response(params=query,
                                                        return_value='full'))

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

    def test_geojson_format_flat(self):
        """Se deberían poder aplanar los resultados GeoJSON."""
        resp = self.get_response({'aplanar': True, 'max': 1,
                                  'formato': 'geojson'})
        self.assertTrue(all([
            not isinstance(v, dict) for v
            in resp['features'][0]['properties'].values()
        ]) and resp)

    def test_csv_fields(self):
        """Una consulta CSV debería tener ciertos campos, ordenados de una
        forma específica."""
        resp = self.get_response({'formato': 'csv', 'campos': 'completo'})
        headers = next(resp)
        self.assertListEqual(headers, ['departamento_id',
                                       'departamento_nombre',
                                       'departamento_nombre_completo',
                                       'departamento_centroide_lat',
                                       'departamento_centroide_lon',
                                       'provincia_id',
                                       'provincia_nombre',
                                       'provincia_interseccion',
                                       'departamento_fuente',
                                       'departamento_categoria'])

    def test_xml_format(self):
        """Se debería poder obtener resultados en formato XML (sin
        parámetros)."""
        self.assert_valid_xml()

    def test_xml_format_query(self):
        """Se debería poder obtener resultados en formato XML (con
        parámetros)."""
        self.assert_valid_xml({
            'max': 100,
            'nombre': 'belgrano'
        })

    def test_shp_format(self):
        """Se debería poder obtener resultados en formato SHP (sin
        parámetros)."""
        self.assert_valid_shp_type(
            shape_type=5,  # 5 == POLYGON
            params={'max': 1}
        )

    def test_shp_format_query(self):
        """Se debería poder obtener resultados en formato SHP (con
        parámetros)."""
        self.assert_valid_shp_query({
            'max': 5,
            'campos': 'completo',
            'nombre': 'belgrano'
        })

    def test_shp_record_fields(self):
        """Los campos obtenidos en formato SHP deberían ser los esperados y
        deberían corresponder a los campos obtenidos en otros formatos."""
        self.assert_shp_fields('completo', [
            'nombre',
            'id',
            'prov_id',
            'prov_nombre',
            'prov_intscn',
            'centr_lat',
            'centr_lon',
            'fuente',
            'categoria',
            'nombre_comp'
        ])
