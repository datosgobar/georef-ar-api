# -*- coding: utf-8 -*-

from elasticsearch import Elasticsearch, ElasticsearchException
import json
import sys
import os

INDEXES = ['provincias', 'departamentos', 'municipios', 'localidades', 'bahra']

DEFAULT_SETTINGS = {
    'analysis': {
        'normalizer': {
            'uppercase_normalizer': {
                'type': 'custom',
                'filter': ['uppercase']
            }
        }
    }
}

MESSAGES = {
    'states_exists': 'Ya existe el índice de Provincias.',
    'states_info': '-- Creando índice de Provincias.',
    'states_success': 'Se creó el índice de Provincias exitosamente.',
    'departments_exists': 'Ya existe el índice de Departamentos.',
    'departments_info': '-- Creando índice de Departamentos.',
    'departments_success': 'Se creó el índice de Departamentos exitosamente.',
    'municipalities_exists': 'Ya existe el índice de Municipios.',
    'municipalities_info': '-- Creando índice de Municipios.',
    'municipalities_success': 'Se creó el índice de Municipios exitosamente.',
    'localities_exists': 'Ya existe el índice de Localidades.',
    'localities_info': '-- Creando índice de Localidades.',
    'localities_sucess': 'Se creó el índice de Localidades exitosamente.',
    'settlements_exists': 'Ya existe el índice de BAHRA.',
    'settlements_info': '-- Creando índice de Asentamientos.',
    'settlements_success': 'Se creó el índice de Asentamientos exitosamente.',
    'roads_exists': 'Ya existe el índice "%s".',
    'roads_info': '-- Creando índice de calles: "%s".',
    'roads_success': 'Se creó el índice de "%s" exitosamente.',
    'index_error_add': 'Error: debe ingresar un índice.',
    'index_delete': 'Se eliminó el índice "%s" correctamente.',
    'invalid_option': 'Opción inválida.',
    'file_not_exists': 'No existe el archivo "%s.json".'
}


def run():
    try:
        args = sys.argv[1:]
        if not args:
            print('''
            crear-entidades         Crear índices de entidades
            crear-vias              Crear índices de Vías de circulación
            borrar <nombre-índice>  Borrar un índice de entidad
            borrar-entidades        Borrar todos los índices de entidades
            ''')
        else:
            if args[0] == 'crear-entidades':
                create_entities_indexes()
            elif args[0] == 'borrar-entidades':
                delete_indexes()
            elif args[0] == 'crear-vias':
                index_roads()
            elif args[0] == 'borrar':
                if len(args) == 1:
                    raise SyntaxError(MESSAGES['index_error_add'])
                delete_index(args[1])
            else:
                print(MESSAGES['invalid_option'])

    except Exception as e:
        print(e)


def create_entities_indexes():
    es = Elasticsearch()
    index_states(es)
    index_departments(es)
    index_municipalities(es)
    index_localities(es)
    index_settlements(es)


def index_states(es):
    path_file = os.environ.get('ENTIDADES_DATA_DIR') + 'provincias.json'

    if es.indices.exists(index='provincias'):
        print(MESSAGES['states_exists'])
        return
    if os.path.exists(path_file):
        print(MESSAGES['states_info'])

        mapping = {
            'provincia': {
                'properties': {
                    'id': {'type': 'keyword'},
                    'nombre': {
                        'type': 'keyword',
                        'normalizer': 'uppercase_normalizer'
                    },
                    'lat': {'type': 'keyword'},
                    'lon': {'type': 'keyword'},
                    'geometry': {'type': 'geo_shape'}
                }
            }
        }
        es.indices.create(index='provincias', body={
            'settings': DEFAULT_SETTINGS,
            'mappings': mapping
        })

        data = json.load(open(path_file))
        es.bulk(index='provincias', doc_type='provincia', body=data,
                refresh=True, request_timeout=320)
        print(MESSAGES['states_success'])
    else:
        print(MESSAGES['file_not_exists'] % 'provincias')


def index_departments(es):
    path_file = os.environ.get('ENTIDADES_DATA_DIR') + 'departamentos.json'

    if es.indices.exists(index='departamentos'):
        print(MESSAGES['departments_exists'])
        return
    if os.path.exists(path_file):
        print(MESSAGES['departments_info'])

        mapping = {
            'departamento': {
                'properties': {
                    'id': {'type': 'keyword'},
                    'nombre': {
                        'type': 'keyword',
                        'normalizer': 'uppercase_normalizer'
                    },
                    'lat': {'type': 'keyword'},
                    'lon': {'type': 'keyword'},
                    'geometry': {'type': 'geo_shape'},
                    'provincia': {
                        'type': 'object',
                        'dynamic': 'false',
                        'properties': {
                            'id': {'type': 'keyword'},
                            'nombre': {
                                'type': 'keyword',
                                'normalizer': 'uppercase_normalizer'
                            },
                        }
                    }
                }
            }
        }

        es.indices.create(index='departamentos', body={
            'settings': DEFAULT_SETTINGS,
            'mappings': mapping
        })

        data = json.load(open(path_file))

        es.bulk(index='departamentos', doc_type='departamento', body=data,
                refresh=True, request_timeout=320)
        print(MESSAGES['departments_success'])
    else:
        print(MESSAGES['file_not_exists'] % 'departamentos')


