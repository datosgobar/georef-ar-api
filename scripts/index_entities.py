# -*- coding: utf-8 -*-

from elasticsearch import Elasticsearch, ElasticsearchException
from elasticsearch_params import *
from elasticsearch_mappings import *
import json
import sys
import os

MESSAGES = {
    'index_exists': 'Ya existe el índice "%s".',
    'creating_index': '--> Creando índice: "%s".',
    'creation_success': 'Se creó el índice de "%s" exitosamente.',
    'index_error_add': 'Error: debe ingresar un índice.',
    'index_delete': 'Se eliminó el índice "%s" correctamente.',
    'invalid_option': 'Opción inválida.',
    'file_not_exists': 'No existe el archivo "%s.json".'
}


def run():
    """Recibe argumentos pasados por línea de comando y ejecuta la acción
        solicitada por el usuario.

     Returns:
        str: Devuelve un mensaje con el resultado de la operación.
    """
    try:
        args = sys.argv[1:]
        if not args:
            print('''
            crear-entidades         Crear índices de entidades
            crear-vias              Crear índices de vías de circulación
            borrar <nombre-índice>  Borrar un índice de entidad
            borrar-entidades        Borrar todos los índices de entidades
            listar                  Listar índices
            ''')
        else:
            if args[0] == 'crear-entidades':
                create_entities_indexes()
            elif args[0] == 'borrar-entidades':
                delete_entities()
            elif args[0] == 'crear-vias':
                index_roads()
            elif args[0] == 'borrar':
                if len(args) == 1:
                    raise SyntaxError(MESSAGES['index_error_add'])
                delete_index(args[1])
            elif args[0] == 'listar':
                list_indexes()
            else:
                print(MESSAGES['invalid_option'])

    except Exception as e:
        print(e)


def create_entities_indexes():
    """Crea índices Elasticsearch de entidades políticas."""
    es = Elasticsearch()
    index_states(es)
    index_departments(es)
    index_municipalities(es)
    index_settlements(es)


def read_json(path):
    with open(path) as f:
        return json.load(f)


def document_list(data, excludes=None):
    docs = []
    for i, doc in enumerate(data):
        docs.append({'index': {'_id': i + 1}})

        if excludes is None:
            excludes = []
        
        docs.append({
            key: doc[key] for key in doc.keys() if key not in excludes
        })
    
    return docs


def index_entity(es, index, doc_type, data, mappings, excludes=None):
    """Genera índices Elasticsearch para una entidad, comprobando que el índice
       ya no exista.

    Args:
        es (elasticsearch.client.Elasticsearch): Instancia cliente
        Elasticsearch.
        index_name (str): Nombre del índice a crear, si no existe.
        doc_type (str): Nombre de documento a utilizar.
        data (list): Lista de datos a indexar.
        excludes (map): Campos a ignorar completamente al momento de indexar.
    """  

    if not es.indices.exists(index=index):
        print(MESSAGES['creating_index'] % index)

        es.indices.create(index=index, body={
            'settings': DEFAULT_SETTINGS,
            'mappings': mappings
        })

        docs = document_list(data, excludes)

        es.bulk(index=index, doc_type=doc_type, body=docs, refresh=True,
            request_timeout=320)

        print(MESSAGES['creation_success'] % index)
    else:
        print(MESSAGES['index_exists'] % index)


def index_states(es):
    """Genera índices Elasticsearch para la entidad Provincia.

    Args:
        es (elasticsearch.client.Elasticsearch): Instancia cliente
        Elasticsearch.
    """
    path_file = os.path.join(os.environ.get('ENTIDADES_DATA_DIR'),
                             'provincias.json')

    if os.path.exists(path_file):
        states = read_json(path_file)
    else:
        print(MESSAGES['file_not_exists'] % 'provincias')
        return

    # Crear índice de provincias sin geometrías
    index_entity(es, 'provincias', 'provincia', states, MAP_STATE, ['geometria'])

    # Crear índice de provincias con geometrías
    index_entity(es, 'provincias-geometria', 'provincia', states, MAP_STATE_GEOM)



