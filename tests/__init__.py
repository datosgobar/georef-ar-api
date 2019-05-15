import io
import os
import shutil
import csv
import copy
import logging
from xml.etree import ElementTree
from unittest import mock, TestCase
import json
import urllib
import zipfile
from flask import current_app
import shapefile
from service import app, formatter

logging.getLogger('georef').setLevel(logging.CRITICAL)


def asciifold(text):
    conv = {
        'Á': 'A',
        'É': 'E',
        'Í': 'I',
        'Ó': 'O',
        'Ú': 'U',
        'Ñ': 'N'
    }

    return text.upper().translate(text.maketrans(conv))


def shapefile_from_zip_bytes(data):
    """Dada una secuencia de bytes representando un zipped Shapefile,
    devuelve una instancia de shapefile.Reader con sus contenidos.

    Args:
        data (bytes): Secuencia de bytes (ZIP).

    Return:
        shapefile.Reader: Contenidos del Shapefile.

    """
    contents = io.BytesIO(data)
    zip_file = zipfile.ZipFile(contents)

    files = {}
    for filename in zip_file.namelist():
        extension = os.path.splitext(filename)[1][1:]
        buf = io.BytesIO()

        with zip_file.open(filename) as f:
            shutil.copyfileobj(f, buf)

        buf.seek(0)
        files[extension] = buf

    return shapefile.Reader(**files)