def index_municipalities(es):
    path_file = os.environ.get('ENTIDADES_DATA_DIR') + 'municipios.json'

    if es.indices.exists(index='municipios'):
        print(MESSAGES['municipalities_exists'])
        return
    if os.path.exists(path_file):
        print(MESSAGES['municipalities_info'])

        mapping = {
            'municipio': {
                'properties': {
                    'id': {'type': 'keyword'},
                    'nombre': {
                        'type': 'keyword',
                        'normalizer': 'uppercase_normalizer'
                    },
                    'lat': {'type': 'keyword'},
                    'lon': {'type': 'keyword'},
                    'geometry': {'type': 'geo_shape'},
                    'departamento': {
                        'type': 'object',
                        'dynamic': 'false',
                        'properties': {
                            'id': {'type': 'keyword'},
                            'nombre': {
                                'type': 'keyword',
                                'normalizer': 'uppercase_normalizer'
                            },
                        }
                    },
                    'provincia': {
                        'type': 'object',
                        'dynamic': 'false',
                        'properties': {
                            'id': {'type': 'keyword'},
                            'nombre': {
                                'type': 'keyword',
                                'normalizer': 'uppercase_normalizer'
                            }
                        }
                    }
                }
            }
        }

        es.indices.create(index='municipios', body={
            'settings': DEFAULT_SETTINGS,
            'mappings': mapping
        })

        data = json.load(open(path_file))

        es.bulk(index='municipios', doc_type='municipio', body=data,
                refresh=True, request_timeout=320)
        print(MESSAGES['municipalities_success'])
    else:
        print(MESSAGES['file_not_exists'] % 'municipios')


def index_localities(es):
    path_file = os.environ.get('ENTIDADES_DATA_DIR') + 'localidades.json'

    if es.indices.exists(index='localidades'):
        print(MESSAGES['localities_exists'])
        return
    if os.path.exists(path_file):
        print(MESSAGES['localities_info'])

        mapping = {
            'localidad': {
                'properties': {
                    'id': {'type': 'keyword'},
                    'nombre': {
                        'type': 'keyword',
                        'normalizer': 'uppercase_normalizer'
                    },
                    'departamento': {
                        'type': 'object',
                        'dynamic': 'false',
                        'properties': {
                            'id': {'type': 'keyword'},
                            'nombre': {
                                'type': 'keyword',
                                'normalizer': 'uppercase_normalizer'
                            },
                        }
                    },
                    'provincia': {
                        'type': 'object',
                        'dynamic': 'false',
                        'properties': {
                            'id': {'type': 'keyword'},
                            'nombre': {
                                'type': 'keyword',
                                'normalizer': 'uppercase_normalizer'
                            }
                        }
                    }
                }
            }
        }

        es.indices.create(index='localidades', body={
            'settings': DEFAULT_SETTINGS,
            'mappings': mapping
        })

        data = json.load(open(path_file))

        es.bulk(index='localidades', doc_type='localidad', body=data,
                refresh=True, request_timeout=120)
        print(MESSAGES['localities_sucess'])
    else:
        print(MESSAGES['file_not_exists'] % 'localidades')


def index_settlements(es):
    path_file = os.environ.get('ENTIDADES_DATA_DIR') + 'asentamientos.json'

    if es.indices.exists(index='bahra'):
        print(MESSAGES['settlements_exists'])
        return
    if os.path.exists(path_file):
        print(MESSAGES['settlements_info'])

        mapping = {
            'asentamiento': {
                'properties': {
                    'id': {'type': 'keyword'},
                    'nombre': {
                        'type': 'keyword',
                        'normalizer': 'uppercase_normalizer'
                    },
                    'tipo': {'type': 'keyword'},
                    'lat': {'type': 'keyword'},
                    'lon': {'type': 'keyword'},
                    'geometry': {'type': 'geo_shape'},
                    'municipio': {
                        'type': 'object',
                        'dynamic': 'false',
                        'properties': {
                            'id': {'type': 'keyword'},
                            'nombre': {
                                'type': 'keyword',
                                'normalizer': 'uppercase_normalizer'
                            },
                        }
                    },
                    'departamento': {
                        'type': 'object',
                        'dynamic': 'false',
                        'properties': {
                            'id': {'type': 'keyword'},
                            'nombre': {
                                'type': 'keyword',
                                'normalizer': 'uppercase_normalizer'
                            },
                        }
                    },
                    'provincia': {
                        'type': 'object',
                        'dynamic': 'false',
                        'properties': {
                            'id': {'type': 'keyword'},
                            'nombre': {
                                'type': 'keyword',
                                'normalizer': 'uppercase_normalizer'
                            },
                        }
                    }
                }
            }
        }

        es.indices.create(index='bahra', body={
            'settings': DEFAULT_SETTINGS,
            'mappings': mapping
        })

        data = json.load(open(path_file))

        es.bulk(index='bahra', doc_type='asentamiento', body=data, refresh=True,
                request_timeout=320)
        print(MESSAGES['settlements_success'])
    else:
        print(MESSAGES['file_not_exists'] % 'asentamientos')


def index_roads():
    es = Elasticsearch()
    path = os.environ.get('VIAS_DATA_DIR')
    objects = os.listdir(path)

    for i in objects:
        index_name = i[:-5]
        if es.indices.exists(index=index_name):
            print(MESSAGES['roads_exists'] % index_name)
            continue
        print(MESSAGES['roads_info'] % index_name)
        data = json.load(open('{}{}'.format(path, i)))
        es.bulk(index=index_name, doc_type='calle', body=data, refresh=True,
                request_timeout=320)
        print(MESSAGES['roads_success'] % index_name)


def delete_index(index):
    try:
        Elasticsearch().indices.delete(index=index)
        print(MESSAGES['index_delete'] % index)
    except (ElasticsearchException, SyntaxError) as error:
        print(error)


def delete_indexes():
    try:
        for index in INDEXES:
            Elasticsearch().indices.delete(index=index)
            print(MESSAGES['index_delete'] % index)
    except (ElasticsearchException, SyntaxError) as error:
        print(error)


if __name__ == '__main__':
    run()
