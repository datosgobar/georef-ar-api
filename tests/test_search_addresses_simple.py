import unittest
import random
from service import formatter
from . import GeorefLiveTest, asciifold

COMMON_ADDRESS = 'Corrientes 1000'


class SearchAddressesBaseTest(GeorefLiveTest):
    def assert_default_results_fields(self, address):
        """Las entidades devueltas deben tener los campos default."""
        data = self.get_response({'direccion': address, 'max': 1})[0]
        fields = sorted([
            'altura',
            'piso',
            'calle',
            'calle_cruce_1',
            'calle_cruce_2',
            'departamento',
            'nomenclatura',
            'provincia',
            'ubicacion'
        ])
        self.assertListEqual(fields, sorted(data.keys()))

    def assert_basic_fields_set(self, address):
        """Se debería poder especificar un conjunto de parámetros
        preseleccionados llamado 'basico'."""
        self.assert_fields_set_equals('basico', ['calle.id', 'calle.nombre',
                                                 'altura.valor',
                                                 'calle_cruce_1.id',
                                                 'calle_cruce_1.nombre',
                                                 'calle_cruce_2.id',
                                                 'calle_cruce_2.nombre',
                                                 'nomenclatura'],
                                      {'direccion': address})

    def assert_standard_fields_set(self, address):
        """Se debería poder especificar un conjunto de parámetros
        preseleccionados llamado 'estandar'."""
        self.assert_fields_set_equals('estandar',
                                      ['altura.valor', 'altura.unidad',
                                       'piso',
                                       'calle.id', 'calle.nombre',
                                       'calle.tipo',
                                       'calle_cruce_1.id',
                                       'calle_cruce_1.nombre',
                                       'calle_cruce_1.tipo',
                                       'calle_cruce_2.id',
                                       'calle_cruce_2.nombre',
                                       'calle_cruce_2.tipo',
                                       'departamento.id',
                                       'departamento.nombre',
                                       'nomenclatura',
                                       'provincia.id', 'provincia.nombre',
                                       'ubicacion.lat', 'ubicacion.lon'],
                                      {'direccion': address})

    def assert_complete_fields_set(self, address):
        """Se debería poder especificar un conjunto de parámetros
        preseleccionados llamado 'completo'."""
        self.assert_fields_set_equals('completo',
                                      ['altura.valor', 'altura.unidad',
                                       'piso',
                                       'calle.id', 'calle.nombre',
                                       'calle.tipo',
                                       'calle_cruce_1.id',
                                       'calle_cruce_1.nombre',
                                       'calle_cruce_1.tipo',
                                       'calle_cruce_2.id',
                                       'calle_cruce_2.nombre',
                                       'calle_cruce_2.tipo',
                                       'departamento.id',
                                       'departamento.nombre',
                                       'nomenclatura',
                                       'provincia.id', 'provincia.nombre',
                                       'ubicacion.lat', 'ubicacion.lon',
                                       'fuente'],
                                      {'direccion': address})