def index_departments(es):
    """Genera índices Elasticsearch para la entidad Departamento.

    Args:
        es (elasticsearch.client.Elasticsearch): Instancia cliente
        Elasticsearch.
    """
    path_file = os.path.join(os.environ.get('ENTIDADES_DATA_DIR'),
                             'departamentos.json')

    if os.path.exists(path_file):
        depts = read_json(path_file)
    else:
        print(MESSAGES['file_not_exists'] % 'departamentos')
        return

    # Crear índice de departamentos sin geometrías
    index_entity(es, 'departamentos', 'departamento', depts, MAP_DEPT, ['geometria'])

    # Crear índice de departamentos con geometrías
    index_entity(es, 'departamentos-geometria', 'departamento', depts, MAP_DEPT_GEOM)


def index_municipalities(es):
    """Genera índices Elasticsearch para la entidad Municipio.

    Args:
        es (elasticsearch.client.Elasticsearch): Instancia cliente
        Elasticsearch.
    """
    path_file = os.path.join(os.environ.get('ENTIDADES_DATA_DIR'),
                             'municipios.json')

    if os.path.exists(path_file):
        munis = read_json(path_file)
    else:
        print(MESSAGES['file_not_exists'] % 'municipios')
        return

    # Crear índice de municipios sin geometrías
    index_entity(es, 'municipios', 'municipio', munis, MAP_MUNI, ['geometria'])

    # Crear índice de municipios con geometrías
    index_entity(es, 'municipios-geometria', 'municipio', munis, MAP_MUNI_GEOM)


def index_settlements(es):
    """Genera índices Elasticsearch para la entidad Asentamientos informales.

    Args:
        es (elasticsearch.client.Elasticsearch): Instancia cliente
        Elasticsearch.
    """
    path_file = os.path.join(os.environ.get('ENTIDADES_DATA_DIR'),
                             'asentamientos.json')

    if os.path.exists(path_file):
        settlements = read_json(path_file)
    else:
        print(MESSAGES['file_not_exists'] % 'asentamientos')
        return

    # Crear índice de asentamientos sin geometrías
    index_entity(es, 'bahra', 'asentamiento', settlements, MAP_SETTLEMENT, ['geometria'])

    # Crear índice de asentamientos con geometrías
    index_entity(es, 'bahra-geometria', 'asentamiento', settlements, MAP_SETTLEMENT_GEOM)


def index_roads():
    """Genera índices Elasticsearch para vías de circulación.

    Returns:
        str: Devuelve un mensaje con el resultado de la operación.
    """
    es = Elasticsearch()
    path = os.environ.get('VIAS_DATA_DIR')
    objects = os.listdir(path)

    for i in objects:
        index_name = i[:-5]
        index_file = os.path.join(path, i)

        if os.path.exists(index_file):
            roads = read_json(index_file)
        else:
            print(MESSAGES['file_not_exists'] % index_name)
            continue

        index_entity(es, index_name, 'calle', roads, MAP_STREET)


def delete_index(index):
    """Elimina un índice Elasticsearch.

    Args:
        index (str): Nombre del índice que se requiere eliminar.

    Returns:
        str: Devuelve un mensaje con el resultado de la operación.
    """
    try:
        Elasticsearch().indices.delete(index=index)
        print(MESSAGES['index_delete'] % index)
    except (ElasticsearchException, SyntaxError) as error:
        print(error)


def delete_entities():
    """Elimina índices Elasticsearch correspondientes a entidades.

    Returns:
        str: Devuelve un mensaje con el resultado de la operación.
    """
    for index in INDEXES:
        delete_index(index)
        delete_index(index + '-geometria')


def list_indexes():
    """Devuelve un listado con índices Elasticsearch activos.

    Returns:
        str: Devuelve un mensaje con el resultado de la operación.
    """
    try:
        for index in sorted(Elasticsearch().indices.get_alias("*")):
            print(index)
    except (ElasticsearchException, SyntaxError) as error:
        print(error)


if __name__ == '__main__':
    run()
