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
import sys

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


class IndexExistsException(Exception):
    pass


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
                        help='Ignorar errores de índices ya existentes'
                        ' (creación) o no existentes (borrado).',
                        dest='ignore')
    args = parser.parse_args()

    if args.timeout <= 0:
        raise ValueError('Se especificó un tiempo de espera inválido.')

    es = Elasticsearch(timeout=args.timeout)
    mode = args.mode[0]

    if mode == 'listar':
        list_indices(es)
    elif mode == 'indexar':
        create_index(es, args.name, args.ignore)
    elif mode == 'borrar':
        delete_index(es, args.name, args.ignore)
    else:
        raise ValueError('Modo inválido.')


def list_indices(es):
    """
    Listar índices existentes en Elasticsearch.

    Args:
        es (elasticsearch.client.Elasticsearch): Instancia cliente
            Elasticsearch.
    """

    for index in sorted(es.indices.get_alias('*')):
        print(index)


def create_index(es, name, ignore):
    """
    Crear índices para entidades o vías de circulación.

    Args:
        es (elasticsearch.client.Elasticsearch): Instancia cliente
            Elasticsearch.
        name (str): Nombre de entidad o 'vias'.
        ignore (bool): Si es verdadero, se ignoran ciertas excepciones lanzadas
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
            create_entity_index(es, file_path, name, MAP_STATE, MAP_STATE_GEOM,
                                ignore)
        elif name == 'departamentos':
            create_entity_index(es, file_path, name, MAP_DEPT, MAP_DEPT_GEOM,
                                ignore)
        elif name == 'municipios':
            create_entity_index(es, file_path, name, MAP_MUNI, MAP_MUNI_GEOM,
                                ignore)
        elif name == 'bahra':
            create_entity_index(es, file_path, name, MAP_SETTLEMENT,
                                MAP_SETTLEMENT_GEOM, ignore)
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
            data = read_json(file_path)

            try:
                index_entity(es, data, index_name, MAP_STREET)
            except IndexExistsException as e:
                if ignore:
                    print(
                        'Se ignoró la siguiente excepción: {}'.format(repr(e)),
                        file=sys.stderr)
                else:
                    raise

    else:
        raise ValueError('Nombre de índice inválido.')


def create_entity_index(es, file_path, index, mapping, mapping_geom, ignore):
    """
    Crear dos índices para una entidad: con y sin geometrías.

    Args:
        es (elasticsearch.client.Elasticsearch): Instancia cliente
            Elasticsearch.
        file_path (str): Path de archivo JSON con entidades.
        index (str): Nombre base del índice a crear.
        mapping (dict): Mapeo Elasticsearch de entidades (sin geometría).
        mapping_geom (dict): Mapeo Elasticsearch de entidades (con geometría).
        ignore (bool): Si es verdadero, se ignoran ciertas excepciones lanzadas
    """

    data = read_json(file_path)

    try:
        # Crear índice para la entidad sin geometrías
        index_entity(es, data, index, mapping, ['geometria'])
    except IndexExistsException as e:
        if ignore:
            print('Se ignoró la siguiente excepción: {}'.format(repr(e)),
                  file=sys.stderr)
        else:
            raise

    try:
        # Crear índice para la entidad con geometrías
        index_entity(es, data, index + '-geometria', mapping_geom)
    except IndexExistsException as e:
        if ignore:
            print('Se ignoró la siguiente excepción: {}'.format(repr(e)),
                  file=sys.stderr)
        else:
            raise


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
                    print('Se ignoró la siguiente excepción: {}'.format(
                        repr(e)),
                          file=sys.stderr)
                else:
                    raise
    elif name == ROAD_INDEX:
        for state_id in STATE_IDS:
            try:
                delete_road_index(es, state_id)
            except IndexMissingException as e:
                if ignore:
                    print('Se ignoró la siguiente excepción: {}'.format(
                        repr(e)),
                          file=sys.stderr)
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


def document_list(data, excludes=None):
    """
    Transforma una lista de entidades a una lista de documentos listos para
    ser indexados en Elasticsearch.

    Args:
        data (list): Lista de entidades a transformar a documentos indexables.
        excludes (list): Lista de atributos a remover de cada entidad antes de
            agregar a la lista de documentos.
    """

    docs = []
    for i, doc in enumerate(data):
        docs.append({'index': {'_id': i + 1, '_type': '_doc'}})

        if excludes is None:
            excludes = []

        docs.append({
            key: doc[key] for key in doc.keys() if key not in excludes
        })

    return docs


def index_entity(es, data, index, mappings, excludes=None):
    """
    Genera índices Elasticsearch para una entidad, comprobando que el índice
    ya no exista.

    Args:
        es (elasticsearch.client.Elasticsearch): Instancia cliente
            Elasticsearch.
        data: Datos a indexar (entidades).
        index (str): Nombre del índice a crear, si no existe.
        mappings (dict): Mapeos de tipos de Elasticsearch.
        excludes (map): Campos a ignorar completamente al momento de indexar.
    """

    if es.indices.exists(index=index):
        raise IndexExistsException('Index already exists: {}'.format(index))

    es.indices.create(index=index, body={
        'settings': DEFAULT_SETTINGS,
        'mappings': mappings
    })

    docs = document_list(data, excludes)
    es.bulk(index=index, body=docs, refresh=True)


if __name__ == '__main__':
    main()
