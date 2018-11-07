import logging
from unittest import TestCase
from service import app


logging.getLogger('georef').setLevel(logging.CRITICAL)


class RoutesTest(TestCase):
    def setUp(self):
        app.testing = True
        self.app = app.test_client()

    def test_v1_0_endpoints(self):
        """Los endpoints con prefijo /api/v1.0 deberían existir incluso si no
        se cuenta con más de una versión de la API."""
        urls = [
            '/api/v1.0/paises',
            '/api/v1.0/provincias',
            '/api/v1.0/departamentos',
            '/api/v1.0/municipios',
            '/api/v1.0/localidades',
            '/api/v1.0/direcciones',
            '/api/v1.0/ubicacion'
        ]

        validations = [
            self.app.options(url).status_code == 200
            for url in urls
        ]

        self.assertTrue(all(validations), list(zip(urls, validations)))

    def test_complete_download_redirect(self):
        """La API debería permitir la descarga total de datos por recurso. Las
        descargas se implementan como una redirección a una URL donde se
        almacenan los datos a descargarse (HTTP 302). La configuración de
        ejemplo de la API utiliza una URL de ejemplo para /provincias.json."""
        resp = self.app.get('/api/provincias.json')
        self.assertTrue(resp.status_code == 302 and
                        resp.headers['Location'] == 'https://www.example.org')
