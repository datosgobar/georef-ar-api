from elasticsearch_params import LOWCASE_ASCII_NORMALIZER
from elasticsearch_params import NAME_ANALYZER
from elasticsearch_params import NAME_ANALYZER_SYNONYMS

# Mapeos de entidades para Elasticsearch
# Por cada entidad, se define un mapeo sin geometría, con campos indexados,
# y otro con geometría, con el resto de los campos sin indexar.
# La separación en dos mapeos por entidad se debe a que las geometrías tienden
# a aumentar significativamente el tamaño de los documentos, por lo que la
# performance de la búsqueda por id/texto/etc se ve disminuida.

# https://www.elastic.co/guide/en/elasticsearch/reference/current/general-recommendations.html#maximum-document-size

MAP_STATE = {
    'provincia': {
        'properties': {
            'id': {'type': 'keyword'},
            'nombre': {
                'type': 'text',
                'analyzer': NAME_ANALYZER_SYNONYMS,
                'search_analyzer': NAME_ANALYZER,
                'fields': {
                    'exacto': {
                        'type': 'keyword',
                        'normalizer': LOWCASE_ASCII_NORMALIZER
                    }
                }
            },
            'lat': {'type': 'keyword'},
            'lon': {'type': 'keyword'}
        }
    }
}

MAP_STATE_GEOM = {
    'provincia': {
        'properties': {
            'id': {'type': 'keyword', 'index': False},
            'nombre': {'type': 'keyword', 'index': False},
            'lat': {'type': 'keyword', 'index': False},
            'lon': {'type': 'keyword', 'index': False},
            'geometria': {'type': 'geo_shape'}
        }
    }
}

MAP_DEPT = {
    'departamento': {
        'properties': {
            'id': {'type': 'keyword'},
            'nombre': {
                'type': 'text',
                'analyzer': NAME_ANALYZER_SYNONYMS,
                'search_analyzer': NAME_ANALYZER,
                'fields': {
                    'exacto': {
                        'type': 'keyword',
                        'normalizer': LOWCASE_ASCII_NORMALIZER
                    }
                }
            },
            'lat': {'type': 'keyword'},
            'lon': {'type': 'keyword'},
            'provincia': {
                'type': 'object',
                'dynamic': 'strict',
                'properties': {
                    'id': {'type': 'keyword'},
                    'nombre': {
                        'type': 'text',
                        'analyzer': NAME_ANALYZER_SYNONYMS,
                        'search_analyzer': NAME_ANALYZER,
                        'fields': {
                            'exacto': {
                                'type': 'keyword',
                                'normalizer': LOWCASE_ASCII_NORMALIZER
                            }
                        }
                    }
                }
            }
        }
    }
}

MAP_DEPT_GEOM = {
    'departamento': {
        'properties': {
            'id': {'type': 'keyword', 'index': False},
            'nombre': {'type': 'keyword', 'index': False},
            'lat': {'type': 'keyword', 'index': False},
            'lon': {'type': 'keyword', 'index': False},
            'provincia': {'type': 'object', 'enabled': False},
            'geometria': {'type': 'geo_shape'}
        }
    }
}

MAP_MUNI = {
    'municipio': {
        'properties': {
            'id': {'type': 'keyword'},
            'nombre': {
                'type': 'text',
                'analyzer': NAME_ANALYZER_SYNONYMS,
                'search_analyzer': NAME_ANALYZER,
                'fields': {
                    'exacto': {
                        'type': 'keyword',
                        'normalizer': LOWCASE_ASCII_NORMALIZER
                    }
                }
            },
            'lat': {'type': 'keyword'},
            'lon': {'type': 'keyword'},
            'departamento': {
                'type': 'object',
                'dynamic': 'strict',
                'properties': {
                    'id': {'type': 'keyword'},
                    'nombre': {
                        'type': 'text',
                        'analyzer': NAME_ANALYZER_SYNONYMS,
                        'search_analyzer': NAME_ANALYZER,
                        'fields': {
                            'exacto': {
                                'type': 'keyword',
                                'normalizer': LOWCASE_ASCII_NORMALIZER
                            }
                        }
                    }
                }
            },
            'provincia': {
                'type': 'object',
                'dynamic': 'strict',
                'properties': {
                    'id': {'type': 'keyword'},
                    'nombre': {
                        'type': 'text',
                        'analyzer': NAME_ANALYZER_SYNONYMS,
                        'search_analyzer': NAME_ANALYZER,
                        'fields': {
                            'exacto': {
                                'type': 'keyword',
                                'normalizer': LOWCASE_ASCII_NORMALIZER
                            }
                        }
                    }
                }
            }
        }
    }
}