class SearchAddressesSimpleTest(SearchAddressesBaseTest):
    """Pruebas de búsqueda por dirección de tipo 'simple'."""

    def setUp(self):
        self.endpoint = '/api/v1.0/direcciones'
        self.entity = 'direcciones'
        super().setUp()

    def test_max_results_returned(self):
        """La cantidad máxima de resultados debe ser configurable."""
        lengths = [1, 4, 9, 10]
        results_lengths = [
            len(self.get_response({
                'max': length,
                'direccion': COMMON_ADDRESS
            }))
            for length in lengths
        ]

        self.assertListEqual(lengths, results_lengths)

    def test_id_length(self):
        """El ID de la entidad debe tener la longitud correcta."""
        data = self.get_response({'direccion': COMMON_ADDRESS, 'max': 1})[0]
        self.assertTrue(len(data['calle']['id']) == 13)

    def test_pagination(self):
        """Los resultados deberían poder ser paginados."""
        page_size = 10
        pages = 5
        results = set()

        for i in range(pages):
            resp = self.get_response({
                'inicio': i * page_size,
                'max': page_size,
                'direccion': COMMON_ADDRESS
            })

            for result in resp:
                results.add(result['calle']['id'])

        # Si el paginado funciona correctamente, no deberían haberse repetido
        # IDs de entidades entre resultados.
        self.assertEqual(len(results), page_size * pages)

    def test_flatten_results(self):
        """Los resultados se deberían poder obtener en formato aplanado."""
        data = self.get_response({
            'direccion': COMMON_ADDRESS,
            'max': 1,
            'aplanar': True
        })[0]

        self.assertTrue(all([
            not isinstance(v, dict) for v in data.values()
        ]) and data)

    def test_default_results_fields(self):
        """Las entidades devueltas deben tener los campos default."""
        self.assert_default_results_fields(COMMON_ADDRESS)

    def test_basic_fields_set(self):
        """Se debería poder especificar un conjunto de parámetros
        preseleccionados llamado 'basico'."""
        self.assert_basic_fields_set(COMMON_ADDRESS)

    def test_standard_fields_set(self):
        """Se debería poder especificar un conjunto de parámetros
        preseleccionados llamado 'estandar'."""
        self.assert_standard_fields_set(COMMON_ADDRESS)

    def test_complete_fields_set(self):
        """Se debería poder especificar un conjunto de parámetros
        preseleccionados llamado 'completo'."""
        self.assert_complete_fields_set(COMMON_ADDRESS)

    def test_filter_results_fields(self):
        """Los campos de las direcciones devueltas deben ser filtrables."""
        fields_lists = [
            ['fuente', 'ubicacion.lat', 'ubicacion.lon'],
            ['fuente', 'piso', 'ubicacion.lat'],
            ['departamento.id', 'ubicacion.lat']
        ]
        for field_list in fields_lists:
            field_list.extend(['calle_cruce_1.nombre', 'calle_cruce_1.id',
                               'calle_cruce_2.nombre', 'calle_cruce_2.id',
                               'calle.id', 'calle.nombre', 'altura.valor',
                               'nomenclatura'])

        fields_lists = [sorted(l) for l in fields_lists]

        fields_results = []

        for fields in fields_lists:
            data = self.get_response({
                'campos': ','.join(fields),
                'direccion': COMMON_ADDRESS,
                'max': 1
            })
            formatter.flatten_dict(data[0], sep='.')
            fields_results.append(sorted(data[0].keys()))

        self.assertListEqual(fields_lists, fields_results)

    def test_no_number_returns_null(self):
        """Si se especifica una dirección sin altura, se debería normalizar por
        lo menos el nombre de la calle, y el resultado debería tener null como
        valor para la altura."""
        response = self.get_response({
            'direccion': 'Mattieto',
            'departamento': '82084'
        })

        self.assertTrue(all(
            addr['altura']['valor'] is None
            for addr in response
        ))

    def test_name_ordering(self):
        """Los resultados deben poder ser ordenados por nombre."""
        resp = self.get_response({
            'direccion': 'santa fe 1000',
            'orden': 'nombre',
            'max': 1000
        })

        ordered = [r['calle']['nombre'] for r in resp]
        expected = sorted(ordered, key=asciifold)
        self.assertListEqual(ordered, expected)

    def test_id_ordering(self):
        """Los resultados deben poder ser ordenados por ID."""
        resp = self.get_response({
            'direccion': 'corrientes 1000',
            'orden': 'id',
            'max': 1000
        })

        ordered = [r['calle']['id'] for r in resp]
        expected = sorted(ordered)
        self.assertListEqual(ordered, expected)

    def test_invalid_address_search(self):
        """Si se busca una dirección que no peude ser interpretada por la
        librería georef-ar-address, se deberían traer 0 resultados."""
        resp = self.get_response({
            'direccion': 'Tucumán y Corrientes y López'
        })

        self.assertEqual(len(resp), 0)

    def test_address_exact_match(self):
        """La búsqueda exacta debe devolver las direcciones
        correspondientes."""
        addresses = [
            (['0208401007915'], 'MANUELA PEDRAZA 1500'),
            (['0627001001540'], 'DICKSON TURNER 600'),
            (['1401401002655'], 'BALTAZAR PARDO DE FIGUEROA 600'),
            (['5002802006060'], 'PJE DR LENCINAS 700'),
            (['4202102000325'], 'AV PEDRO LURO 100'),
            (['6602805000690'], 'AV DEL BICENT DE LA BATALLA DE SALTA 1200')
        ]

        self.assert_address_search_id_matches(addresses, exact=True)

    def test_address_exact_search_ignores_case(self):
        """La búsqueda exacta debe ignorar mayúsculas y minúsculas."""
        expected = [
            (['0205601006685'], 'JOSE BARROS PAZOS 5000'),
            (['0205601006685'], 'jose barros pazos 5000'),
            (['0205601006685'], 'Jose Barros Pazos 5000'),
            (['0205601006685'], 'JoSe BaRrOs PaZoS 5000')
        ]

        self.assert_address_search_id_matches(expected, exact=True)

    def test_address_exact_search_ignores_tildes(self):
        """La búsqueda exacta debe ignorar tildes."""
        expected = [
            (['0663804007285'], 'INT MANUEL MARTIGNONÉ 500'),
            (['0663804007285'], 'INT MANUEL MARTIGNONE 500'),
            (['0663804007285'], 'INT MANUEL MARTIGNOÑE 500'),
            (['0663804007285'], 'INT MANUEL MARTIGÑONÉ 500')
        ]

        self.assert_address_search_id_matches(expected, exact=True)

    def assert_address_search_id_matches(self, term_matches, exact=False):
        results = []
        for code, query in term_matches:
            params = {'direccion': query, 'provincia': code[0][:2]}
            if exact:
                params['exacto'] = 1
            res = self.get_response(params)
            results.append(sorted([p['calle']['id'] for p in res]))

        self.assertListEqual([sorted(ids) for ids, _ in term_matches], results)

    def test_address_exact_gibberish_search(self):
        """La búsqueda exacta debe devolver 0 resultados cuando se utiliza una
        dirección no existente."""
        data = self.get_response({'direccion': 'FoobarFoobar 1', 'exacto': 1})
        self.assertTrue(len(data) == 0)

    def test_address_wrong_number_search(self):
        """La búsqueda debe devolver 0 resultados cuando se utiliza una altura
        no existente."""
        data = self.get_response({
            'direccion': 'ANGEL PELUFFO 1000000',
            'provincia': '02'
        })
        self.assertTrue(len(data) == 0)

    def test_address_search_fuzziness(self):
        """La búsqueda aproximada debe tener una tolerancia de AUTO:4,8."""
        expected = [
            (['0676305002780'], 'RACONDEGUI 500'),      # -2 caracteres (de 8+)
            (['0676305002780'], 'ARACONDEGUI 500'),     # -1 caracteres (de 8+)
            (['0676305002780'], 'zZARACONDEGUI 500'),   # +1 caracteres (de 8+)
            (['0676305002780'], 'zZARACONDEGUIi 500'),  # +2 caracteres (de 8+)
            (['0202801006430'], 'NCLAN 3000'),         # -1 caracteres (de 4-7)
            (['0202801006430'], 'iINCLAN 3000')        # +1 caracteres (de 4-7)
        ]

        self.assert_address_search_id_matches(expected)

    def test_address_search_number_limits(self):
        """La búsqueda debe funcionar cuando la altura epecificada se encuentra
         dentro del límite inferior derecho y el límite superior izquierdo."""
        expected = [
            (['1401401002760'], 'BARTOLOME ARGENSOLA 100'),  # desde_d
            (['1401401002760'], 'BARTOLOME ARGENSOLA 1999')  # hasta_i
        ]

        self.assert_address_search_id_matches(expected)

    def test_address_search_autocompletes(self):
        """La búsqueda aproximada debe también actuar como autocompletar cuando
        la longitud de la query es >= 4."""
        expected = [
            (['0207701007975'], 'MARCOS SASTRE 2600'),
            (['0207701007975'], 'MARCOS SASTR 2600'),
            (['0207701007975'], 'MARCOS SAST 2600'),
            (['0207701007975'], 'MARCOS SAS 2600'),
            (['0209101004195', '0208401004195'], 'CAP GRL RAMON FREIRE 2000'),
            (['0209101004195', '0208401004195'], 'CAP GRL RAMON FREIR 2000'),
            (['0209101004195', '0208401004195'], 'CAP GRL RAMON FREI 2000'),
            (['0209101004195', '0208401004195'], 'CAP GRL RAMON FRE 2000'),
            (['0209101004195', '0208401004195'], 'CAP GRL RAMON FR 2000')
        ]

        self.assert_address_search_id_matches(expected)

    def test_address_search_stopwords(self):
        """La búsqueda aproximada debe ignorar stopwords."""
        expected = [
            (['8208427005185'], 'HILARION DE LA QUINTANA BIS 100'),
            (['8208427005185'], 'HILARION DE DE QUINTANA BIS 100'),
            (['8208427005185'], 'HILARION DE DE LA QUINTANA BIS 100'),
            (['8208427005185'], 'HILARION DE LA LA QUINTANA BIS 100'),
            (['8208427005185'], 'HILARION DE DE LA LA LA QUINTANA BIS 100'),
        ]

        self.assert_address_search_id_matches(expected)

    def test_address_search_fuzzy_various(self):
        """La búsqueda aproximada debe devolver las direcciones correctas
        incluso cuando el usuario comite varios errores (mayúsculas, tildes,
        stopwords, letras incorrectas, etc.)."""
        expected = [
            (['0662310000330'], 'bv paraguay 1000'),
            (['0662310000330'], 'boulevar paraguay 1000'),
            (['0662310000330'], 'boulevár paraguay 1000'),
            (['5804201000085'], 'avenida estanislao flore 1000'),
            (['5804201000085'], 'av estanislao flore 1000'),
            (['5804201000085'], 'AV ESTANISLAOOO FLORES 1000'),
            (['8208427000835'], 'AVenide ESTANISLAO lope 1000'),
            (['0203501005600'], 'FRANCISCO ACUñA DE FIGUERO 1000'),
            (['0203501005600'], 'fransisco acuna figeroa 1000')
        ]

        self.assert_address_search_id_matches(expected)

    def test_filter_by_state_name(self):
        """Se debe poder filtrar los resultados por nombre de provincia."""
        validations = []

        states = [
            ('02', 'CIUDAD AUTÓNOMA DE BUENOS AIRES'),
            ('06', 'BUENOS AIRES'),
            ('14', 'CÓRDOBA')
        ]

        for state_code, state_name in states:
            res = self.get_response({
                'direccion': COMMON_ADDRESS,
                'provincia': state_name,
                'exacto': True
            })

            validations.append(all(
                street['provincia']['id'] == state_code for street in res
            ))

        self.assertTrue(validations and all(validations))

    def test_filter_by_state_id(self):
        """Se debe poder filtrar los resultados por ID de provincia."""
        validations = []

        states = [
            ('02', 'Ciudad Autónoma de Buenos Aires'),
            ('06', 'Buenos Aires'),
            ('14', 'Córdoba')
        ]

        for state_code, state_name in states:
            res = self.get_response({
                'direccion': COMMON_ADDRESS,
                'provincia': state_code
            })

            validations.append(all(
                street['provincia']['nombre'] == state_name for street in res
            ))

        self.assertTrue(validations and all(validations))

    def test_filter_by_department_name(self):
        """Se debe poder filtrar los resultados por nombre de departamento."""
        validations = []
        departments = [
            ('02007', 'COMUNA 1'),
            ('02105', 'COMUNA 15'),
            ('66147', 'ROSARIO DE LERMA')
        ]

        for dept_code, dept_name in departments:
            res = self.get_response({
                'direccion': 'AV CORRIENTES 1000',
                'departamento': dept_name,
                'exacto': True
            })

            validations.append(all(
                street['departamento']['id'] == dept_code for street in res
            ))

        self.assertTrue(validations and all(validations))

    def test_filter_by_department_id(self):
        """Se debe poder filtrar los resultados por ID de departamento."""
        validations = []
        departments = [
            ('02007', 'Comuna 1'),
            ('02105', 'Comuna 15'),
            ('66147', 'Rosario de Lerma')
        ]

        for dept_code, dept_name in departments:
            res = self.get_response({
                'direccion': 'AV CORRIENTES 1000',
                'departamento': dept_code
            })

            validations.append(all(
                street['departamento']['nombre'] == dept_name for street in res
            ))

        self.assertTrue(validations and all(validations))

    def test_empty_params(self):
        """Los parámetros que esperan valores no pueden tener valores
        vacíos."""
        params = ['direccion', 'tipo', 'departamento', 'provincia', 'max',
                  'campos']
        self.assert_empty_params_return_400(params)

    def test_unknown_param_returns_400(self):
        """El endpoint no debe aceptar parámetros desconocidos."""
        self.assert_unknown_param_returns_400()

    def test_bulk_empty_400(self):
        """La búsqueda bulk vacía debería retornar un error 400."""
        status = self.get_response(method='POST', body={},
                                   return_value='status', expect_status=[400])
        self.assertEqual(status, 400)

    def test_bulk_response_len(self):
        """La longitud de la respuesta bulk debería ser igual a la cantidad
        de queries envíadas."""
        req_len = random.randint(10, 20)
        query = {
            'direccion': COMMON_ADDRESS
        }

        body = {
            'direcciones': [query] * req_len
        }

        results = self.get_response(method='POST', body=body)
        self.assertEqual(len(results), req_len)

    def test_bulk_equivalent(self):
        """Los resultados de una query envíada vía bulk deberían ser idénticos a
        los resultados de una query individual (GET)."""
        queries = [
            {
                'direccion': COMMON_ADDRESS
            },
            {
                'direccion': COMMON_ADDRESS,
                'max': 3
            },
            {
                'direccion': COMMON_ADDRESS,
                'campos': 'calle.nombre,calle.tipo'
            },
            {
                'direccion': COMMON_ADDRESS,
                'provincia': '14'
            },
            {
                'direccion': COMMON_ADDRESS,
                'departamento': '06805'
            },
            {
                'direccion': COMMON_ADDRESS,
                'exacto': True
            },
            {
                'direccion': COMMON_ADDRESS,
                'aplanar': True
            }
        ]

        individual_results = []
        for query in queries:
            individual_results.append(self.get_response(params=query,
                                                        return_value='full'))

        bulk_results = self.get_response(method='POST', body={
            'direcciones': queries
        })

        self.assertEqual(individual_results, bulk_results)

    def test_json_format(self):
        """Por default, los resultados de una query deberían estar en
        formato JSON."""
        default_response = self.get_response({'direccion': COMMON_ADDRESS})
        json_response = self.get_response({
            'formato': 'json',
            'direccion': COMMON_ADDRESS
        })
        self.assertEqual(default_response, json_response)

    def test_csv_format_query(self):
        """Se debería poder obtener resultados en formato
        CSV (con parámetros)."""
        self.assert_valid_csv({
            'direccion': COMMON_ADDRESS,
            'campos': 'nombre,tipo,ubicacion.lat'
        })

    def test_empty_csv_valid(self):
        """Una consulta CSV con respuesta vacía debería ser CSV válido."""
        self.assert_valid_csv({
            'direccion': 'foobarfoobar 100'
        })

    def test_csv_fields(self):
        """Una consulta CSV debería tener ciertos campos, ordenados de una
        forma específica."""
        resp = self.get_response({
            'formato': 'csv',
            'direccion': COMMON_ADDRESS
        })

        headers = next(resp)
        self.assertListEqual(headers, ['direccion_nomenclatura',
                                       'calle_nombre',
                                       'calle_id',
                                       'calle_tipo',
                                       'altura_valor',
                                       'altura_unidad',
                                       'calle_cruce_1_nombre',
                                       'calle_cruce_1_id',
                                       'calle_cruce_1_tipo',
                                       'calle_cruce_2_nombre',
                                       'calle_cruce_2_id',
                                       'calle_cruce_2_tipo',
                                       'piso',
                                       'provincia_id',
                                       'provincia_nombre',
                                       'departamento_id',
                                       'departamento_nombre',
                                       'direccion_lat',
                                       'direccion_lon'])

    def test_csv_empty_value(self):
        """Un valor vacío (None) debería estar representado como '' en CSV."""
        resp = self.get_response({
            'formato': 'csv',
            'direccion': 'NAON 1200',
            'departamento': 6427,  # 0 inicial agregado por API
            'max': 1
        })

        header = next(resp)
        row = next(resp)
        self.assertTrue(row[header.index('direccion_lat')] == '' and
                        row[header.index('direccion_lon')] == '')

    def test_geojson_format(self):
        """Se debería poder obtener resultados en formato
        GEOJSON (sin parámetros)."""
        self.assert_valid_geojson({'direccion': COMMON_ADDRESS})

    def test_xml_format_query(self):
        """Se debería poder obtener resultados en formato XML (con
        parámetros)."""
        self.assert_valid_xml({
            'direccion': COMMON_ADDRESS
        })


if __name__ == '__main__':
    unittest.main()
