import unittest
from service import app
from . import SearchEntitiesTest, asciifold

VALID_ADDRESS = 'Corrientes 1000'

class SearchAddressesTest(SearchEntitiesTest):
    """Pruebas de búsqueda por dirección."""

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
                'direccion': VALID_ADDRESS
            }))
            for length in lengths
        ]

        self.assertListEqual(lengths, results_lengths)

    def test_id_length(self):
        """El ID de la entidad debe tener la longitud correcta."""
        data = self.get_response({'direccion': VALID_ADDRESS, 'max': 1})[0]
        self.assertTrue(len(data['id']) == 13)

    def test_flatten_results(self):
        """Los resultados se deberían poder obtener en formato aplanado."""
        data = self.get_response({
            'direccion': VALID_ADDRESS,
            'max': 1,
            'aplanar': True
        })[0]

        self.assertTrue(all([
            not isinstance(v, dict) for v in data.values()
        ]) and data)

    def test_default_results_fields(self):
        """Las entidades devueltas deben tener los campos default."""
        data = self.get_response({'direccion': VALID_ADDRESS, 'max': 1})[0]
        fields = sorted([
            'altura',
            'departamento',
            'id',
            'nombre',
            'nomenclatura',
            'fuente',
            'provincia',
            'tipo',
            'ubicacion'
        ])
        self.assertListEqual(fields, sorted(data.keys()))

    def test_filter_results_fields(self):
        """Los campos de las direcciones devueltas deben ser filtrables."""
        fields_lists = [
            ['altura', 'fuente', 'id', 'nombre', 'ubicacion'],
            ['altura', 'fuente', 'id', 'nombre', 'nomenclatura',
                'ubicacion'],
            ['altura', 'departamento', 'fuente', 'id', 'nombre',
                'ubicacion']
        ]
        fields_results = []

        for fields in fields_lists:
            data = self.get_response({
                'campos': ','.join(fields),
                'direccion': VALID_ADDRESS,
                'max': 1
            })
            fields_results.append(sorted(data[0].keys()))

        self.assertListEqual(fields_lists, fields_results)

    def test_no_number_returns_400(self):
        """La búsqueda debe fallar si no se especifica una altura."""
        response = self.app.get(self.endpoint + '?direccion=Corrientes')
        self.assertEqual(response.status_code, 400)

    def test_number_0_returns_400(self):
        """La búsqueda debe fallar si la altura es cero."""
        response = self.app.get(self.endpoint + '?direccion=Corrientes 0')
        self.assertEqual(response.status_code, 400)

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
            results.append(sorted([p['id'] for p in res]))

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
            (['0676305002780'], 'RACONDEGUI 500'),     # -2 caracteres (de 8+)
            (['0676305002780'], 'ARACONDEGUI 500'),    # -1 caracteres (de 8+)
            (['0676305002780'], 'zZARACONDEGUI 500'),  # +1 caracteres (de 8+)
            (['0676305002780'], 'zZARACONDEGUIi 500'), # +2 caracteres (de 8+)
            (['0202801006430'], 'NCLAN 3000'),         # -1 caracteres (de 4-7)
            (['0202801006430'], 'iINCLAN 3000')        # +1 caracteres (de 4-7)
        ]

        self.assert_address_search_id_matches(expected)

    def test_address_search_number_limits(self):
        """La búsqueda debe funcionar cuando la altura epecificada se encuentra
         dentro del límite inferior derecho y el límite superior izquierdo."""
        expected = [
            (['1401401002760'], 'BARTOLOME ARGENSOLA 100'), # desde_d
            (['1401401002760'], 'BARTOLOME ARGENSOLA 1999') # hasta_i
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
            (['0207701007975'], 'MARCOS SA 2600'),
            (['0209101004195', '0208401004195'], 'CAP GRL RAMON FREIRE 2000'),
            (['0209101004195', '0208401004195'], 'CAP GRL RAMON FREIR 2000'),
            (['0209101004195', '0208401004195'], 'CAP GRL RAMON FREI 2000'),
            (['0209101004195', '0208401004195'], 'CAP GRL RAMON FRE 2000'),
            (['0209101004195', '0208401004195'], 'CAP GRL RAMON FR 2000'),
            (['0209101004195', '0208401004195'], 'CAP GRL RAMON F 2000')
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

    def test_search_road_type(self):
        """Se debe poder especificar el tipo de calle en la búsqueda."""
        roads = self.get_response({
            'tipo': 'calle',
            'direccion': VALID_ADDRESS
        })

        avenues = self.get_response({
            'tipo': 'avenida',
            'direccion': VALID_ADDRESS
        })

        roadsValid = roads and all(road['tipo'] == 'CALLE' for road in roads)
        avenuesValid = avenues and all(av['tipo'] == 'AV' for av in avenues)

        self.assertTrue(roadsValid and avenuesValid)

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
                'direccion': VALID_ADDRESS,
                'provincia': state_name,
                'exacto': True
            })

            validations.append(all(
                road['provincia']['id'] == state_code for road in res
            ))

        self.assertTrue(validations and all(validations))

    def test_filter_by_state_id(self):
        """Se debe poder filtrar los resultados por ID de provincia."""
        validations = []
        
        states = [
            ('02', 'CIUDAD AUTÓNOMA DE BUENOS AIRES'),
            ('06', 'BUENOS AIRES'),
            ('14', 'CÓRDOBA')
        ]

        for state_code, state_name in states:
            res = self.get_response({
                'direccion': VALID_ADDRESS,
                'provincia': state_code
            })

            validations.append(all(
                road['provincia']['nombre'] == state_name for road in res
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
                road['departamento']['id'] == dept_code for road in res
            ))

        self.assertTrue(validations and all(validations))

    def test_filter_by_department_id(self):
        """Se debe poder filtrar los resultados por ID de departamento."""
        validations = []
        departments = [
            ('02007', 'COMUNA 1'),
            ('02105', 'COMUNA 15'),
            ('66147', 'ROSARIO DE LERMA')
        ]

        for dept_code, dept_name in departments:
            res = self.get_response({
                'direccion': 'AV CORRIENTES 1000',
                'departamento': dept_code
            })

            validations.append(all(
                road['departamento']['nombre'] == dept_name for road in res
            ))

        self.assertTrue(validations and all(validations))

    def test_batch_search_no_addresses(self):
        """La búsqueda en baches debería fallar si no se pasan direcciones."""
        addresses = {
            'direcciones': []
        }
        response = self.app.post(self.endpoint, json=addresses)
        self.assertEqual(response.status_code, 400)

    def test_batch_search_matches(self):
        """La búsqueda en baches debería encontrar resultados para una
        dirección."""
        addresses = {
            'direcciones': [VALID_ADDRESS]
        }
        response = self.get_response(params=addresses, method='POST')
        results = response[0]['normalizadas']
        self.assertTrue(len(response) > 0 and len(results) > 0)

    def test_empty_params(self):
        """Los parámetros que esperan valores no pueden tener valores
        vacíos."""
        params = ['direccion', 'tipo', 'departamento', 'provincia', 'max',
            'campos']
        self.assert_empty_params_return_400(params)

    def test_unknown_param_returns_400(self):
        """El endpoint no debe aceptar parámetros desconocidos."""
        self.assert_unknown_param_returns_400()


if __name__ == '__main__':
    unittest.main()
