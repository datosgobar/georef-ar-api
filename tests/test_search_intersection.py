import unittest
from . import SearchEntitiesTest


class SearchStatesTest(SearchEntitiesTest):
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

    def test_intersection_muni_dept_state(self):
        """Se debería poder buscar municipios utilizando geometrías de
        departamentos y provincias por intersección."""
        self.assert_intersection_contains_ids(
            'municipios',
            {'interseccion': 'departamento:82021,provincia:90', 'max': 5000},
            ['822315', '822287', '822378', '900042', '908371', '908567']
        )

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


if __name__ == '__main__':
    unittest.main()
