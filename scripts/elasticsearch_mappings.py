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

TIMESTAMP = {
    'type': 'date',
    'format': 'epoch_second',
    'index': False
}

MAP_STATE = {
    '_doc': {
        'properties': {
            'id': {'type': 'keyword'},
            'timestamp': TIMESTAMP,
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
            'centroide_lat': {'type': 'float', 'index': False},
            'centroide_lon': {'type': 'float', 'index': False}
        }
    }
}

MAP_STATE_GEOM = {
    '_doc': {
        'properties': {
            'id': {'type': 'keyword', 'index': False},
            'timestamp': TIMESTAMP,
            'nombre': {'type': 'keyword', 'index': False},
            'centroide_lat': {'type': 'float', 'index': False},
            'centroide_lon': {'type': 'float', 'index': False},
            'geometria': {'type': 'geo_shape'}
        }
    }
}

MAP_DEPT = {
    '_doc': {
        'properties': {
            'id': {'type': 'keyword'},
            'timestamp': TIMESTAMP,
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
            'centroide_lat': {'type': 'float', 'index': False},
            'centroide_lon': {'type': 'float', 'index': False},
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
    '_doc': {
        'properties': {
            'id': {'type': 'keyword', 'index': False},
            'timestamp': TIMESTAMP,
            'nombre': {'type': 'keyword', 'index': False},
            'centroide_lat': {'type': 'float', 'index': False},
            'centroide_lon': {'type': 'float', 'index': False},
            'provincia': {'type': 'object', 'enabled': False},
            'geometria': {'type': 'geo_shape'}
        }
    }
}

MAP_MUNI = {
    '_doc': {
        'properties': {
            'id': {'type': 'keyword'},
            'timestamp': TIMESTAMP,
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
            'centroide_lat': {'type': 'float', 'index': False},
            'centroide_lon': {'type': 'float', 'index': False},
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
    '_doc': {
        'properties': {
            'id': {'type': 'keyword', 'index': False},
            'timestamp': TIMESTAMP,
            'nombre': {'type': 'keyword', 'index': False},
            'centroide_lat': {'type': 'float', 'index': False},
            'centroide_lon': {'type': 'float', 'index': False},
            'departamento': {'type': 'object', 'enabled': False},
            'provincia': {'type': 'object', 'enabled': False},
            'geometria': {'type': 'geo_shape'}
        }
    }
}

MAP_SETTLEMENT = {
    '_doc': {
        'properties': {
            'id': {'type': 'keyword'},
            'timestamp': TIMESTAMP,
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
            'centroide_lat': {'type': 'float', 'index': False},
            'centroide_lon': {'type': 'float', 'index': False},
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
    '_doc': {
        'properties': {
            'id': {'type': 'keyword', 'index': False},
            'timestamp': TIMESTAMP,
            'nombre': {'type': 'keyword', 'index': False},
            'tipo': {'type': 'keyword', 'index': False},
            'centroide_lat': {'type': 'float', 'index': False},
            'centroide_lon': {'type': 'float', 'index': False},
            'municipio': {'type': 'object', 'enabled': False},
            'departamento': {'type': 'object', 'enabled': False},
            'provincia': {'type': 'object', 'enabled': False},
            'geometria': {'type': 'geo_shape'}
        }
    }
}

MAP_STREET = {
    '_doc': {
        'properties': {
            'nomenclatura': {
                'type': 'text',
                'index': False
            },
            'id': {'type': 'keyword'},
            'timestamp': TIMESTAMP,
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
            'altura_inicio_derecha': {
                'type': 'integer'
            },
            'altura_inicio_izquierda': {
                'type': 'integer'
            },
            'altura_fin_derecha': {
                'type': 'integer'
            },
            'altura_fin_izquierda': {
                'type': 'integer'
            },
            'geometria': {
                'type': 'text',
                'index': False
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
