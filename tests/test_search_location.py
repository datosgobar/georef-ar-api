import random
from service import formatter
from . import GeorefLiveTest


LOCATIONS = [
    ('-27.27416', '-66.75292', {
        'provincia': '10',
        'departamento': '10035',
        'gobierno_local': '100077'
    }),
    ('-35.493', '-60.968', {
        'provincia': '06',
        'departamento': '06588',
        'gobierno_local': '060588'
    }),
    ('-53.873', '-67.825', {
        'provincia': '94',
        'departamento': '94008',
        'gobierno_local': '940007'
    }),
    ('-25.718', '-53.994', {
        'provincia': '54',
        'departamento': '54049',
        'gobierno_local': '540182'
    })
]

LOCATIONS_NO_GL = [
    ('-31.480693', '-59.0928132', {
        'provincia': '30',
        'departamento': '30113'
    })
]


class SearchLocationTest(GeorefLiveTest):
    """Pruebas de búsqueda por ubicación."""

    def setUp(self):
        self.endpoint = '/api/v1.0/ubicacion'
        self.entity = 'ubicacion'
        super().setUp()

    def test_default_results_fields(self):
        """La ubicación devuelta debe tener los campos default."""
        location = LOCATIONS[0]
        data = self.get_response({'lat': location[0], 'lon': location[1]})
        fields = sorted([
            'provincia',
            'departamento',
            'gobierno_local',
            'lat',
            'lon'
        ])
        self.assertListEqual(fields, sorted(data.keys()))

    def test_basic_fields_set(self):
        """Se debería poder especificar un conjunto de parámetros
        preseleccionados llamado 'basico'."""
        location = LOCATIONS[0]
        self.assert_fields_set_equals('basico', ['provincia.id',
                                                 'provincia.nombre',
                                                 'lat', 'lon'],
                                      {'lat': location[0], 'lon': location[1]},
                                      iterable=False)

    def test_standard_fields_set(self):
        """Se debería poder especificar un conjunto de parámetros
        preseleccionados llamado 'estandar'."""
        location = LOCATIONS[0]

        self.assert_fields_set_equals('estandar',
                                      ['provincia.id', 'provincia.nombre',
                                       'lat', 'lon', 'departamento.id',
                                       'departamento.nombre',
                                       'gobierno_local.id', 'gobierno_local.nombre'],
                                      {'lat': location[0], 'lon': location[1]},
                                      iterable=False)

    def test_complete_fields_set(self):
        """Se debería poder especificar un conjunto de parámetros
        preseleccionados llamado 'completo'."""
        location = LOCATIONS[0]

        self.assert_fields_set_equals('completo',
                                      ['provincia.id', 'provincia.nombre',
                                       'lat', 'lon', 'departamento.id',
                                       'departamento.nombre',
                                       'gobierno_local.id', 'gobierno_local.nombre',
                                       'provincia.fuente',
                                       'departamento.fuente',
                                       'gobierno_local.fuente'],
                                      {'lat': location[0], 'lon': location[1]},
                                      iterable=False)

    def test_filter_results_fields(self):
        """Los campos de la ubicación devuelta deben ser filtrables."""
        location = LOCATIONS[0]
        fields_lists = [
            ['provincia.id', 'provincia.nombre', 'lat', 'lon'],
            ['departamento.id', 'provincia.fuente', 'lat', 'lon',
             'provincia.id', 'provincia.nombre'],
            ['lon', 'gobierno_local.id', 'provincia.id',
             'provincia.nombre', 'lat', 'gobierno_local.fuente']
        ]
        fields_lists = [sorted(l) for l in fields_lists]

        fields_results = []

        for fields in fields_lists:
            data = self.get_response({
                'campos': ','.join(fields),
                'lat': location[0],
                'lon': location[1]
            })
            formatter.flatten_dict(data, sep='.')
            fields_results.append(sorted(data.keys()))

        self.assertListEqual(fields_lists, fields_results)

    def test_valid_coordinates(self):
        """Se deberían encontrar resultados para coordenadas válidas."""
        validations = []

        for lat, lon, data in LOCATIONS:
            res = self.get_response({'lat': lat, 'lon': lon})
            validations.append(all([
                res['gobierno_local']['id'] == data['gobierno_local'],
                res['departamento']['id'] == data['departamento'],
                res['provincia']['id'] == data['provincia']
            ]))

        self.assertTrue(validations and all(validations))

    def test_invalid_coordinates(self):
        """No se deberían encontrar resultados cuando se utilizan coordenadas
        erroneas."""
        data = self.get_response({'lat': 0, 'lon': 0})
        empty_entity = {
            'id': None,
            'nombre': None
        }

        validations = [
            data[field] == empty_entity
            for field in ['departamento', 'gobierno_local', 'provincia']
        ]

        self.assertTrue(validations and all(validations))

    def test_no_gl(self):
        """Cuando se especifican coordenadas que no contienen un gobierno local,
        el campo 'gobierno_local' debe tener un valor nulo."""
        location = LOCATIONS_NO_GL[0]
        data = self.get_response({'lat': location[0], 'lon': location[1]})
        gl = data['gobierno_local']
        self.assertTrue(gl['id'] is None and gl['nombre'] is None)

    def test_infinity(self):
        """Cuando se especifica Infinity como valor numérico, se debe responder
        con una respuesta 400."""
        status = self.get_response(body={'lat': 'Infinity', 'lon': 'inf'},
                                   return_value='status',
                                   expect_status=[400])
        self.assertEqual(status, 400)

    def test_nan(self):
        """Cuando se especifica NaN como valor numérico, se debe responder con
        una respuesta 400."""
        status = self.get_response(body={'lat': 'NaN', 'lon': 'NaN'},
                                   return_value='status',
                                   expect_status=[400])
        self.assertEqual(status, 400)

    def test_flat_results(self):
        """El parametro aplanar deberia aplanar los resultados devueltos."""
        location = LOCATIONS[0]
        resp = self.get_response({
            'lat': location[0],
            'lon': location[1],
            'aplanar': 1
        })

        self.assertTrue(all([
            not isinstance(v, dict) for v in resp.values()
        ]) and resp)

    def test_state_centroids(self):
        """Cuando se utiliza el centroide de una entidad (con geometría convexa
        o casi convexa) como ubicación, se debería obtener la misma entidad
        como parte de la respuesta."""
        states = self.get_response(endpoint='/api/provincias',
                                   entity='provincias',
                                   params={
                                       'campos': 'centroide.lat,centroide.lon'
                                   })

        validations = []

        for state in states:
            if state['id'] == '66':
                # La geometría de Salta es muy cóncava
                continue

            lat = state['centroide']['lat']
            lon = state['centroide']['lon']
            location = self.get_response({'lat': lat, 'lon': lon})

            validations.append(location['provincia']['id'] == state['id'])

        self.assertTrue(validations and all(validations))

    def test_department_centroids(self):
        """Cuando se utiliza el centroide de una entidad (con geometría convexa
        o casi convexa) como ubicación, se debería obtener la misma entidad
        como parte de la respuesta."""
        depts = self.get_response(endpoint='/api/departamentos',
                                  entity='departamentos',
                                  params={
                                      'campos': 'centroide.lat,centroide.lon',
                                      'max': 30
                                  })

        validations = []

        for dept in depts:
            lat = dept['centroide']['lat']
            lon = dept['centroide']['lon']
            location = self.get_response({'lat': lat, 'lon': lon})

            validations.append(location['departamento']['id'] == dept['id'])

        self.assertTrue(validations and all(validations))

    def test_local_government_centroids(self):
        """Cuando se utiliza el centroide de una entidad (con geometría convexa
        o casi convexa) como ubicación, se debería obtener la misma entidad
        como parte de la respuesta."""
        concave_gls = ['060595', '500014', '625140', '460049', '386266',
                         '220469']

        results = self.get_response(
            endpoint='/api/gobiernos-locales',
            method='POST',
            body={
                'gobiernos_locales': [
                    {'id': mun_id} for mun_id in concave_gls
                ]
            }
        )

        validations = []

        for result in results:
            gl = result['gobiernos_locales'][0]
            lat = gl['centroide']['lat']
            lon = gl['centroide']['lon']
            location = self.get_response({'lat': lat, 'lon': lon})

            validations.append(location['gobiernos_locales']['id'] == gl['id'])

        self.assertTrue(validations and all(validations))

    def test_malvinas(self):
        """Cualquier coordenada situada sobre las islas Malvinas debería
        devolver el departamento ID 94021 y la provincia ID 94 como
        resultado."""
        resp = self.get_response({'lat': -51.694444, 'lon': -57.852778})
        self.assertTrue(resp['provincia']['id'] == '94' and
                        resp['departamento']['id'] == '94021')

    def test_geojson_coordinates(self):
        """Dada una respuesta en formato GeoJSON, se debería poder tomar las
        coordenadas de cualquier Feature y encontrar la misma entidad vía el
        recurso /ubicacion."""
        name = random.choice(['tucuman', 'buenos aires', 'cordoba',
                              'entre rios', 'santa cruz', 'la pampa'])

        resp = self.get_response(
            params={
                'nombre': name,
                'formato': 'geojson'
            },
            endpoint='/api/provincias',
            return_value='full'
        )

        state_id = resp['features'][0]['properties']['id']
        state_coordinates = resp['features'][0]['geometry']['coordinates']
        lon, lat = state_coordinates[0], state_coordinates[1]

        location = self.get_response({'lat': lat, 'lon': lon})
        self.assertEqual(location['provincia']['id'], state_id)

    def test_bulk_response_len(self):
        """La longitud de la respuesta bulk debería ser igual a la cantidad
        de queries envíadas."""
        req_len = random.randint(10, 20)
        location = LOCATIONS[0]

        query = {
            'lat': location[0],
            'lon': location[1]
        }

        body = {
            'ubicaciones': [query] * req_len
        }

        results = self.get_response(method='POST', body=body)
        self.assertEqual(len(results), req_len)

    def test_bulk_equivalent(self):
        """Los resultados de una query envíada vía bulk deberían ser idénticos a
        los resultados de una query individual (GET)."""
        location = LOCATIONS[0]

        queries = [
            {
                'lat': location[0],
                'lon': location[1]
            },
            {
                'lat': 0,
                'lon': 0
            },
            {
                'lat': location[0],
                'lon': location[1],
                'aplanar': True
            },
            {
                'lat': location[0],
                'lon': location[1],
                'campos': 'lat,lon'
            }
        ]

        individual_results = []
        for query in queries:
            individual_results.append(self.get_response(params=query,
                                                        return_value='full'))

        bulk_results = self.get_response(method='POST', body={
            'ubicaciones': queries
        })

        self.assertListEqual(individual_results, bulk_results)

    def test_json_format(self):
        """Por default, los resultados de una query deberían estar en
        formato JSON."""
        location = LOCATIONS[1]

        default_response = self.get_response({
            'lat': location[0],
            'lon': location[1]
        })
        json_response = self.get_response({
            'formato': 'json',
            'lat': location[0],
            'lon': location[1]
        })
        self.assertEqual(default_response, json_response)

    def test_geojson_format_query(self):
        """Se debería poder obtener resultados en formato
        GEOJSON (con parámetros)."""
        location = LOCATIONS[1]

        self.assert_valid_geojson({
            'lat': location[0],
            'lon': location[1]
        })

    def test_xml_format(self):
        """Se debería poder obtener resultados en formato XML (con
        parámetros)."""
        location = LOCATIONS[1]

        self.assert_valid_xml({
            'lat': location[0],
            'lon': location[1]
        })
