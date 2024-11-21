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

    def test_intersection_state_gl(self):
        """Se debería poder buscar provincias utilizando geometrías de
        gobiernos locales por intersección."""
        self.assert_intersection_contains_ids(
            'provincias',
            {'interseccion': 'gobierno_local:060798'},
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

    def test_intersection_state_gl_dept(self):
        """Se debería poder buscar provincias utilizando geometrías de
        gobiernos locales y departamentos por intersección."""
        self.assert_intersection_contains_ids(
            'provincias',
            {'interseccion': 'gobierno_local:100056,departamento:22007'},
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

    def test_intersection_dept_gl(self):
        """Se debería poder buscar departamentos utilizando geometrías de
        gobierno locales por intersección."""
        self.assert_intersection_contains_ids(
            'departamentos',
            {'interseccion': 'gobierno_local:620224', 'max': 100},
            ['62056', '62070', '62021']
        )

    def test_intersection_dept_street(self):
        """Se debería poder buscar departamentos utilizando geometrías de
        calles por intersección."""
        self.assert_intersection_contains_ids(
            'departamentos',
            {'interseccion': 'calle:0638503000700'},
            ['06385']
        )

    def test_intersection_dept_gl_bounds(self):
        """Cuando se buscan departamentos por intersección con geometría de
        gobierno local, los departamentos resultantes siempre deben pertenecer a la
        misma provincia que el gobierno local utilizado."""
        resp = self.get_response({
            'interseccion': 'gobierno_local:620133',
            'max': 5000,
            'aplanar': True
        }, endpoint='/api/departamentos', entity='departamentos')

        self.assertTrue(resp and
                        all(dept['provincia_id'] == '62' for dept in resp))

    def test_intersection_dept_gl_state(self):
        """Se debería poder buscar departamentos utilizando geometrías de
        gobierno locales y provincias por intersección."""
        self.assert_intersection_contains_ids(
            'departamentos',
            {'interseccion': 'gobierno_local:540378,provincia:34', 'max': 100},
            ['54091', '34035']
        )

    def test_intersection_gl_state(self):
        """Se debería poder buscar gobiernos locales utilizando geometrías de
        provincias por intersección."""
        self.assert_intersection_contains_ids(
            'gobiernos-locales',
            {'interseccion': 'provincia:14', 'max': 1000},
            ['140077']
        )

    def test_intersection_gl_dept(self):
        """Se debería poder buscar gobiernos locales utilizando geometrías de
        departamentos por intersección."""
        self.assert_intersection_contains_ids(
            'gobiernos-locales',
            {'interseccion': 'departamento:18105', 'max': 1000},
            ['180231', '180245', '180238']
        )

    def test_intersection_gl_dept_bounds(self):
        """Cuando se buscan gobiernos locales por intersección con geometría de
        departamento, los gobiernos locales resultantes siempre deben pertenecer a la
        misma provincia que el departamento utilizado."""
        resp = self.get_response({
            'interseccion': 'departamento:82042',
            'max': 5000,
            'aplanar': True
        }, endpoint='/api/gobiernos-locales', entity='gobiernos_locales')

        self.assertTrue(resp and
                        all(mun['provincia_id'] == '82' for mun in resp))

    def test_intersection_gl_dept_state(self):
        """Se debería poder buscar gobiernos locales utilizando geometrías de
        departamentos y provincias por intersección."""
        self.assert_intersection_contains_ids(
            'gobiernos-locales',
            {'interseccion': 'departamento:82021,provincia:90', 'max': 5000},
            ['822315', '822287', '822378', '900042', '908371', '908567']
        )

    def test_intersection_gl_street(self):
        """Se debería poder buscar gobiernos locales utilizando geometrías de
        calles por intersección."""
        self.assert_intersection_contains_ids(
            'gobiernos-locales',
            {'interseccion': 'calle:0638503000700'},
            ['060385']
        )

    def test_intersection_street_gl(self):
        """Se debería poder buscar calles utilizando geometrías de
        gobiernos locales por intersección."""
        self.assert_intersection_contains_ids(
            'calles',
            {'interseccion': 'gobierno_local:220084', 'max': 1000},
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
        }, endpoint='/api/gobiernos-locales', entity='gobiernos_locales')

        self.assertListEqual(resp, [])

    def assert_intersection_contains_ids(self, endpoint, params, ids):
        api_endpoint = '/api/' + endpoint
        resp = self.get_response(params, endpoint=api_endpoint,
                                 entity=endpoint.replace("-", "_"))
        matched_ids = [hit['id'] for hit in resp]

        self.assertTrue(all(i in matched_ids for i in ids))
