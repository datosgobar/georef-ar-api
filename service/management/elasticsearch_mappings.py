"""Mappeos de entidades para Elasticsearch.

El excluimiento del campo 'geometria' en _source se debe a que las geometrías
tienden a aumentar significativamente el tamaño de los documentos, por lo que
la performance de la búsqueda por id/texto/etc se ve disminuida. Para poder
contar con las geometrías originales (para queries GeoShape), se crean
índices adicionales con las geometrías originales.

Para más información, ver:
https://www.elastic.co/guide/en/elasticsearch/reference/current/general-recommendations.html#maximum-document-size

"""

from .elasticsearch_params import LOWCASE_ASCII_NORMALIZER
from .elasticsearch_params import NAME_ANALYZER
from .elasticsearch_params import NAME_ANALYZER_SYNONYMS

MAP_STATE = {
    '_doc': {
        '_source': {
            'excludes': ['geometria']
        },
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
            'geometria': {'type': 'geo_shape'},
            'centroide': {
                'type': 'object',
                'dynamic': 'strict',
                'properties': {
                    'lat': {'type': 'float', 'index': False},
                    'lon': {'type': 'float', 'index': False}
                }
            }
        }
    }
}

MAP_STATE_GEOM = {
    '_doc': {
        'properties': {
            'id': {'type': 'keyword'},
            'geometria': {'type': 'geo_shape'}
        }
    }
}

MAP_DEPT = {
    '_doc': {
        '_source': {
            'excludes': ['geometria']
        },
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
            'centroide': {
                'type': 'object',
                'dynamic': 'strict',
                'properties': {
                    'lat': {'type': 'float', 'index': False},
                    'lon': {'type': 'float', 'index': False}
                }
            },
            'geometria': {'type': 'geo_shape'},
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
            'id': {'type': 'keyword'},
            'geometria': {'type': 'geo_shape'}
        }
    }
}

MAP_MUNI = {
    '_doc': {
        '_source': {
            'excludes': ['geometria']
        },
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
            'geometria': {'type': 'geo_shape'},
            'centroide': {
                'type': 'object',
                'dynamic': 'strict',
                'properties': {
                    'lat': {'type': 'float', 'index': False},
                    'lon': {'type': 'float', 'index': False}
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
            'id': {'type': 'keyword'},
            'geometria': {'type': 'geo_shape'}
        }
    }
}

MAP_LOCALITY = {
    '_doc': {
        '_source': {
            'excludes': ['geometria']
        },
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
            'geometria': {'type': 'geo_shape'},
            'centroide': {
                'type': 'object',
                'dynamic': 'strict',
                'properties': {
                    'lat': {'type': 'float', 'index': False},
                    'lon': {'type': 'float', 'index': False}
                }
            },
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

MAP_STREET = {
    '_doc': {
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
            'altura': {
                'type': 'object',
                'dynamic': 'strict',
                'properties': {
                    'inicio': {
                        'type': 'object',
                        'dynamic': 'strict',
                        'properties': {
                            'derecha': {
                                'type': 'integer'
                            },
                            'izquierda': {
                                'type': 'integer'
                            }
                        }
                    },
                    'fin': {
                        'type': 'object',
                        'dynamic': 'strict',
                        'properties': {
                            'derecha': {
                                'type': 'integer'
                            },
                            'izquierda': {
                                'type': 'integer'
                            }
                        }
                    }
                }
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