class GeorefLiveTest(TestCase):
    """Clase de utilidad para implementar tests para Georef API. Las clases que
    hereden de GeorefLiveTest pueden utilizar el método 'get_response' para
    realizar consultas a una API de prueba.

    Nota: cada test ejecutado bajo GeorefLiveTest cuenta con una conexión real
    a Elasticsearch y tiene acceso a todos los datos almacenados allí. Esto
    permite realizar pruebas contra los datos utilizados por Georef API, además
    del código mismo de la API. Por defecto, se utilizan los valores de la
    configuración de ejemplo (config/georef.example.cfg) para establecer la
    conexión (ver Makefile).

    """

    def __init__(self, *args, **kwargs):
        self.endpoint = None
        self.entity = None
        super().__init__(*args, **kwargs)

    def setUp(self):
        app.testing = True
        self.app = app.test_client()

    def get_response(self, params=None, method='GET', body=None,
                     return_value='data', endpoint=None, entity=None,
                     expect_status=None, url=None):
        """Método de uso general para obtener respuestas de la API. El método
        permite consultar la API especificando parámetros, formato de la
        respuesta, valor de retorno deseado y más. Internamente, se utiliza una
        app Flask de prueba para obtener las respuestas. El objetivo es simular
        una consulta HTTP a la API desde un cliente externo.

        Por defecto (con return_value == 'data'), se procesa la respuesta
        dependiendo de su formato y se retorna un objeto Python apropiado. Por
        ejemplo, una respuesta con formato=json retorna dict, una con
        formato=xml returna un ElementTree y una con formato=csv retorna un
        csv.Reader.

        Args:
            params (dict): Diccionario de parámetros a utilizar cuando
                method == 'GET'. Se agregan los valores del diccionario a la
                URL en forma de un query string.
            method (str): Método HTTP a utilizar. Valores permitidos: 'GET' o
                'POST'.
            body (dict): Valor a utilizar como cuerpo de la petición HTTP en
                caso de que method == 'POST'.
            return_value (str): Valor de retorno deseado de la consulta HTTP.
                Los valores posibles son: 'data' para obtener el cuerpo de la
                respuesta procesado, 'full' para obtener la enteridad de la
                respuesta en formato JSON sin procesar, 'raw' para obtener los
                bytes de respuesta sin procesar y 'status' para obtener
                sólamente el status_code HTTP de la respuesta como número
                entero.
            endpoint (str): Recurso de la API a consultar. Por defecto, se
                utiliza el valor de 'self.endpoint'.
            entity (str): Nombre (plural) de la entidad que se desea consultar.
                Por defecto, se utiliza el valor de 'self.entity'.
            expect_status (list): Lista de códigos HTTP que se deberían tomar
                como válidos en las respuestas.
            url (str): Utilizar una URL predeterminada en vez de construir una
                utilizando 'endpoint' y 'params'.

        Returns:
            ElementTree, dict, csv.Reader, int, bytes: resultado dependiendo de
                los parámetros especificados.

        """
        params = params or {}
        expect_status = expect_status or [200]
        endpoint = endpoint or self.endpoint
        entity = entity or self.entity
        url = url or '{}?{}'.format(endpoint, urllib.parse.urlencode(params))
        fmt = params.get('formato', 'json')

        if method == 'POST' and fmt != 'json':
            raise ValueError(
                'Las consultas POST solo están disponibles en JSON.')

        if method == 'GET':
            response = self.app.get(url)
        elif method == 'POST':
            response = self.app.post(url, json=body)
        else:
            raise ValueError('Unknown method: {}'.format(method))

        if response.status_code not in expect_status:
            raise RuntimeError('Unexpected status code: {}'.format(
                response.status_code))

        if return_value == 'status':
            return response.status_code

        if return_value in ['data', 'full', 'raw']:
            if return_value == 'data':
                if fmt == 'json':
                    key = entity if method == 'GET' else 'resultados'
                    return json.loads(response.data)[key]

                if fmt == 'geojson':
                    return json.loads(response.data)

                if fmt == 'csv':
                    return csv.reader(response.data.decode().splitlines(),
                                      delimiter=formatter.CSV_SEP,
                                      quotechar=formatter.CSV_QUOTE,
                                      lineterminator=formatter.CSV_NEWLINE)

                if fmt == 'xml':
                    return ElementTree.fromstring(response.data.decode())

                if fmt == 'shp':
                    return shapefile_from_zip_bytes(response.data)

                raise ValueError('Unknown format')

            if return_value == 'full':
                return json.loads(response.data)

            if return_value == 'raw':
                return response.data

        raise ValueError('Unknown return type')

    def assert_valid_csv(self, params=None):
        if not params:
            params = {}

        params['formato'] = 'csv'

        query = self.endpoint + '?' + urllib.parse.urlencode(params)
        response = self.app.get(query)
        text = response.data.decode()

        dialect = csv.Sniffer().sniff(text)
        has_header = csv.Sniffer().has_header(text)
        row_count = len(text.splitlines())

        self.assertTrue(all([dialect.delimiter == formatter.CSV_SEP,
                             has_header,
                             row_count > 0]))

    def assert_valid_geojson(self, params=None):
        if not params:
            params = {}
        params['formato'] = 'geojson'

        geodata = self.get_response(params)
        self.assertTrue(len(geodata['features']) > 0)

    def assert_valid_xml(self, params=None):
        if not params:
            params = {}

        json_resp = self.get_response(params=params, return_value='full')
        json_as_xml = formatter.value_to_xml(self.entity,
                                             json_resp[self.entity])

        params['formato'] = 'xml'
        xml_resp = self.get_response(params=params)
        xml_entities = xml_resp.find('resultado').find(self.entity)

        self.assert_xml_equal(json_as_xml, xml_entities)

    def assert_xml_equal(self, element_a, element_b):
        self.assertEqual(ElementTree.tostring(element_a, encoding='unicode'),
                         ElementTree.tostring(element_b, encoding='unicode'))

    def assert_shp_projection_present(self):
        data = self.get_response({'formato': 'shp'}, return_value='raw')
        contents = io.BytesIO(data)
        zip_file = zipfile.ZipFile(contents)

        buf = io.BytesIO()
        with zip_file.open(self.entity + '.prj') as f:
            shutil.copyfileobj(f, buf)
            buf.seek(0)

        # pylint: disable=protected-access
        self.assertEqual(formatter._SHP_PRJ, buf.getvalue().decode('utf-8'))

    def assert_valid_shp_type(self, shape_type, params=None):
        if not params:
            params = {}
        params['formato'] = 'shp'

        shape = self.get_response(params)
        self.assertEqual(shape.shapeType, shape_type)

    def assert_valid_shp_query(self, params=None):
        if not params:
            params = {}

        json_resp = self.get_response(params)

        params['formato'] = 'shp'
        shape = self.get_response(params)

        self.assertEqual(len(json_resp), len(shape.shapes()))

        json_records = sorted([
            (entity['id'], entity['nombre'])
            for entity in json_resp
        ])

        shape_records = sorted([
            (record['id'], record['nombre'])
            for record in shape.records()
        ])

        self.assertListEqual(json_records, shape_records)

    def assert_shp_fields(self, set_name, fields):
        params = {
            'campos': set_name,
            'formato': 'shp',
            'max': 1
        }
        fields = sorted(fields)

        shape = self.get_response(params)
        shp_fields = sorted([field[0] for field in shape.fields[1:]])

        # TODO: Cambiar a self.assertListEqual(fields, shp_fields)
        # Por alguna razón, pyshp está truncando los nombres de los campos
        # a 10 cuando lee un .shp (pero el archivo se está escribiendo bien)
        self.assertTrue(all(
            field.startswith(shp_field)
            for field, shp_field in zip(fields, shp_fields)
        ) and len(shp_fields) == len(fields))

    def assert_flat_results(self):
        resp = self.get_response({'aplanar': 1, 'max': 1})
        self.assertTrue(all([
            not isinstance(v, dict) for v in resp[0].values()
        ]) and resp)

    def assert_fields_set_equals(self, set_name, fields, params=None,
                                 iterable=True):
        if not params:
            params = {}

        params['campos'] = set_name
        resp = self.get_response(params)
        entity_a = resp[0] if iterable else resp
        formatter.flatten_dict(entity_a, sep='.')

        params['campos'] = ', '.join(fields)
        resp = self.get_response(params)
        entity_b = resp[0] if iterable else resp
        formatter.flatten_dict(entity_b, sep='.')

        self.assertListEqual(sorted(entity_a.keys()), sorted(entity_b.keys()))

    def assert_name_search_id_matches(self, term_matches, exact=False):
        results = []
        for _, query in term_matches:
            params = {'nombre': query}
            if exact:
                params['exacto'] = 1
            res = self.get_response(params)
            results.append(sorted([p['id'] for p in res]))

        self.assertListEqual([sorted(ids) for ids, _ in term_matches], results)


