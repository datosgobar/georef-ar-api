from elasticsearch import Elasticsearch
from elasticsearch_params import DEFAULT_SETTINGS
from elasticsearch_mappings import MAP_STATE, MAP_STATE_GEOM
from elasticsearch_mappings import MAP_DEPT, MAP_DEPT_GEOM
from elasticsearch_mappings import MAP_MUNI, MAP_MUNI_GEOM
from elasticsearch_mappings import MAP_SETTLEMENT, MAP_SETTLEMENT_GEOM
from elasticsearch_mappings import MAP_STREET

import argparse
import json
import os
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.addHandler(handler)

GEOM = '-geometria'
OPERATIONS = ['indexar', 'borrar', 'listar']
ENTITY_INDICES = ['provincias', 'departamentos', 'municipios', 'bahra']
ROAD_INDEX = 'vias'
STATE_IDS = [
    '02',
    '06',
    '10',
    '14',
    '18',
    '22',
    '26',
    '30',
    '34',
    '38',
    '42',
    '46',
    '50',
    '54',
    '58',
    '62',
    '66',
    '70',
    '74',
    '78',
    '82',
    '86',
    '90',
    '94'
]


class IndexMissingException(Exception):
    pass


class InvalidEnvException(Exception):
    pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', metavar='<mode>', nargs=1, choices=OPERATIONS,
                        help='Indexar, borrar o listar.')
    parser.add_argument('-n', '--name', metavar='<name>',
                        choices=ENTITY_INDICES + [ROAD_INDEX],
                        help='Nombre de índice.')
    parser.add_argument('-t', '--timeout', metavar='<seconds>', default=300,
                        type=int, help='Tiempo de espera para transferencias.')
    parser.add_argument('-i', '--ignore', action='store_true',
                        help='Ignorar errores de índices no \
                            existentes (al borrar).',
                        dest='ignore')
    parser.add_argument('-c', '--create', action='store_true',
                        help='Crear índices si no existen (al indexar).',
                        dest='create')
    args = parser.parse_args()

    if args.timeout <= 0:
        raise ValueError('Se especificó un tiempo de espera inválido.')

    es = Elasticsearch(timeout=args.timeout)
    mode = args.mode[0]

    logger.info('Iniciando en modo: {}...'.format(mode))

    if mode == 'listar':
        list_indices(es)
    elif mode == 'indexar':
        update_index(es, args.name, args.create)
    elif mode == 'borrar':
        delete_index(es, args.name, args.ignore)
    else:
        raise ValueError('Modo inválido.')

    logger.info('Operación finalizada.')


def list_indices(es):
    """
    Listar índices existentes en Elasticsearch.

    Args:
        es (elasticsearch.client.Elasticsearch): Instancia cliente
            Elasticsearch.
    """

    for index in sorted(es.indices.get_alias('*')):
        logger.info(index)


def update_index(es, name, create):
    """
    Actualiza índices para entidades o vías de circulación.

    Args:
        es (elasticsearch.client.Elasticsearch): Instancia cliente
            Elasticsearch.
        name (str): Nombre de entidad o 'vias'.
        create (bool): Si es verdadero, se crean los índices si no existen
    """

    if name in ENTITY_INDICES:
        base_path = os.environ.get('ENTIDADES_DATA_DIR')
        if not base_path:
            raise InvalidEnvException(
                'Valor de entorno no encontrado: ENTIDADES_DATA_DIR')

        if name != 'bahra':
            file_path = os.path.join(base_path, name + '.json')
        else:
            file_path = os.path.join(base_path, 'asentamientos.json')

        if name == 'provincias':
            update_entity_index(es, file_path, name, MAP_STATE, MAP_STATE_GEOM,
                                create)
        elif name == 'departamentos':
            update_entity_index(es, file_path, name, MAP_DEPT, MAP_DEPT_GEOM,
                                create)
        elif name == 'municipios':
            update_entity_index(es, file_path, name, MAP_MUNI, MAP_MUNI_GEOM,
                                create)
        elif name == 'bahra':
            update_entity_index(es, file_path, name, MAP_SETTLEMENT,
                                MAP_SETTLEMENT_GEOM, create)
        else:
            raise ValueError('Nombre de entidad inválido: {}'.format(name))

    elif name == ROAD_INDEX:
        base_path = os.environ.get('VIAS_DATA_DIR')
        if not base_path:
            raise InvalidEnvException(
                'Valor de entorno no encontrado: VIAS_DATA_DIR')

        for state_id in STATE_IDS:
            index_name = 'calles-' + state_id
            file_path = os.path.join(base_path, index_name + '.json')
            contents = read_json(file_path)
            data = contents['vias']
            timestamp = contents['timestamp']

            if create:
                create_index(es, index_name, MAP_STREET)

            index_entity(es, data, timestamp, index_name, ['codigo_postal'])

    else:
        raise ValueError('Nombre de índice inválido.')


