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


DEFAULT_SETTINGS = {
    'index': {
        'number_of_shards': 5,
        'number_of_replicas': 2
    },
    'analysis': {
        'filter': {
            SPANISH_STOP_FILTER: {
                'type': 'stop',
                'stopwords': SPANISH_STOP_WORDS
            },
            NAME_SYNONYMS_FILTER: {
                'type': 'synonym',
                'synonyms_path': 'georef_synonyms.txt'
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
