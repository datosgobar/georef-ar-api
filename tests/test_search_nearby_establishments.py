from service import formatter
from . import GeorefLiveTest


LOCATIONS = [
    ('-34.599637173', '-58.392930988', {

    }),
    # ('-35.493', '-60.968', {
    #     'provincia': '06',
    #     'departamento': '06588',
    #     'gobierno_local': '060588'
    # }),

]


class SearchLocationTest(GeorefLiveTest):
    """Pruebas de búsqueda por ubicación."""

    def setUp(self):
        self.endpoint = '/api/v2.0/establecimientos-cercanos'
        self.entity = 'establecimientos_cercanos'
        super().setUp()

    def test_default_results_fields(self):
        """La ubicación devuelta debe tener los campos default."""
        location = LOCATIONS[0]
        data = self.get_response({'lat': location[0], 'lon': location[1]})
        fields = sorted([
            'centroide',
            'distancia',
            'domicilio',
            'id',
            'nombre',
            'tipo_establecimiento',
        ])
        self.assertListEqual(fields, sorted(data[0].keys()))

    def test_basic_fields_set(self):
        """Se debería poder especificar un conjunto de parámetros
        preseleccionados llamado 'basico'."""
        location = LOCATIONS[0]
        self.assert_fields_set_equals('basico', [
            'centroide',
            'id',
            'tipo_establecimiento',],
                                    {'lat': location[0], 'lon': location[1]},
                                      iterable=True)

    def test_standard_fields_set(self):
        """Se debería poder especificar un conjunto de parámetros
        preseleccionados llamado 'estandar'."""
        location = LOCATIONS[0]

        self.assert_fields_set_equals('estandar',
                                      [
                                          'centroide',
                                          'distancia',
                                          'domicilio',
                                          'id',
                                          'nombre',
                                          'tipo_establecimiento',
                                       ],
                                      {'lat': location[0], 'lon': location[1]},
                                      iterable=True)

    def test_complete_fields_set(self):
        """Se debería poder especificar un conjunto de parámetros
        preseleccionados llamado 'completo'."""
        location = LOCATIONS[0]

        self.assert_fields_set_equals('completo',
                                      [
                                          'centroide',
                                          'distancia',
                                          'domicilio',
                                          'id',
                                          'nombre',
                                          'tipo_establecimiento',
                                          'fuente'
                                      ],
                                      {'lat': location[0], 'lon': location[1]},
                                      iterable=True)

    def test_filter_results_fields(self):
        """Los campos de los establecimientos cercanos deben ser filtrables."""
        location = LOCATIONS[0]
        fields_lists = [
            ['centroide.lat', 'centroide.lon', 'id', 'tipo_establecimiento'],
            ['centroide.lat', 'centroide.lon', 'id', 'tipo_establecimiento',
             'nombre', 'domicilio'],
            ['centroide.lon', 'distancia', 'domicilio', 'tipo_establecimiento', 'id',
             'nombre', 'centroide.lat', 'fuente']
        ]
        fields_lists = [sorted(l) for l in fields_lists]

        fields_results = []

        for fields in fields_lists:
            data = self.get_response({
                'campos': ','.join(fields),
                'lat': location[0],
                'lon': location[1]
            })[0]
            formatter.flatten_dict(data, sep='.')
            fields_results.append(sorted(data.keys()))

        self.assertListEqual(fields_lists, fields_results)

    def test_max_result(self):
        location = LOCATIONS[0]
        data = self.get_response({
            'lat': location[0],
            'lon': location[1]
        })
        self.assertTrue(len(data) == 10)

        data = self.get_response({
            'lat': location[0],
            'lon': location[1],
            'max': 20
        })
        self.assertTrue(len(data) > 10)

        data = self.get_response({
            'lat': location[0],
            'lon': location[1],
            'max': 1
        })
        self.assertTrue(len(data) == 1)

    def test_distance(self):
        location = LOCATIONS[0]

        distance_establisments = {}
        radius_list = [
            100,
            1000,
            20000,
        ]

        for radius in radius_list:
            distance_establisments[radius] = len(
                self.get_response({
                    'lat': location[0],
                    'lon': location[1],
                    'max': 5000,
                    'distancia': radius
                })
            )

        for p in range(len(radius_list) - 1):
            r_out = radius_list[p + 1]
            r_in = radius_list[p]
            self.assertGreater(distance_establisments[r_out], distance_establisments[r_in])
