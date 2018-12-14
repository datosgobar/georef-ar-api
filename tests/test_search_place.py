import random
import unittest
from service import formatter
from . import GeorefLiveTest


PLACES = [
    ('-27.27416', '-66.75292', {
        'provincia': '10',
        'departamento': '10035',
        'municipio': '100077'
    }),
    ('-35.493', '-60.968', {
        'provincia': '06',
        'departamento': '06588',
        'municipio': '060588'
    }),
    ('-53.873', '-67.825', {
        'provincia': '94',
        'departamento': '94008',
        'municipio': '940007'
    }),
    ('-25.718', '-53.994', {
        'provincia': '54',
        'departamento': '54049',
        'municipio': '540182'
    })
]

PLACES_NO_MUNI = [
    ('-31.480693', '-59.0928132', {
        'provincia': '30',
        'departamento': '30113'
    })
]


class SearchPlaceTest(GeorefLiveTest):
    """Pruebas de búsqueda por ubicación."""

    def setUp(self):
        self.endpoint = '/api/v1.0/ubicacion'
        self.entity = 'ubicacion'
        super().setUp()

    def test_default_results_fields(self):
        """La ubicación devuelta debe tener los campos default."""
        place = PLACES[0]
        data = self.get_response({'lat': place[0], 'lon': place[1]})
        fields = sorted([
            'provincia',
            'departamento',
            'municipio',
            'lat',
            'lon'
        ])
        self.assertListEqual(fields, sorted(data.keys()))

    def test_basic_fields_set(self):
        """Se debería poder especificar un conjunto de parámetros
        preseleccionados llamado 'basico'."""
        place = PLACES[0]
        self.assert_fields_set_equals('basico', ['provincia.id',
                                                 'provincia.nombre',
                                                 'lat', 'lon'],
                                      {'lat': place[0], 'lon': place[1]},
                                      iterable=False)

    def test_standard_fields_set(self):
        """Se debería poder especificar un conjunto de parámetros
        preseleccionados llamado 'estandar'."""
        place = PLACES[0]

        self.assert_fields_set_equals('estandar',
                                      ['provincia.id', 'provincia.nombre',
                                       'lat', 'lon', 'departamento.id',
                                       'departamento.nombre',
                                       'municipio.id', 'municipio.nombre'],
                                      {'lat': place[0], 'lon': place[1]},
                                      iterable=False)

    def test_complete_fields_set(self):
        """Se debería poder especificar un conjunto de parámetros
        preseleccionados llamado 'completo'."""
        place = PLACES[0]

        self.assert_fields_set_equals('completo',
                                      ['provincia.id', 'provincia.nombre',
                                       'lat', 'lon', 'departamento.id',
                                       'departamento.nombre',
                                       'municipio.id', 'municipio.nombre',
                                       'fuente'],
                                      {'lat': place[0], 'lon': place[1]},
                                      iterable=False)

    def test_filter_results_fields(self):
        """Los campos de la ubicación devuelta deben ser filtrables."""
        place = PLACES[0]
        fields_lists = [
            ['provincia.id', 'provincia.nombre', 'lat', 'lon'],
            ['departamento.id', 'fuente', 'lat', 'lon', 'provincia.id',
             'provincia.nombre'],
            ['lon', 'municipio.id', 'provincia.id',
             'provincia.nombre', 'lat', 'fuente']
        ]
        fields_lists = [sorted(l) for l in fields_lists]

        fields_results = []

        for fields in fields_lists:
            data = self.get_response({
                'campos': ','.join(fields),
                'lat': place[0],
                'lon': place[1]
            })
            formatter.flatten_dict(data, sep='.')
            fields_results.append(sorted(data.keys()))

        self.assertListEqual(fields_lists, fields_results)

    def test_valid_coordinates(self):
        """Se deberían encontrar resultados para coordenadas válidas."""
        validations = []

        for lat, lon, data in PLACES:
            res = self.get_response({'lat': lat, 'lon': lon})
            validations.append(all([
                res['municipio']['id'] == data['municipio'],
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
            for field in ['departamento', 'municipio', 'provincia']
        ]

        self.assertTrue(validations and all(validations))

    def test_no_muni(self):
        """Cuando se especifican coordenadas que no contienen un municipio,
        el campo 'municipio' debe tener un valor nulo."""
        place = PLACES_NO_MUNI[0]
        data = self.get_response({'lat': place[0], 'lon': place[1]})
        muni = data['municipio']
        self.assertTrue(muni['id'] is None and muni['nombre'] is None)

    def test_empty_params(self):
        """Los parámetros que esperan valores no pueden tener valores
        vacíos."""
        params = ['lat', 'lon']
        self.assert_empty_params_return_400(params)

    def test_unknown_param_returns_400(self):
        """El endpoint no debe aceptar parámetros desconocidos."""
        self.assert_unknown_param_returns_400()

    def test_flat_results(self):
        """El parametro aplanar deberia aplanar los resultados devueltos."""
        place = PLACES[0]
        resp = self.get_response({
            'lat': place[0],
            'lon': place[1],
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
            place = self.get_response({'lat': lat, 'lon': lon})

            validations.append(place['provincia']['id'] == state['id'])

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
            place = self.get_response({'lat': lat, 'lon': lon})

            validations.append(place['departamento']['id'] == dept['id'])

        self.assertTrue(validations and all(validations))

    def test_municipality_centroids(self):
        """Cuando se utiliza el centroide de una entidad (con geometría convexa
        o casi convexa) como ubicación, se debería obtener la misma entidad
        como parte de la respuesta."""
        concave_munis = ['060595', '500014', '625140', '460049', '386266',
                         '220469']

        results = self.get_response(
            endpoint='/api/municipios',
            method='POST',
            body={
                'municipios': [
                    {'id': mun_id} for mun_id in concave_munis
                ]
            }
        )

        validations = []

        for result in results:
            muni = result['municipios'][0]
            lat = muni['centroide']['lat']
            lon = muni['centroide']['lon']
            place = self.get_response({'lat': lat, 'lon': lon})

            validations.append(place['municipio']['id'] == muni['id'])

        self.assertTrue(validations and all(validations))

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

        place = self.get_response({'lat': lat, 'lon': lon})
        self.assertEqual(place['provincia']['id'], state_id)

    def test_bulk_empty_400(self):
        """La búsqueda bulk vacía debería retornar un error 400."""
        status = self.get_response(method='POST', body={},
                                   return_value='status')
        self.assertEqual(status, 400)

    def test_bulk_response_len(self):
        """La longitud de la respuesta bulk debería ser igual a la cantidad
        de queries envíadas."""
        req_len = random.randint(10, 20)
        place = PLACES[0]

        query = {
            'lat': place[0],
            'lon': place[1]
        }

        body = {
            'ubicaciones': [query] * req_len
        }

        results = self.get_response(method='POST', body=body)
        self.assertEqual(len(results), req_len)

    def test_bulk_equivalent(self):
        """Los resultados de una query envíada vía bulk deberían ser idénticos a
        los resultados de una query individual (GET)."""
        place = PLACES[0]

        queries = [
            {
                'lat': place[0],
                'lon': place[1]
            },
            {
                'lat': 0,
                'lon': 0
            },
            {
                'lat': place[0],
                'lon': place[1],
                'aplanar': True
            },
            {
                'lat': place[0],
                'lon': place[1],
                'campos': 'lat,lon'
            }
        ]

        individual_results = []
        for query in queries:
            individual_results.append({
                'ubicacion': self.get_response(params=query)
            })

        bulk_results = self.get_response(method='POST', body={
            'ubicaciones': queries
        })

        self.assertEqual(individual_results, bulk_results)

    def test_json_format(self):
        """Por default, los resultados de una query deberían estar en
        formato JSON."""
        place = PLACES[1]

        default_response = self.get_response({
            'lat': place[0],
            'lon': place[1]
        })
        json_response = self.get_response({
            'formato': 'json',
            'lat': place[0],
            'lon': place[1]
        })
        self.assertEqual(default_response, json_response)

    def test_geojson_format_query(self):
        """Se debería poder obtener resultados en formato
        GEOJSON (con parámetros)."""
        place = PLACES[1]

        self.assert_valid_geojson({
            'lat': place[0],
            'lon': place[1]
        })

    def test_xml_format(self):
        """Se debería poder obtener resultados en formato XML (con
        parámetros)."""
        place = PLACES[1]

        self.assert_valid_xml({
            'lat': place[0],
            'lon': place[1]
        })


if __name__ == '__main__':
    unittest.main()
