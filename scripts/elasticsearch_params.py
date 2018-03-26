from synonyms_entities import SYNONYMS_ENTITIES
from synonyms_roads import SYNONYMS_ROADS

INDEXES = ['provincias', 'departamentos', 'municipios', 'localidades', 'bahra']

# Uso General
SPANISH_STOP_FILTER = 'name_stop_spanish'
LOWCASE_ASCII_NORMALIZER = 'lowcase_ascii_normalizer'
NAME_ANALYZER = 'name_analyzer'
SPANISH_STOP_WORDS = [
    'la', 'las', 'el', 'los', 'de', 'del', 'y', 'e', 'lo', 'al', 'd'
]

# Entidades
ENTITY_NAME_SYNONYMS_FILTER = 'entity_name_synonyms'
NAME_ANALYZER_ENTITY_SYNONYMS = 'name_analyzer_entity_synonyms'

# Calles
ROAD_NAME_SYNONYMS_FILTER = 'road_name_synonyms'
NAME_ANALYZER_ROAD_SYNONYMS = 'name_analyzer_road_synonyms'


DEFAULT_SETTINGS = {
    'analysis': {
        'filter': {
            SPANISH_STOP_FILTER: {
                'type': 'stop',
                'stopwords': SPANISH_STOP_WORDS
            },
            ENTITY_NAME_SYNONYMS_FILTER: {
                'type': 'synonym',
                'synonyms': SYNONYMS_ENTITIES
            },
            ROAD_NAME_SYNONYMS_FILTER: {
                'type': 'synonym',
                'synonyms': SYNONYMS_ROADS
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
            NAME_ANALYZER_ENTITY_SYNONYMS: {
                'type': 'custom',
                'tokenizer': 'standard',
                'filter': [
                    'lowercase',
                    'asciifolding',
                    SPANISH_STOP_FILTER,
                    ENTITY_NAME_SYNONYMS_FILTER
                ]
            },
            NAME_ANALYZER_ROAD_SYNONYMS: {
                'type': 'custom',
                'tokenizer': 'standard',
                'filter': [
                    'lowercase',
                    'asciifolding',
                    SPANISH_STOP_FILTER,
                    ROAD_NAME_SYNONYMS_FILTER
                ]                
            }
        }
    }
}