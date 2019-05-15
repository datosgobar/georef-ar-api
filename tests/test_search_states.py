import random
from service import formatter
from . import GeorefLiveTest, asciifold


STATES = [
    (['54'], 'Misiones'),
    (['74'], 'San Luis'),
    (['86'], 'Santiago del Estero'),
    (['94'], 'Tierra del Fuego, Antártida e Islas del Atlántico Sur'),
    (['18'], 'Corrientes'),
    (['30'], 'Entre Ríos'),
    (['34'], 'Formosa'),
    (['38'], 'Jujuy'),
    (['46'], 'La Rioja'),
    (['82'], 'Santa Fe'),
    (['06'], 'Buenos Aires'),
    (['14'], 'Córdoba'),
    (['22'], 'Chaco'),
    (['58'], 'Neuquén'),
    (['78'], 'Santa Cruz'),
    (['02'], 'Ciudad Autónoma de Buenos Aires'),
    (['26'], 'Chubut'),
    (['50'], 'Mendoza'),
    (['62'], 'Río Negro'),
    (['70'], 'San Juan'),
    (['10'], 'Catamarca'),
    (['42'], 'La Pampa'),
    (['66'], 'Salta'),
    (['90'], 'Tucumán')
]


class SearchStatesTest(GeorefLiveTest):
    """Pruebas de búsqueda de provincias."""

    def setUp(self):
        self.endpoint = '/api/v1.0/provincias'
        self.entity = 'provincias'
        super().setUp()

    def test_24_states_present(self):
        """Deben existir 24 provincias."""
        data = self.get_response(return_value='full')
        self.assertEqual(data['total'], 24)

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
                results.add(result['id'])

        # Si el paginado funciona correctamente, no deberían haberse repetido
        # IDs de entidades entre resultados.
        self.assertEqual(len(results), page_size * pages)

    def test_total_results(self):
        """Dada una query sin parámetros, se deben retornar los metadatos de
        resultados apropiados."""
        resp = self.get_response(return_value='full')
        self.assertTrue(resp['total'] == 24 and resp['cantidad'] == 24)

    def test_id_search(self):
        """La búsqueda por ID debe devolver la provincia correspondiente."""
        data = self.get_response({'id': '06'})
        self.assertListEqual([p['nombre'] for p in data], ['Buenos Aires'])

    def test_id_list_search(self):
        """La búsqueda por lista de IDs debe devolver las provincias
        correspondientes."""
        data = self.get_response({'id': '66,14,26,38', 'orden': 'nombre'})

        self.assertListEqual([p['nombre'] for p in data], [
            'Chubut',
            'Córdoba',
            'Jujuy',
            'Salta'
        ])

    def test_filter_results_fields(self):
        """Los campos de las provincias devueltas deben ser filtrables."""
        fields_lists = [
            ['fuente', 'id', 'nombre'],
            ['fuente', 'id', 'centroide.lat', 'centroide.lon', 'nombre'],
            ['fuente', 'id', 'centroide.lat', 'nombre'],
            ['fuente', 'id', 'categoria', 'nombre'],
            ['fuente', 'id', 'categoria', 'nombre', 'iso_id']
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
                                       'centroide.lon'])

    def test_complete_fields_set(self):
        """Se debería poder especificar un conjunto de parámetros
        preseleccionados llamado 'completo'."""
        self.assert_fields_set_equals('completo',
                                      ['id', 'nombre', 'centroide.lat',
                                       'centroide.lon', 'fuente',
                                       'categoria', 'iso_id', 'iso_nombre',
                                       'nombre_completo'])

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
        status = self.get_response(params={'id': 99999}, return_value='status',
                                   expect_status=[400])
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

    def test_name_search_excluding_terms(self):
        """La búsqueda por nombre aproximado debe tener en cuenta términos
        excluyentes. Por ejemplo, buscar 'salta' no debería traer resultados
        con 'santa', aunque las dos palabras sean textualmente similares."""
        expected = [
            (['02'], 'caba'),
            (['14'], 'cba'),
            (['66'], 'salta'),
            (['78', '82'], 'santa')
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
            },
            {
                'interseccion': 'departamento:82133'
            },
            {
                'interseccion': 'municipio:060014'
            }
        ]

        individual_results = []
        for query in queries:
            individual_results.append(self.get_response(params=query,
                                                        return_value='full'))

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
        resp = self.get_response({'formato': 'csv', 'campos': 'completo'})
        headers = next(resp)
        self.assertListEqual(headers, ['provincia_id',
                                       'provincia_nombre',
                                       'provincia_nombre_completo',
                                       'provincia_iso_id',
                                       'provincia_iso_nombre',
                                       'provincia_centroide_lat',
                                       'provincia_centroide_lon',
                                       'provincia_fuente',
                                       'provincia_categoria'])

    def test_csv_quoting(self):
        """El primer campo de la respuesta CSV (ID) siempre debe estar
        entrecomillado para que sea interpretado como texto."""
        resp = self.get_response({'formato': 'csv'},
                                 return_value='raw').decode()
        first_row = resp.splitlines()[1]  # Saltear la cabecera CSV
        first_value = first_row.split(formatter.CSV_SEP)[0]  # ID de la fila

        self.assertTrue(first_value.startswith('"') and
                        first_value.endswith('"') and
                        len(first_value) > 2)

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

    def test_xml_format(self):
        """Se debería poder obtener resultados en formato XML (sin
        parámetros)."""
        self.assert_valid_xml()

    def test_xml_format_query(self):
        """Se debería poder obtener resultados en formato XML (con
        parámetros)."""
        self.assert_valid_xml({
            'max': 1,
            'nombre': 'santa'
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
            'max': 2,
            'campos': 'completo'
        })

    def test_shp_record_fields(self):
        """Los campos obtenidos en formato SHP deberían ser los esperados y
        deberían corresponder a los campos obtenidos en otros formatos."""
        self.assert_shp_fields('completo', [
            'nombre',
            'nombre_comp',
            'id',
            'centr_lat',
            'centr_lon',
            'fuente',
            'iso_id',
            'iso_nombre',
            'categoria'
        ])

    def test_shp_projection_present(self):
        """El archivo .prj debería estar presente en el Shapefile."""
        self.assert_shp_projection_present()