def update_entity_index(es, file_path, index, mapping, mapping_geom, create):
    """
    Actualiza (y crea) dos índices para una entidad: con y sin geometrías.

    Args:
        es (elasticsearch.client.Elasticsearch): Instancia cliente
            Elasticsearch.
        file_path (str): Path de archivo JSON con entidades.
        index (str): Nombre base del índice a crear.
        mapping (dict): Mapeo Elasticsearch de entidades (sin geometría).
        mapping_geom (dict): Mapeo Elasticsearch de entidades (con geometría).
        create (bool): Si es verdadero, se crean los índices si no existen
    """

    contents = read_json(file_path)
    data = contents['entidades']
    timestamp = contents['timestamp']

    if create:
        create_index(es, index, mapping)
    index_entity(es, data, timestamp, index, ['geometria'])

    if create:
        create_index(es, index + '-geometria', mapping_geom)
    index_entity(es, data, timestamp, index + '-geometria')


def delete_index(es, name, ignore):
    """
    Borra índice para una entidad o para vías de circulación.

    Args:
        es (elasticsearch.client.Elasticsearch): Instancia cliente
            Elasticsearch.
        name (str): Nombre de la entidad o 'vias'.
        ignore (bool): Si es verdadero, se ignoran ciertas excepciones lanzadas
    """

    if not name:
        raise ValueError('Se debe especificar un nombre de índice.')

    if name in ENTITY_INDICES:
        geom_index = name + '-geometria'
        for index in [name, geom_index]:
            try:
                delete_entity_index(es, index)
            except IndexMissingException as e:
                if ignore:
                    logger.warning(
                        'Se ignoró la siguiente excepción: {}'.format(
                            repr(e)))
                else:
                    raise
    elif name == ROAD_INDEX:
        for state_id in STATE_IDS:
            try:
                delete_road_index(es, state_id)
            except IndexMissingException as e:
                if ignore:
                    logger.warning(
                        'Se ignoró la siguiente excepción: {}'.format(
                            repr(e)))
                else:
                    raise
    else:
        raise ValueError('Nombre de índice inválido.')


def delete_entity_index(es, name):
    """
    Borra índice de una entidad.

    Args:
        es (elasticsearch.client.Elasticsearch): Instancia cliente
            Elasticsearch.
        name (str): Nombre de la entidad.
    """

    if not es.indices.exists(index=name):
        raise IndexMissingException(
            'El índice especificado no existe: {}'.format(name))

    es.indices.delete(name)

    logger.info('Se eliminó el índice {}.'.format(name))


def delete_road_index(es, state_id):
    """
    Borra índice de vías de circulación para una provincia.

    Args:
        es (elasticsearch.client.Elasticsearch): Instancia cliente
            Elasticsearch.
        state_id (str): Código INDEC de la provincia.
    """

    index = 'calles-' + state_id
    if not es.indices.exists(index=index):
        raise IndexMissingException(
            'El índice especificado no existe: {}'.format(index))

    es.indices.delete(index)

    logger.info('Se eliminó el índice {}.'.format(index))


def read_json(path):
    """
    Lee un archivo JSON y devuelve sus contenidos.

    Args:
        path (str): Path a archivo a leer.
    Returns:
        dict: contenido del archivo JSON.
    """
    with open(path) as f:
        return json.load(f)


def bulk_update_generator(data, timestamp, excludes=None):
    if not excludes:
        excludes = []

    for original_doc in data:
        doc = {
            key: original_doc[key]
            for key in original_doc
            if key not in excludes
        }
        doc['timestamp'] = timestamp

        action = {
            'update': {
                '_type': '_doc',
                '_id': doc['id']
            }
        }

        source = {
            'doc': doc,
            'doc_as_upsert': True
        }

        yield action
        yield source


def create_index(es, index, mappings):
    """
    Asegura que el índice especificado exista.

    Args:
        es (elasticsearch.client.Elasticsearch): Instancia cliente
            Elasticsearch.
        index (str): Nombre del índice a crear, si no existe.
        mappings (dict): Mapeos de tipos de Elasticsearch.
    """

    if es.indices.exists(index=index):
        logger.warning('El índice ya existe: {}'.format(index))
        return

    es.indices.create(index=index, body={
        'settings': DEFAULT_SETTINGS,
        'mappings': mappings
    })

    logger.info('Índice creado: {}'.format(index))


def index_entity(es, data, timestamp, index, excludes=None):
    """
    Inserta datos en un índice Elasticsearch.

    Args:
        es (elasticsearch.client.Elasticsearch): Instancia cliente
            Elasticsearch.
        data: Datos a indexar (entidades).
        timestamp (int): Fecha (UNIX epoch UTC) en el que fueron creados
            los datos.
        index (str): Nombre del índice a crear, si no existe.
        excludes (map): Campos a ignorar completamente al momento de indexar.
    """
    if not es.indices.exists(index=index):
        # Si el índice no existe, evitar que se cree automáticamente
        # con mappings dinámicos, ya que siempre se desea utilizar
        # mappings explícitos.
        raise IndexMissingException('No existe el índice: {}'.format(index))

    logger.info('Indexando datos en: {}...'.format(index))

    operations = bulk_update_generator(data, timestamp, excludes)
    es.bulk(index=index, body=operations, refresh=True)

    logger.info('Terminado.')


if __name__ == '__main__':
    main()
