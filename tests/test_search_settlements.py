import random
from service import formatter
from . import GeorefLiveTest, asciifold
from .test_search_states import STATES


SETTLEMENTS = [
    (['06007000007'], 'CASEY'),
    (['14007000030'], 'FALDA DE LOS REARTES'),
    (['82021000008'], 'CAMPO AMBROGGIO'),
    (['26007000010'], 'EL RIACHO SAN JOSE'),
    (['26056010000'], 'ALDEA EPULEF'),
    (['94021000011'], 'PUERTO ARGENTINO'),
    (['94015010000'], 'LAGUNA ESCONDIDA')
]


class SearchSettlementTest(GeorefLiveTest):
    """Pruebas de búsqueda de asentamientos (índice de asentamientos)."""

    def setUp(self):
        self.endpoint = '/api/asentamientos'
        self.entity = 'asentamientos'
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
        """La búsqueda por ID debe devolver el asentamiento correspondiente."""
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
        """Los asentamientos con departamento nulo deberían ser válidos y
        existir en la API."""
        resp = self.get_response({'id': '02000010000'})
        self.assertTrue(resp[0]['departamento']['id'] is None and
                        resp[0]['departamento']['nombre'] is None)

    def test_total_results(self):
        """Dada una query sin parámetros, se deben retornar los metadatos de
        resultados apropiados."""
        resp = self.get_response(return_value='full')
        self.assertTrue(resp['cantidad'] == 10 and resp['inicio'] == 0)

    def test_filter_results_fields(self):
        """Los campos de los asentamientos devueltos deben ser filtrables."""
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
        """La búsqueda por nombre exacto debe devolver los asentamientos
         correspondientes."""
        self.assert_name_search_id_matches(SETTLEMENTS, exact=True)

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

    def test_code_prefix(self):
        """Los IDs de los asentamientos deben comenzar con el ID de sus
        provincias."""
        data = self.get_response({'max': 25})
        results = [
            mun['id'].startswith(mun['provincia']['id'])
            for mun in data
        ]

        self.assertTrue(all(results) and results)

    def test_search_by_state(self):
        """Se debe poder buscar asentamientos por provincia."""
        state = random.choice(STATES)
        state_id, state_name = state[0][0], state[1]

        data = self.get_response({'provincia': state_id})
        data.extend(self.get_response({'provincia': state_name}))
        data.extend(self.get_response({'provincia': state_name, 'exacto': 1}))

        results = [loc['id'].startswith(state_id) for loc in data]
        self.assertTrue(all(results) and results)

    def test_search_by_department(self):
        """Se debe poder buscar asentamientos por departamento."""

        # Algunos departamentos no tienen asentamientos, por el momento buscar
        # utilizando un departamento que sabemos contiene una o mas
        dept_id, dept_name = '70119', 'Valle Fértil'

        data = self.get_response({'departamento': dept_id})
        data.extend(self.get_response({'departamento': dept_name}))
        data.extend(self.get_response({
            'departamento': dept_name,
            'exacto': 1
        }))

        results = [loc['departamento']['id'] == dept_id for loc in data]
        self.assertTrue(all(results) and results)

    def test_search_by_municipality(self):
        """Se debe poder buscar asentamientos por municipio."""

        # Algunos municipios no tienen asentamientos, por el momento buscar
        # utilizando un municipio que sabemos contiene una o mas
        mun_id, mun_name = '100224', 'Fiambalá'

        data = self.get_response({'municipio': mun_id})
        data.extend(self.get_response({'municipio': mun_name}))
        data.extend(self.get_response({'municipio': mun_name, 'exacto': 1}))

        results = [loc['municipio']['id'] == mun_id for loc in data]
        self.assertTrue(all(results) and results)

    def test_search_by_census_locality(self):
        """Se debe poder buscar entidades por localidad censal."""
        # Tomar una localidad censal que tiene asentamientos
        cloc_id = '06252010'
        data = self.get_response({'localidad_censal': cloc_id})
        self.assertTrue(data and all([
            loc['localidad_censal']['nombre'] == 'Escobar' for loc in data
        ]))

    def test_flat_results(self):
        """El parametro aplanar deberia aplanar los resultados devueltos."""
        self.assert_flat_results()

    def test_bulk_response_len(self):
        """La longitud de la respuesta bulk debería ser igual a la cantidad
        de queries envíadas."""
        req_len = random.randint(10, 20)
        query = {
            'nombre': 'CAPILLA'
        }

        body = {
            'asentamientos': [query] * req_len
        }

        results = self.get_response(method='POST', body=body)
        self.assertEqual(len(results), req_len)

    def test_bulk_basic(self):
        """La búsqueda de una query sin parámetros debería funcionar
        correctamente."""
        results = self.get_response(method='POST', body={
            'asentamientos': [{}]
        })

        first = results[0]
        self.assertTrue(len(results) == 1 and
                        len(first['asentamientos']) == 10)

    def test_bulk_equivalent(self):
        """Los resultados de una query envíada vía bulk deberían ser idénticos
        a los resultados de una query individual (GET)."""
        queries = [
            {
                'nombre': 'BARRIO'
            },
            {
                'id': '14007000022'
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
                'orden': 'nombre'
            },
            {
                'exacto': True,
                'nombre': 'VILLA TRONQUILS'
            }
        ]

        individual_results = []
        for query in queries:
            individual_results.append(self.get_response(params=query,
                                                        return_value='full'))

        bulk_results = self.get_response(method='POST', body={
            'asentamientos': queries
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
