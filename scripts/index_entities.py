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
    'states_exists': '-- Ya existe el índice de Provincias.',
    'states_info': '-- Creando índice de Provincias.',
    'states_success': '-- Se creó el índice de Provincias exitosamente.',
    'departments_exists': '-- Ya existe el índice de Departamentos.',
    'departments_info': '-- Creando índice de Departamentos.',
    'departments_success': '-- Se creó el índice de Departamentos exitosamente.',
    'municipality_exists': '-- Ya existe el índice de Municipios.',
    'municipality_info': '-- Creando índice de Municipios.',
    'municipality_success': '-- Se creó el índice de Municipios exitosamente.',
    'locality_exists': '-- Ya existe el índice de Localidades.',
    'locality_info': '-- Creando índice de Localidades.',
    'locality_sucess': '-- Se creó el índice de Localidades exitosamente.',
    'settlement_exists': '-- Ya existe el índice de BAHRA.',
    'settlement_info': '-- Creando índice de Asentamientos.',
    'settlement_success': '-- Se creó el índice de Asentamientos exitosamente.',
    'index_error_add': 'Error: debe ingresar un índice.',
    'index_delete': 'Se eliminó el índice "%s" correctamente.',
    'invalid_option': 'Opción inválida.'
}


def run():
    try:
        args = sys.argv[1:]
        if not args:
            print('''
            create                  Crear índices de entidades
            delete <nombre-índice>  Borrar un índice de entidad
            delete-all              Borrar todos los índices de entidades
            ''')
        else:
            if args[0] == 'create':
                create_entities_indexes()
            elif args[0] == 'delete':
                if len(args) == 1:
                    raise SyntaxError(MESSAGES['index_error_add'])
                delete_index(args[1])
            elif args[0] == 'delete-all':
                delete_indexes()
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
    if es.indices.exists(index='provincias'):
        print(MESSAGES['states_exists'])
        return
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

    data = json.load(open(os.environ.get('PROVINCIAS_DATA_PATH')))

    es.bulk(index='provincias', doc_type='provincia', body=data, refresh=True,
            request_timeout=320)
    print(MESSAGES['states_success'])


def index_departments(es):
    if es.indices.exists(index='departamentos'):
        print(MESSAGES['departments_exists'])
        return
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

    data = json.load(open(os.environ.get('DEPARTAMENTOS_DATA_PATH')))

    es.bulk(index='departamentos', doc_type='departamento', body=data,
            refresh=True, request_timeout=320)
    print(MESSAGES['departments_success'])


def index_municipalities(es):
    if es.indices.exists(index='municipios'):
        print(MESSAGES['municipality_exists'])
        return
    print(MESSAGES['municipality_info'])

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

    data = json.load(open(os.environ.get('MUNICIPIOS_DATA_PATH')))

    es.bulk(index='municipios', doc_type='municipio', body=data,
            refresh=True, request_timeout=320)
    print(MESSAGES['municipality_success'])


def index_localities(es):
    if es.indices.exists(index='localidades'):
        print(MESSAGES['locality_exists'])
        return
    print(MESSAGES['locality_info'])

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

    data = json.load(open(os.environ.get('LOCALIDADES_DATA_PATH')))

    es.bulk(index='localidades', doc_type='localidad', body=data, refresh=True,
            request_timeout=120)
    print(MESSAGES['locality_sucess'])


def index_settlements(es):
    if es.indices.exists(index='bahra'):
        print(MESSAGES['settlement_exists'])
        return
    print(MESSAGES['settlement_info'])

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

    data = json.load(open(os.environ.get('ASENTAMIENTOS_DATA_PATH')))

    es.bulk(index='bahra', doc_type='asentamiento', body=data, refresh=True,
            request_timeout=320)
    print(MESSAGES['settlement_success'])


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
