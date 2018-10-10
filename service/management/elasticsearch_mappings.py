"""Mappeos de entidades para Elasticsearch
"""

import copy

from .elasticsearch_params import LOWCASE_ASCII_NORMALIZER
from .elasticsearch_params import NAME_ANALYZER
from .elasticsearch_params import NAME_ANALYZER_SYNONYMS


def with_geom(original):
    """Dado un mappeo de una entidad, crea una copia con un campo 'geometria'
    agregado.

    Por cada entidad geográfica con geometría, se crean dos mappeos: uno sin
    geometría y otro con. Esto se debe a que las geometría aumentan
    significativamente el tamaño de los documentos, lo cual hace que la
    performance de búsqueda por nombre/id/etc. se vea disminuida (incluso si no
    se incluye la geometría en los resultados). Una forma de evitar este
    problema es indexar las geometrías, pero no incluirlas en los documentos
    almacenados (utilizando _source 'excludes'). El problema de esta solución
    es que no permite utilizar queries como GeoShape con los datos indexados,
    ya que las geometrías originales se perdieron.

    Para más información, ver:
    https://www.elastic.co/guide/en/elasticsearch/reference/current/general-recommendations.html#maximum-document-size

    Args:
        original (dict): Mappeo Elasticsearch de una entidad.

    Returns:
        dict: Mappeo basado en el original, con campo 'geometria' adicional.

    """
    mapping = copy.deepcopy(original)
    mapping['_doc']['properties']['geometria'] = {
        'type': 'geo_shape'
    }

    return mapping


MAP_STATE = {
    '_doc': {
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
            }
        }
    }
}

MAP_STATE_GEOM = with_geom(MAP_STATE)

MAP_DEPT = {
    '_doc': {
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

MAP_DEPT_GEOM = with_geom(MAP_DEPT)

MAP_MUNI = {
    '_doc': {
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

MAP_MUNI_GEOM = with_geom(MAP_MUNI)

MAP_LOCALITY = {
    '_doc': {
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
