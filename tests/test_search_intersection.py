from . import GeorefLiveTest


class IntersectionsTest(GeorefLiveTest):
    """Pruebas de búsqueda de entidades por intersección."""

    def test_intersection_state_dept(self):
        """Se debería poder buscar provincias utilizando geometrías de
        departamentos por intersección."""
        self.assert_intersection_contains_ids(
            'provincias',
            {'interseccion': 'departamento:42154'},
            ['42']
        )

    def test_intersection_state_muni(self):
        """Se debería poder buscar provincias utilizando geometrías de
        municipios por intersección."""
        self.assert_intersection_contains_ids(
            'provincias',
            {'interseccion': 'municipio:060798'},
            ['06']
        )

    def test_intersection_state_street(self):
        """Se debería poder buscar provincias utilizando geometrías de
        calles por intersección."""
        self.assert_intersection_contains_ids(
            'provincias',
            {'interseccion': 'calle:7801407000555'},
            ['78']
        )

    def test_intersection_state_muni_dept(self):
        """Se debería poder buscar provincias utilizando geometrías de
        municipios y departamentos por intersección."""
        self.assert_intersection_contains_ids(
            'provincias',
            {'interseccion': 'municipio:100056,departamento:22007'},
            ['10', '22']
        )

    def test_intersection_dept_state(self):
        """Se debería poder buscar departamentos utilizando geometrías de
        provincias por intersección."""
        self.assert_intersection_contains_ids(
            'departamentos',
            {'interseccion': 'provincia:38', 'max': 100},
            ['38028']
        )

    def test_intersection_dept_muni(self):
        """Se debería poder buscar departamentos utilizando geometrías de
        municipios por intersección."""
        self.assert_intersection_contains_ids(
            'departamentos',
            {'interseccion': 'municipio:625056', 'max': 100},
            ['62035', '62014', '62049', '62091']
        )

    def test_intersection_dept_street(self):
        """Se debería poder buscar departamentos utilizando geometrías de
        calles por intersección."""
        self.assert_intersection_contains_ids(
            'departamentos',
            {'interseccion': 'calle:0638503000700'},
            ['06385']
        )

    def test_intersection_dept_muni_bounds(self):
        """Cuando se buscan departamentos por intersección con geometría de
        municipio, los departamentos resultantes siempre deben pertenecer a la
        misma provincia que el municipio utilizado."""
        resp = self.get_response({
            'interseccion': 'municipio:620133',
            'max': 5000,
            'aplanar': True
        }, endpoint='/api/departamentos', entity='departamentos')

        self.assertTrue(resp and
                        all(dept['provincia_id'] == '62' for dept in resp))

    def test_intersection_dept_muni_state(self):
        """Se debería poder buscar departamentos utilizando geometrías de
        municipios y provincias por intersección."""
        self.assert_intersection_contains_ids(
            'departamentos',
            {'interseccion': 'municipio:540378,provincia:34', 'max': 100},
            ['54091', '34035']
        )

    def test_intersection_muni_state(self):
        """Se debería poder buscar municipios utilizando geometrías de
        provincias por intersección."""
        self.assert_intersection_contains_ids(
            'municipios',
            {'interseccion': 'provincia:14', 'max': 1000},
            ['140077']
        )

    def test_intersection_muni_dept(self):
        """Se debería poder buscar municipios utilizando geometrías de
        departamentos por intersección."""
        self.assert_intersection_contains_ids(
            'municipios',
            {'interseccion': 'departamento:18105', 'max': 1000},
            ['180231', '180245', '180238']
        )

    def test_intersection_muni_dept_bounds(self):
        """Cuando se buscan municipios por intersección con geometría de
        departamento, los municipios resultantes siempre deben pertenecer a la
        misma provincia que el departamento utilizado."""
        resp = self.get_response({
            'interseccion': 'departamento:82042',
            'max': 5000,
            'aplanar': True
        }, endpoint='/api/municipios', entity='municipios')

        self.assertTrue(resp and
                        all(mun['provincia_id'] == '82' for mun in resp))

    def test_intersection_muni_dept_state(self):
        """Se debería poder buscar municipios utilizando geometrías de
        departamentos y provincias por intersección."""
        self.assert_intersection_contains_ids(
            'municipios',
            {'interseccion': 'departamento:82021,provincia:90', 'max': 5000},
            ['822315', '822287', '822378', '900042', '908371', '908567']
        )

    def test_intersection_muni_street(self):
        """Se debería poder buscar municipios utilizando geometrías de
        calles por intersección."""
        self.assert_intersection_contains_ids(
            'municipios',
            {'interseccion': 'calle:0638503000700'},
            ['060385']
        )

    def test_intersection_street_muni(self):
        """Se debería poder buscar calles utilizando geometrías de
        municipios por intersección."""
        self.assert_intersection_contains_ids(
            'calles',
            {'interseccion': 'municipio:220084', 'max': 1000},
            ['2202801000850', '2202801000125', '2202801001110']
        )

    def test_intersection_street_street(self):
        """Se debería poder buscar calles utilizando geometrías de
        calles por intersección."""
        self.assert_intersection_contains_ids(
            'calles',
            {'interseccion': 'calle:0209101002235', 'max': 1000},
            ['0209101011450', '0209101011450', '0209101008685']
        )

    def test_intersection_street_not_self_intersect(self):
        """Cuando se buscan calles con geometrías de otra calle, la calle
        utilizada no debería aparecer en los resultados."""
        resp = self.get_response({
            # Buscar calles que interseccionen con calle ID X, y limitar los
            # resultados a calles con ID X. Como los resultados de intersección
            # de calles con calle X no trae la calle X, cuando se limitan los
            # resultados a ID == X, los resultados son vacíos.
            'interseccion': 'calle:0201301002235',
            'id': '0201301002235'
        }, endpoint='/api/calles', entity='calles')

        self.assertListEqual(resp, [])

    def test_intersection_invalid_id(self):
        """Una búsqueda por intersección de ID/s inválido/s debería resultar
        vacía."""
        resp = self.get_response({
            'interseccion': 'departamento:99999'
        }, endpoint='/api/municipios', entity='municipios')

        self.assertListEqual(resp, [])

    def assert_intersection_contains_ids(self, endpoint, params, ids):
        api_endpoint = '/api/' + endpoint
        resp = self.get_response(params, endpoint=api_endpoint,
                                 entity=endpoint)
        matched_ids = [hit['id'] for hit in resp]

        self.assertTrue(all(i in matched_ids for i in ids))
