"""Definiciones de los analizadores, normalizadores y filtros utilizados en los
mappeos de entidades de Elasticsearch.
"""

SPANISH_STOP_WORDS = [
    'la', 'las', 'el', 'los', 'de', 'del', 'y', 'e', 'lo', 'al'
]


# Filters
SPANISH_STOP_FILTER = 'name_stop_spanish'
NAME_SYNONYMS_FILTER = 'name_synonyms'

# Normalizers
LOWCASE_ASCII_NORMALIZER = 'lowcase_ascii_normalizer'

# Analyzers
NAME_ANALYZER = 'name_analyzer'
NAME_ANALYZER_SYNONYMS = 'name_analyzer_synonyms'


def get_defaults(shards=5, replicas=2, synonyms=None):
    """Construye la configuración default para índices Elasticsearch de Georef.

    Args:
        shards (int): Número de 'shards' a utilizar.
        replicas (int): Número de réplicas a utilizar.
        synonyms (list): Lista de sinónimos a utilizar para el analizador de
            nombres.

    Returns:
        dict: Configuración para índice Elasticsearch.

    """
    if not synonyms:
        synonyms = []

    defaults = {
        'index': {
            'number_of_shards': shards,
            'number_of_replicas': replicas
        },
        'analysis': {
            'filter': {
                SPANISH_STOP_FILTER: {
                    'type': 'stop',
                    'stopwords': SPANISH_STOP_WORDS
                },
                NAME_SYNONYMS_FILTER: {
                    'type': 'synonym',
                    'synonyms': synonyms
                }
            },
            'normalizer': {
                LOWCASE_ASCII_NORMALIZER: {
                    'type': 'custom',
                    'filter': [
                        'lowercase',
                        'asciifolding'
                    ]
                }
            },
            'analyzer': {
                NAME_ANALYZER: {
                    'type': 'custom',
                    'tokenizer': 'standard',
                    'filter': [
                        'lowercase',
                        'asciifolding',
                        SPANISH_STOP_FILTER
                    ]
                },
                NAME_ANALYZER_SYNONYMS: {
                    'type': 'custom',
                    'tokenizer': 'standard',
                    'filter': [
                        'lowercase',
                        'asciifolding',
                        NAME_SYNONYMS_FILTER,
                        SPANISH_STOP_FILTER
                    ]
                }
            }
        }
    }

    return defaults
