import random
import unittest
from service import app
from . import SearchEntitiesTest, asciifold
from .test_search_states import STATES
from .test_search_departments import DEPARTMENTS
from .test_search_municipalities import MUNICIPALITIES

LOCALITIES = [
    (['06840010015'], 'VILLA RAFFO'),
    (['06756010003'], 'BOULOGNE SUR MER'),
    (['62042450001'], 'BARRIO PINO AZUL'),
    (['14021150001'], 'DUMESNIL'),
    (['70056020000'], 'GRAN CHINA'),
    (['50028020003'], 'CAPILLA DEL ROSARIO'),
    (['54112010000'], 'CRUCE CABALLERO'),
    (['82021270000'], 'PLAZA CLUCELLAS'),
    (['94014010000'], 'LAGUNA ESCONDIDA'),
    (['38077030000'], 'CIENEGUILLAS'),
    (['34035030000'], 'COMANDANTE FONTANA'),
    (['78014040000'], 'JARAMILLO'),
    (['86014030000'], 'DONADEU'),
    (['26035010000'], 'ALDEA ESCOLAR'),
    (['26021030009'], 'BARRIO MANANTIAL ROSALES'),
]

class SearchLocalityTest(SearchEntitiesTest):
    """Pruebas de búsqueda de localidades (índice de asentamientos)."""

    def setUp(self):
        self.endpoint = '/api/v1.0/localidades'
        self.entity = 'localidades'
        super().setUp()

    def test_max_results_returned(self):
        """La cantidad máxima de resultados debe ser configurable."""
        lengths = [0, 5, 25, 50]
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

    def test_default_results_fields(self):
        """Las entidades devueltas deben tener los campos default."""
        data = self.get_response({'max': 1})[0]
        fields = sorted([
            'id',
            'lat',
            'lon',
            'nombre',
            'provincia',
            'departamento',
            'municipio',
            'tipo'
        ])
        self.assertListEqual(fields, sorted(data.keys()))

    def test_filter_results_fields(self):
        """Los campos de las localidades devueltas deben ser filtrables."""
        fields_lists = [
            ['id', 'nombre'],
            ['id', 'lat', 'lon', 'nombre'],
            ['id', 'lat', 'nombre'],
            ['id', 'lat', 'nombre', 'provincia'],
            ['departamento', 'id', 'nombre'],
            ['id', 'municipio', 'nombre', 'provincia']
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
            (['06476060000'], 'MANGUEYU'),      # -2 caracteres (de 8+)
            (['06476060000'], 'AMANGUEYU'),     # -1 caracteres (de 8+)
            (['06476060000'], 'tTAMANGUEYU'),   # +1 caracteres (de 8+)
            (['06476060000'], 'tTAMANGUEYUu'),  # +2 caracteres (de 8+)
            (['06819020000'], 'LDUNGARAY'),     # -2 caracteres (de 8+)
            (['06819020000'], 'ALDUNGARAY'),    # -1 caracteres (de 8+)
            (['06819020000'], 'sSALDUNGARAY'),  # +1 caracteres (de 8+)
            (['06819020000'], 'sSALDUNGARAYy'), # +2 caracteres (de 8+)
            (['82098050000'], 'OMANG'),         # -1 caracteres (de 4-7)
            (['82098050000'], 'rROMANG'),       # +1 caracteres (de 4-7)
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
            (['86056070000'], 'PAMPA DE LOS GU'),
            (['86056070000'], 'PAMPA DE LOS G')
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
        data.extend(self.get_response({'departamento': dept_name, 'exacto': 1}))

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

    def test_empty_params(self):
        """Los parámetros que esperan valores no pueden tener valores
        vacíos."""
        params = ['id', 'nombre', 'orden', 'campos', 'max', 'formato',
                  'provincia', 'departamento', 'municipio']
        self.assert_empty_params_return_400(params)

    def test_unknown_param_returns_400(self):
        """El endpoint no debe aceptar parámetros desconocidos."""
        self.assert_unknown_param_returns_400()

    def test_formats(self):
        """El endpoint debe tener distintos formatos de respuesta."""
        self.assert_formats_ok()

    def test_flat_results(self):
        """El parametro aplanar deberia aplanar los resultados devueltos."""
        self.assert_flat_results()


if __name__ == '__main__':
    unittest.main()
