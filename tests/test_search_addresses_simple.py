import random
import itertools
from service import formatter
from service.geometry import Point
from . import GeorefLiveTest, asciifold

COMMON_ADDRESS = 'Corrientes 1000'


class SearchAddressesBaseTest(GeorefLiveTest):
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
                                       'calle.categoria',
                                       'calle_cruce_1.id',
                                       'calle_cruce_1.nombre',
                                       'calle_cruce_1.categoria',
                                       'calle_cruce_2.id',
                                       'calle_cruce_2.nombre',
                                       'calle_cruce_2.categoria',
                                       'departamento.id',
                                       'departamento.nombre',
                                       'localidad_censal.id',
                                       'localidad_censal.nombre',
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
                                       'calle.categoria',
                                       'calle_cruce_1.id',
                                       'calle_cruce_1.nombre',
                                       'calle_cruce_1.categoria',
                                       'calle_cruce_2.id',
                                       'calle_cruce_2.nombre',
                                       'calle_cruce_2.categoria',
                                       'departamento.id',
                                       'departamento.nombre',
                                       'localidad_censal.id',
                                       'localidad_censal.nombre',
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
        points = []

        for i in range(pages):
            resp = self.get_response({
                'inicio': i * page_size,
                'max': page_size,
                'direccion': COMMON_ADDRESS
            })

            for result in resp:
                points.append(result['ubicacion'])

        # Si el paginado funciona correctamente, todos los puntos obtenidos
        # deberían provenir de distintas direcciones posibles. No se deberían
        # haber repetido direcciones (ubicaciones) entre iteraciones.
        for p1, p2 in itertools.combinations(points, 2):
            self.assertNotAlmostEqual(p1['lat'], p2['lat'])
            self.assertNotAlmostEqual(p1['lon'], p2['lon'])

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
            (['0627001001535'], 'DICKSON TURNER 600'),
            (['1401401002655'], 'BALTAZAR PARDO DE FIGUEROA 600'),
            (['5002802006060'], 'PJE DR LENCINAS 700'),
            (['4202102000325'], 'AV PEDRO LURO 600'),
            (['6602805000690'], 'AV DEL BICENT DE LA BATALLA DE SALTA 1201')
        ]

        self.assert_address_search_id_matches(addresses, exact=True)

    def test_address_exact_search_ignores_case(self):
        """La búsqueda exacta debe ignorar mayúsculas y minúsculas."""
        expected = [
            (['0205601006685'], 'JOSE BARROS PAZOS 5500'),
            (['0205601006685'], 'jose barros pazos 5500'),
            (['0205601006685'], 'Jose Barros Pazos 5500'),
            (['0205601006685'], 'JoSe BaRrOs PaZoS 5500')
        ]

        self.assert_address_search_id_matches(expected, exact=True)

    def test_address_exact_search_ignores_tildes(self):
        """La búsqueda exacta debe ignorar tildes."""
        expected = [
            (['0663804007285'], 'INT MANUEL MARTIGNONÉ 250'),
            (['0663804007285'], 'INT MANUEL MARTIGNONE 250'),
            (['0663804007285'], 'INT MANUEL MARTIGNOÑE 250'),
            (['0663804007285'], 'INT MANUEL MARTIGÑONÉ 250')
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

        target = [sorted(ids) for ids, _ in term_matches]
        self.assertListEqual(target, results,
                             '\nTarget:\n{}\nResult:\n{}\n'.format(target,
                                                                   results))

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

    def test_address_number_0(self):
        """Se deberían aceptar búsquedas con altura 0."""
        data = self.get_response({
            'direccion': 'MAIPU 0'
        })
        self.assertTrue(len(data) > 0)

    def test_address_search_fuzziness(self):
        """La búsqueda aproximada debe tener una tolerancia de AUTO:4,8."""
        expected = [
            (['0676305002780'], 'RACONDEGUI 301'),      # -2 caracteres (de 8+)
            (['0676305002780'], 'ARACONDEGUI 301'),     # -1 caracteres (de 8+)
            (['0676305002780'], 'zZARACONDEGUI 301'),   # +1 caracteres (de 8+)
            (['0676305002780'], 'zZARACONDEGUIi 301'),  # +2 caracteres (de 8+)
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
            (['0209101004195'], 'CAP GRL RAMON FREIRE 2201'),
            (['0209101004195'], 'CAP GRL RAMON FREIR 2201'),
            (['0209101004195'], 'CAP GRL RAMON FREI 2201'),
            (['0209101004195'], 'CAP GRL RAMON FRE 2201'),
            (['0209101004195'], 'CAP GRL RAMON FR 2201')
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

    def test_filter_by_department_id(self):
        """Se debe poder filtrar los resultados por ID de departamento."""
        validations = []
        departments = [
            ('06252', 'Escobar'),
            ('50007', 'Capital'),
            ('82084', 'Rosario')
        ]

        for dept_code, dept_name in departments:
            res = self.get_response({
                'direccion': 'Santa fe 1000',
                'departamento': dept_code
            })

            validations.append(all(
                street['departamento']['nombre'] == dept_name for street in res
            ) and res)

        self.assertTrue(validations and all(validations))

    def test_filter_by_census_locality(self):
        """Se debe poder filtrar los resultados por ID de localidad censal."""
        validations = []
        census_localities = [
            ('06056010', 'Bahía Blanca'),
            ('14098230', 'Río Cuarto'),
            ('66126070', 'San Ramón de la Nueva Orán')
        ]

        for cloc_code, cloc_name in census_localities:
            res = self.get_response({
                'direccion': 'CORRIENTES 1000',
                'localidad_censal': cloc_code
            })

            validations.append(all(
                street['localidad_censal']['nombre'] == cloc_name
                for street in res
            ) and res)

        self.assertTrue(validations and all(validations))

    def test_filter_by_locality(self):
        """Se debería poder filtrar direcciones por localidad."""
        self.assert_locality_search(
            '0207701011160', 'Vallejos 4500', 'Villa Devoto'
        )

        self.assert_locality_search(
            '0207701011160', 'Vallejos 4500', '02077010002'
        )

        self.assert_locality_search(
            '0207701011160', 'Vallejos 4500', '02077010002'
        )

    def test_filter_by_locality_and_census_locality(self):
        """Se debería poder filtrar direcciones por localidad y localidad
        censal a la vez."""
        self.assert_locality_search(
            '8208431000190', 'Balcarce 2000', 'Gobernador Galvez',
            'Villa Gobernador Gálvez'
        )

        self.assert_locality_search(
            '8208431000190', 'Balcarce 2000', '82084310000',
            'Villa Gobernador Gálvez'
        )

        self.assert_locality_search(
            '8208431000190', 'Balcarce 2000', 'Gobernador Galvez',
            '82084310'
        )

        self.assert_locality_search(
            '8208431000190', 'Balcarce 2000', '82084310000',
            '82084310'
        )

    def assert_locality_search(self, street_id, address, locality=None,
                               census_locality=None):
        params = {
            'direccion': address,
            'max': 1
        }

        if locality:
            params['localidad'] = locality

        if census_locality:
            params['localidad_censal'] = census_locality

        resp = self.get_response(params)
        self.assertEqual(resp[0]['calle']['id'], street_id)

    def test_position(self):
        """Cuando sea posible, se debería georreferenciar la dirección
        utilizando los datos de la calle y la altura."""
        resp = self.get_response({
            'direccion': 'Billinghurst nro 650',
            'departamento': 'Comuna 5'
        })

        point_resp = Point.from_json_location(resp[0]['ubicacion'])
        point_target = Point(-58.415413, -34.602319)
        error_m = point_resp.approximate_distance_meters(point_target)

        self.assertTrue(error_m < 15, error_m)

    def test_position_no_number(self):
        """Si no se especifica una altura, se debería retornar varias
        direcciones sin altura, y con su ubicación siendo el centroide de cada
        cuadra."""
        resp = self.get_response({
            'direccion': 'Dean Funes',
            'provincia': '14'
        })

        for address in resp:
            self.assertTrue(address['ubicacion']['lat'] is not None and
                            address['ubicacion']['lon'] is not None)

    def test_position_noncontinuous_street(self):
        """Varias calles NO pueden ser representadas utilizando una única recta
        continua, ya que son interrumpidas por otras calles, edificios, etc.
        Sin embargo, al tener datos de altura cuadra por cuadra, estos
        problemas no afectan el cálculo de posición de altura.

        Este test comprueba que se puede georreferenciar una dirección sobre
        una calle (Arribeños, CABA) que NO es continua. Antes de incorporar los
        datos de cuadras en la API, esto no era posible.
        """
        resp = self.get_response({
            'direccion': 'Arribeños 2230',
            'departamento': 'Comuna 13'
        })

        for address in resp:
            self.assertTrue(address['ubicacion']['lat'] is not None and
                            address['ubicacion']['lon'] is not None)

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
                'campos': 'calle.nombre,calle.categoria'
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
            },
            {
                'direccion': COMMON_ADDRESS,
                'localidad': 'San Nicolás'
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
            'campos': 'nombre,categoria,ubicacion.lat'
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
            'direccion': COMMON_ADDRESS,
            'campos': 'completo'
        })

        headers = next(resp)
        self.assertListEqual(headers, ['direccion_nomenclatura',
                                       'calle_nombre',
                                       'calle_id',
                                       'calle_categoria',
                                       'altura_valor',
                                       'altura_unidad',
                                       'calle_cruce_1_nombre',
                                       'calle_cruce_1_id',
                                       'calle_cruce_1_categoria',
                                       'calle_cruce_2_nombre',
                                       'calle_cruce_2_id',
                                       'calle_cruce_2_categoria',
                                       'piso',
                                       'provincia_id',
                                       'provincia_nombre',
                                       'departamento_id',
                                       'departamento_nombre',
                                       'localidad_censal_id',
                                       'localidad_censal_nombre',
                                       'direccion_lat',
                                       'direccion_lon',
                                       'direccion_fuente'])

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
