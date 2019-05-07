import random
from service import formatter
from . import GeorefLiveTest, asciifold
from .test_search_states import STATES


LOCALITIES = [
    (['06840010015'], 'VILLA RAFFO'),
    (['06756010003'], 'BOULOGNE SUR MER'),
    (['62042450001'], 'BARRIO PINO AZUL'),
    (['14021150001'], 'DUMESNIL'),
    (['70056020000'], 'GRAN CHINA'),
    (['50028020003'], 'CAPILLA DEL ROSARIO'),
    (['54112010000'], 'CRUCE CABALLERO'),
    (['82021270000'], 'PLAZA CLUCELLAS'),
    (['94015010000'], 'LAGUNA ESCONDIDA'),
    (['38077030000'], 'CIENEGUILLAS'),
    (['34035030000'], 'COMANDANTE FONTANA'),
    (['78014040000'], 'JARAMILLO'),
    (['86014030000'], 'DONADEU'),
    (['26035010000'], 'ALDEA ESCOLAR'),
    (['26021030009'], 'BARRIO MANANTIAL ROSALES'),
]


class SearchLocalityTest(GeorefLiveTest):
    """Pruebas de búsqueda de localidades (índice de localidades)."""

    def setUp(self):
        self.endpoint = '/api/v1.0/localidades'
        self.entity = 'localidades'
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
        self.assertTrue(len(data['id']) == 11)

    def test_id_search(self):
        """La búsqueda por ID debe devolver la localidad correspondiente."""
        data = self.get_response({'id': '06840010015'})
        self.assertListEqual([p['nombre'] for p in data], ['VILLA RAFFO'])

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

    def test_null_dept_locality(self):
        """Las localidades con departamento nulo deberían ser válidas y existir
        en la API."""
        resp = self.get_response({'id': '02000010000'})
        self.assertTrue(resp[0]['departamento']['id'] is None and
                        resp[0]['departamento']['nombre'] is None)

    def test_total_results(self):
        """Dada una query sin parámetros, se deben retornar los metadatos de
        resultados apropiados."""
        resp = self.get_response(return_value='full')
        self.assertTrue(resp['cantidad'] == 10 and resp['inicio'] == 0)

    def test_filter_results_fields(self):
        """Los campos de las localidades devueltas deben ser filtrables."""
        fields_lists = [
            ['fuente', 'id', 'nombre'],
            ['fuente', 'id', 'centroide.lat', 'centroide.lon', 'nombre'],
            ['fuente', 'id', 'centroide.lat', 'nombre'],
            ['fuente', 'id', 'centroide.lat', 'nombre', 'provincia.id'],
            ['departamento.id', 'fuente', 'id', 'nombre'],
            ['fuente', 'id', 'municipio.id', 'nombre', 'provincia.nombre']
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
                                       'provincia.nombre', 'departamento.id',
                                       'departamento.nombre',
                                       'municipio.id', 'municipio.nombre',
                                       'localidad_censal.id',
                                       'localidad_censal.nombre',
                                       'categoria'])

    def test_complete_fields_set(self):
        """Se debería poder especificar un conjunto de parámetros
        preseleccionados llamado 'completo'."""
        self.assert_fields_set_equals('completo',
                                      ['id', 'fuente', 'nombre',
                                       'centroide.lat', 'centroide.lon',
                                       'provincia.id', 'provincia.nombre',
                                       'departamento.id',
                                       'departamento.nombre',
                                       'municipio.id', 'municipio.nombre',
                                       'localidad_censal.id',
                                       'localidad_censal.nombre',
                                       'categoria'])

    def test_field_prefixes(self):
        """Se debería poder especificar prefijos de otros campos como campos
        a incluir en la respuesta."""
        self.assert_fields_set_equals('provincia', ['id', 'nombre',
                                                    'provincia.nombre',
                                                    'provincia.id'])

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
        """La búsqueda por nombre exacto debe devolver las localidades
         correspondientes."""
        self.assert_name_search_id_matches(LOCALITIES, exact=True)

    def test_name_exact_search_ignores_case(self):
        """La búsqueda por nombre exacto debe ignorar mayúsculas y
        minúsculas."""
        expected = [
            (['14098090000'], 'CORONEL BAIGORRIA'),
            (['14098090000'], 'coronel baigorria'),
            (['14098090000'], 'Coronel Baigorria'),
            (['14098090000'], 'CoRoNeL BaIgOrRiA')
        ]

        self.assert_name_search_id_matches(expected, exact=True)

    def test_name_exact_search_ignores_tildes(self):
        """La búsqueda por nombre exacto debe ignorar tildes."""
        expected = [
            (['46049060000'], 'CHAÑARMUYO'),
            (['46049060000'], 'CHANARMUYO'),
            (['46049060000'], 'chañarmuyo'),
            (['46049060000'], 'chanarmuyo')
        ]

        self.assert_name_search_id_matches(expected, exact=True)

    def test_id_invalid_search(self):
        """La búsqueda por ID debe devolver error 400 cuando se
        utiliza un ID no válido."""
        status = self.get_response(params={'id': 9999999999999},
                                   return_value='status', expect_status=[400])
        self.assertEqual(status, 400)

    def test_short_id_search(self):
        """La búsqueda por ID debe devolver la entidad correcta incluso si
        se omiten ceros iniciales."""
        data = self.get_response({'id': '6021020000'})
        self.assertTrue(data[0]['id'] == '06021020000')

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
            (['06476060000'], 'MANGUEYU'),      # -2 caracteres (de 8+)
            (['06476060000'], 'AMANGUEYU'),     # -1 caracteres (de 8+)
            (['06476060000'], 'tTAMANGUEYU'),   # +1 caracteres (de 8+)
            (['06476060000'], 'tTAMANGUEYUu'),  # +2 caracteres (de 8+)
            (['06819020000'], 'LDUNGARAY'),     # -2 caracteres (de 8+)
            (['06819020000'], 'ALDUNGARAY'),    # -1 caracteres (de 8+)
            (['06819020000'], 'sSALDUNGARAY'),  # +1 caracteres (de 8+)
            (['06819020000'], 'sSALDUNGARAYy'),  # +2 caracteres (de 8+)
            (['82098050000'], 'OMANG'),          # -1 caracteres (de 4-7)
            (['82098050000'], 'rROMANG'),        # +1 caracteres (de 4-7)
        ]

        self.assert_name_search_id_matches(expected)

    def test_name_search_autocompletes(self):
        """La búsqueda por nombre aproximado debe también actuar como
        autocompletar cuando la longitud de la query es >= 4."""
        expected = [
            (['38098030000'], 'PURMAMARCA'),
            (['38098030000'], 'PURMAMARC'),
            (['38098030000'], 'PURMAMAR'),
            (['38098030000'], 'PURMAMA'),
            (['38098030000'], 'PURMAM'),
            (['86056070000'], 'PAMPA DE LOS GUANACOS'),
            (['86056070000'], 'PAMPA DE LOS GUANACO'),
            (['86056070000'], 'PAMPA DE LOS GUANA'),
            (['86056070000'], 'PAMPA DE LOS GUAN'),
            (['86056070000'], 'PAMPA DE LOS GUA'),
            (['86056070000'], 'PAMPA DE LOS GU')
        ]

        self.assert_name_search_id_matches(expected)

    def test_name_search_stopwords(self):
        """La búsqueda por nombre aproximado debe ignorar stopwords."""
        expected = [
            (['10063040003'], 'LA FALDA DE DE SAN ANTONIO'),
            (['10063040003'], 'LA LA FALDA DE SAN ANTONIO'),
            (['10063040003'], 'FALDA DE SAN ANTONIO'),
            (['10063040003'], 'FALDA SAN ANTONIO')
        ]

        self.assert_name_search_id_matches(expected)

    def test_code_prefix(self):
        """Los IDs de las localidades deben comenzar con el ID de sus
        provincias."""
        data = self.get_response({'max': 25})
        results = [
            mun['id'].startswith(mun['provincia']['id'])
            for mun in data
        ]

        self.assertTrue(all(results) and results)

    def test_search_by_state(self):
        """Se debe poder buscar localidades por provincia."""
        state = random.choice(STATES)
        state_id, state_name = state[0][0], state[1]

        data = self.get_response({'provincia': state_id})
        data.extend(self.get_response({'provincia': state_name}))
        data.extend(self.get_response({'provincia': state_name, 'exacto': 1}))

        results = [loc['id'].startswith(state_id) for loc in data]
        self.assertTrue(all(results) and results)

    def test_search_by_department(self):
        """Se debe poder buscar localidades por departamento."""

        # Algunos departamentos no tienen localidades, por el momento buscar
        # utilizando un departamento que sabemos contiene una o mas
        dept_id, dept_name = '14007', 'CALAMUCHITA'

        data = self.get_response({'departamento': dept_id})
        data.extend(self.get_response({'departamento': dept_name}))
        data.extend(self.get_response({
            'departamento': dept_name,
            'exacto': 1
        }))

        results = [loc['departamento']['id'] == dept_id for loc in data]
        self.assertTrue(all(results) and results)

    def test_search_by_municipality(self):
        """Se debe poder buscar localidades por municipio."""

        # Algunos municipios no tienen localidades, por el momento buscar
        # utilizando un municipio que sabemos contiene una o mas
        mun_id, mun_name = '620133', 'CIPOLLETTI'

        data = self.get_response({'municipio': mun_id})
        data.extend(self.get_response({'municipio': mun_name}))
        data.extend(self.get_response({'municipio': mun_name, 'exacto': 1}))

        results = [loc['municipio']['id'] == mun_id for loc in data]
        self.assertTrue(all(results) and results)

    def test_search_by_census_locality(self):
        """Se debe poder buscar entidades por localidad censal."""
        # Tomar una localidad censal que tiene localidades
        cloc_id = '06638040'
        data = self.get_response({'localidad_censal': cloc_id})
        self.assertTrue(data and all([
            loc['localidad_censal']['nombre'] == 'Pilar' for loc in data
        ]))

    def test_flat_results(self):
        """El parametro aplanar deberia aplanar los resultados devueltos."""
        self.assert_flat_results()

    def test_bulk_response_len(self):
        """La longitud de la respuesta bulk debería ser igual a la cantidad
        de queries envíadas."""
        req_len = random.randint(10, 20)
        query = {
            'nombre': 'BARRIO'
        }

        body = {
            'localidades': [query] * req_len
        }

        results = self.get_response(method='POST', body=body)
        self.assertEqual(len(results), req_len)

    def test_bulk_basic(self):
        """La búsqueda de una query sin parámetros debería funcionar
        correctamente."""
        results = self.get_response(method='POST', body={
            'localidades': [{}]
        })

        first = results[0]
        self.assertTrue(len(results) == 1 and len(first['localidades']) == 10)

    def test_bulk_equivalent(self):
        """Los resultados de una query envíada vía bulk deberían ser idénticos a
        los resultados de una query individual (GET)."""
        queries = [
            {
                'nombre': 'BARRIO'
            },
            {
                'id': '06756010003'
            },
            {
                'max': 2
            },
            {
                'campos': 'id,nombre'
            },
            {
                'provincia': '06'
            },
            {
                'departamento': '14007'
            },
            {
                'municipio': '620133'
            },
            {
                'localidad_censal': 'Villa'
            },
            {
                'orden': 'nombre'
            },
            {
                'exacto': True,
                'nombre': 'BARRIO MANANTIAL ROSALES'
            }
        ]

        individual_results = []
        for query in queries:
            individual_results.append(self.get_response(params=query,
                                                        return_value='full'))

        bulk_results = self.get_response(method='POST', body={
            'localidades': queries
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
            'nombre': 'BARRIO',
            'campos': 'nombre,provincia.id,lat'
        })

    def test_geojson_format(self):
        """Se debería poder obtener resultados en formato
        GEOJSON (sin parámetros)."""
        self.assert_valid_geojson()

    def test_geojson_format_query(self):
        """Se debería poder obtener resultados en formato
        GEOJSON (con parámetros)."""
        self.assert_valid_geojson({
            'nombre': 'BARRIO',
            'max': '15'
        })

    def test_csv_fields(self):
        """Una consulta CSV debería tener ciertos campos, ordenados de una
        forma específica."""
        resp = self.get_response({'formato': 'csv', 'campos': 'completo'})
        headers = next(resp)
        self.assertListEqual(headers, ['localidad_id',
                                       'localidad_nombre',
                                       'localidad_centroide_lat',
                                       'localidad_centroide_lon',
                                       'provincia_id',
                                       'provincia_nombre',
                                       'departamento_id',
                                       'departamento_nombre',
                                       'municipio_id',
                                       'municipio_nombre',
                                       'localidad_censal_id',
                                       'localidad_censal_nombre',
                                       'localidad_fuente',
                                       'localidad_categoria'])

    def test_csv_empty_value(self):
        """Un valor vacío (None) debería estar representado como '' en CSV."""
        resp = self.get_response({
            'formato': 'csv',
            'id': '78007020000'
        })

        header = next(resp)
        row = next(resp)
        self.assertTrue(row[header.index('municipio_id')] == '' and
                        row[header.index('municipio_nombre')] == '')

    def test_xml_format(self):
        """Se debería poder obtener resultados en formato XML (sin
        parámetros)."""
        self.assert_valid_xml()

    def test_xml_format_query(self):
        """Se debería poder obtener resultados en formato XML (con
        parámetros)."""
        self.assert_valid_xml({
            'max': 100,
            'nombre': 'sarmiento'
        })

    def test_shp_format(self):
        """Se debería poder obtener resultados en formato SHP (sin
        parámetros)."""
        self.assert_valid_shp_type(
            shape_type=8,  # 8 == MULTIPOINT
            params={'max': 1}
        )

    def test_shp_format_query(self):
        """Se debería poder obtener resultados en formato SHP (con
        parámetros)."""
        self.assert_valid_shp_query({
            'max': 100,
            'campos': 'completo',
            'nombre': 'martin'
        })

    def test_shp_record_fields(self):
        """Los campos obtenidos en formato SHP deberían ser los esperados y
        deberían corresponder a los campos obtenidos en otros formatos."""
        self.assert_shp_fields('completo', [
            'nombre',
            'id',
            'prov_id',
            'prov_nombre',
            'muni_nombre',
            'muni_id',
            'dpto_nombre',
            'dpto_id',
            'categoria',
            'centr_lat',
            'centr_lon',
            'fuente',
            'lcen_id',
            'lcen_nombre'
        ])