MAP_MUNI_GEOM = {
    'municipio': {
        'properties': {
            'id': {'type': 'keyword', 'index': False},
            'nombre': {'type': 'keyword', 'index': False},
            'lat': {'type': 'keyword', 'index': False},
            'lon': {'type': 'keyword', 'index': False},
            'departamento': {'type': 'object', 'enabled': False},
            'provincia': {'type': 'object', 'enabled': False},
            'geometria': {'type': 'geo_shape'}
        }
    }
}

MAP_SETTLEMENT = {
    'asentamiento': {
        'properties': {
            'id': {'type': 'keyword'},
            'nombre': {
                'type': 'text',
                'analyzer': NAME_ANALYZER_SYNONYMS,
                'search_analyzer': NAME_ANALYZER,
                'fields': {
                    'exacto': {
                        'type': 'keyword',
                        'normalizer': LOWCASE_ASCII_NORMALIZER
                    }
                }
            },
            'tipo': {'type': 'keyword'},
            'lat': {'type': 'keyword'},
            'lon': {'type': 'keyword'},
            'municipio': {
                'type': 'object',
                'dynamic': 'strict',
                'properties': {
                    'id': {'type': 'keyword'},
                    'nombre': {
                        'type': 'text',
                        'analyzer': NAME_ANALYZER_SYNONYMS,
                        'search_analyzer': NAME_ANALYZER,
                        'fields': {
                            'exacto': {
                                'type': 'keyword',
                                'normalizer': LOWCASE_ASCII_NORMALIZER
                            }
                        }
                    },
                }
            },
            'departamento': {
                'type': 'object',
                'dynamic': 'strict',
                'properties': {
                    'id': {'type': 'keyword'},
                    'nombre': {
                        'type': 'text',
                        'analyzer': NAME_ANALYZER_SYNONYMS,
                        'search_analyzer': NAME_ANALYZER,
                        'fields': {
                            'exacto': {
                                'type': 'keyword',
                                'normalizer': LOWCASE_ASCII_NORMALIZER
                            }
                        }
                    }
                }
            },
            'provincia': {
                'type': 'object',
                'dynamic': 'strict',
                'properties': {
                    'id': {'type': 'keyword'},
                    'nombre': {
                        'type': 'text',
                        'analyzer': NAME_ANALYZER_SYNONYMS,
                        'search_analyzer': NAME_ANALYZER,
                        'fields': {
                            'exacto': {
                                'type': 'keyword',
                                'normalizer': LOWCASE_ASCII_NORMALIZER
                            }
                        }
                    }
                }
            }
        }
    }
}

MAP_SETTLEMENT_GEOM = {
    'asentamiento': {
        'properties': {
            'id': {'type': 'keyword', 'index': False},
            'nombre': {'type': 'keyword', 'index': False},
            'tipo': {'type': 'keyword', 'index': False},
            'lat': {'type': 'keyword', 'index': False},
            'lon': {'type': 'keyword', 'index': False},
            'municipio': {'type': 'object', 'enabled': False},
            'departamento': {'type': 'object', 'enabled': False},
            'provincia': {'type': 'object', 'enabled': False},
            'geometria': {'type': 'geo_shape'}
        }
    }
}

MAP_STREET = {
    'calle': {
        'properties': {
            'nomenclatura': {
                'type': 'text',
                'index': False
            },
            'id': {'type': 'keyword'},
            'nombre': {
                'type': 'text',
                'analyzer': NAME_ANALYZER_SYNONYMS,
                'search_analyzer': NAME_ANALYZER,
                'fields': {
                    'exacto': {
                        'type': 'keyword',
                        'normalizer': LOWCASE_ASCII_NORMALIZER
                    }
                }
            },
            'tipo': {
                'type': 'text',
                'analyzer': NAME_ANALYZER_SYNONYMS,
                'search_analyzer': NAME_ANALYZER
            },
            'inicio_derecha': {
                'type': 'integer'
            },
            'inicio_izquierda': {
                'type': 'integer',
                # Solo START_R y END_L son necesarias para la busqueda de
                # calles por altura.
                'index': False
            },
            'fin_derecha': {
                'type': 'integer',
                # Solo START_R y END_L son necesarias para la busqueda de
                # calles por altura.
                'index': False
            },
            'fin_izquierda': {
                'type': 'integer'
            },
            'geometria': {
                'type': 'text',
                'index': False
            },
            'codigo_postal': {
                'type': 'text',
                'index': False
            },
            'provincia': {
                'type': 'text',
                'analyzer': NAME_ANALYZER_SYNONYMS,
                'search_analyzer': NAME_ANALYZER,
                'fields': {
                    'exacto': {
                        'type': 'keyword',
                        'normalizer': LOWCASE_ASCII_NORMALIZER
                    }
                }
            },
            'departamento': {
                'type': 'text',
                'analyzer': NAME_ANALYZER_SYNONYMS,
                'search_analyzer': NAME_ANALYZER,
                'fields': {
                    'exacto': {
                        'type': 'keyword',
                        'normalizer': LOWCASE_ASCII_NORMALIZER
                    }
                }
            }
        }
    }
}
