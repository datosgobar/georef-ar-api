import random
from service import formatter
from . import GeorefLiveTest, asciifold


class SearchStreetsTest(GeorefLiveTest):
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

    def test_name_ordering(self):
        """Los resultados deben poder ser ordenados por nombre."""
        resp = self.get_response({
            'orden': 'nombre',
            'max': 100
        })

        ordered = [r['nombre'] for r in resp]
        expected = sorted(ordered, key=asciifold)

        self.assertListEqual(ordered, expected)

    def test_id_ordering(self):
        """Los resultados deben poder ser ordenados por ID."""
        resp = self.get_response({
            'orden': 'id',
            'max': 1000
        })

        ordered = [r['id'] for r in resp]
        expected = sorted(ordered)
        self.assertListEqual(ordered, expected)

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

    def test_filter_results_fields(self):
        """Los campos de las direcciones devueltas deben ser filtrables."""
        fields_lists = [
            ['fuente', 'id', 'nombre'],
            ['fuente', 'id', 'nombre', 'nomenclatura'],
            ['departamento.nombre', 'fuente', 'id', 'nombre'],
            ['fuente', 'id', 'altura.inicio.derecha', 'nombre'],
        ]
        fields_lists = [sorted(l) for l in fields_lists]
        fields_results = []

        for fields in fields_lists:
            data = self.get_response({
                'campos': ','.join(fields),
                'max': 1
            })
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
                                      ['id', 'nombre',
                                       'altura.fin.derecha',
                                       'altura.fin.izquierda',
                                       'altura.inicio.derecha',
                                       'altura.inicio.izquierda',
                                       'departamento.id',
                                       'departamento.nombre',
                                       'localidad_censal.id',
                                       'localidad_censal.nombre',
                                       'nomenclatura',
                                       'provincia.id', 'provincia.nombre',
                                       'categoria'])

    def test_complete_fields_set(self):
        """Se debería poder especificar un conjunto de parámetros
        preseleccionados llamado 'completo'."""
        self.assert_fields_set_equals('completo',
                                      ['id', 'fuente', 'nombre',
                                       'altura.fin.derecha',
                                       'altura.fin.izquierda',
                                       'altura.inicio.derecha',
                                       'altura.inicio.izquierda',
                                       'departamento.id',
                                       'departamento.nombre',
                                       'localidad_censal.id',
                                       'localidad_censal.nombre',
                                       'nomenclatura',
                                       'provincia.id', 'provincia.nombre',
                                       'categoria'])

    def test_field_prefixes(self):
        """Se debería poder especificar prefijos de otros campos como campos
        a incluir en la respuesta."""
        self.assert_fields_set_equals('altura', ['id', 'nombre',
                                                 'altura.fin.derecha',
                                                 'altura.fin.izquierda',
                                                 'altura.inicio.derecha',
                                                 'altura.inicio.izquierda'])

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

    def test_search_street_type(self):
        """Se debe poder especificar el tipo de calle en la búsqueda."""
        validations = []
        street_types = [
            ('AV', 'avenida'),
            ('RUTA', 'ruta'),
            ('AUT', 'autopista'),
            ('CALLE', 'calle'),
            ('PJE', 'pasaje')
        ]

        for street_type, street_type_long in street_types:
            res = self.get_response({
                'categoria': street_type_long,
                'max': 100
            })

            validations.append(len(res) > 0)
            validations.append(all(
                street['categoria'] == street_type for street in res
            ))

        assert(validations and all(validations))

    def test_id_search(self):
        """Se debería poder buscar calles por ID."""
        identifier = '8208416001280'
        data = self.get_response({'id': identifier})[0]

        self.assertEqual(identifier, data['id'])

    def test_flatten_results(self):
        """Los resultados se deberían poder obtener en formato aplanado."""
        data = self.get_response({'max': 1, 'aplanar': True})[0]

        self.assertTrue(all([
            not isinstance(v, dict) for v in data.values()
        ]) and data)

    def test_bulk_response_len(self):
        """La longitud de la respuesta bulk debería ser igual a la cantidad
        de queries envíadas."""
        req_len = random.randint(10, 20)
        query = {
            'nombre': 'SANTA FE'
        }

        body = {
            'calles': [query] * req_len
        }

        results = self.get_response(method='POST', body=body)
        self.assertEqual(len(results), req_len)

    def test_bulk_basic(self):
        """La búsqueda de una query sin parámetros debería funcionar
        correctamente."""
        results = self.get_response(method='POST', body={
            'calles': [{}]
        })

        first = results[0]
        self.assertTrue(len(results) == 1 and len(first['calles']) == 10)

    def test_bulk_equivalent(self):
        """Los resultados de una query envíada vía bulk deberían ser idénticos a
        los resultados de una query individual (GET)."""
        queries = [
            {
                'nombre': 'CORRIENTES'
            },
            {
                'categoria': 'avenida'
            },
            {
                'max': 3
            },
            {
                'id': '8208416001280'
            },
            {
                'campos': 'nombre,categoria'
            },
            {
                'provincia': '02'
            },
            {
                'departamento': '06805'
            },
            {
                'exacto': True,
                'nombre': 'LISANDRO DE LA TORRE'
            }
        ]

        individual_results = []
        for query in queries:
            individual_results.append(self.get_response(params=query,
                                                        return_value='full'))

        bulk_results = self.get_response(method='POST', body={
            'calles': queries
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
            'nombre': 'SANTA FE',
            'campos': 'nombre,id,categoria'
        })

    def test_csv_fields(self):
        """Una consulta CSV debería tener ciertos campos, ordenados de una
        forma específica."""
        resp = self.get_response({'formato': 'csv', 'campos': 'completo'})
        headers = next(resp)
        self.assertListEqual(headers, ['calle_id',
                                       'calle_nombre',
                                       'calle_altura_inicio_derecha',
                                       'calle_altura_inicio_izquierda',
                                       'calle_altura_fin_derecha',
                                       'calle_altura_fin_izquierda',
                                       'calle_nomenclatura',
                                       'calle_categoria',
                                       'provincia_id',
                                       'provincia_nombre',
                                       'departamento_id',
                                       'departamento_nombre',
                                       'localidad_censal_id',
                                       'localidad_censal_nombre',
                                       'calle_fuente'])

    def test_xml_format(self):
        """Se debería poder obtener resultados en formato XML (sin
        parámetros)."""
        self.assert_valid_xml()

    def test_xml_format_query(self):
        """Se debería poder obtener resultados en formato XML (con
        parámetros)."""
        self.assert_valid_xml({
            'max': 100,
            'nombre': 'mayo',
            'categoria': 'avenida'
        })

    def test_shp_format(self):
        """Se debería poder obtener resultados en formato SHP (sin
        parámetros)."""
        self.assert_valid_shp_type(
            shape_type=3,  # 3 == POLYLINE
            params={'max': 1}
        )

    def test_shp_format_query(self):
        """Se debería poder obtener resultados en formato SHP (con
        parámetros)."""
        self.assert_valid_shp_query({
            'max': 500,
            'campos': 'completo',
            'categoria': 'avenida'
        })

    def test_shp_record_fields(self):
        """Los campos obtenidos en formato SHP deberían ser los esperados y
        deberían corresponder a los campos obtenidos en otros formatos."""
        self.assert_shp_fields('completo', [
            'nombre',
            'nomencla',
            'id',
            'prov_id',
            'prov_nombre',
            'dpto_nombre',
            'dpto_id',
            'categoria',
            'alt_ini_der',
            'alt_ini_izq',
            'alt_fin_der',
            'alt_fin_izq',
            'fuente',
            'lcen_id',
            'lcen_nombre'
        ])