class GeorefMockTest(GeorefLiveTest):
    """La clase GeorefMockTest debería ser considerada idéntica a
    GeorefLiveTest, con la excepción de que cualquier clase que herede de ella
    *no* cuenta con una conexión a Elasticsearch en sus tests: se utiliza el
    módulo 'mock' de Python para crear una conexión simulada.

    Los tests ejecutados bajo GeorefMockTest *no* requieren de una conexión
    real a Elasticsearch, y nunca intentarán abrir una.

    """

    def setUp(self):
        self.patcher = mock.patch('elasticsearch.Elasticsearch', autospec=True)
        self.es = self.patcher.start()
        super().setUp()

    def tearDown(self):
        with app.app_context():
            if hasattr(current_app, 'elasticsearch'):
                delattr(current_app, 'elasticsearch')

        self.es = None
        self.patcher.stop()
        self.patcher = None
        super().tearDown()

    def set_msearch_results(self, results):
        """Establece los valores que debería retornar el método msearch() de
        Elasticsearch. Notar que se establecen los resultados para una sola
        query: si se llega a utilizar uno de los recursos POST con más de una
        query, ocurriría un error interno en la API.

        Args:
            results (list): Lista de 'hits' (documentos) para una única query.

        """
        hits = [{'_source': copy.deepcopy(result)} for result in results]

        class Total:
            value = 0
            relation = 'eq'

        total = Total()
        total.value = len(hits)

        self.es.return_value.msearch.return_value = {
            'responses': [
                {
                    'hits': {
                        'hits': hits,
                        'total': total
                    }
                }
            ]
        }
