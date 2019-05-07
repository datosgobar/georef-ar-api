import os
import unittest
from . import GeorefMockTest

EXAMPLE_CONFIG = 'config/georef.example.cfg'


class RoutesTest(GeorefMockTest):
    def test_v1_0_endpoints(self):
        """Los endpoints con prefijo /api/v1.0 deberían existir incluso si no
        se cuenta con más de una versión de la API. Esto se debe a que
        versiones iniciales de la API fueron publicadas que utilizaban el
        prefijo /v1.0."""
        urls = [
            '/api/v1.0/provincias',
            '/api/v1.0/departamentos',
            '/api/v1.0/municipios',
            '/api/v1.0/localidades',
            '/api/v1.0/direcciones',
            '/api/v1.0/calles',
            '/api/v1.0/ubicacion'
        ]

        validations = [
            self.app.options(url).status_code == 200
            for url in urls
        ]

        self.assertTrue(all(validations))

    @unittest.skipIf(os.environ['GEOREF_CONFIG'] != EXAMPLE_CONFIG,
                     'No se está utilizando la config de ejemplo')
    def test_complete_download_redirect(self):
        """La API debería permitir la descarga total de datos por recurso. Las
        descargas se implementan como una redirección a una URL donde se
        almacenan los datos a descargarse (HTTP 302).

        La configuración de ejemplo de la API utiliza una URL de ejemplo para
        /provincias.json."""
        resp = self.app.get('/api/provincias.json')
        self.assertTrue(resp.status_code == 302 and
                        resp.headers['Location'] == 'https://www.example.org')

    @unittest.skipIf(os.environ['GEOREF_CONFIG'] != EXAMPLE_CONFIG,
                     'No se está utilizando la config de ejemplo')
    def test_complete_download_redirect_unset(self):
        """Si no se configura uno de los recursos de descarga completa, al
        acceder al recurso se debería obtener un error 404.

        La configuración de ejemplo de la API solo configura el recurso
        /provincias.json. El resto quedan sin configurar."""
        resp = self.app.get('/api/departamentos.json')
        self.assertTrue(resp.status_code == 404)
